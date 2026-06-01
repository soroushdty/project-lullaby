from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable

REQUIRED_FIELDS = ("Date", "Spec", "Summary", "Rationale", "Impact", "Targets")
TARGET_PATTERN = re.compile(r"^(?:-\s*)?(?P<path>[^|]+?)\s*\|\s*\+(?P<added>\d+)\s*-(?P<removed>\d+)\s*$")
SPEC_ID_PATTERN = re.compile(r"(?i)\b(spec[-_ ]?\d+|speckit[-_ ]?\d+)\b")


@dataclass
class ValidationError:
    code: str
    message: str
    entry_index: int | None = None
    spec_id: str | None = None
    field: str | None = None


@dataclass
class ValidationReport:
    ok: bool
    errors: list[ValidationError] = field(default_factory=list)
    checked_entries: int = 0
    checked_spec_ids: list[str] = field(default_factory=list)


@dataclass
class ParsedEntry:
    raw: dict[str, str]
    entry_index: int
    spec_id: str | None = None


def normalize_spec_id(value: str) -> str:
    return re.sub(r"[^a-z0-9-]", "-", value.lower()).strip("-")


def parse_iso_date(raw: str) -> datetime:
    cleaned = raw.strip()
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    if "T" in cleaned or "+" in cleaned:
        return datetime.fromisoformat(cleaned)
    return datetime.strptime(cleaned, "%Y-%m-%d")


def extract_spec_id(spec_value: str) -> str | None:
    match = SPEC_ID_PATTERN.search(spec_value)
    if match:
        return normalize_spec_id(match.group(1))

    # Match both '/specs/<id>' and 'specs/<id>' occurrences
    path_match = re.search(r"(?:/|\b)specs/([^/\)\s]+)", spec_value)
    if path_match:
        return normalize_spec_id(path_match.group(1))

    bare = spec_value.strip().rstrip(")").split("/")[-1]
    bare = bare.replace(".md", "")
    if bare:
        return normalize_spec_id(bare)
    return None


def _split_entries(lines: list[str]) -> list[list[str]]:
    entries: list[list[str]] = []
    current: list[str] = []
    in_fence = False

    for raw_line in lines:
        line = raw_line.rstrip("\n")
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue

        if in_fence:
            continue

        if re.match(r"^Date:\s*", line):
            if current:
                entries.append(current)
            current = [line]
            continue

        if current:
            current.append(line)

    if current:
        entries.append(current)

    return entries


def parse_changelog(content: str) -> list[ParsedEntry]:
    lines = content.splitlines(True)
    raw_entries = _split_entries(lines)
    parsed_entries: list[ParsedEntry] = []

    for index, block in enumerate(raw_entries, start=1):
        fields: dict[str, str] = {}
        current_field: str | None = None
        buffered_lines: list[str] = []

        def flush_field() -> None:
            nonlocal buffered_lines, current_field
            if current_field is not None:
                fields[current_field] = "\n".join(buffered_lines).strip()
            buffered_lines = []

        for line in block:
            field_match = re.match(r"^(Date|Spec|Summary|Rationale|Impact|Targets):\s*(.*)$", line)
            if field_match:
                flush_field()
                current_field = field_match.group(1)
                remainder = field_match.group(2).strip()
                buffered_lines = [remainder] if remainder else []
                continue

            if current_field is not None:
                buffered_lines.append(line.strip())

        flush_field()

        spec_id = extract_spec_id(fields.get("Spec", "")) if fields.get("Spec") else None
        parsed_entries.append(ParsedEntry(raw=fields, entry_index=index, spec_id=spec_id))

    return parsed_entries


def _validate_targets(targets_value: str, entry: ParsedEntry) -> list[ValidationError]:
    errors: list[ValidationError] = []
    target_lines = [line.strip() for line in targets_value.splitlines() if line.strip()]

    if not target_lines:
        errors.append(
            ValidationError(
                code="E_TARGETS_MISSING",
                message="Targets must include at least one target line",
                entry_index=entry.entry_index,
                spec_id=entry.spec_id,
                field="Targets",
            )
        )
        return errors

    for line in target_lines:
        match = TARGET_PATTERN.match(line)
        if not match:
            errors.append(
                ValidationError(
                    code="E_TARGET_FORMAT",
                    message=f"Invalid Targets line format: '{line}'",
                    entry_index=entry.entry_index,
                    spec_id=entry.spec_id,
                    field="Targets",
                )
            )
            continue

        path = match.group("path").strip()
        if not path or path.startswith("/"):
            errors.append(
                ValidationError(
                    code="E_TARGET_PATH",
                    message=f"Target path must be non-empty and repository-relative: '{line}'",
                    entry_index=entry.entry_index,
                    spec_id=entry.spec_id,
                    field="Targets",
                )
            )

    return errors


