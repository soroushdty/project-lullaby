from __future__ import annotations

import pandas as pd

from src.visualization.eda_core import generate_core_dashboards, load_eda_tables


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
