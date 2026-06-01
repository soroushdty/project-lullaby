from __future__ import annotations

import pandas as pd

from src.visualization.validation import validate_entity


def test_required_role_failure_is_structured():
    df = pd.DataFrame({"participant_id": ["P1"], "date": ["2026-01-01"]})
    result = validate_entity("daily_vitals", df, source_file="daily.csv")
    assert result.status == "fail"
    assert any("vital.systolic_bp" in error for error in result.errors)


def test_optional_missingness_warns_and_extra_columns_are_preserved():
    df = pd.DataFrame(
        {
            "participant_id": ["P1"],
            "date": ["2026-01-01"],
            "sbp_mean": [120],
            "source_extra": ["kept"],
        }
    )
    result = validate_entity("daily_vitals", df, source_file="daily.csv")
    assert result.status == "warn"
    assert "source_extra" in result.extra_columns
    assert result.errors == []


def test_validation_does_not_mutate_or_impute_source_frame():
    df = pd.DataFrame(
        {
            "participant_id": ["P1"],
            "date": ["2026-01-01"],
            "sbp_mean": [None],
        }
    )
    before = df.copy(deep=True)
    validate_entity("daily_vitals", df, source_file="daily.csv")
    pd.testing.assert_frame_equal(df, before)


def test_hard_range_violation_preserves_row():
    df = pd.DataFrame(
        {
            "participant_id": ["P1"],
            "date": ["2026-01-01"],
            "sbp_mean": [300],
        }
    )
    result = validate_entity("daily_vitals", df, source_file="daily.csv")
    assert result.status == "fail"
    assert result.row_count == 1
    assert result.range_violations[0]["role"] == "vital.systolic_bp"


def test_capture_worthy_value_is_reported_not_failed():
    df = pd.DataFrame(
        {
            "participant_id": ["P1"],
            "date": ["2026-01-01"],
            "sbp_mean": [190],
        }
    )
    result = validate_entity("daily_vitals", df, source_file="daily.csv")
    assert result.status == "warn"
    assert result.capture_worthy_values[0]["role"] == "vital.systolic_bp"
