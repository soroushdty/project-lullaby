from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any
import copy
import hashlib

import numpy as np
import yaml


DEFAULT_CONFIG_PATH = Path("config/simulation.yaml")
DEFAULT_OUTPUT_DIR = Path("data/synthetic/longitudinal")


@dataclass(frozen=True)
class ArchetypeConfig:
    name: str
    target_weight: float
    adherence_level: str
    missingness_pattern: str
    physiologic_risk: str
    normalized_weight: float = 0.0


@dataclass(frozen=True)
class EventRateConfig:
    cv_event: float = 0.075
    heat_illness: float = 0.05
    ed_visit: float = 0.10
    hospitalization: float = 0.04


@dataclass(frozen=True)
class SummerHeatConfig:
    enabled: bool = True
    start_date: str = "2026-06-01"
    baseline_temp_f: float = 94.0
    heat_wave_probability: float = 0.20
    heat_wave_temp_f: float = 108.0
    heat_index_noise_sd: float = 4.0


@dataclass(frozen=True)
class AdherenceConfig:
    initial_wear_hours_mean: float = 18.0
    weekly_decline_hours: float = 0.8
    scale_initial_probability: float = 0.85
    scale_weekly_decline: float = 0.08


@dataclass(frozen=True)
class MissingnessConfig:
    random_cell_missing_rate: float = 0.03
    participant_dropout_rate: float = 0.08
    clustered_gap_probability: float = 0.15
    hot_afternoon_gap_multiplier: float = 2.0


@dataclass(frozen=True)
class PhysiologyConfig:
    cv_bp_slope_per_day: tuple[float, float] = (0.6, 1.4)
    cv_hr_slope_per_day: tuple[float, float] = (0.2, 0.8)
    cv_body_water_slope_per_day: tuple[float, float] = (0.05, 0.20)
    heat_hr_spike: tuple[float, float] = (10.0, 28.0)
    heat_skin_temp_spike_f: tuple[float, float] = (1.0, 4.0)
    heat_body_water_drop: tuple[float, float] = (0.3, 1.5)


@dataclass(frozen=True)
class AlertsConfig:
    meows_thresholds_path: str = "config/meows_thresholds.synthetic.yaml"
    survey_completion_probability: float = 0.65
    call_completion_probability: float = 0.55


