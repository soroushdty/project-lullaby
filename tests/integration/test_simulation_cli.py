from __future__ import annotations

import json
import subprocess
import sys

import yaml

from src.simulation.config import default_config_dict


def _run_cli(*args):
    return subprocess.run(
        [sys.executable, "scripts/generate_synthetic.py", *args],
        check=False,
        capture_output=True,
        text=True,
    )


def test_generator_cli_happy_path(simulation_output_dir):
    result = _run_cli(
        "--config",
        "config/simulation.yaml",
        "--out-dir",
        str(simulation_output_dir),
        "--seed",
        "20260601",
    )

    assert result.returncode == 0
    assert "Ready for downstream: True" in result.stdout
    summary = json.loads((simulation_output_dir / "simulation_summary.json").read_text())
    assert summary["seed"] == 20260601


def test_generator_cli_invalid_config_returns_usage_error(tmp_path):
    bad_config = tmp_path / "bad.yaml"
    bad_config.write_text("n_participants: 0\n")

    result = _run_cli("--config", str(bad_config), "--out-dir", str(tmp_path / "out"))

    assert result.returncode == 2
    assert "ERROR:" in result.stderr


def test_generator_cli_schema_failure_leaves_artifacts_inspectable(tmp_path):
    raw = default_config_dict()
    raw["summer_heat"]["baseline_temp_f"] = 170
    raw["summer_heat"]["heat_wave_temp_f"] = 190
    config_path = tmp_path / "schema_fail.yaml"
    config_path.write_text(yaml.safe_dump(raw))
    out_dir = tmp_path / "out"

    result = _run_cli("--config", str(config_path), "--out-dir", str(out_dir))

    assert result.returncode == 1
    assert (out_dir / "daily_vitals.csv").exists()
    summary = json.loads((out_dir / "simulation_summary.json").read_text())
    assert summary["ready_for_downstream"] is False
    assert summary["schema_validation_status"] == "fail"


def test_generator_cli_target_failure_leaves_artifacts_inspectable(tmp_path):
    raw = default_config_dict()
    raw["summer_heat"]["enabled"] = False
    raw["event_rate"]["heat_illness"] = 0.20
    config_path = tmp_path / "target_fail.yaml"
    config_path.write_text(yaml.safe_dump(raw))
    out_dir = tmp_path / "out"

    result = _run_cli("--config", str(config_path), "--out-dir", str(out_dir))

    assert result.returncode == 1
    assert (out_dir / "simulation_summary.json").exists()
    summary = json.loads((out_dir / "simulation_summary.json").read_text())
    assert summary["ready_for_downstream"] is False
    assert any(check["status"] == "fail" for check in summary["target_checks"])
