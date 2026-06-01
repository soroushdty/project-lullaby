from tools.changelog_validator import parse_changelog, validate_entries


def _valid_entry() -> str:
    return "\n".join(
        [
            "Date: 2026-06-01",
            "Spec: specs/000-changelog-creation/spec.md",
            "Summary: Adds policy validator",
            "Rationale: Enforce changelog consistency",
            "Impact: Introduces CI merge gate",
            "Targets:",
            "  tools/changelog_validator.py | +120 -0",
            "  .github/workflows/changelog-policy.yml | +30 -0",
            "",
        ]
    )


def test_contract_requires_all_mandatory_fields() -> None:
    content = _valid_entry().replace("Summary: Adds policy validator", "")
    report = validate_entries(parse_changelog(content))
    assert not report.ok
    assert any(error.code == "E_REQUIRED_FIELD" and error.field == "Summary" for error in report.errors)


def test_contract_targets_must_follow_grammar() -> None:
    content = _valid_entry().replace(
        "tools/changelog_validator.py | +120 -0",
        "tools/changelog_validator.py: +120 -0",
    )
    report = validate_entries(parse_changelog(content))
    assert not report.ok
    assert any(error.code == "E_TARGET_FORMAT" for error in report.errors)


def test_contract_targets_require_non_empty_relative_path() -> None:
    content = _valid_entry().replace(
        "tools/changelog_validator.py | +120 -0",
        "/tools/changelog_validator.py | +120 -0",
    )
    report = validate_entries(parse_changelog(content))
    assert not report.ok
    assert any(error.code == "E_TARGET_PATH" for error in report.errors)


def test_contract_spec_id_is_unique() -> None:
    content = _valid_entry() + _valid_entry()
    report = validate_entries(parse_changelog(content))
    assert not report.ok
    assert any(error.code == "E_SPEC_ID_DUPLICATE" for error in report.errors)
