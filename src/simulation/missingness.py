from __future__ import annotations

import numpy as np

from src.simulation.config import SimulationConfig


OBSERVED_VALUE_COLUMNS = (
    "systolic_bp",
    "diastolic_bp",
    "heart_rate",
    "respiratory_rate",
    "skin_temperature_c",
    "weight_kg",
    "body_water_pct",
    "sleep_hours",
    "steps",
    "active_minutes",
)


def clamp(value: float, lower: float, upper: float) -> float:
    return float(min(max(value, lower), upper))


def adherence_values(
    config: SimulationConfig,
    archetype: str,
    week: int,
    rng: np.random.Generator,
) -> tuple[float, bool]:
    adjustment = {
        "diligent_monitor": 2.0,
        "overwhelmed_mom": -0.8,
        "heat_stressed": -0.2,
        "true_emergency": -0.5,
        "silent_decliner": -1.0,
    }.get(archetype, 0.0)
    decline_multiplier = {
        "diligent_monitor": 0.45,
        "overwhelmed_mom": 1.25,
        "heat_stressed": 0.9,
        "true_emergency": 0.8,
        "silent_decliner": 1.45,
    }.get(archetype, 1.0)
    wear = (
        config.adherence.initial_wear_hours_mean
        + adjustment
        - config.adherence.weekly_decline_hours * max(week - 1, 0) * decline_multiplier
        + rng.normal(0, 0.7)
    )
    wear = clamp(wear, 0.0, 24.0)
    scale_probability = (
        config.adherence.scale_initial_probability
        - config.adherence.scale_weekly_decline * max(week - 1, 0) * decline_multiplier
        + adjustment * 0.015
    )
    scale_used = bool(rng.random() < clamp(scale_probability, 0.05, 0.98))
    return wear, scale_used


def row_missing_probability(
    config: SimulationConfig,
    archetype: str,
    *,
    heat_exposure_level: str,
    cv_event_window: bool,
    heat_strain_day: bool,
    week: int,
) -> float:
    base = config.missingness.random_cell_missing_rate
    archetype_adjustment = {
        "diligent_monitor": -0.015,
        "overwhelmed_mom": 0.08,
        "heat_stressed": 0.05,
        "true_emergency": 0.04,
        "silent_decliner": 0.10,
    }.get(archetype, 0.0)
    heat_adjustment = 0.0
    if heat_exposure_level in {"high", "extreme"}:
        heat_adjustment = base * (config.missingness.hot_afternoon_gap_multiplier - 1.0) + 0.035
    worsening_adjustment = 0.05 if cv_event_window or heat_strain_day else 0.0
    week_adjustment = max(week - 1, 0) * 0.006
    return clamp(base + archetype_adjustment + heat_adjustment + worsening_adjustment + week_adjustment, 0.0, 0.85)


def dropout_day(
    config: SimulationConfig,
    participant_index: int,
    is_dropout_participant: bool,
    rng: np.random.Generator,
) -> int | None:
    if not is_dropout_participant:
        return None
    low = max(15, config.study_days // 3)
    high = max(low + 1, config.study_days - 7)
    return int(rng.integers(low, high))
