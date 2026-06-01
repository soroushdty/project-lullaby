from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
from PIL import Image

from src.visualization.eda_relationships import (
    RELATIONSHIP_PANEL_FILENAMES,
    generate_relationship_dashboards,
)


def test_relationship_outputs_and_manifest_entries(tmp_path):
    data_dir = _write_spec010_fixture(tmp_path / "data")
    out_dir = Path("outputs/figures/eda_test_spec010_outputs")
    shutil.rmtree(out_dir, ignore_errors=True)
    manifest_path = tmp_path / "manifest.json"

    results = generate_relationship_dashboards(data_dir, out_dir, manifest_path=manifest_path)

    assert len(results) == 4
    for filename in RELATIONSHIP_PANEL_FILENAMES.values():
        path = out_dir / filename
        assert path.exists()
        with Image.open(path) as image:
            width, height = image.size
        assert width >= 1600
        assert height >= 900

    manifest = json.loads(manifest_path.read_text())
    entries = {entry["artifact_id"]: entry for entry in manifest["entries"]}
    expected_suffixes = {
        "eda_relationships_10_relationships",
        "eda_relationships_11_heat_environment",
        "eda_relationships_12_archetype_explorer",
        "eda_relationships_13_recruitment_timeline",
    }
    assert all(any(artifact_id.endswith(suffix) for artifact_id in entries) for suffix in expected_suffixes)
    for entry in entries.values():
        assert entry["spec"] == "SPEC-010"
        assert entry["path"].startswith("outputs/")
        assert entry["required_roles"]
        assert entry["metadata"]

    relationship = next(entry for entry in entries.values() if entry["artifact_id"].endswith("10_relationships"))
    heat = next(entry for entry in entries.values() if entry["artifact_id"].endswith("11_heat_environment"))
    archetypes = next(entry for entry in entries.values() if entry["artifact_id"].endswith("12_archetype_explorer"))
    recruitment = next(entry for entry in entries.values() if entry["artifact_id"].endswith("13_recruitment_timeline"))

    assert "observed pairs only" in relationship["metadata"]["observed_data_policy"].lower()
    assert relationship["metadata"]["pairwise_n"]["heat_index_bivariates"]["heart_rate"] > 0
    assert heat["metadata"]["environment_data_fabricated"] is False
    assert heat["metadata"]["environment_available"] is True
    assert archetypes["metadata"]["label_source"] == "explicit"
    assert {row["archetype"] for row in archetypes["metadata"]["segments"]} >= {
        "diligent monitor",
        "overwhelmed mom",
        "heat-stressed",
        "true emergency",
        "silent decliner",
    }
    assert recruitment["metadata"]["calendar_aware"] is True
    shutil.rmtree(out_dir, ignore_errors=True)


def test_heat_environment_unavailable_panel_without_environment(tmp_path):
    data_dir = _write_spec010_fixture(tmp_path / "no_environment", include_environment=False)

    results = generate_relationship_dashboards(data_dir, tmp_path / "eda", manifest_path=tmp_path / "manifest.json")

    heat = next(result for result in results if result.artifact_id.endswith("11_heat_environment"))
    assert heat.path.exists()
    assert heat.metadata["environment_available"] is False
    assert heat.metadata["environment_data_fabricated"] is False
    assert any("environment table unavailable" in warning for warning in heat.warnings)


def test_archetype_labels_are_provisional_when_explicit_labels_absent(tmp_path):
    data_dir = _write_spec010_fixture(tmp_path / "provisional", include_archetype=False)

    results = generate_relationship_dashboards(data_dir, tmp_path / "eda", manifest_path=tmp_path / "manifest.json")

    archetypes = next(result for result in results if result.artifact_id.endswith("12_archetype_explorer"))
    assert archetypes.metadata["label_source"] == "provisional"
    assert archetypes.metadata["provisional"] is True
    assert archetypes.metadata["rule_summary"]
    assert {row["archetype"] for row in archetypes.metadata["segments"]} >= {
        "diligent monitor",
        "overwhelmed mom",
        "heat-stressed",
        "true emergency",
        "silent decliner",
    }


def test_recruitment_timeline_unavailable_when_dates_are_missing(tmp_path):
    data_dir = _write_spec010_fixture(
        tmp_path / "missing_dates",
        include_environment=False,
        include_recruitment=False,
        parseable_dates=False,
    )

    results = generate_relationship_dashboards(data_dir, tmp_path / "eda", manifest_path=tmp_path / "manifest.json")

    timeline = next(result for result in results if result.artifact_id.endswith("13_recruitment_timeline"))
    assert timeline.path.exists()
    assert timeline.metadata["calendar_aware"] is False
    assert any("timeline unavailable" in warning or "no parseable calendar dates" in warning for warning in timeline.warnings)


