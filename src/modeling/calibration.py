from __future__ import annotations

import numpy as np

from src.modeling.metrics import brier


def expected_calibration_error(y_true: np.ndarray, y_score: np.ndarray, *, n_bins: int = 10) -> float:
    y = np.asarray(y_true).astype(int)
    score = np.clip(np.asarray(y_score, dtype=float), 0.0, 1.0)
    if len(y) == 0:
        return np.nan
    bins = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for left, right in zip(bins[:-1], bins[1:]):
        mask = (score >= left) & (score < right if right < 1 else score <= right)
        if not mask.any():
            continue
        ece += mask.mean() * abs(score[mask].mean() - y[mask].mean())
    return float(ece)


def calibration_slope_intercept(y_true: np.ndarray, y_score: np.ndarray) -> tuple[float, float, bool, str]:
    y = np.asarray(y_true).astype(int)
    score = np.clip(np.asarray(y_score, dtype=float), 1e-6, 1 - 1e-6)
    if len(np.unique(y)) < 2 or np.unique(score).size < 2:
        return np.nan, np.nan, False, "calibration slope/intercept not estimable for degenerate labels or scores"
    logit = np.log(score / (1 - score))
    x = np.column_stack([np.ones(len(logit)), logit])
    try:
        coef, *_ = np.linalg.lstsq(x, y.astype(float), rcond=None)
    except np.linalg.LinAlgError:
        return np.nan, np.nan, False, "calibration least-squares fit failed"
    return float(coef[0]), float(coef[1]), True, ""


def calibration_record(model_id: str, repeat: int, fold: int, y_true: np.ndarray, y_score: np.ndarray) -> dict[str, object]:
    intercept, slope, estimable, notes = calibration_slope_intercept(y_true, y_score)
    return {
        "model_id": model_id,
        "repeat": repeat,
        "fold": fold,
        "brier": brier(y_true, y_score),
        "calibration_intercept": intercept,
        "calibration_slope": slope,
        "expected_calibration_error": expected_calibration_error(y_true, y_score),
        "estimable": estimable,
        "notes": notes,
    }
