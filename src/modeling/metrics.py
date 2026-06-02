from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class ThresholdResult:
    threshold: float
    target_met: bool
    precision: float
    recall: float
    notes: str


def _clean(y_true: np.ndarray, y_score: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    y = np.asarray(y_true).astype(int)
    score = np.asarray(y_score, dtype=float)
    mask = np.isfinite(score)
    return y[mask], np.clip(score[mask], 0.0, 1.0)


def precision_recall_points(y_true: np.ndarray, y_score: np.ndarray) -> pd.DataFrame:
    y, score = _clean(y_true, y_score)
    thresholds = np.unique(score)
    rows = []
    for threshold in np.sort(thresholds)[::-1]:
        pred = score >= threshold
        tp = int(np.sum((pred == 1) & (y == 1)))
        fp = int(np.sum((pred == 1) & (y == 0)))
        fn = int(np.sum((pred == 0) & (y == 1)))
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        rows.append({"threshold": float(threshold), "precision": precision, "recall": recall})
    if not rows:
        rows.append({"threshold": 0.5, "precision": 0.0, "recall": 0.0})
    return pd.DataFrame(rows)


def auprc(y_true: np.ndarray, y_score: np.ndarray) -> float:
    y, score = _clean(y_true, y_score)
    positives = int(np.sum(y == 1))
    if positives == 0:
        return np.nan
    order = np.argsort(-score, kind="mergesort")
    y_sorted = y[order]
    tp = np.cumsum(y_sorted == 1)
    fp = np.cumsum(y_sorted == 0)
    precision = tp / np.maximum(tp + fp, 1)
    recall = tp / positives
    recall_prev = np.concatenate([[0.0], recall[:-1]])
    return float(np.sum((recall - recall_prev) * precision))


def auroc(y_true: np.ndarray, y_score: np.ndarray) -> float:
    y, score = _clean(y_true, y_score)
    pos = score[y == 1]
    neg = score[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return np.nan
    comparisons = (pos[:, None] > neg[None, :]).mean()
    ties = 0.5 * (pos[:, None] == neg[None, :]).mean()
    return float(comparisons + ties)


def brier(y_true: np.ndarray, y_score: np.ndarray) -> float:
    y, score = _clean(y_true, y_score)
    return float(np.mean((score - y) ** 2)) if len(y) else np.nan


def recall_at_precision(y_true: np.ndarray, y_score: np.ndarray, *, min_precision: float) -> tuple[float, str]:
    points = precision_recall_points(y_true, y_score)
    eligible = points[points["precision"] >= float(min_precision)]
    if eligible.empty:
        return 0.0, f"precision target {min_precision:.2f} not met"
    return float(eligible["recall"].max()), ""


def select_threshold(y_true: np.ndarray, y_score: np.ndarray, *, min_precision: float) -> ThresholdResult:
    points = precision_recall_points(y_true, y_score)
    eligible = points[points["precision"] >= float(min_precision)].copy()
    if not eligible.empty:
        eligible = eligible.sort_values(["recall", "precision", "threshold"], ascending=[False, False, False])
        row = eligible.iloc[0]
        return ThresholdResult(float(row.threshold), True, float(row.precision), float(row.recall), "")
    fallback = points.sort_values(["precision", "recall", "threshold"], ascending=[False, False, False]).iloc[0]
    return ThresholdResult(
        float(fallback.threshold),
        False,
        float(fallback.precision),
        float(fallback.recall),
        f"precision target {min_precision:.2f} unmet; fallback selected highest precision",
    )


def classification_stats(y_true: np.ndarray, y_score: np.ndarray, threshold: float) -> dict[str, float]:
    y, score = _clean(y_true, y_score)
    pred = score >= float(threshold)
    tp = int(np.sum((pred == 1) & (y == 1)))
    fp = int(np.sum((pred == 1) & (y == 0)))
    tn = int(np.sum((pred == 0) & (y == 0)))
    fn = int(np.sum((pred == 0) & (y == 1)))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    specificity = tn / (tn + fp) if tn + fp else 0.0
    fpr = fp / (fp + tn) if fp + tn else 0.0
    return {
        "threshold": float(threshold),
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
        "false_positive_rate": fpr,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
    }


def metric_records(
    *,
    model_id: str,
    repeat: int,
    fold: int,
    y_true: np.ndarray,
    y_score: np.ndarray,
    min_precision: float,
) -> list[dict[str, object]]:
    recall_value, recall_note = recall_at_precision(y_true, y_score, min_precision=min_precision)
    values = [
        ("auprc", auprc(y_true, y_score), True, ""),
        ("recall_at_precision", recall_value, True, recall_note),
        ("brier", brier(y_true, y_score), True, ""),
        ("auroc", auroc(y_true, y_score), False, "secondary metric"),
    ]
    return [
        {
            "model_id": model_id,
            "repeat": repeat,
            "fold": fold,
            "metric": metric,
            "value": value,
            "primary_metric": primary,
            "threshold": "",
            "notes": note,
        }
        for metric, value, primary, note in values
    ]


def summarize_metrics(metrics_by_fold: pd.DataFrame, *, n_bootstrap: int, level: float, seed: int) -> pd.DataFrame:
    rows = []
    rng = np.random.default_rng(seed)
    grouped = metrics_by_fold.copy()
    grouped["value"] = pd.to_numeric(grouped["value"], errors="coerce")
    from src.validation.semantics import parse_domain_boolean_series, DomainBooleanParsePolicy
    
    for (model_id, metric), frame in grouped.groupby(["model_id", "metric"], sort=True):
        values = frame["value"].dropna().to_numpy(dtype=float)
        parsed_primary = parse_domain_boolean_series(
            frame["primary_metric"],
            DomainBooleanParsePolicy(role="model_metric.primary_metric", required=False),
            source_column="primary_metric"
        )
        primary = bool(parsed_primary.true_mask.any())
        notes = "; ".join(sorted({str(v) for v in frame["notes"].dropna() if str(v)}))
        if len(values) == 0:
            rows.append(
                {
                    "model_id": model_id,
                    "metric": metric,
                    "mean": np.nan,
                    "sd": np.nan,
                    "ci_lower": np.nan,
                    "ci_upper": np.nan,
                    "n_folds": 0,
                    "n_repeats": 0,
                    "primary_metric": primary,
                    "notes": notes or "metric unavailable",
                }
            )
            continue
        means = []
        for _ in range(int(n_bootstrap)):
            sample = rng.choice(values, size=len(values), replace=True)
            means.append(float(np.mean(sample)))
        alpha = (1 - float(level)) / 2
        rows.append(
            {
                "model_id": model_id,
                "metric": metric,
                "mean": float(np.mean(values)),
                "sd": float(np.std(values, ddof=1)) if len(values) > 1 else 0.0,
                "ci_lower": float(np.quantile(means, alpha)),
                "ci_upper": float(np.quantile(means, 1 - alpha)),
                "n_folds": int(frame["fold"].nunique()),
                "n_repeats": int(frame["repeat"].nunique()),
                "primary_metric": primary,
                "notes": notes,
            }
        )
    return pd.DataFrame(rows)


def operating_points(
    predictions: pd.DataFrame,
    *,
    participant_days: float,
    thresholds: list[float],
) -> pd.DataFrame:
    rows = []
    for model_id, frame in predictions.groupby("model_id", sort=True):
        y = frame["y_true"].to_numpy(dtype=int)
        score = frame["y_score"].to_numpy(dtype=float)
        for threshold in sorted(set(round(float(t), 6) for t in thresholds)):
            stats = classification_stats(y, score, threshold)
            predicted_positive = stats["tp"] + stats["fp"]
            alerts_per_100 = (predicted_positive / participant_days * 100.0) if participant_days else np.nan
            nta = (predicted_positive / stats["tp"]) if stats["tp"] else np.nan
            rows.append(
                {
                    "model_id": model_id,
                    "threshold": threshold,
                    "precision": stats["precision"],
                    "recall": stats["recall"],
                    "specificity": stats["specificity"],
                    "false_positive_rate": stats["false_positive_rate"],
                    "alerts_per_100_participant_days": alerts_per_100,
                    "number_needed_to_alert": nta,
                    "estimated_calls": float(predicted_positive),
                }
            )
    return pd.DataFrame(rows)


def decision_curve(predictions: pd.DataFrame, thresholds: list[float]) -> pd.DataFrame:
    rows = []
    for model_id, frame in predictions.groupby("model_id", sort=True):
        y = frame["y_true"].to_numpy(dtype=int)
        score = frame["y_score"].to_numpy(dtype=float)
        n = max(len(y), 1)
        rounded_thresholds = {round(float(t), 6) for t in thresholds if np.isfinite(float(t))}
        for threshold in sorted(t for t in rounded_thresholds if 0 < t < 1):
            stats = classification_stats(y, score, threshold)
            odds = threshold / (1 - threshold)
            net_benefit = stats["tp"] / n - stats["fp"] / n * odds
            rows.append(
                {
                    "model_id": model_id,
                    "threshold": threshold,
                    "net_benefit": float(net_benefit),
                    "notes": "exploratory signal characterization; not clinical deployment guidance",
                }
            )
    return pd.DataFrame(rows)
