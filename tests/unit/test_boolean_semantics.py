from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.validation.semantics import (
    DomainBooleanParsePolicy,
    parse_domain_boolean_scalar,
    parse_domain_boolean_series,
)


def test_parser_accepts_native_numeric_string_blank_and_null_tokens():
    values = pd.Series(
        [
            True,
            False,
            1,
            0,
            1.0,
            0.0,
            " true ",
            "False",
            "YES",
            "n",
            "",
            "unknown",
            np.nan,
            None,
        ]
    )

    parsed = parse_domain_boolean_series(values, DomainBooleanParsePolicy(role="test.flag", required=True))

    assert parsed.counts == {
        "true": 5,
        "false": 5,
        "missing_unknown": 4,
        "invalid": 0,
    }
    assert not parsed.errors


def test_required_invalid_tokens_fail_with_role_column_and_row_context():
    values = pd.Series(["yes", "maybe", "0"], index=[10, 11, 12])

    parsed = parse_domain_boolean_series(
        values,
        DomainBooleanParsePolicy(role="outcome.cv_event", required=True),
        source_column="cv_event",
    )

    assert parsed.counts["true"] == 1
    assert parsed.counts["false"] == 1
    assert parsed.counts["invalid"] == 1
    assert parsed.errors == [
        "Invalid boolean token for role outcome.cv_event column cv_event at row 11: 'maybe'"
    ]


def test_optional_invalid_tokens_warn_and_are_missing_unknown_downstream():
    parsed = parse_domain_boolean_series(
        pd.Series(["yes", "possibly", ""]),
        DomainBooleanParsePolicy(role="participant.has_ac", required=False),
        source_column="has_ac",
    )

    assert parsed.counts == {
        "true": 1,
        "false": 0,
        "missing_unknown": 2,
        "invalid": 1,
    }
    assert not parsed.errors
    assert parsed.warnings == [
        "Invalid boolean token for role participant.has_ac column has_ac at row 1: 'possibly'"
    ]
    assert parsed.as_nullable_boolean().isna().sum() == 2


def test_scalar_parser_never_uses_non_empty_string_truthiness():
    policy = DomainBooleanParsePolicy(role="test.flag", required=False)

    assert parse_domain_boolean_scalar("False", policy) is False
    assert parse_domain_boolean_scalar("0", policy) is False
    assert parse_domain_boolean_scalar("not sure", policy) is None


def test_domain_boolean_source_paths_do_not_use_generic_astype_bool():
    checked_roots = [Path("src/ingestion"), Path("src/simulation"), Path("src/visualization")]
    allowed = {Path("src/simulation/environment.py")}
    offenders: list[str] = []

    for root in checked_roots:
        for path in root.rglob("*.py"):
            if path in allowed:
                continue
            text = path.read_text()
            if ".astype(bool)" in text:
                offenders.append(path.as_posix())

    assert offenders == []
