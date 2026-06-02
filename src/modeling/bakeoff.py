from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json

import numpy as np
import pandas as pd
import yaml

from src.modeling.calibration import calibration_record
from src.modeling.datasets import ModelingDataError, ModelingDataset, build_modeling_dataset
from src.modeling.explainability import feature_importance_rows, local_explanation_notes
from src.modeling.metrics import decision_curve, metric_records, operating_points, select_threshold, summarize_metrics
from src.modeling.models import ModelError, enabled_model_specs, make_pipeline
from src.modeling.splits import SplitError, make_repeated_grouped_stratified_splits


class BakeoffError(ValueError):
    """Raised when the bake-off cannot complete."""


@dataclass
class ModelingConfig:
    path: Path
    values: dict[str, Any]


def load_config(config_path: str | Path, *, seed_override: int | None = None) -> ModelingConfig:
    path = Path(config_path)
    if not path.exists():
        raise BakeoffError(f"Config file does not exist: {path}")
    with path.open("r", encoding="utf-8") as handle:
        values = yaml.safe_load(handle) or {}
    if seed_override is not None:
        values["seed"] = int(seed_override)
    _validate_config(values)
    return ModelingConfig(path=path, values=values)


def _validate_config(values: dict[str, Any]) -> None:
    required = ["seed", "target", "participant_id_role", "cv", "features", "imbalance", "metrics", "models"]
    missing = [key for key in required if key not in values]
    if missing:
        raise BakeoffError(f"Missing config keys: {missing}")
    cv = values["cv"]
    if cv.get("strategy") != "stratified_group_kfold":
        raise BakeoffError("Only cv.strategy=stratified_group_kfold is supported")
    if int(cv.get("n_splits", 0)) < 2 or int(cv.get("n_repeats", 0)) < 1:
        raise BakeoffError("cv.n_splits must be >=2 and cv.n_repeats must be >=1")
    imbalance = values["imbalance"]
    if imbalance.get("resampling", "none") != "none":
        raise BakeoffError("SPEC-011 MVP supports resampling: none only")
    if not imbalance.get("resampling_allowed_inside_fold_only", False):
        raise BakeoffError("resampling_allowed_inside_fold_only must be true")


def _participant_days(dataset: ModelingDataset) -> float:
    if "vital_sensor_wear_hours_observed_days" in dataset.features.columns:
        return float(dataset.features["vital_sensor_wear_hours_observed_days"].fillna(0).sum())
    if "feature_window_observed_rows" in dataset.features.columns:
        return float(dataset.features["feature_window_observed_rows"].fillna(0).sum())
    return float(len(dataset.participant_ids) * 84)


def _empty_outputs(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for filename in [
        "predictions_oof.csv",
        "predictions_by_fold.csv",
        "metrics_by_fold.csv",
        "metrics_summary.csv",
        "operating_points.csv",
        "calibration_table.csv",
        "decision_curve.csv",
        "feature_importance.csv",
        "local_explanations.csv",
        "bakeoff_config_used.yaml",
        "bakeoff_summary.json",
    ]:
        path = out_dir / filename
        if path.exists():
            path.unlink()


def _write_csv(path: Path, rows: list[dict[str, object]] | pd.DataFrame, columns: list[str] | None = None) -> None:
    frame = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)
    if columns is not None:
        for column in columns:
            if column not in frame.columns:
                frame[column] = np.nan
        frame = frame[columns]
    frame.to_csv(path, index=False)


