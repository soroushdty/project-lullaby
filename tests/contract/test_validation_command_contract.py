from __future__ import annotations

import json
import subprocess
import sys


def _run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "src.cli.validate_visualization_foundation", *args],
        check=False,
        capture_output=True,
        text=True,
    )


def test_cli_defaults_to_data_dir_with_custom_report_and_manifest(visualization_paths):
    result = _run_cli(
        "--report",
        str(visualization_paths["report"]),
        "--manifest",
        str(visualization_paths["manifest"]),
    )
    assert result.returncode == 0
    assert "Data directory: data" in result.stdout
    report = json.loads(visualization_paths["report"].read_text())
    assert report["data_dir"] == "data"
    assert visualization_paths["manifest"].exists()


def test_cli_config_loading_overrides_paths(tmp_path):
    report = tmp_path / "report.json"
    manifest = tmp_path / "outputs" / "figures" / "manifest.json"
    config = tmp_path / "visualization.yaml"
    config.write_text(
        "\n".join(
            [
                "data_dir: data/synthetic",
                f"validation_report_path: {report}",
                f"manifest_path: {manifest}",
            ]
        )
    )
    result = _run_cli("--config", str(config))
    assert result.returncode == 0
    assert report.exists()
    assert manifest.exists()
    payload = json.loads(report.read_text())
    assert payload["data_dir"] == "data/synthetic"


def test_cli_missing_required_role_exits_one(tmp_path, visualization_paths):
    data_dir = tmp_path / "bad-data"
    data_dir.mkdir()
    _write_minimal_tables(data_dir, include_sbp=False)
    result = _run_cli(
        "--data-dir",
        str(data_dir),
        "--report",
        str(visualization_paths["report"]),
        "--manifest",
        str(visualization_paths["manifest"]),
    )
    assert result.returncode == 1
    payload = json.loads(visualization_paths["report"].read_text())
    assert payload["status"] == "fail"
    assert "vital.systolic_bp" in json.dumps(payload)


def test_cli_usage_error_exits_two():
    result = _run_cli("--unknown-flag")
    assert result.returncode == 2


def _write_minimal_tables(data_dir, *, include_sbp: bool = True):
    (data_dir / "lullaby_participants.csv").write_text("participant_id\nP1\n")
    daily_header = "participant_id,date"
    daily_values = "P1,2026-01-01"
    if include_sbp:
        daily_header += ",sbp_mean"
        daily_values += ",120"
    (data_dir / "lullaby_daily_vitals.csv").write_text(
        f"{daily_header}\n{daily_values}\n"
    )
    (data_dir / "lullaby_alerts.csv").write_text(
        "alert_id,participant_id,alert_level\nA1,P1,yellow\n"
    )
    (data_dir / "lullaby_staff_contacts.csv").write_text("contact_type\nphone\n")
    (data_dir / "lullaby_clinical_outcomes.csv").write_text(
        "participant_id,cv_event\nP1,False\n"
    )
