from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.visualization.config import VisualizationConfig


class ManifestValidationError(ValueError):
    pass


@dataclass(frozen=True)
class FigureArtifact:
    artifact_id: str
    path: str
    title: str
    spec: str
    inputs: list[str]
    required_roles: list[str]
    optional_roles_used: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at_utc: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    deterministic: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FigureArtifactManifest:
    schema_version: str = "1.0.0"
    manifest_path: str = "outputs/figures/manifest.json"
    entries: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "manifest_path": self.manifest_path,
            "entries": sorted(self.entries, key=lambda e: e["artifact_id"]),
            "warnings": self.warnings,
        }


REQUIRED_ENTRY_FIELDS = {
    "artifact_id",
    "path",
    "title",
    "spec",
    "inputs",
    "required_roles",
    "optional_roles_used",
    "warnings",
    "created_at_utc",
    "deterministic",
}


def create_empty_manifest(
    path: Path | str | None = None,
    *,
    config: VisualizationConfig | None = None,
) -> FigureArtifactManifest:
    path = _manifest_path(path, config)
    if path.exists():
        return read_manifest(path)
    manifest = FigureArtifactManifest(manifest_path=_repo_relative(path))
    write_manifest(path, manifest)
    return manifest


def read_manifest(path: Path | str) -> FigureArtifactManifest:
    path = Path(path)
    data = json.loads(path.read_text())
    manifest = FigureArtifactManifest(
        schema_version=data.get("schema_version", "1.0.0"),
        manifest_path=data.get("manifest_path", _repo_relative(path)),
        entries=list(data.get("entries", [])),
        warnings=list(data.get("warnings", [])),
    )
    validate_manifest(manifest)
    return manifest


def write_manifest(path: Path | str, manifest: FigureArtifactManifest) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    validate_manifest(manifest)
    path.write_text(json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n")
    return path


def validate_manifest(manifest: FigureArtifactManifest | dict[str, Any]) -> None:
    data = manifest.to_dict() if isinstance(manifest, FigureArtifactManifest) else manifest
    if "entries" not in data or not isinstance(data["entries"], list):
        raise ManifestValidationError("Manifest requires an entries list")
    seen: set[str] = set()
    for entry in data["entries"]:
        missing = REQUIRED_ENTRY_FIELDS - set(entry)
        if missing:
            raise ManifestValidationError(f"Manifest entry missing fields: {sorted(missing)}")
        artifact_id = entry["artifact_id"]
        if artifact_id in seen:
            raise ManifestValidationError(f"Duplicate artifact_id: {artifact_id}")
        seen.add(artifact_id)
        _validate_entry_path(entry["path"])
        _validate_timestamp(entry["created_at_utc"])


def register_artifact(
    manifest_path: Path | str,
    artifact: FigureArtifact | dict[str, Any],
) -> FigureArtifactManifest:
    path = Path(manifest_path)
    manifest = create_empty_manifest(path)
    entry = artifact.to_dict() if isinstance(artifact, FigureArtifact) else dict(artifact)
    validate_manifest(
        FigureArtifactManifest(
            manifest_path=manifest.manifest_path,
            entries=[entry],
            warnings=[],
        )
    )
    entries = list(manifest.entries)
    for existing in entries:
        if existing["artifact_id"] != entry["artifact_id"]:
            continue
        if _same_except_timestamp(existing, entry):
            return manifest
        raise ManifestValidationError(f"Duplicate artifact_id with different metadata: {entry['artifact_id']}")
    entries.append(entry)
    updated = FigureArtifactManifest(
        schema_version=manifest.schema_version,
        manifest_path=manifest.manifest_path,
        entries=entries,
        warnings=manifest.warnings,
    )
    write_manifest(path, updated)
    return updated


def participant_compatibility_artifact_path(
    output_root: Path | str = Path("outputs/figures"),
) -> Path:
    return Path(output_root) / "participant_visualization_compatibility.png"


def participant_compatibility_artifact(
    output_root: Path | str = Path("outputs/figures"),
) -> FigureArtifact:
    path = participant_compatibility_artifact_path(output_root)
    return FigureArtifact(
        artifact_id="participant_visualization_compatibility",
        path=_repo_relative(path),
        title="Participant Visualization Compatibility",
        spec="SPEC-004A",
        inputs=["participants"],
        required_roles=["participant.id"],
        optional_roles_used=[],
        warnings=[],
        deterministic=True,
    )


def _manifest_path(
    path: Path | str | None,
    config: VisualizationConfig | None,
) -> Path:
    if path is not None:
        return Path(path)
    if config is not None:
        return config.manifest_path
    return VisualizationConfig().manifest_path


def _validate_entry_path(path_value: str) -> None:
    path = Path(path_value)
    if path.is_absolute() or ".." in path.parts:
        raise ManifestValidationError(f"Artifact path must be repository-relative: {path_value}")
    if not path.parts:
        raise ManifestValidationError(f"Artifact path must be repository-relative: {path_value}")


def _validate_timestamp(value: str) -> None:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ManifestValidationError("created_at_utc must include timezone")


def _repo_relative(path: Path) -> str:
    path = Path(path)
    try:
        return path.relative_to(Path.cwd()).as_posix()
    except ValueError:
        return path.as_posix()


def _same_except_timestamp(left: dict[str, Any], right: dict[str, Any]) -> bool:
    left_cmp = {k: v for k, v in left.items() if k != "created_at_utc"}
    right_cmp = {k: v for k, v in right.items() if k != "created_at_utc"}
    return left_cmp == right_cmp


__all__ = [
    "FigureArtifact",
    "FigureArtifactManifest",
    "ManifestValidationError",
    "create_empty_manifest",
    "participant_compatibility_artifact",
    "participant_compatibility_artifact_path",
    "read_manifest",
    "register_artifact",
    "validate_manifest",
    "write_manifest",
]
