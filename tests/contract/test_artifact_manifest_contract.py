from __future__ import annotations

import pytest

from src.visualization.artifacts import (
    FigureArtifact,
    ManifestValidationError,
    create_empty_manifest,
    register_artifact,
    validate_manifest,
)


def _artifact(**overrides):
    data = {
        "artifact_id": "test_artifact",
        "path": "outputs/figures/test.png",
        "title": "Test Artifact",
        "spec": "SPEC-004A",
        "inputs": ["participants"],
        "required_roles": ["participant.id"],
    }
    data.update(overrides)
    return FigureArtifact(**data)


def test_empty_manifest_validates(visualization_paths):
    manifest = create_empty_manifest(visualization_paths["manifest"])
    validate_manifest(manifest)
    assert manifest.entries == []


def test_register_entry_preserves_required_fields(visualization_paths):
    manifest = register_artifact(visualization_paths["manifest"], _artifact())
    entry = manifest.entries[0]
    assert entry["artifact_id"] == "test_artifact"
    assert entry["deterministic"] is True


def test_invalid_artifact_path_fails_validation():
    with pytest.raises(ManifestValidationError):
        validate_manifest(
            {
                "entries": [
                    _artifact(path="../outside.png").to_dict(),
                ]
            }
        )


def test_missing_required_manifest_field_fails():
    entry = _artifact().to_dict()
    entry.pop("title")
    with pytest.raises(ManifestValidationError):
        validate_manifest({"entries": [entry]})


def test_duplicate_artifact_id_with_different_metadata_fails(visualization_paths):
    register_artifact(visualization_paths["manifest"], _artifact())
    with pytest.raises(ManifestValidationError):
        register_artifact(
            visualization_paths["manifest"],
            _artifact(title="Different"),
        )
