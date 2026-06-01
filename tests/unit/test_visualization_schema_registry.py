from __future__ import annotations

import pandas as pd

from src.visualization.schema_registry import (
    get_entity,
    resolve_column,
    require_roles,
)


def test_entity_source_filename_order_prefers_root_data():
    spec = get_entity("daily_vitals")
    assert spec.source_filenames[0] == "lullaby_daily_vitals.csv"
    assert spec.source_filenames[1] == "daily_vitals.csv"


def test_ordered_alias_resolution_selects_single_match():
    df = pd.DataFrame({"sbp_mean": [120]})
    resolution = resolve_column(df, "vital.systolic_bp", entity="daily_vitals")
    assert resolution.column == "sbp_mean"


def test_ambiguous_aliases_report_error():
    df = pd.DataFrame({"participant_id": ["P1"], "record_id": ["R1"]})
    resolution = resolve_column(df, "participant.id", entity="participants")
    assert resolution.match_type == "ambiguous"
    assert "Ambiguous" in (resolution.error or "")


def test_missing_required_role_fails_require_roles():
    df = pd.DataFrame({"date": ["2026-01-01"]})
    result = require_roles(
        df,
        ["vital.participant_id", "vital.date"],
        entity="daily_vitals",
    )
    assert result.status == "fail"
    assert result.errors


def test_missing_optional_role_warns_without_error():
    df = pd.DataFrame({"participant_id": ["P1"]})
    result = require_roles(
        df,
        ["participant.id", "participant.has_ac"],
        entity="participants",
    )
    assert result.status == "warn"
    assert result.errors == []
