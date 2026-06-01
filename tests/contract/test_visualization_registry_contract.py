from __future__ import annotations

import pandas as pd

from src.visualization.schema_registry import (
    available_roles,
    get_entity,
    load_entity,
    require_roles,
    resolve_column,
)


def test_current_and_future_entities_are_registered():
    assert get_entity("participants").status == "current"
    assert get_entity("environment").status == "future_optional"


def test_load_entity_prefers_root_lullaby_filename():
    df = load_entity(__import__("pathlib").Path("data"), "participants")
    assert "participant_id" in df.columns


def test_required_role_resolves_from_root_data():
    df = load_entity(__import__("pathlib").Path("data"), "participants")
    resolution = resolve_column(df, "participant.id", entity="participants")
    assert resolution.column == "participant_id"
    assert resolution.match_type == "alias"


def test_available_roles_returns_resolved_columns():
    df = pd.DataFrame({"participant_id": ["P1"], "age": [30]})
    roles = available_roles(df, ["participant.id", "participant.age"], entity="participants")
    assert roles == {"participant.id": "participant_id", "participant.age": "age"}


def test_require_roles_reports_optional_warning_and_extra_columns():
    df = pd.DataFrame({"participant_id": ["P1"], "unexpected": ["kept"]})
    result = require_roles(
        df,
        ["participant.id", "participant.age"],
        entity="participants",
    )
    assert result.status == "warn"
    assert "participant.id" in result.resolved_roles
    assert result.warnings
    assert result.extra_columns == ["unexpected"]
