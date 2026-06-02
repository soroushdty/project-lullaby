from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from src.modeling.bakeoff import run_bakeoff
from src.modeling.datasets import ModelingDataError, build_modeling_dataset


REQUIRED_OUTPUTS = {
    "predictions_oof.csv",
    "predictions_by_fold.csv",
    "metrics_by_fold.csv",
    "metrics_summary.csv",
    "operating_points.csv",
    "calibration_table.csv",
    "decision_curve.csv",
    "bakeoff_config_used.yaml",
    "bakeoff_summary.json",
}


def test_dataset_role_resolution_participant_level_and_leakage_guard(default_modeling_config):
    dataset = build_modeling_dataset("data/synthetic/longitudinal", default_modeling_config)

    assert len(dataset.participant_ids) == len(set(dataset.participant_ids))
    assert dataset.observation_ids == dataset.participant_ids
    assert dataset.y.sum() > 0
    assert "vital_systolic_bp_mean" in dataset.features.columns
    assert dataset.metadata["synthetic_detected"] is True


def test_dataset_validation_rejects_one_class(tmp_path, default_modeling_config):
    source = Path("data/synthetic/longitudinal")
    for path in source.glob("*.csv"):
        (tmp_path / path.name).write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    outcomes = pd.read_csv(tmp_path / "clinical_outcomes.csv")
    outcomes["cv_event"] = False
    outcomes.to_csv(tmp_path / "clinical_outcomes.csv", index=False)

    with pytest.raises(ModelingDataError, match="at least two classes"):
        build_modeling_dataset(tmp_path, default_modeling_config)


def test_bakeoff_writes_required_outputs_and_schemas(tmp_path, fast_modeling_config_path):
    out_dir = tmp_path / "modeling"

    summary = run_bakeoff(
        config_path=fast_modeling_config_path,
        data_dir="data/synthetic/longitudinal",
        out_dir=out_dir,
        seed=20260601,
    )

    assert REQUIRED_OUTPUTS.issubset({path.name for path in out_dir.iterdir()})
    assert REQUIRED_OUTPUTS.issubset(set(summary["artifact_paths"]))
    predictions = pd.read_csv(out_dir / "predictions_oof.csv")
    assert list(predictions.columns) == [
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
    assert predictions["y_score"].between(0, 1).all()
    metrics = pd.read_csv(out_dir / "metrics_summary.csv")
    assert {"model_id", "metric", "mean", "sd", "ci_lower", "ci_upper", "n_folds", "n_repeats", "primary_metric", "notes"} == set(metrics.columns)
    operating = pd.read_csv(out_dir / "operating_points.csv")
    assert {"model_id", "threshold", "precision", "recall", "specificity", "false_positive_rate", "alerts_per_100_participant_days", "number_needed_to_alert", "estimated_calls"} == set(operating.columns)


def test_bakeoff_is_reproducible_by_seed(tmp_path, fast_modeling_config_path):
    out_a = tmp_path / "a"
    out_b = tmp_path / "b"

    run_bakeoff(config_path=fast_modeling_config_path, data_dir="data/synthetic/longitudinal", out_dir=out_a, seed=20260601)
    run_bakeoff(config_path=fast_modeling_config_path, data_dir="data/synthetic/longitudinal", out_dir=out_b, seed=20260601)

    assert (out_a / "predictions_oof.csv").read_text(encoding="utf-8") == (out_b / "predictions_oof.csv").read_text(encoding="utf-8")
    assert (out_a / "metrics_summary.csv").read_text(encoding="utf-8") == (out_b / "metrics_summary.csv").read_text(encoding="utf-8")


def test_summary_frames_synthetic_runs_as_signal_characterization(tmp_path, fast_modeling_config_path):
    out_dir = tmp_path / "modeling"

    run_bakeoff(config_path=fast_modeling_config_path, data_dir="data/synthetic/longitudinal", out_dir=out_dir, seed=20260601)
    summary = json.loads((out_dir / "bakeoff_summary.json").read_text(encoding="utf-8"))

    assert summary["synthetic_detected"] is True
    assert any("signal characterization" in item for item in summary["limitations"])
    assert any("not validated clinical performance" in item for item in summary["limitations"])
    assert any("class_weight" in warning for warning in summary["warnings"])


def test_cli_raw_data_fallback_succeeds(tmp_path):
    out_dir = tmp_path / "raw_modeling"

    summary = run_bakeoff(config_path="config/modeling.yaml", data_dir="data/raw", out_dir=out_dir, seed=20260601)

    assert summary["n_participants"] > 0
    assert any("resolved default raw-data path" in warning for warning in summary["warnings"])