def run_bakeoff(
    *,
    config_path: str | Path,
    data_dir: str | Path,
    out_dir: str | Path,
    seed: int | None = None,
) -> dict[str, Any]:
    config = load_config(config_path, seed_override=seed)
    values = config.values
    run_seed = int(values["seed"])
    output_dir = Path(out_dir)
    _empty_outputs(output_dir)
    try:
        dataset = build_modeling_dataset(data_dir, values)
        assignments = make_repeated_grouped_stratified_splits(
            dataset.participant_ids,
            dataset.y,
            n_splits=int(values["cv"]["n_splits"]),
            n_repeats=int(values["cv"]["n_repeats"]),
            seed=run_seed,
        )
        model_specs = enabled_model_specs(values)
    except (ModelingDataError, SplitError, ModelError) as exc:
        raise BakeoffError(str(exc)) from exc

    min_precision = float(values["metrics"].get("recall_at_precision", {}).get("min_precision", 0.80))
    class_weight = values["imbalance"].get("class_weight", None)
    predictions: list[dict[str, object]] = []
    prediction_details: list[dict[str, object]] = []
    metric_rows: list[dict[str, object]] = []
    calibration_rows: list[dict[str, object]] = []
    feature_rows: list[dict[str, object]] = []
    warnings: list[str] = list(dataset.metadata.get("load_warnings", []))
    for assignment in assignments:
        warnings.extend(assignment.warnings)
        x_train = dataset.features.iloc[assignment.train_indices].copy()
        y_train = dataset.y[assignment.train_indices]
        x_val = dataset.features.iloc[assignment.validation_indices].copy()
        y_val = dataset.y[assignment.validation_indices]
        for spec in model_specs:
            model_seed = run_seed + assignment.repeat * 1000 + assignment.fold * 100 + sum(ord(c) for c in spec.model_id)
            pipeline = make_pipeline(spec, seed=model_seed, class_weight=class_weight)
            fit_status = "trained"
            unavailable_reason = ""
            try:
                pipeline.fit(x_train, y_train)
                train_scores = pipeline.predict_scores(x_train)
                val_scores = pipeline.predict_scores(x_val)
                warnings.extend(f"{spec.model_id} repeat {assignment.repeat} fold {assignment.fold}: {note}" for note in pipeline.notes)
            except ModelError as exc:
                fit_status = "unavailable"
                unavailable_reason = str(exc)
                val_scores = np.full(len(y_val), np.nan)
                train_scores = np.full(len(y_train), np.nan)
                warnings.append(f"{spec.model_id} repeat {assignment.repeat} fold {assignment.fold}: {exc}")
            threshold = select_threshold(y_train, train_scores, min_precision=min_precision)
            if threshold.notes:
                warnings.append(f"{spec.model_id} repeat {assignment.repeat} fold {assignment.fold}: {threshold.notes}")
            for local_idx, score, true in zip(assignment.validation_indices, val_scores, y_val):
                base = {
                    "participant_id": dataset.participant_ids[int(local_idx)],
                    "observation_id": dataset.observation_ids[int(local_idx)],
                    "fold": assignment.fold,
                    "repeat": assignment.repeat,
                    "model_id": spec.model_id,
                    "y_true": int(true),
                    "y_score": float(score) if np.isfinite(score) else np.nan,
                    "y_pred_default_threshold": int(score >= 0.5) if np.isfinite(score) else "",
                    "y_pred_selected_threshold": int(score >= threshold.threshold) if np.isfinite(score) else "",
                    "selected_threshold": threshold.threshold,
                }
                predictions.append(base)
                detail = dict(base)
                detail.update(
                    {
                        "threshold_target_met": threshold.target_met,
                        "fit_status": fit_status,
                        "unavailable_reason": unavailable_reason,
                        "threshold_notes": threshold.notes,
                    }
                )
                prediction_details.append(detail)
            if fit_status == "trained":
                metric_rows.extend(
                    metric_records(
                        model_id=spec.model_id,
                        repeat=assignment.repeat,
                        fold=assignment.fold,
                        y_true=y_val,
                        y_score=val_scores,
                        min_precision=min_precision,
                    )
                )
                calibration_rows.append(calibration_record(spec.model_id, assignment.repeat, assignment.fold, y_val, val_scores))
                feature_rows.extend(feature_importance_rows(spec.model_id, assignment.repeat, assignment.fold, pipeline.feature_importance()))

    pred_df = pd.DataFrame(predictions).sort_values(["model_id", "repeat", "fold", "participant_id", "observation_id"])
    detail_df = pd.DataFrame(prediction_details).sort_values(["model_id", "repeat", "fold", "participant_id", "observation_id"])
    metrics_df = pd.DataFrame(metric_rows).sort_values(["model_id", "repeat", "fold", "metric"])
    ci_cfg = values["metrics"].get("bootstrap_ci", {})
    summary_df = summarize_metrics(
        metrics_df,
        n_bootstrap=int(ci_cfg.get("n_bootstrap", 1000)),
        level=float(ci_cfg.get("level", 0.95)),
        seed=run_seed,
    ).sort_values(["model_id", "primary_metric", "metric"], ascending=[True, False, True])
    calibration_df = pd.DataFrame(calibration_rows).sort_values(["model_id", "repeat", "fold"])
    thresholds = [0.5]
    if not pred_df.empty:
        thresholds.extend(pred_df["selected_threshold"].dropna().astype(float).unique().tolist())
        thresholds.extend([0.1, 0.2, 0.8])
    operating_df = operating_points(pred_df, participant_days=_participant_days(dataset), thresholds=thresholds)
    decision_df = decision_curve(pred_df, thresholds=thresholds)

    pred_cols = [
        "participant_id",
        "observation_id",
        "fold",
        "repeat",
        "model_id",
        "y_true",
        "y_score",
        "y_pred_default_threshold",
        "y_pred_selected_threshold",
        "selected_threshold",
    ]
    _write_csv(output_dir / "predictions_oof.csv", pred_df, pred_cols)
    _write_csv(output_dir / "predictions_by_fold.csv", detail_df)
    _write_csv(output_dir / "metrics_by_fold.csv", metrics_df)
    _write_csv(
        output_dir / "metrics_summary.csv",
        summary_df,
        ["model_id", "metric", "mean", "sd", "ci_lower", "ci_upper", "n_folds", "n_repeats", "primary_metric", "notes"],
    )
    _write_csv(output_dir / "operating_points.csv", operating_df)
    _write_csv(output_dir / "calibration_table.csv", calibration_df)
    _write_csv(output_dir / "decision_curve.csv", decision_df)
    if feature_rows:
        _write_csv(output_dir / "feature_importance.csv", pd.DataFrame(feature_rows).sort_values(["model_id", "rank", "feature"]))

    local_notes = local_explanation_notes([spec.model_id for spec in model_specs])
    if local_notes:
        warnings.extend(local_notes)

    with (output_dir / "bakeoff_config_used.yaml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(values, handle, sort_keys=False)

    limitations = [
        "Results are exploratory signal characterization, not validated clinical performance.",
    ]
    if dataset.metadata.get("synthetic_detected"):
        limitations.append("Input data are synthetic; metrics must not be interpreted as clinical validation.")
    artifact_paths = sorted(path.name for path in output_dir.iterdir() if path.is_file())
    if "bakeoff_summary.json" not in artifact_paths:
        artifact_paths.append("bakeoff_summary.json")
        artifact_paths = sorted(artifact_paths)
    summary = {
        "run_started_at": datetime.now(timezone.utc).isoformat(),
        "seed": run_seed,
        "data_dir": str(data_dir),
        "out_dir": str(output_dir),
        "synthetic_detected": bool(dataset.metadata.get("synthetic_detected")),
        "n_participants": int(dataset.metadata["n_participants"]),
        "n_events": int(dataset.metadata["n_events"]),
        "enabled_models": [spec.model_id for spec in model_specs],
        "primary_metrics": values["metrics"].get("primary", []),
        "warnings": sorted(set(warnings)),
        "limitations": limitations,
        "artifact_paths": artifact_paths,
    }
    with (output_dir / "bakeoff_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
    return summary
