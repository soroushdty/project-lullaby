from __future__ import annotations

import json
import shutil
from pathlib import Path

import pandas as pd
import pytest
from PIL import Image

from src.visualization.eda_longitudinal import LongitudinalInputError, generate_longitudinal_dashboards

from tests.test_eda_longitudinal_outputs import _write_longitudinal_fixture


def test_patient_timeline_contains_expected_tracks_and_summary_metadata(tmp_path):
    data_dir = _write_longitudinal_fixture(tmp_path / "timeline_data")
    out_dir = Path("outputs/figures/eda_test_spec009_timeline")
    shutil.rmtree(out_dir, ignore_errors=True)
    manifest_path = tmp_path / "manifest.json"

    results = generate_longitudinal_dashboards(
        data_dir,
        out_dir,
        manifest_path=manifest_path,
        participant_id="P2",
        overlay_environment=True,
    )

    timeline = next(result for result in results if result.artifact_id.endswith("07_patient_timeline"))
    path = out_dir / "07_patient_timeline.png"

    assert path.exists()
    with Image.open(path) as image:
        width, height = image.size
    assert width >= 1600
    assert height >= 900
    assert timeline.metadata["selected_participant"]["participant_id"] == "P2"
    assert timeline.metadata["track_counts"]["vital_tracks"] >= 5
    assert timeline.metadata["track_counts"]["alert_markers"] == 2
    assert timeline.metadata["track_counts"]["contact_markers"] == 1
    assert timeline.metadata["track_counts"]["outcome_markers"] == 1
    assert timeline.metadata["has_missingness_wear_track"] is True
    assert timeline.metadata["summary_fields"]["pih_severity"] == "severe"
    assert "insurance" in timeline.metadata["summary_fields"]
    assert "parity" in timeline.metadata["summary_fields"]

    manifest = json.loads(manifest_path.read_text())
    entry = next(entry for entry in manifest["entries"] if entry["artifact_id"].endswith("07_patient_timeline"))
    assert entry["metadata"]["selected_participant"]["participant_id"] == "P2"
    assert "alert.date" in entry["required_roles"]
    assert "contact.date" in entry["required_roles"]
    assert "outcome.cv_event_date" in entry["required_roles"]
    shutil.rmtree(out_dir, ignore_errors=True)


def test_patient_timeline_preserves_visible_vital_gaps(tmp_path):
    data_dir = _write_longitudinal_fixture(tmp_path / "timeline_gap_data")

    results = generate_longitudinal_dashboards(
        data_dir,
        tmp_path / "eda",
        manifest_path=tmp_path / "manifest.json",
        participant_id="P1",
    )

    timeline = next(result for result in results if result.artifact_id.endswith("07_patient_timeline"))

    assert timeline.metadata["vital_gap_days"]["vital.systolic_bp"] == [3]
    assert timeline.metadata["imputation_performed"] is False


def test_patient_timeline_missing_event_marker_roles_fail_before_write(tmp_path):
    data_dir = _write_longitudinal_fixture(tmp_path / "missing_alert_date")
    alerts = pd.read_csv(data_dir / "alerts.csv").drop(columns=["date"])
    alerts.to_csv(data_dir / "alerts.csv", index=False)
    out_dir = tmp_path / "eda"

    with pytest.raises(LongitudinalInputError) as excinfo:
        generate_longitudinal_dashboards(data_dir, out_dir, participant_id="P1")

    message = str(excinfo.value)
    assert "Panel 7" in message
    assert "alert.date" in message
    assert not out_dir.exists()
