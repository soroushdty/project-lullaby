from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from src.simulation.environment import fahrenheit_to_celsius


def bounded_uniform(
    rng: np.random.Generator,
    bounds: tuple[float, float],
) -> float:
    lower, upper = bounds
    if lower == upper:
        return float(lower)
    return float(rng.uniform(lower, upper))


def cv_ramp_multiplier(study_day: int, event_day: int | None, *, window_days: int = 7) -> float:
    if event_day is None:
        return 0.0
    start = event_day - window_days
    if study_day < start or study_day > event_day:
        return 0.0
    return float(study_day - start)


def heat_skin_spike_c(bounds_f: tuple[float, float], rng: np.random.Generator) -> float:
    spike_f = bounded_uniform(rng, bounds_f)
    return fahrenheit_to_celsius(32.0 + spike_f)


def simple_auc(values: Sequence[float], labels: Sequence[bool]) -> float:
    pairs = [(float(value), bool(label)) for value, label in zip(values, labels) if not np.isnan(float(value))]
    positives = [value for value, label in pairs if label]
    negatives = [value for value, label in pairs if not label]
    if not positives or not negatives:
        return 0.5
    wins = 0.0
    total = len(positives) * len(negatives)
    for pos in positives:
        for neg in negatives:
            if pos > neg:
                wins += 1.0
            elif pos == neg:
                wins += 0.5
    auc = wins / total
    return float(max(auc, 1.0 - auc))