def validate_entries(
    entries: Iterable[ParsedEntry],
    merge_date: str | None = None,
    required_spec_id: str | None = None,
) -> ValidationReport:
    parsed_entries = list(entries)
    errors: list[ValidationError] = []
    spec_id_to_indexes: dict[str, list[int]] = {}

    normalized_required_spec_id = normalize_spec_id(required_spec_id) if required_spec_id else None

    for entry in parsed_entries:
        for field_name in REQUIRED_FIELDS:
            if not entry.raw.get(field_name):
                errors.append(
                    ValidationError(
                        code="E_REQUIRED_FIELD",
                        message=f"Missing required field: {field_name}",
                        entry_index=entry.entry_index,
                        spec_id=entry.spec_id,
                        field=field_name,
                    )
                )

        date_value = entry.raw.get("Date")
        if date_value:
            try:
                parsed_date = parse_iso_date(date_value)
                # If a specific required_spec_id is provided, only apply the merge-date
                # equality policy to the entry that matches that spec-id. Otherwise,
                # apply the merge-date check to all entries when merge_date is given.
                if merge_date:
                    merge_dt = parse_iso_date(merge_date)
                    should_check = True
                    if normalized_required_spec_id:
                        should_check = entry.spec_id == normalized_required_spec_id
                    if should_check and parsed_date.date() != merge_dt.date():
                        errors.append(
                            ValidationError(
                                code="E_DATE_POLICY",
                                message=(
                                    f"Date {parsed_date.date().isoformat()} does not match merge date "
                                    f"{merge_dt.date().isoformat()}"
                                ),
                                entry_index=entry.entry_index,
                                spec_id=entry.spec_id,
                                field="Date",
                            )
                        )
            except ValueError as exc:
                errors.append(
                    ValidationError(
                        code="E_DATE_PARSE",
                        message=f"Date is not valid ISO format: {exc}",
                        entry_index=entry.entry_index,
                        spec_id=entry.spec_id,
                        field="Date",
                    )
                )

        spec_value = entry.raw.get("Spec")
        if spec_value and not entry.spec_id:
            errors.append(
                ValidationError(
                    code="E_SPEC_ID_EXTRACT",
                    message="Unable to derive spec-id from Spec field",
                    entry_index=entry.entry_index,
                    field="Spec",
                )
            )

        if entry.spec_id:
            spec_id_to_indexes.setdefault(entry.spec_id, []).append(entry.entry_index)

        targets_value = entry.raw.get("Targets")
        if targets_value:
            errors.extend(_validate_targets(targets_value, entry))

    for spec_id, indexes in spec_id_to_indexes.items():
        if len(indexes) > 1:
            errors.append(
                ValidationError(
                    code="E_SPEC_ID_DUPLICATE",
                    message=f"Duplicate spec-id '{spec_id}' at entries {indexes}",
                    spec_id=spec_id,
                    field="Spec",
                )
            )

    if normalized_required_spec_id:
        match_count = len(spec_id_to_indexes.get(normalized_required_spec_id, []))
        if match_count != 1:
            errors.append(
                ValidationError(
                    code="E_SPEC_ID_COUNT",
                    message=(
                        f"Expected exactly one entry for spec-id '{normalized_required_spec_id}', "
                        f"found {match_count}"
                    ),
                    spec_id=normalized_required_spec_id,
                    field="Spec",
                )
            )

    return ValidationReport(
        ok=not errors,
        errors=errors,
        checked_entries=len(parsed_entries),
        checked_spec_ids=sorted(spec_id_to_indexes),
    )


def format_report(report: ValidationReport) -> str:
    if report.ok:
        return (
            "PASS: "
            f"checked_entries={report.checked_entries} "
            f"checked_spec_ids={len(report.checked_spec_ids)}"
        )

    lines = [
        "FAIL: "
        f"checked_entries={report.checked_entries} "
        f"errors={len(report.errors)}"
    ]
    for error in report.errors:
        context = []
        if error.field:
            context.append(f"field={error.field}")
        if error.spec_id:
            context.append(f"spec_id={error.spec_id}")
        if error.entry_index is not None:
            context.append(f"entry={error.entry_index}")
        detail = " ".join(context)
        lines.append(f"- [{error.code}] {detail}: {error.message}".strip())
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate changelog policy compliance")
    parser.add_argument("--changelog", default="CHANGELOG.md", help="Path to changelog file")
    parser.add_argument("--spec-dir", default="specs", help="Path to specs directory")
    parser.add_argument("--merge-date", default=None, help="Merge date or datetime (ISO 8601)")
    parser.add_argument("--spec-id", default=None, help="Expected implemented spec-id")
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    changelog_path = Path(args.changelog)
    if not changelog_path.exists():
        print(f"FAIL: changelog file not found: {changelog_path}")
        return 2

    if not Path(args.spec_dir).exists():
        print(f"FAIL: spec directory not found: {args.spec_dir}")
        return 2

    parsed_entries = parse_changelog(changelog_path.read_text(encoding="utf-8"))
    report = validate_entries(parsed_entries, merge_date=args.merge_date, required_spec_id=args.spec_id)
    print(format_report(report))
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
