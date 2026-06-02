from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import warnings

import pytest

from src.visualization.artifacts import (
    FigureArtifact,
    ManifestValidationError,
    participant_compatibility_artifact,
    read_manifest,
    register_artifact,
    validate_manifest,
)
from src.visualization.eda_core import generate_core_dashboards


def test_manifest_entries_are_sorted(visualization_paths):
    register_artifact(
        visualization_paths["manifest"],
        FigureArtifact(
            artifact_id="b",
            path="outputs/figures/b.png",
            title="B",
            spec="SPEC-004",
            inputs=[],
            required_roles=[],
        ),
    )
    register_artifact(
        visualization_paths["manifest"],
        FigureArtifact(
            artifact_id="a",
            path="outputs/figures/a.png",
            title="A",
            spec="SPEC-004",
            inputs=[],
            required_roles=[],
            warnings=["missing optional role"],
        ),
    )
    manifest = read_manifest(visualization_paths["manifest"])
    assert [entry["artifact_id"] for entry in manifest.entries] == ["a", "b"]
    assert manifest.entries[0]["warnings"] == ["missing optional role"]


def test_timestamp_must_be_timezone_aware():
    entry = FigureArtifact(
        artifact_id="bad",
        path="outputs/figures/bad.png",
        title="Bad",
        spec="SPEC-004",
        inputs=[],
        required_roles=[],
        created_at_utc=datetime.now().isoformat(),
    ).to_dict()
    with pytest.raises(ManifestValidationError):
        validate_manifest({"entries": [entry]})


def test_participant_compatibility_artifact_defaults_to_outputs_figures():
    artifact = participant_compatibility_artifact()
    assert artifact.artifact_id == "participant_visualization_compatibility"
    assert artifact.path.startswith("outputs/figures/")


def test_manifest_allows_safe_repo_relative_alternate_paths(visualization_paths):
    register_artifact(
        visualization_paths["manifest"],
        FigureArtifact(
            artifact_id="alternate",
            path="tmp_figures/eda/panel.png",
            title="Alternate",
            spec="SPEC-007",
            inputs=["participants"],
            required_roles=["participant.id"],
        ),
    )

    manifest = read_manifest(visualization_paths["manifest"])
    assert manifest.entries[0]["path"] == "tmp_figures/eda/panel.png"


def test_outside_repo_outputs_warn_and_do_not_register(tmp_path, monkeypatch):
    monkeypatch.delenv("LULLABY_TEST_MODE", raising=False)
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _write_core_fixture(data_dir)
    manifest = tmp_path / "manifest.json"

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        generate_core_dashboards(data_dir, tmp_path / "outside" / "eda", manifest_path=manifest)

    assert any("outside the repository" in str(item.message) for item in caught)
    assert not manifest.exists()


def _write_core_fixture(data_dir: Path) -> None:
    import pandas as pd

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