def test_generate_eda_cli_relationships_panels(tmp_path):
    data_dir = _write_spec010_fixture(tmp_path / "cli_data")
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
            "relationships",
            "--manifest",
            str(tmp_path / "manifest.json"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Generated 4 EDA relationships dashboard artifacts" in result.stdout
    assert all((out_dir / filename).exists() for filename in RELATIONSHIP_PANEL_FILENAMES.values())


def _write_spec010_fixture(
    data_dir: Path,
    *,
    include_environment: bool = True,
    include_recruitment: bool = True,
    include_archetype: bool = True,
    parseable_dates: bool = True,
) -> Path:
    data_dir.mkdir()
    participant_rows = {
        "participant_id": ["P1", "P2", "P3", "P4", "P5"],
        "enrollment_date": ["2026-05-20", "2026-05-21", "2026-05-22", "2026-05-23", "2026-05-24"],
        "delivery_date": ["2026-05-31"] * 5,
        "observation_start_date": ["2026-06-01"] * 5,
        "pih_severity": ["mild", "moderate", "mild", "severe", "moderate"],
        "has_ac": [True, True, False, True, False],
        "health_literacy": [4.5, 2.4, 3.2, 3.8, 2.9],
        "social_support": [4.6, 2.8, 3.6, 4.0, 2.5],
        "depression": [5, 12, 8, 7, 13],
        "anxiety": [8, 20, 13, 12, 19],
    }
    if include_archetype:
        participant_rows["archetype"] = [
            "diligent_monitor",
            "overwhelmed_mom",
            "heat_stressed",
            "true_emergency",
            "silent_decliner",
        ]
    if not parseable_dates:
        participant_rows["enrollment_date"] = [""] * 5
        participant_rows["delivery_date"] = [""] * 5
        participant_rows["observation_start_date"] = [""] * 5
    pd.DataFrame(participant_rows).to_csv(data_dir / "participants.csv", index=False)

    rows = []
    for participant in ["P1", "P2", "P3", "P4", "P5"]:
        for day in range(1, 6):
            date_value = f"2026-06-{day:02d}" if parseable_dates else "not-a-date"
            missing_for_silent = participant == "P5" and day >= 3
            rows.append(
                {
                    "participant_id": participant,
                    "date": date_value,
                    "study_day": day,
                    "systolic_bp": None if missing_for_silent else 118 + day + (45 if participant == "P4" and day >= 4 else 0),
                    "diastolic_bp": None if missing_for_silent else 76 + day + (30 if participant == "P4" and day >= 4 else 0),
                    "heart_rate": None if missing_for_silent else 78 + day + (15 if participant in {"P3", "P4"} else 0),
                    "respiratory_rate": None if missing_for_silent else 16 + day / 10,
                    "skin_temperature_c": None if missing_for_silent else 36.3 + day / 10 + (0.6 if participant == "P3" else 0),
                    "weight_kg": None if missing_for_silent else 70 + day / 10,
                    "body_water_pct": None if missing_for_silent else 52 + (day / 10 if participant == "P4" else -day / 10 if participant == "P3" else 0),
                    "sleep_hours": None if participant == "P2" and day >= 4 else 6.5,
                    "steps": 3500 + day * 100,
                    "sensor_wear_hours": 22 if participant == "P1" else 14 if participant == "P5" else 18,
                    "scale_used": participant != "P5" or day < 3,
                    "heat_index_c": 37 + day + (3 if participant == "P3" else 0),
                }
            )
    pd.DataFrame(rows).to_csv(data_dir / "daily_vitals.csv", index=False)

    pd.DataFrame(
        {
            "participant_id": ["P1", "P2", "P3", "P4", "P5"],
            "cv_event": [False, False, False, True, False],
            "cv_event_date": [None, None, None, "2026-06-05" if parseable_dates else None, None],
            "ed_visit": [False, False, False, True, False],
            "hospitalized": [False, False, False, False, False],
            "heat_illness": [0, 0, 1, 0, 0],
        }
    ).to_csv(data_dir / "clinical_outcomes.csv", index=False)

    pd.DataFrame(
        {
            "alert_id": ["A1", "A2", "A3", "A4"],
            "participant_id": ["P2", "P3", "P4", "P4"],
            "date": ["2026-06-02", "2026-06-03", "2026-06-04", "2026-06-05"] if parseable_dates else [""] * 4,
            "alert_level": ["yellow", "yellow", "red", "yellow"],
        }
    ).to_csv(data_dir / "alerts.csv", index=False)

    pd.DataFrame(
        {
            "participant_id": ["P1", "P2"],
            "contact_date": ["2026-06-02", "2026-06-04"] if parseable_dates else ["", ""],
            "contact_type": ["nurse_call", "nurse_call"],
        }
    ).to_csv(data_dir / "staff_contacts.csv", index=False)

    if include_environment:
        pd.DataFrame(
            {
                "date": [f"2026-06-{day:02d}" for day in range(1, 6)] if parseable_dates else [""] * 5,
                "study_day": list(range(1, 6)),
                "ambient_temp_c": [34, 35, None, 38, 39],
                "heat_index_c": [36, 37, 39, 42, 43],
                "heat_wave": [False, False, True, True, True],
                "heat_exposure_level": ["moderate", "high", "high", "extreme", "extreme"],
            }
        ).to_csv(data_dir / "environment.csv", index=False)

    if include_recruitment:
        pd.DataFrame(
            {
                "participant_id": ["P1", "P2", "P3", "P4", "P5"],
                "recruitment_date": ["2026-05-18", "2026-05-18", "2026-05-19", "2026-05-20", "2026-05-21"] if parseable_dates else [""] * 5,
                "recruitment_source": ["postpartum_unit"] * 5,
                "eligible": [True] * 5,
                "enrolled": [True] * 5,
            }
        ).to_csv(data_dir / "recruitment.csv", index=False)
    return data_dir
