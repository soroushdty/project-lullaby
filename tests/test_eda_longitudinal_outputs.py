from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest
from PIL import Image

from src.visualization.eda_longitudinal import (
    LONGITUDINAL_PANEL_FILENAMES,
    LongitudinalInputError,
    calculate_quality_scores,
    generate_longitudinal_dashboards,
    load_longitudinal_tables,
    prepare_selected_vital_series,
    select_default_participant,
)


def test_longitudinal_outputs_and_manifest_entries(tmp_path):
    data_dir = _write_longitudinal_fixture(tmp_path / "data")
    out_dir = Path("outputs/figures/eda_test_spec009_outputs")
    shutil.rmtree(out_dir, ignore_errors=True)
    manifest_path = tmp_path / "manifest.json"

    results = generate_longitudinal_dashboards(
        data_dir,
        out_dir,
        manifest_path=manifest_path,
        participant_id="P1",
        overlay_environment=True,
    )

    assert len(results) == 5
    for filename in LONGITUDINAL_PANEL_FILENAMES.values():
        path = out_dir / filename
        assert path.exists()
        with Image.open(path) as image:
            width, height = image.size
        assert width >= 1600
        assert height >= 900

    manifest = json.loads(manifest_path.read_text())
    entries = {entry["artifact_id"]: entry for entry in manifest["entries"]}
    expected_ids = {
        "eda_longitudinal_05_vital_trajectories",
        "eda_longitudinal_06_missingness_adherence",
        "eda_longitudinal_07_patient_timeline",
        "eda_longitudinal_08_data_quality_scorecard",
        "eda_longitudinal_09_missingness_mechanism",
    }
    assert all(any(artifact_id.endswith(expected) for artifact_id in entries) for expected in expected_ids)
    for artifact_id, entry in entries.items():
        assert entry["spec"] == "SPEC-009"
        assert entry["path"].startswith("outputs/")
        assert entry["required_roles"]
        assert entry["metadata"]
    vital_entry = next(entry for artifact_id, entry in entries.items() if artifact_id.endswith("05_vital_trajectories"))
    quality_entry = next(entry for artifact_id, entry in entries.items() if artifact_id.endswith("08_data_quality_scorecard"))
    assert vital_entry["metadata"]["selected_participant"]["participant_id"] == "P1"
    assert quality_entry["metadata"]["quality_score_formula"]["base_weights"]["wear_completeness"] == 0.40
    shutil.rmtree(out_dir, ignore_errors=True)


def test_generate_eda_cli_longitudinal_panels(tmp_path):
    data_dir = _write_longitudinal_fixture(tmp_path / "cli_data")
    out_dir = tmp_path / "cli_eda"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.visualization.generate_eda",
            "--data-dir",
            str(data_dir),
            "--out-dir",
            str(out_dir),
            "--panels",
            "longitudinal",
            "--participant-id",
            "P1",
            "--week-start",
            "1",
            "--week-end",
            "2",
            "--overlay-environment",
            "true",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Generated 5 EDA longitudinal dashboard artifacts" in result.stdout
    assert all((out_dir / filename).exists() for filename in LONGITUDINAL_PANEL_FILENAMES.values())


def test_required_longitudinal_input_failure_writes_nothing(tmp_path):
    data_dir = tmp_path / "missing"
    data_dir.mkdir()
    out_dir = tmp_path / "eda"
    manifest = tmp_path / "manifest.json"

    with pytest.raises(LongitudinalInputError, match="daily_vitals"):
        generate_longitudinal_dashboards(data_dir, out_dir, manifest_path=manifest)

    assert not out_dir.exists()
    assert not manifest.exists()


def test_invalid_week_range_and_unknown_participant_fail_before_writes(tmp_path):
    data_dir = _write_longitudinal_fixture(tmp_path / "data")

    with pytest.raises(LongitudinalInputError, match="week-start"):
        generate_longitudinal_dashboards(data_dir, tmp_path / "bad_week", week_start=3, week_end=2)

    with pytest.raises(LongitudinalInputError, match="NOT_REAL"):
        generate_longitudinal_dashboards(data_dir, tmp_path / "bad_participant", participant_id="NOT_REAL")


def test_panel7_marker_date_roles_are_required(tmp_path):
    data_dir = _write_longitudinal_fixture(tmp_path / "missing_marker_date")
    contacts = pd.read_csv(data_dir / "staff_contacts.csv").drop(columns=["contact_date"])
    contacts.to_csv(data_dir / "staff_contacts.csv", index=False)

    with pytest.raises(LongitudinalInputError) as excinfo:
        generate_longitudinal_dashboards(data_dir, tmp_path / "eda", participant_id="P1")

    message = str(excinfo.value)
    assert "contact.date" in message
    assert "Panel 7" in message


def test_selected_vital_series_preserves_missing_day_gap(tmp_path):
    data_dir = _write_longitudinal_fixture(tmp_path / "gap_data")
    tables = load_longitudinal_tables(data_dir)

    series = prepare_selected_vital_series(tables.daily_vitals, "P1", "vital.systolic_bp")

    day3 = series.loc[series["study_day"] == 3, "value"].iloc[0]
    assert pd.isna(day3)
    assert series["study_day"].tolist() == [1, 2, 3, 4, 5]


def test_default_participant_selection_records_richest_trace(tmp_path):
    data_dir = _write_longitudinal_fixture(tmp_path / "selection_data")
    tables = load_longitudinal_tables(data_dir)

    selected = select_default_participant(tables)

    assert selected.participant_id == "P2"
    assert selected.selection_mode == "automatic"
    assert selected.selection_score > 0
    assert "observed_vital_days" in selected.to_metadata()


