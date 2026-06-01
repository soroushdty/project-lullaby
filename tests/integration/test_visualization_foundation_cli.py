from __future__ import annotations

import json
import subprocess
import sys
import time

from src.visualization.artifacts import participant_compatibility_artifact_path


def _run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "src.cli.validate_visualization_foundation", *args],
        check=False,
        capture_output=True,
        text=True,
    )


def test_default_data_validation_from_repo_root(visualization_paths):
    result = _run_cli(
        "--report",
        str(visualization_paths["report"]),
        "--manifest",
        str(visualization_paths["manifest"]),
    )
    assert result.returncode == 0
    assert "Status:" in result.stdout
    payload = json.loads(visualization_paths["report"].read_text())
    assert payload["entities"]["participants"]["row_count"] > 0
    assert visualization_paths["manifest"].exists()


def test_synthetic_data_validation_from_repo_root(visualization_paths):
    result = _run_cli(
        "--data-dir",
        "data/synthetic",
        "--report",
        str(visualization_paths["report"]),
        "--manifest",
        str(visualization_paths["manifest"]),
    )
    assert result.returncode == 0
    payload = json.loads(visualization_paths["report"].read_text())
    assert payload["data_dir"] == "data/synthetic"


def test_cli_module_is_importable():
    from src.cli.validate_visualization_foundation import build_parser

    assert build_parser().prog


def test_participant_compatibility_artifact_path_is_dashboard_grade_location():
    path = participant_compatibility_artifact_path()
    assert path.as_posix() == "outputs/figures/participant_visualization_compatibility.png"


def test_focused_foundation_cli_completes_under_two_minutes(visualization_paths):
    start = time.monotonic()
    result = _run_cli(
        "--report",
        str(visualization_paths["report"]),
        "--manifest",
        str(visualization_paths["manifest"]),
    )
    elapsed = time.monotonic() - start
    assert result.returncode == 0
    assert elapsed < 120
