from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest
from PIL import Image

from src.visualization.eda_core import EDAInputError, PANEL_FILENAMES, generate_core_dashboards


def test_core_eda_outputs_and_manifest_entries():
    out_dir = Path("outputs/figures/eda")
    results = generate_core_dashboards("data/raw", out_dir)

    assert len(results) == 4
    for filename in PANEL_FILENAMES.values():
        path = out_dir / filename
        assert path.exists()
        with Image.open(path) as image:
            width, height = image.size
        assert width >= 1600
        assert height >= 900

    manifest = json.loads(Path("outputs/figures/manifest.json").read_text())
    entries = {entry["path"]: entry for entry in manifest["entries"]}
    for filename in PANEL_FILENAMES.values():
        path = f"outputs/figures/eda/{filename}"
        assert path in entries
        assert entries[path]["spec"] == "SPEC-006"
        assert entries[path]["title"]
        assert entries[path]["required_roles"]


def test_generate_eda_cli_core_panels(tmp_path):
    import subprocess
    import sys

    out_dir = tmp_path / "eda"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.visualization.generate_eda",
            "--data-dir",
            "data/synthetic/longitudinal",
            "--out-dir",
            str(out_dir),
            "--panels",
            "core",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Generated 4 EDA core dashboard artifacts" in result.stdout
    assert all((out_dir / filename).exists() for filename in PANEL_FILENAMES.values())


def test_required_table_missing_fails_before_artifacts_or_manifest(tmp_path):
    data_dir = tmp_path / "missing_required"
    data_dir.mkdir()
    out_dir = tmp_path / "eda"
    manifest = tmp_path / "manifest.json"

    with pytest.raises(EDAInputError, match="clinical_outcomes"):
        generate_core_dashboards(data_dir, out_dir, manifest_path=manifest)

    assert not out_dir.exists()
    assert not manifest.exists()


def test_schema_invalid_required_role_names_entity_path_and_role(tmp_path):
    data_dir = _write_core_fixture(tmp_path / "invalid_required")
    (data_dir / "clinical_outcomes.csv").write_text("participant_id,cv_event\nP1,maybe\n")

    with pytest.raises(EDAInputError) as excinfo:
        generate_core_dashboards(data_dir, tmp_path / "eda", manifest_path=tmp_path / "manifest.json")

    message = str(excinfo.value)
    assert "clinical_outcomes" in message
    assert "clinical_outcomes.csv" in message
    assert "outcome.cv_event" in message
    assert "maybe" in message


def test_generate_eda_cli_required_failure_returns_nonzero(tmp_path):
    import subprocess
    import sys

    data_dir = tmp_path / "missing_cli_required"
    data_dir.mkdir()

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.visualization.generate_eda",
            "--data-dir",
            str(data_dir),
            "--out-dir",
            str(tmp_path / "eda"),
            "--panels",
            "core",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "Required EDA input validation failed" in result.stderr


def test_trigger_reason_overflow_is_preserved_in_manifest_metadata(tmp_path):
    data_dir = _write_core_fixture(tmp_path / "many_reasons")
    reasons = [f"reason_{idx}" for idx in range(12)]
    pd.DataFrame(
        {
            "alert_id": [f"A{idx}" for idx in range(12)],
            "participant_id": ["P1"] * 12,
            "alert_level": ["yellow"] * 12,
            "trigger_reasons": reasons,
        }
    ).to_csv(data_dir / "alerts.csv", index=False)
    manifest = tmp_path / "outputs" / "figures" / "manifest.json"

    results = generate_core_dashboards(data_dir, tmp_path / "eda", manifest_path=manifest)

    alert_result = next(result for result in results if "alert_engagement_funnel" in result.artifact_id)
    assert any("trigger_reasons overflow categories preserved" in warning for warning in alert_result.warnings)
    assert "category_completeness" in alert_result.metadata


def test_low_count_demographic_categories_are_not_suppressed(tmp_path):
    data_dir = _write_core_fixture(tmp_path / "low_count_categories")
    pd.DataFrame(
        {
            "participant_id": ["P1", "P2", "P3"],
            "race_ethnicity": ["A", "B", "C"],
            "insurance": ["private", "medicaid", "uninsured"],
        }
    ).to_csv(data_dir / "participants.csv", index=False)

    results = generate_core_dashboards(data_dir, tmp_path / "eda", manifest_path=tmp_path / "manifest.json")

    assert len(results) == 4
    assert (tmp_path / "eda" / PANEL_FILENAMES["cohort_overview"]).exists()


def _write_core_fixture(data_dir: Path) -> Path:
    data_dir.mkdir()
    pd.DataFrame({"participant_id": ["P1"], "age": [31], "has_ac": [True]}).to_csv(
        data_dir / "participants.csv",
        index=False,
    )
    pd.DataFrame({"participant_id": ["P1"], "date": ["2026-06-01"], "systolic_bp": [120]}).to_csv(
        data_dir / "daily_vitals.csv",
        index=False,
    )
    pd.DataFrame({"participant_id": ["P1"], "cv_event": [False]}).to_csv(
        data_dir / "clinical_outcomes.csv",
        index=False,
    )
    pd.DataFrame({"alert_id": ["A1"], "participant_id": ["P1"], "alert_level": ["yellow"]}).to_csv(
        data_dir / "alerts.csv",
        index=False,
    )
    pd.DataFrame({"participant_id": ["P1"], "contact_type": ["nurse_call"]}).to_csv(
        data_dir / "staff_contacts.csv",
        index=False,
    )
    return data_dir
