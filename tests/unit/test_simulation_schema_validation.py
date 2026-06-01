from __future__ import annotations

import pandas as pd

from src.simulation import generate_synthetic
from src.validation.semantics import DomainBooleanParsePolicy, parse_domain_boolean_series
from src.visualization.schema_registry import get_entity, resolve_column
from src.visualization.validation import validate_data_dir


REQUIRED_FILES = {
    "participants.csv",
    "daily_vitals.csv",
    "alerts.csv",
    "staff_contacts.csv",
    "clinical_outcomes.csv",
    "environment.csv",
    "recruitment.csv",
    "simulation_config_used.yaml",
    "simulation_summary.json",
}


def test_registry_has_synthetic_longitudinal_environment_recruitment_and_aliases():
    assert get_entity("environment").status == "future_optional"
    assert get_entity("recruitment").status == "future_optional"

    df = pd.DataFrame(
        {
            "participant_id": ["P0001"],
            "date": ["2026-06-01"],
            "systolic_bp": [120],
            "body_water_pct": [50],
            "weight_kg": [75],
            "sleep_hours": [6.5],
            "steps": [4200],
            "active_minutes": [32],
            "sensor_wear_hours": [18],
            "scale_used": [True],
            "ambient_temp_c": [35],
            "heat_index_c": [38],
        }
    )

    assert resolve_column(df, "vital.body_water_pct", entity="daily_vitals").column == "body_water_pct"
    assert resolve_column(df, "vital.scale_used", entity="daily_vitals").column == "scale_used"
    assert resolve_column(df, "vital.heat_index_c", entity="daily_vitals").column == "heat_index_c"


def test_output_package_required_files_full_grid_and_schema_validation(simulation_output_dir):
    result = generate_synthetic("config/simulation.yaml", out_dir=simulation_output_dir, seed=20260601)

    assert REQUIRED_FILES.issubset({path.name for path in simulation_output_dir.iterdir()})
    daily = pd.read_csv(simulation_output_dir / "daily_vitals.csv")
    assert len(daily) == 200 * 84
    assert daily[["participant_id", "date"]].duplicated().sum() == 0
    validation = validate_data_dir(simulation_output_dir)
    assert validation.status != "fail"
    assert result.ready_for_downstream


def test_raw_nulls_and_post_dropout_full_grid_are_preserved(simulation_output_dir):
    generate_synthetic("config/simulation.yaml", out_dir=simulation_output_dir, seed=20260601)
    daily = pd.read_csv(simulation_output_dir / "daily_vitals.csv")

    assert daily["systolic_bp"].isna().any()
    dropout_rows = daily.loc[_bool_mask(daily, "dropout_active")]
    assert not dropout_rows.empty
    assert dropout_rows["heart_rate"].isna().all()
    assert daily.groupby("participant_id")["study_day"].count().eq(84).all()


def test_alerts_and_outcomes_align_to_cv_heat_and_overlap_cases(simulation_output_dir):
    generate_synthetic("config/simulation.yaml", out_dir=simulation_output_dir, seed=20260601)
    daily = pd.read_csv(simulation_output_dir / "daily_vitals.csv")
    alerts = pd.read_csv(simulation_output_dir / "alerts.csv")
    outcomes = pd.read_csv(simulation_output_dir / "clinical_outcomes.csv")

    cv_ids = set(outcomes.loc[_bool_mask(outcomes, "cv_event"), "participant_id"])
    heat_ids = set(outcomes.loc[_bool_mask(outcomes, "heat_illness"), "participant_id"])
    assert cv_ids
    assert heat_ids
    assert cv_ids.issubset(set(daily.loc[_bool_mask(daily, "cv_event_window"), "participant_id"]))
    assert heat_ids.issubset(set(daily.loc[_bool_mask(daily, "heat_strain_day"), "participant_id"]))
    assert {"cv_like", "heat_like", "overlap"} & set(alerts["classification"])
    assert alerts["alert_level"].isin(["yellow", "red", "composite-red"]).all()


def _bool_mask(frame: pd.DataFrame, column: str) -> pd.Series:
    parsed = parse_domain_boolean_series(
        frame[column],
        DomainBooleanParsePolicy(role=column, required=True),
        source_column=column,
    )
    assert not parsed.errors
    return parsed.true_mask
