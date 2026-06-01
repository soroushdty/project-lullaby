from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from src.visualization.eda_core import PANEL_FILENAMES, generate_core_dashboards


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
