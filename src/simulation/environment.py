from __future__ import annotations

import numpy as np
import pandas as pd

from src.simulation.config import SimulationConfig


def fahrenheit_to_celsius(value_f: float) -> float:
    return (float(value_f) - 32.0) * 5.0 / 9.0


def generate_environment(config: SimulationConfig) -> pd.DataFrame:
    dates = pd.date_range(config.summer_heat.start_date, periods=config.study_days, freq="D")
    rng = config.rng_for("environment")
    if config.summer_heat.enabled:
        heat_wave = rng.random(config.study_days) < config.summer_heat.heat_wave_probability
        if config.study_days and not heat_wave.any() and config.summer_heat.heat_wave_probability > 0:
            heat_wave[int(rng.integers(0, config.study_days))] = True
        seasonal = 3.0 * np.sin(np.linspace(0, np.pi, config.study_days))
        noise = rng.normal(0, 1.8, config.study_days)
        ambient_f = (
            config.summer_heat.baseline_temp_f
            + seasonal
            + noise
            + heat_wave * (config.summer_heat.heat_wave_temp_f - config.summer_heat.baseline_temp_f)
        )
        heat_index_f = ambient_f + rng.normal(
            config.summer_heat.heat_index_noise_sd,
            max(config.summer_heat.heat_index_noise_sd / 3.0, 0.1),
            config.study_days,
        )
    else:
        heat_wave = np.zeros(config.study_days, dtype=bool)
        ambient_f = np.full(config.study_days, 72.0)
        heat_index_f = ambient_f + 1.0

    ambient_c = np.round([fahrenheit_to_celsius(v) for v in ambient_f], 2)
    heat_index_c = np.round([fahrenheit_to_celsius(v) for v in heat_index_f], 2)
    exposure = np.where(
        heat_index_c >= 40,
        "extreme",
        np.where(heat_index_c >= 35, "high", np.where(heat_index_c >= 30, "moderate", "low")),
    )
    return pd.DataFrame(
        {
            "date": [d.date().isoformat() for d in dates],
            "study_day": np.arange(1, config.study_days + 1),
            "ambient_temp_c": ambient_c,
            "heat_index_c": heat_index_c,
            "heat_wave": heat_wave.astype(bool),
            "heat_exposure_level": exposure,
            "synthetic_data": True,
        }
    )