@dataclass(frozen=True)
class SimulationConfig:
    seed: int = 20260601
    n_participants: int = 200
    study_days: int = 84
    output_dir: Path = DEFAULT_OUTPUT_DIR
    event_rate: EventRateConfig = field(default_factory=EventRateConfig)
    summer_heat: SummerHeatConfig = field(default_factory=SummerHeatConfig)
    adherence: AdherenceConfig = field(default_factory=AdherenceConfig)
    missingness: MissingnessConfig = field(default_factory=MissingnessConfig)
    physiology: PhysiologyConfig = field(default_factory=PhysiologyConfig)
    alerts: AlertsConfig = field(default_factory=AlertsConfig)
    archetypes: tuple[ArchetypeConfig, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = ()
    source_path: str = ""

    def rng_for(self, component: str) -> np.random.Generator:
        digest = hashlib.sha256(f"{self.seed}:{component}".encode("utf-8")).digest()
        child_seed = int.from_bytes(digest[:8], "little", signed=False)
        return np.random.default_rng(child_seed)

    def with_overrides(
        self,
        *,
        seed: int | None = None,
        output_dir: str | Path | None = None,
    ) -> "SimulationConfig":
        updates: dict[str, Any] = {}
        if seed is not None:
            updates["seed"] = int(seed)
        if output_dir is not None:
            updates["output_dir"] = Path(output_dir)
        return replace(self, **updates)

    def to_effective_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["output_dir"] = str(self.output_dir)
        payload["archetypes"] = [asdict(item) for item in self.archetypes]
        return _plain(payload)


DEFAULT_ARCHETYPES: tuple[ArchetypeConfig, ...] = (
    ArchetypeConfig("diligent_monitor", 0.30, "high", "low_random", "low_to_moderate"),
    ArchetypeConfig("overwhelmed_mom", 0.30, "declining", "clustered_overnight_and_feeding", "moderate"),
    ArchetypeConfig("heat_stressed", 0.15, "moderate", "hot_afternoon_gaps", "heat_strain"),
    ArchetypeConfig("true_emergency", 0.06, "variable", "variable", "cv_event"),
    ArchetypeConfig("silent_decliner", 0.14, "declining", "increasing_dropout", "gradual_cv_decline"),
)


def load_simulation_config(
    path: str | Path = DEFAULT_CONFIG_PATH,
    *,
    seed: int | None = None,
    output_dir: str | Path | None = None,
) -> SimulationConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Simulation config not found: {config_path}")
    raw = yaml.safe_load(config_path.read_text()) or {}
    if not isinstance(raw, dict):
        raise ValueError("Simulation config must be a YAML mapping")
    config = simulation_config_from_dict(raw, source_path=config_path)
    return config.with_overrides(seed=seed, output_dir=output_dir)


def simulation_config_from_dict(
    raw: dict[str, Any],
    *,
    source_path: str | Path = "",
) -> SimulationConfig:
    source = str(source_path) if source_path else ""
    warnings = _unknown_top_level_warnings(raw)
    merged = _merge_dict(default_config_dict(), raw)
    archetypes = _parse_archetypes(merged.get("archetypes") or [])
    config = SimulationConfig(
        seed=int(merged["seed"]),
        n_participants=int(merged["n_participants"]),
        study_days=int(merged["study_days"]),
        output_dir=Path(merged.get("output_dir") or DEFAULT_OUTPUT_DIR),
        event_rate=EventRateConfig(**_section(merged, "event_rate")),
        summer_heat=SummerHeatConfig(**_section(merged, "summer_heat")),
        adherence=AdherenceConfig(**_section(merged, "adherence")),
        missingness=MissingnessConfig(**_section(merged, "missingness")),
        physiology=_physiology_from_dict(_section(merged, "physiology")),
        alerts=AlertsConfig(**_section(merged, "alerts")),
        archetypes=archetypes,
        warnings=tuple(warnings),
        source_path=source,
    )
    _validate_config(config)
    return config


def default_config_dict() -> dict[str, Any]:
    return {
        "seed": 20260601,
        "n_participants": 200,
        "study_days": 84,
        "output_dir": str(DEFAULT_OUTPUT_DIR),
        "event_rate": asdict(EventRateConfig()),
        "summer_heat": asdict(SummerHeatConfig()),
        "adherence": asdict(AdherenceConfig()),
        "missingness": asdict(MissingnessConfig()),
        "physiology": {
            key: list(value) for key, value in asdict(PhysiologyConfig()).items()
        },
        "alerts": asdict(AlertsConfig()),
        "archetypes": [asdict(item) for item in DEFAULT_ARCHETYPES],
    }


def _section(raw: dict[str, Any], name: str) -> dict[str, Any]:
    value = raw.get(name)
    if not isinstance(value, dict):
        raise ValueError(f"Simulation config section '{name}' must be a mapping")
    return value


def _unknown_top_level_warnings(raw: dict[str, Any]) -> list[str]:
    known = set(default_config_dict())
    return [f"Unknown top-level config key ignored: {key}" for key in sorted(raw) if key not in known]


def _parse_archetypes(items: list[dict[str, Any]]) -> tuple[ArchetypeConfig, ...]:
    if not items:
        raise ValueError("Simulation config must define at least one archetype")
    total = sum(float(item.get("target_weight", 0.0)) for item in items)
    if total <= 0:
        raise ValueError("Archetype target weights must sum to a positive value")
    parsed = []
    for item in items:
        parsed.append(
            ArchetypeConfig(
                name=str(item["name"]),
                target_weight=float(item["target_weight"]),
                adherence_level=str(item["adherence_level"]),
                missingness_pattern=str(item["missingness_pattern"]),
                physiologic_risk=str(item["physiologic_risk"]),
                normalized_weight=float(item["target_weight"]) / total,
            )
        )
    return tuple(parsed)


def _physiology_from_dict(raw: dict[str, Any]) -> PhysiologyConfig:
    return PhysiologyConfig(
        cv_bp_slope_per_day=_range_tuple(raw["cv_bp_slope_per_day"], "cv_bp_slope_per_day"),
        cv_hr_slope_per_day=_range_tuple(raw["cv_hr_slope_per_day"], "cv_hr_slope_per_day"),
        cv_body_water_slope_per_day=_range_tuple(raw["cv_body_water_slope_per_day"], "cv_body_water_slope_per_day"),
        heat_hr_spike=_range_tuple(raw["heat_hr_spike"], "heat_hr_spike"),
        heat_skin_temp_spike_f=_range_tuple(raw["heat_skin_temp_spike_f"], "heat_skin_temp_spike_f"),
        heat_body_water_drop=_range_tuple(raw["heat_body_water_drop"], "heat_body_water_drop"),
    )


def _range_tuple(value: Any, name: str) -> tuple[float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError(f"{name} must contain exactly two numeric values")
    lower, upper = float(value[0]), float(value[1])
    if lower > upper:
        raise ValueError(f"{name} lower bound must be <= upper bound")
    return (lower, upper)


def _validate_config(config: SimulationConfig) -> None:
    if config.seed < 0:
        raise ValueError("seed must be non-negative")
    if config.n_participants <= 0:
        raise ValueError("n_participants must be positive")
    if config.study_days <= 0:
        raise ValueError("study_days must be positive")
    for name, value in asdict(config.event_rate).items():
        _validate_probability(value, f"event_rate.{name}")
    for name in ("heat_wave_probability",):
        _validate_probability(getattr(config.summer_heat, name), f"summer_heat.{name}")
    for name in ("scale_initial_probability", "scale_weekly_decline"):
        _validate_probability(getattr(config.adherence, name), f"adherence.{name}")
    for name in ("random_cell_missing_rate", "participant_dropout_rate", "clustered_gap_probability"):
        _validate_probability(getattr(config.missingness, name), f"missingness.{name}")
    for name in ("survey_completion_probability", "call_completion_probability"):
        _validate_probability(getattr(config.alerts, name), f"alerts.{name}")
    if config.adherence.initial_wear_hours_mean <= 0:
        raise ValueError("adherence.initial_wear_hours_mean must be positive")
    if config.adherence.weekly_decline_hours < 0:
        raise ValueError("adherence.weekly_decline_hours must be non-negative")
    if config.missingness.hot_afternoon_gap_multiplier <= 0:
        raise ValueError("missingness.hot_afternoon_gap_multiplier must be positive")


def _validate_probability(value: float, name: str) -> None:
    if value < 0 or value > 1:
        raise ValueError(f"{name} must be between 0 and 1")


def _merge_dict(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_dict(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def _plain(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    if isinstance(value, list):
        return [_plain(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    return value
