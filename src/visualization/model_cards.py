"""SPEC-012: TRIPOD-AI model card generator for the analytic dashboard."""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import yaml


_REQUIRED_SECTIONS = [
    "Intended Use",
    "Data Source",
    "Participants and Outcome Definition",
    "Candidate Models",
    "Validation Design",
    "Leakage Prevention",
    "Missing Data Handling",
    "Class Imbalance Handling",
    "Metrics and Uncertainty",
    "Calibration",
    "Subgroup Assessment",
    "Limitations",
    "Synthetic-Data Caveat",
    "Reproducibility Command",
]


def generate_tripod_ai_card(
    model_dir: Path | str,
    data_dir: Path | str,
    cost_config_path: Path | str | None,
    out_path: Path | str,
) -> Path:
    model_dir = Path(model_dir)
    data_dir = Path(data_dir)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    summary = _load_json(model_dir / "bakeoff_summary.json")
    config_used = _load_yaml(model_dir / "bakeoff_config_used.yaml")
    metrics = _load_csv_text(model_dir / "metrics_summary.csv")
    is_synthetic = _is_synthetic(model_dir, summary)

    config_note = str(model_dir / "bakeoff_config_used.yaml") if (model_dir / "bakeoff_config_used.yaml").exists() else "bakeoff_config_used.yaml not found"
    cost_note = str(cost_config_path) if cost_config_path and Path(cost_config_path).exists() else "costs.yaml not provided"

    seed = summary.get("seed", config_used.get("seed", "see bakeoff_config_used.yaml")) if (summary or config_used) else "see bakeoff_config_used.yaml"
    models_trained = summary.get("models_trained", list(config_used.get("models", {}).keys()) if config_used else []) if summary else []
    n_participants = summary.get("n_participants", "see bakeoff_summary.json") if summary else "see bakeoff_summary.json"
    n_events = summary.get("n_events", "see bakeoff_summary.json") if summary else "see bakeoff_summary.json"
    run_ts = summary.get("run_timestamp", "see bakeoff_summary.json") if summary else "see bakeoff_summary.json"

    lines: list[str] = []
    lines += [
        "---",
        "id: TRIPOD-AI-CARD-012",
        "spec: SPEC-012",
        f"generated: {datetime.now(UTC).strftime('%Y-%m-%d')}",
        f"model_dir: {model_dir}",
        f"data_dir: {data_dir}",
        f"config: {config_note}",
        f"costs: {cost_note}",
        "---",
        "",
        "# TRIPOD-AI Model Card — Lullaby Postpartum CV Risk Bake-off",
        "",
    ]

    lines += [
        "## Intended Use",
        "",
        "This model card describes candidate risk-prediction models evaluated for postpartum",
        "cardiovascular (CV) event signal characterization in the Project Lullaby study cohort.",
        "The primary purpose is exploratory signal characterization: identifying which model",
        "families and feature sets best separate participants who experienced a CV composite",
        "event from those who did not, in a severely class-imbalanced synthetic cohort.",
        "These models are **not validated for clinical deployment**. Outputs must be treated",
        "as research signal, not clinical decision support.",
        "",
    ]

    lines += [
        "## Data Source",
        "",
        f"- Data directory: `{data_dir}`",
        f"- Model outputs directory: `{model_dir}`",
        f"- Bake-off run timestamp: {run_ts}",
        f"- Configuration file: `{config_note}`",
        "",
    ]

    lines += [
        "## Participants and Outcome Definition",
        "",
        f"- Participants: {n_participants}",
        f"- Confirmed CV composite events: {n_events}",
        "- Target role: `outcome.cv_event` (binary; 1 = confirmed CV composite event)",
        "- Modeling unit: one row per participant (participant-level, not observation-level)",
        "- Observation window: full observed window for non-event participants;",
        "  truncated before `cv_event_date − leakage_guard_days` for event participants",
        "",
    ]

    model_list = "\n".join(f"- `{m}`" for m in models_trained) if models_trained else "- see bakeoff_summary.json"
    lines += [
        "## Candidate Models",
        "",
        model_list,
        "",
        "Each candidate is trained inside participant-grouped stratified cross-validation folds.",
        "The MEOWS-rules logistic regression serves as the transparent clinical baseline.",
        "",
    ]

    lines += [
        "## Validation Design",
        "",
        "- Strategy: participant-grouped stratified k-fold cross-validation",
        "- Folds and repeats: see `bakeoff_config_used.yaml`",
        "- Grouping: by `participant.id` — each participant appears in exactly one side of",
        "  each fold (training or validation, never both)",
        "- Stratification: by event label where the participant-group constraint permits",
        "- Out-of-fold predictions aggregated across all folds and repeats",
        "",
    ]

    lines += [
        "## Leakage Prevention",
        "",
        "- No participant contributes records to both training and validation in any fold",
        "- Preprocessing (scaling, imputation), threshold selection, and any resampling",
        "  are performed exclusively within each fold's training pipeline",
        "- Feature summaries for event participants use only observations strictly before",
        "  `cv_event_date − leakage_guard_days_before_event`",
        "- Raw EDA tables are never modified by the modeling pipeline",
        "",
    ]

    lines += [
        "## Missing Data Handling",
        "",
        "- Imputation is performed inside fold-local training pipelines only",
        "- Missing optional feature groups are excluded rather than imputed with constants",
        "- Participants with no pre-event observations (after leakage guard) are retained",
        "  with unavailable longitudinal feature summaries",
        "",
    ]

    lines += [
        "## Class Imbalance Handling",
        "",
        "- Class weights: balanced (inverse-frequency weighting) for all classifiers",
        "- Resampling: none (resampling before the CV split is prohibited)",
        "- Threshold selection: inner-CV — maximize recall subject to precision ≥ 0.80;",
        "  ties broken by higher precision then higher threshold",
        "",
    ]

    lines += [
        "## Metrics and Uncertainty",
        "",
        "**Headline metrics** (primary, imbalance-appropriate):",
        "- AUPRC (Area Under Precision-Recall Curve)",
        "- Recall at fixed precision ≥ 0.80",
        "- Brier score",
        "",
        "**Secondary metric** (not headline):",
        "- AUROC — reported for context only",
        "",
        "**Accuracy is not reported as a headline metric.**",
        "",
        "Confidence intervals are bootstrapped over fold/repeat metric values.",
        "All per-fold and per-repeat values are reported before aggregation.",
        "",
    ]

    if metrics:
        lines += [
            "<details><summary>Metrics summary (from metrics_summary.csv)</summary>",
            "",
            "```",
            metrics[:3000],
            "```",
            "",
            "</details>",
            "",
        ]

    lines += [
        "## Calibration",
        "",
        "- Calibration diagnostics: intercept, slope, and Brier score per model",
        "- Expected calibration error reported where implemented",
        "- Calibration artifacts: `calibration_table.csv` in model directory",
        "- Decision-curve net benefit: `decision_curve.csv` in model directory",
        "- Sparse calibration bins (< 3 non-empty or any bin < 10 samples) are",
        "  flagged as insufficient for reliable calibration belt estimation",
        "",
    ]

    lines += [
        "## Subgroup Assessment",
        "",
        "- Subgroup fairness audit: Panel 9 of the analytic dashboard",
        "- Subgroups assessed where columns available: race/ethnicity, insurance,",
        "  AC access, health literacy",
        "- Sparse-subgroup warning: N < 10 in subgroup → metric suppressed",
        "- Overinterpretation warning: positive events < 3 in subgroup → caution annotation",
        "- Denominators (N and positive-event count) are shown for every subgroup",
        "",
    ]

    lines += [
        "## Limitations",
        "",
        "- Class imbalance is severe; metric confidence intervals are wide",
        "- Sample size is small; generalizability is uncertain",
        "- Feature coverage depends on data availability and leakage-guard truncation",
        "- Deep sequence models are not evaluated in this bake-off run (disabled by default)",
        "- Threshold selection uses a fixed minimum-precision target; performance at other",
        "  operating points may differ substantially",
        "- Results should not be used to make clinical decisions",
        "",
    ]

    if is_synthetic:
        lines += [
            "## Synthetic-Data Caveat",
            "",
            "⚠️ **All results in this card were produced on bundled synthetic data.**",
            "",
            "The synthetic dataset was generated to match the structural properties of the",
            "Project Lullaby study design but does not represent real patient records.",
            "Performance metrics, calibration estimates, and operating points reported here",
            "reflect synthetic-data signal characterization only and **do not constitute",
            "validated clinical performance** on any real population.",
            "",
        ]
    else:
        lines += [
            "## Synthetic-Data Caveat",
            "",
            "This run used non-synthetic data. All results are candidate-model",
            "characterization and have not been validated for clinical deployment.",
            "",
        ]

    lines += [
        "## Reproducibility Command",
        "",
        f"```bash",
        f"python scripts/run_model_bakeoff.py \\",
        f"  --config {config_note} \\",
        f"  --data-dir {data_dir} \\",
        f"  --out-dir {model_dir} \\",
        f"  --seed {seed}",
        "```",
        "",
        "Dashboard regeneration:",
        "",
        "```bash",
        "python -m src.visualization.analytic_dashboard \\",
        f"  --model-dir {model_dir} \\",
        f"  --data-dir {data_dir} \\",
        "  --out-dir outputs/figures/analytic \\",
        f"  --cost-config {cost_note}",
        "```",
        "",
    ]

    out_path.write_text("\n".join(lines))
    return out_path


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return yaml.safe_load(path.read_text()) or {}
    except Exception:
        return {}


def _load_csv_text(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text()
    except Exception:
        return ""


def _is_synthetic(model_dir: Path, summary: dict) -> bool:
    if summary.get("data_source") == "synthetic":
        return True
    return "synthetic" in str(model_dir).lower()


TRIPOD_AI_REQUIRED_SECTIONS = _REQUIRED_SECTIONS

__all__ = ["TRIPOD_AI_REQUIRED_SECTIONS", "generate_tripod_ai_card"]
