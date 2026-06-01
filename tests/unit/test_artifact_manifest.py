from __future__ import annotations

from datetime import UTC, datetime

import pytest

from src.visualization.artifacts import (
    FigureArtifact,
    ManifestValidationError,
    participant_compatibility_artifact,
    read_manifest,
    register_artifact,
    validate_manifest,
)


def test_manifest_entries_are_sorted(visualization_paths):
    register_artifact(
        visualization_paths["manifest"],
        FigureArtifact(
            artifact_id="b",
            path="outputs/figures/b.png",
            title="B",
            spec="SPEC-004A",
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
            spec="SPEC-004A",
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
        spec="SPEC-004A",
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
