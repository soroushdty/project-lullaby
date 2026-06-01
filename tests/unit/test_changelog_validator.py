from pathlib import Path

from tools.changelog_validator import parse_changelog, validate_entries


def _entry(
    date: str = "2026-06-01",
    spec: str = "specs/000-changelog-creation/spec.md",
    summary: str = "Summary text",
    rationale: str = "Rationale text",
    impact: str = "Impact text",
    targets: str = "tools/changelog_validator.py | +10 -2",
) -> str:
    return "\n".join(
        [
            f"Date: {date}",
            f"Spec: {spec}",
            f"Summary: {summary}",
            f"Rationale: {rationale}",
            f"Impact: {impact}",
            "Targets:",
            f"  {targets}",
            "",
        ]
    )


def test_missing_required_field_fails() -> None:
    content = _entry(summary="")
    report = validate_entries(parse_changelog(content))
    assert not report.ok
    assert any(error.code == "E_REQUIRED_FIELD" and error.field == "Summary" for error in report.errors)


def test_duplicate_spec_id_fails() -> None:
    content = _entry() + _entry()
    report = validate_entries(parse_changelog(content))
    assert not report.ok
    assert any(error.code == "E_SPEC_ID_DUPLICATE" for error in report.errors)


def test_targets_format_validation() -> None:
    content = _entry(targets="bad-target-format")
    report = validate_entries(parse_changelog(content))
    assert not report.ok
    assert any(error.code == "E_TARGET_FORMAT" for error in report.errors)


def test_targets_path_must_be_repo_relative() -> None:
    content = _entry(targets="/abs/path/file.py | +1 -0")
    report = validate_entries(parse_changelog(content))
    assert not report.ok
    assert any(error.code == "E_TARGET_PATH" for error in report.errors)


def test_merge_date_policy_validation() -> None:
    content = _entry(date="2026-06-01")
    report = validate_entries(parse_changelog(content), merge_date="2026-06-02")
    assert not report.ok
    assert any(error.code == "E_DATE_POLICY" for error in report.errors)


def test_date_parse_validation() -> None:
    content = _entry(date="not-a-date")
    report = validate_entries(parse_changelog(content))
    assert not report.ok
    assert any(error.code == "E_DATE_PARSE" for error in report.errors)


def test_required_spec_id_count_exactly_one() -> None:
    content = _entry(spec="specs/000-changelog-creation/spec.md")
    report = validate_entries(parse_changelog(content), required_spec_id="000-changelog-creation")
    assert report.ok

    report_missing = validate_entries(parse_changelog(content), required_spec_id="spec-999")
    assert not report_missing.ok
    assert any(error.code == "E_SPEC_ID_COUNT" for error in report_missing.errors)


def test_ignores_date_in_fenced_code_block() -> None:
    content = "\n".join(
        [
            "```",
            "Date: 2020-01-01",
            "Spec: sample",
            "```",
            _entry(),
        ]
    )
    parsed = parse_changelog(content)
    assert len(parsed) == 1


def test_parse_changelog_no_entries() -> None:
    report = validate_entries(parse_changelog("# CHANGELOG\nNo entries yet"))
    assert report.ok
    assert report.checked_entries == 0
