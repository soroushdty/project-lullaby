from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.visualization import schema_registry as registry


@dataclass
class EntityValidationResult:
    status: str
    entity: str
    source_file: str
    row_count: int
    resolved_roles: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    extra_columns: list[str] = field(default_factory=list)
    range_violations: list[dict[str, Any]] = field(default_factory=list)
    capture_worthy_values: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "source_file": self.source_file,
            "row_count": self.row_count,
            "resolved_roles": self.resolved_roles,
            "warnings": self.warnings,
            "errors": self.errors,
            "extra_columns": self.extra_columns,
            "range_violations": self.range_violations,
            "capture_worthy_values": self.capture_worthy_values,
        }


@dataclass
class ValidationResult:
    status: str
    data_dir: str
    report_path: str = "artifacts/validation-report.json"
    manifest_path: str = "outputs/figures/manifest.json"
    entities: dict[str, EntityValidationResult] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    range_violations: list[dict[str, Any]] = field(default_factory=list)
    capture_worthy_values: list[dict[str, Any]] = field(default_factory=list)
    generated_at_utc: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "data_dir": self.data_dir,
            "report_path": self.report_path,
            "manifest_path": self.manifest_path,
            "entities": {
                entity: result.to_dict() for entity, result in self.entities.items()
            },
            "warnings": self.warnings,
            "errors": self.errors,
            "range_violations": self.range_violations,
            "capture_worthy_values": self.capture_worthy_values,
            "generated_at_utc": self.generated_at_utc,
        }


def validate_entity(
    entity: str,
    df: pd.DataFrame,
    *,
    source_file: str = "",
) -> EntityValidationResult:
    spec = registry.get_entity(entity)
    roles = list(spec.required_roles + spec.optional_roles)
    role_result = registry.require_roles(df, roles, entity=entity)
    result = EntityValidationResult(
        status=role_result.status,
        entity=entity,
        source_file=source_file,
        row_count=len(df),
        resolved_roles=role_result.resolved_roles,
        warnings=role_result.warnings,
        errors=role_result.errors,
        extra_columns=role_result.extra_columns,
    )
    _append_range_results(result, df)
    if result.errors or result.range_violations:
        result.status = "fail"
    elif result.warnings or result.capture_worthy_values:
        result.status = "warn"
    else:
        result.status = "pass"
    return result


def validate_data_dir(
    data_dir: Path,
    *,
    report_path: Path | str = Path("artifacts/validation-report.json"),
    manifest_path: Path | str = Path("outputs/figures/manifest.json"),
) -> ValidationResult:
    data_dir = Path(data_dir)
    result = ValidationResult(
        status="pass",
        data_dir=str(data_dir),
        report_path=str(report_path),
        manifest_path=str(manifest_path),
    )
    for spec in registry.current_entities():
        try:
            source_path = _find_source_path(data_dir, spec.source_filenames)
            df = registry.load_entity(data_dir, spec.name)
            entity_result = validate_entity(
                spec.name,
                df,
                source_file=str(source_path),
            )
        except registry.SchemaValidationError as exc:
            entity_result = EntityValidationResult(
                status="fail",
                entity=spec.name,
                source_file=str(data_dir),
                row_count=0,
                errors=[str(exc)],
            )
        result.entities[spec.name] = entity_result
        result.warnings.extend(
            f"{spec.name}: {warning}" for warning in entity_result.warnings
        )
        result.errors.extend(f"{spec.name}: {error}" for error in entity_result.errors)
        result.range_violations.extend(entity_result.range_violations)
        result.capture_worthy_values.extend(entity_result.capture_worthy_values)

    for spec in registry.future_optional_entities():
        result.warnings.append(
            f"{spec.name}: optional future entity is not required until its producer spec lands"
        )

    if result.errors or result.range_violations:
        result.status = "fail"
    elif result.warnings or result.capture_worthy_values:
        result.status = "warn"
    else:
        result.status = "pass"
    return result


def _find_source_path(data_dir: Path, filenames: tuple[str, ...]) -> Path:
    for filename in filenames:
        path = data_dir / filename
        if path.exists():
            return path
    raise registry.SchemaValidationError(
        f"Missing source file in {data_dir}",
        candidates=list(filenames),
    )


def _append_range_results(result: EntityValidationResult, df: pd.DataFrame) -> None:
    for role_id, column in result.resolved_roles.items():
        role = registry.get_role(role_id)
        if role.hard_range is None and role.capture_worthy_range is None:
            continue
        values = pd.to_numeric(df[column], errors="coerce")
        for index, value in values.items():
            if pd.isna(value):
                continue
            numeric = float(value)
            if _outside(numeric, role.hard_range):
                result.range_violations.append(
                    _range_record(result.entity, role_id, column, index, numeric, "hard")
                )
                continue
            if _outside(numeric, role.capture_worthy_range):
                result.capture_worthy_values.append(
                    _range_record(
                        result.entity,
                        role_id,
                        column,
                        index,
                        numeric,
                        "capture_worthy",
                    )
                )


def _outside(
    value: float,
    bounds: tuple[float | None, float | None] | None,
) -> bool:
    if bounds is None:
        return False
    lower, upper = bounds
    if lower is not None and value < lower:
        return True
    if upper is not None and value > upper:
        return True
    return False


def _range_record(
    entity: str,
    role_id: str,
    column: str,
    row_index: Any,
    value: float,
    severity: str,
) -> dict[str, Any]:
    return {
        "entity": entity,
        "role": role_id,
        "column": column,
        "row_index": int(row_index) if isinstance(row_index, int) else str(row_index),
        "value": value,
        "severity": severity,
    }
