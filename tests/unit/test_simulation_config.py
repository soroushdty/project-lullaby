from __future__ import annotations

import pytest

from src.simulation.config import (
    default_config_dict,
    load_simulation_config,
    simulation_config_from_dict,
)


def test_default_config_loads_and_normalizes_archetypes():
    config = load_simulation_config("config/simulation.yaml")

    assert config.seed == 20260601
    assert config.study_days == 84
    assert config.n_participants == 200
    assert round(sum(item.normalized_weight for item in config.archetypes), 8) == 1.0
    assert {item.name for item in config.archetypes} >= {"diligent_monitor", "true_emergency"}


def test_component_rng_streams_are_deterministic_and_independent():
    config = load_simulation_config("config/simulation.yaml")

    first = config.rng_for("participants").integers(0, 1_000_000, size=5).tolist()
    second = config.rng_for("participants").integers(0, 1_000_000, size=5).tolist()
    events = config.rng_for("events").integers(0, 1_000_000, size=5).tolist()

    assert first == second
    assert first != events


def test_invalid_probability_rejected():
    raw = default_config_dict()
    raw["event_rate"]["cv_event"] = 1.5

    with pytest.raises(ValueError, match="event_rate.cv_event"):
        simulation_config_from_dict(raw)


def test_custom_config_and_cli_style_overrides(simulation_output_dir):
    raw = default_config_dict()
    raw["n_participants"] = 20
    raw["archetypes"][0]["target_weight"] = 4
    raw["archetypes"][1]["target_weight"] = 1

    config = simulation_config_from_dict(raw).with_overrides(
        seed=7,
        output_dir=simulation_output_dir,
    )

    assert config.seed == 7
    assert config.output_dir == simulation_output_dir
    assert config.n_participants == 20
    assert round(sum(item.normalized_weight for item in config.archetypes), 8) == 1.0