def test_quality_score_formula_and_missing_component_redistribution(tmp_path):
    data_dir = _write_longitudinal_fixture(tmp_path / "quality_data")
    tables = load_longitudinal_tables(data_dir)
    scores, metadata, warnings = calculate_quality_scores(tables)

    assert {"wear_completeness", "scale_adherence", "vital_completeness", "contact_traceability"} <= set(scores.columns)
    assert metadata["base_weights"]["wear_completeness"] == 0.40
    assert warnings == []
    assert scores["quality_score"].between(0, 1).all()

    tables_without_wear = load_longitudinal_tables(data_dir)
    tables_without_wear.daily_vitals.drop(columns=["sensor_wear_hours"], inplace=True)
    adjusted_scores, adjusted_metadata, adjusted_warnings = calculate_quality_scores(tables_without_wear)

    assert "wear_completeness" in adjusted_metadata["unavailable_components"]
    assert any("wear_completeness unavailable" in warning for warning in adjusted_warnings)
    assert adjusted_scores["quality_score"].between(0, 1).all()
    assert abs(sum(adjusted_metadata["adjusted_weights"].values()) - 1.0) < 1e-9


def test_missingness_mechanism_metadata_is_exploratory_and_not_imputed(tmp_path):
    data_dir = _write_longitudinal_fixture(tmp_path / "mechanism_data")
    results = generate_longitudinal_dashboards(
        data_dir,
        tmp_path / "eda",
        manifest_path=tmp_path / "manifest.json",
        participant_id="P1",
        overlay_environment=True,
    )

    mechanism = next(result for result in results if result.artifact_id.endswith("09_missingness_mechanism"))

    assert "signals consistent with" in mechanism.metadata["mechanism_label"]
    assert mechanism.metadata["imputation_performed"] is False


def _write_longitudinal_fixture(data_dir: Path) -> Path:
    data_dir.mkdir()
    pd.DataFrame(
        {
            "participant_id": ["P1", "P2", "P3"],
            "observation_start_date": ["2026-06-01"] * 3,
            "pih_severity": ["mild", "severe", "mild"],
            "has_ac": [True, False, True],
            "insurance": ["private", "medicaid", "uninsured"],
            "para": [1, 2, 0],
            "bhls_health_literacy": [4.0, 2.5, 3.0],
            "mspss_social_support": [5.0, 3.0, 4.0],
            "epds_depression": [7.0, 11.0, 5.0],
            "pass_anxiety": [14.0, 18.0, 9.0],
            "archetype": ["steady", "true_emergency", "heat_strain"],
        }
    ).to_csv(data_dir / "participants.csv", index=False)

    rows = []
    for participant in ("P1", "P2", "P3"):
        days = [1, 2, 4, 5] if participant == "P1" else [1, 2, 3, 4, 5]
        for day in days:
            rows.append(
                {
                    "participant_id": participant,
                    "date": f"2026-06-{day:02d}",
                    "study_day": day,
                    "week": 1,
                    "systolic_bp": 118 + day + (20 if participant == "P2" and day == 4 else 0),
                    "diastolic_bp": 78 + day,
                    "heart_rate": 80 + day,
                    "respiratory_rate": 16 + day / 10,
                    "skin_temperature_c": 36.5 + day / 20,
                    "weight_kg": 70 + day / 10,
                    "body_water_pct": 51 - day / 10,
                    "sleep_hours": 6.5 - day / 20,
                    "steps": 3000 + day * 100,
                    "sensor_wear_hours": 20 - (0 if participant == "P2" else day / 4),
                    "scale_used": day % 2 == 1,
                    "ambient_temp_c": 34 + day,
                    "heat_index_c": 36 + day,
                    "archetype": "true_emergency" if participant == "P2" else "steady",
                }
            )
    daily = pd.DataFrame(rows)
    daily.loc[(daily["participant_id"] == "P1") & (daily["study_day"] == 4), "heart_rate"] = None
    daily.to_csv(data_dir / "daily_vitals.csv", index=False)

    pd.DataFrame(
        {
            "alert_id": ["A1", "A2", "A3"],
            "participant_id": ["P1", "P2", "P2"],
            "date": ["2026-06-02", "2026-06-03", "2026-06-04"],
            "alert_hour": [9, 15, 2],
            "alert_level": ["yellow", "red", "yellow"],
            "trigger_reasons": ["bp", "heat", "overnight"],
            "called_nurse": [True, True, False],
        }
    ).to_csv(data_dir / "alerts.csv", index=False)

    pd.DataFrame(
        {
            "contact_id": ["C1", "C2"],
            "participant_id": ["P1", "P2"],
            "contact_date": ["2026-06-02", "2026-06-04"],
            "contact_type": ["nurse_call", "nurse_call"],
            "completed": [True, False],
            "reason": ["alert", "followup"],
        }
    ).to_csv(data_dir / "staff_contacts.csv", index=False)

    pd.DataFrame(
        {
            "participant_id": ["P1", "P2", "P3"],
            "cv_event": [False, True, False],
            "cv_event_type": [None, "primary_cv_composite", None],
            "cv_event_date": [None, "2026-06-05", None],
            "ed_visit": [False, True, False],
            "hospitalized": [False, False, False],
            "heat_illness": [0, 1, 0],
        }
    ).to_csv(data_dir / "clinical_outcomes.csv", index=False)

    pd.DataFrame(
        {
            "date": [f"2026-06-{day:02d}" for day in range(1, 6)],
            "study_day": list(range(1, 6)),
            "ambient_temp_c": [34, 35, 36, 37, 38],
            "heat_index_c": [36, 37, 38, 39, 40],
            "heat_exposure_level": ["moderate", "high", "high", "extreme", "extreme"],
        }
    ).to_csv(data_dir / "environment.csv", index=False)
    return data_dir
