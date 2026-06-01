from __future__ import annotations

import pandas as pd

from src.visualization.eda_core import (
    _call_attempted_count,
    _call_completed_count,
    _completion_series,
    _outcome_series,
    _survey_states,
    generate_core_dashboards,
    load_eda_tables,
)


def test_missing_optional_roles_render_warning_panels_without_crashing(tmp_path):
    data_dir = tmp_path / "minimal_data"
    data_dir.mkdir()
    pd.DataFrame({"participant_id": ["P1", "P2"]}).to_csv(data_dir / "participants.csv", index=False)
    pd.DataFrame(
        {
            "participant_id": ["P1", "P1", "P2"],
            "date": ["2026-06-01", "2026-06-02", "2026-06-01"],
            "systolic_bp": [120, None, 145],
            "heart_rate": [80, 82, None],
        }
    ).to_csv(data_dir / "daily_vitals.csv", index=False)
    pd.DataFrame({"participant_id": ["P1", "P2"], "cv_event": [True, False]}).to_csv(
        data_dir / "clinical_outcomes.csv",
        index=False,
    )
    pd.DataFrame(
        {
            "alert_id": ["A1", "A2"],
            "participant_id": ["P1", "P2"],
            "alert_level": ["yellow", "red"],
            "trigger_reasons": ["sBP>140", None],
            "survey_completion": ["completed", None],
            "called_nurse": [True, None],
        }
    ).to_csv(data_dir / "alerts.csv", index=False)
    pd.DataFrame(
        {
            "participant_id": ["P1"],
            "contact_date": ["2026-06-02"],
            "contact_type": ["nurse_call"],
            "participant_reached": [None],
        }
    ).to_csv(data_dir / "staff_contacts.csv", index=False)

    results = generate_core_dashboards(data_dir, tmp_path / "eda")

    assert len(results) == 4
    cohort_warnings = next(result.warnings for result in results if "cohort_overview" in result.artifact_id)
    assert "age unavailable" in cohort_warnings
    loaded = load_eda_tables(data_dir)
    assert loaded.daily_vitals["systolic_bp"].isna().sum() == 1
    assert loaded.daily_vitals["heart_rate"].isna().sum() == 1


def test_missing_values_are_counted_not_imputed_in_synthetic_source():
    tables = load_eda_tables("data/synthetic/longitudinal")

    assert tables.daily_vitals["systolic_bp"].isna().any()
    assert tables.daily_vitals["heart_rate"].isna().any()
    assert tables.daily_vitals.groupby("participant_id")["study_day"].count().eq(84).all()


def test_outcome_prevalence_parses_positive_negative_and_missing_counts():
    outcomes = pd.DataFrame({"cv_event": [True, False, None, "", "unknown", "False", "1"]})

    parsed = _outcome_series(outcomes, "cv_event", required=True)

    assert parsed.counts == {
        "true": 2,
        "false": 2,
        "missing_unknown": 3,
        "invalid": 0,
    }


def test_alert_funnel_keeps_missing_states_and_explicit_completion_only():
    alerts = pd.DataFrame(
        {
            "survey_completed": [True, False, None, "yes", "not sure"],
            "called_nurse": [True, False, None, "0", "1"],
            "nurse_outcome": ["completed", "left voicemail", None, "pending", "reached"],
        }
    )
    contacts = pd.DataFrame(
        {
            "contact_type": ["nurse_call", "nurse_call", "text"],
            "completed": ["completed", "left voicemail", None],
        }
    )

    survey_states, survey_warnings = _survey_states(alerts)
    attempted, attempted_warnings = _call_attempted_count(alerts, contacts)
    completed_from_alerts, completion_warnings = _call_completed_count(alerts, contacts)
    completion, contact_warnings = _completion_series(contacts)

    assert survey_states.tolist() == ["completed", "abandoned", "missing/unknown", "completed", "missing/unknown"]
    assert survey_warnings
    assert attempted == 2
    assert attempted_warnings == []
    assert completed_from_alerts == 2
    assert completion_warnings == []
    assert completion.tolist()[:2] == [True, False]
    assert completion.isna().sum() == 1
    assert contact_warnings == []


def test_optional_invalid_boolean_values_warn_and_render_as_missing(tmp_path):
    data_dir = tmp_path / "invalid_optional"
    data_dir.mkdir()
    pd.DataFrame({"participant_id": ["P1"], "has_ac": ["perhaps"]}).to_csv(data_dir / "participants.csv", index=False)
    pd.DataFrame({"participant_id": ["P1"], "date": ["2026-06-01"], "systolic_bp": [120]}).to_csv(
        data_dir / "daily_vitals.csv",
        index=False,
    )
    pd.DataFrame({"participant_id": ["P1"], "cv_event": [False]}).to_csv(data_dir / "clinical_outcomes.csv", index=False)
    pd.DataFrame({"alert_id": ["A1"], "participant_id": ["P1"], "alert_level": ["yellow"]}).to_csv(
        data_dir / "alerts.csv",
        index=False,
    )
    pd.DataFrame({"participant_id": ["P1"], "contact_type": ["nurse_call"]}).to_csv(
        data_dir / "staff_contacts.csv",
        index=False,
    )

    results = generate_core_dashboards(data_dir, tmp_path / "eda")

    cohort_warnings = next(result.warnings for result in results if "cohort_overview" in result.artifact_id)
    assert any("Invalid boolean token" in warning and "has_ac" in warning for warning in cohort_warnings)
