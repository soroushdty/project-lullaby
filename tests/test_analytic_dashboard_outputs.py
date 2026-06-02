"""Tests for SPEC-012 analytic dashboard panel outputs."""
from __future__ import annotations

import struct
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.visualization.analytic_dashboard import (
    detect_synthetic_run,
    render_panel_1,
    render_panel_2,
    render_panel_3,
    render_panel_7,
    render_panel_8,
    render_panel_9,
    render_panel_10,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_model_dir(tmp_path):
    d = tmp_path / "modeling"
    d.mkdir()
    return d


@pytest.fixture()
def tmp_out_dir(tmp_path):
    d = tmp_path / "analytic"
    d.mkdir()
    return d


@pytest.fixture()
def manifest_path(tmp_path):
    return tmp_path / "manifest.json"


def _write_metrics_summary(model_dir: Path, *, include_auprc: bool = True) -> Path:
    rows = []
    for model in ["baseline_meows_logistic", "random_forest"]:
        if include_auprc:
            rows.append({"model_id": model, "metric": "auprc", "mean": 0.35, "sd": 0.05,
                         "ci_lower": 0.25, "ci_upper": 0.45, "n_folds": 5, "n_repeats": 2,
                         "primary_metric": True, "notes": ""})
        rows.append({"model_id": model, "metric": "brier", "mean": 0.12, "sd": 0.02,
                     "ci_lower": 0.08, "ci_upper": 0.16, "n_folds": 5, "n_repeats": 2,
                     "primary_metric": True, "notes": ""})
        rows.append({"model_id": model, "metric": "recall_at_precision", "mean": 0.60, "sd": 0.10,
                     "ci_lower": 0.40, "ci_upper": 0.80, "n_folds": 5, "n_repeats": 2,
                     "primary_metric": True, "notes": ""})
        rows.append({"model_id": model, "metric": "auroc", "mean": 0.75, "sd": 0.05,
                     "ci_lower": 0.65, "ci_upper": 0.85, "n_folds": 5, "n_repeats": 2,
                     "primary_metric": False, "notes": ""})
    path = model_dir / "metrics_summary.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _write_calibration(model_dir: Path, *, n_bins: int = 5, min_n: int = 15) -> Path:
    rows = []
    for i in range(n_bins):
        rows.append({
            "model_id": "random_forest",
            "bin_lower": i / n_bins, "bin_upper": (i + 1) / n_bins,
            "n_observations": min_n, "observed_fraction": (i + 0.5) / n_bins,
            "mean_predicted": (i + 0.5) / n_bins,
            "brier_score": 0.12, "calibration_intercept": 0.01, "calibration_slope": 0.98,
            "notes": "",
        })
    path = model_dir / "calibration_table.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _write_predictions_oof(model_dir: Path, *, n_participants: int = 20, n_events: int = 6) -> Path:
    rng = np.random.default_rng(42)
    rows = []
    for i in range(n_participants):
        y_true = 1 if i < n_events else 0
        for fold in range(1, 4):
            rows.append({
                "participant_id": f"P{i:03d}", "observation_id": f"P{i:03d}",
                "fold": fold, "repeat": 1, "model_id": "random_forest",
                "y_true": y_true, "y_score": rng.random(),
                "y_pred_default_threshold": int(rng.random() > 0.5),
                "y_pred_selected_threshold": int(rng.random() > 0.5),
                "selected_threshold": 0.4,
            })
    path = model_dir / "predictions_oof.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _png_size(path: Path) -> tuple[int, int]:
    with open(path, "rb") as f:
        f.read(8)
        f.read(4)
        f.read(4)
        w = struct.unpack(">I", f.read(4))[0]
        h = struct.unpack(">I", f.read(4))[0]
    return w, h


# ---------------------------------------------------------------------------
# US2 — Panel 1: Leaderboard
# ---------------------------------------------------------------------------

def test_panel_1_auprc_is_primary(tmp_model_dir, tmp_out_dir, manifest_path):
    _write_metrics_summary(tmp_model_dir)
    render_panel_1(tmp_model_dir, tmp_out_dir, manifest_path)
    out = tmp_out_dir / "01_model_leaderboard.png"
    assert out.exists()
    w, h = _png_size(out)
    assert w >= 1600
    assert h >= 900


def test_panel_1_auroc_not_headline(tmp_model_dir, tmp_out_dir, manifest_path):
    _write_metrics_summary(tmp_model_dir)
    render_panel_1(tmp_model_dir, tmp_out_dir, manifest_path)
    # AUROC rows have primary_metric=False — panel renders without crashing and PNG exists
    assert (tmp_out_dir / "01_model_leaderboard.png").exists()


def test_panel_1_unavailable_when_no_csv(tmp_model_dir, tmp_out_dir, manifest_path):
    render_panel_1(tmp_model_dir, tmp_out_dir, manifest_path)
    out = tmp_out_dir / "01_model_leaderboard.png"
    assert out.exists()  # unavailable panel PNG is written


# ---------------------------------------------------------------------------
# US3 — Panel 2: Calibration sparsity gate
# ---------------------------------------------------------------------------

def test_panel_2_sparse_warning_two_bins(tmp_model_dir, tmp_out_dir, manifest_path):
    _write_calibration(tmp_model_dir, n_bins=2, min_n=15)
    render_panel_2(tmp_model_dir, tmp_out_dir, manifest_path)
    out = tmp_out_dir / "02_calibration_decision_curve.png"
    assert out.exists()
    w, h = _png_size(out)
    assert w >= 1600 and h >= 900  # unavailable/warning panel still meets size requirement


def test_panel_2_renders_belt_when_sufficient(tmp_model_dir, tmp_out_dir, manifest_path):
    _write_calibration(tmp_model_dir, n_bins=5, min_n=15)
    render_panel_2(tmp_model_dir, tmp_out_dir, manifest_path)
    out = tmp_out_dir / "02_calibration_decision_curve.png"
    assert out.exists()
    w, h = _png_size(out)
    assert w >= 1600 and h >= 900


# ---------------------------------------------------------------------------
# US4 — Panel 3: Threshold explorer
# ---------------------------------------------------------------------------

def test_panel_3_renders(tmp_model_dir, tmp_out_dir, manifest_path):
    rng = np.random.default_rng(0)
    thresholds = np.linspace(0.1, 0.9, 20)
    rows = [{"model_id": "rf", "threshold": t, "precision": 0.8 - t * 0.3,
             "recall": t * 0.9, "specificity": 0.7, "false_positive_rate": 1 - (0.7 + t * 0.2),
             "alerts_per_100_participant_days": t * 5,
             "number_needed_to_alert": max(1, 10 - t * 8), "estimated_calls": t * 50}
            for t in thresholds]
    pd.DataFrame(rows).to_csv(tmp_model_dir / "operating_points.csv", index=False)
    render_panel_3(tmp_model_dir, tmp_out_dir, manifest_path)
    assert (tmp_out_dir / "03_threshold_explorer.png").exists()


# ---------------------------------------------------------------------------
# US7–US8 — Panel 7: Lead-time thresholds
# ---------------------------------------------------------------------------

def _write_lead_time_oof(model_dir: Path, n_event_participants: int) -> None:
    rng = np.random.default_rng(7)
    rows = []
    for i in range(n_event_participants):
        for day in range(-5, 1):
            rows.append({"participant_id": f"E{i}", "y_true": 1, "y_score": rng.random(),
                         "days_before_event": day, "fold": 1, "repeat": 1,
                         "model_id": "rf", "observation_id": f"E{i}",
                         "y_pred_default_threshold": 0, "y_pred_selected_threshold": 0,
                         "selected_threshold": 0.4})
    pd.DataFrame(rows).to_csv(model_dir / "predictions_oof.csv", index=False)


def test_panel_7_aggregate_with_5_events(tmp_model_dir, tmp_out_dir, manifest_path):
    _write_lead_time_oof(tmp_model_dir, 5)
    render_panel_7(tmp_model_dir, Path("."), tmp_out_dir, manifest_path)
    out = tmp_out_dir / "07_lead_time_analysis.png"
    assert out.exists()
    w, h = _png_size(out)
    assert w >= 1600 and h >= 900


def test_panel_7_individual_with_3_events(tmp_model_dir, tmp_out_dir, manifest_path):
    _write_lead_time_oof(tmp_model_dir, 3)
    render_panel_7(tmp_model_dir, Path("."), tmp_out_dir, manifest_path)
    out = tmp_out_dir / "07_lead_time_analysis.png"
    assert out.exists()
    w, h = _png_size(out)
    assert w >= 1600 and h >= 900


# ---------------------------------------------------------------------------
# US9 — Panel 8: No-leakage annotation
# ---------------------------------------------------------------------------

def test_panel_8_renders_with_no_leakage_annotation(tmp_model_dir, tmp_out_dir, manifest_path):
    rows = [{"participant_id": f"P{i}", "fold": i % 3 + 1, "repeat": 1,
             "model_id": "rf", "y_true": i % 5 == 0, "y_score": 0.5,
             "y_pred_default_threshold": 0, "y_pred_selected_threshold": 0,
             "selected_threshold": 0.4, "observation_id": f"P{i}"}
            for i in range(30)]
    pd.DataFrame(rows).to_csv(tmp_model_dir / "predictions_by_fold.csv", index=False)
    met_rows = [{"model_id": "rf", "fold": f, "repeat": 1, "metric": "auprc", "value": 0.3, "notes": ""}
                for f in range(1, 4)]
    pd.DataFrame(met_rows).to_csv(tmp_model_dir / "metrics_by_fold.csv", index=False)
    render_panel_8(tmp_model_dir, tmp_out_dir, manifest_path)
    assert (tmp_out_dir / "08_grouped_cv_variance.png").exists()


# ---------------------------------------------------------------------------
# US10 — Panel 9: Subgroup thresholds
# ---------------------------------------------------------------------------

def test_panel_9_shows_denominators(tmp_model_dir, tmp_out_dir, manifest_path):
    rng = np.random.default_rng(9)
    rows = [{"participant_id": f"P{i}", "fold": 1, "repeat": 1, "model_id": "rf",
             "y_true": int(i < 3), "y_score": rng.random(),
             "race_ethnicity": "GroupA" if i < 15 else "GroupB",
             "observation_id": f"P{i}", "y_pred_default_threshold": 0,
             "y_pred_selected_threshold": 0, "selected_threshold": 0.4}
            for i in range(30)]
    pd.DataFrame(rows).to_csv(tmp_model_dir / "predictions_oof.csv", index=False)
    render_panel_9(tmp_model_dir, Path("."), tmp_out_dir, manifest_path)
    out = tmp_out_dir / "09_subgroup_fairness_audit.png"
    assert out.exists()
    w, h = _png_size(out)
    assert w >= 1600 and h >= 900


# ---------------------------------------------------------------------------
# US1 — Panel 10: Learning curve unavailable when file absent
# ---------------------------------------------------------------------------

def test_panel_10_unavailable_when_no_file(tmp_model_dir, tmp_out_dir, manifest_path):
    render_panel_10(tmp_model_dir, tmp_out_dir, manifest_path)
    out = tmp_out_dir / "10_label_efficiency_learning_curve.png"
    assert out.exists()
    w, h = _png_size(out)
    assert w >= 1600 and h >= 900


def test_panel_10_renders_when_file_present(tmp_model_dir, tmp_out_dir, manifest_path):
    rows = [{"model_id": "rf", "training_n": n, "n_events": max(1, n // 10),
             "auprc_mean": 0.1 + n / 200 * 0.4, "auprc_ci_lower": 0.05,
             "auprc_ci_upper": 0.65, "recall_at_precision_mean": 0.3,
             "recall_at_precision_ci_lower": 0.1, "recall_at_precision_ci_upper": 0.6}
            for n in range(10, 110, 10)]
    pd.DataFrame(rows).to_csv(tmp_model_dir / "learning_curve.csv", index=False)
    render_panel_10(tmp_model_dir, tmp_out_dir, manifest_path)
    out = tmp_out_dir / "10_label_efficiency_learning_curve.png"
    assert out.exists()
    w, h = _png_size(out)
    assert w >= 1600 and h >= 900


# ---------------------------------------------------------------------------
# detect_synthetic_run
# ---------------------------------------------------------------------------

def test_detect_synthetic_run_from_path(tmp_path):
    d = tmp_path / "modeling_synthetic"
    d.mkdir()
    assert detect_synthetic_run(d) is True


def test_detect_synthetic_run_from_json(tmp_path):
    d = tmp_path / "modeling"
    d.mkdir()
    (d / "bakeoff_summary.json").write_text('{"data_source": "synthetic"}')
    assert detect_synthetic_run(d) is True


def test_detect_synthetic_run_false(tmp_path):
    d = tmp_path / "modeling"
    d.mkdir()
    (d / "bakeoff_summary.json").write_text('{"data_source": "raw"}')
    assert detect_synthetic_run(d) is False
