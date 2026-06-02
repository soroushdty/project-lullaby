from __future__ import annotations

import numpy as np
import pandas as pd

from src.modeling.calibration import calibration_record
from src.modeling.metrics import auprc, brier, decision_curve, metric_records, operating_points, recall_at_precision, summarize_metrics


def test_primary_metrics_are_estimable():
    y = np.array([1, 0, 1, 0, 0])
    scores = np.array([0.9, 0.2, 0.8, 0.4, 0.1])

    assert auprc(y, scores) > 0.9
    assert recall_at_precision(y, scores, min_precision=0.8)[0] == 1.0
    assert brier(y, scores) < 0.1


def test_metric_summary_bootstraps_fold_repeat_values():
    rows = []
    for repeat in range(2):
        for fold in range(3):
            rows.append(
                {
                    "model_id": "m",
                    "repeat": repeat,
                    "fold": fold,
                    "metric": "auprc",
                    "value": 0.5 + 0.1 * fold,
                    "primary_metric": True,
                    "threshold": "",
                    "notes": "",
                }
            )
    summary = summarize_metrics(pd.DataFrame(rows), n_bootstrap=100, level=0.95, seed=123)

    assert summary.loc[0, "n_folds"] == 3
    assert summary.loc[0, "n_repeats"] == 2
    assert summary.loc[0, "ci_lower"] <= summary.loc[0, "mean"] <= summary.loc[0, "ci_upper"]


def test_metrics_mark_auroc_secondary_and_accuracy_absent():
    rows = metric_records(
        model_id="m",
        repeat=0,
        fold=0,
        y_true=np.array([1, 0, 1, 0]),
        y_score=np.array([0.9, 0.1, 0.8, 0.2]),
        min_precision=0.8,
    )

    by_metric = {row["metric"]: row for row in rows}
    assert by_metric["auprc"]["primary_metric"] is True
    assert by_metric["recall_at_precision"]["primary_metric"] is True
    assert by_metric["brier"]["primary_metric"] is True
    assert by_metric["auroc"]["primary_metric"] is False
    assert "accuracy" not in by_metric


def test_calibration_record_handles_estimable_and_degenerate_cases():
    ok = calibration_record("m", 0, 0, np.array([1, 0, 1, 0]), np.array([0.9, 0.1, 0.7, 0.2]))
    bad = calibration_record("m", 0, 1, np.array([1, 1, 1]), np.array([0.9, 0.9, 0.9]))

    assert ok["estimable"] is True
    assert np.isfinite(ok["brier"])
    assert bad["estimable"] is False
    assert "not estimable" in bad["notes"]


def test_operating_points_and_decision_curve_use_explicit_thresholds():
    predictions = pd.DataFrame(
        {
            "model_id": ["m"] * 4,
            "y_true": [1, 0, 1, 0],
            "y_score": [0.9, 0.3, 0.7, 0.2],
        }
    )

    ops = operating_points(predictions, participant_days=100, thresholds=[0.5])
    curve = decision_curve(predictions, thresholds=[0.5])

    assert ops.loc[0, "threshold"] == 0.5
    assert ops.loc[0, "alerts_per_100_participant_days"] == 2.0
    assert curve.loc[0, "threshold"] == 0.5
    assert "exploratory" in curve.loc[0, "notes"]
