from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

import numpy as np
import pandas as pd


DEFAULT_TRUE_TOKENS = frozenset({"1", "1.0", "true", "t", "yes", "y"})
DEFAULT_FALSE_TOKENS = frozenset({"0", "0.0", "false", "f", "no", "n"})
DEFAULT_MISSING_TOKENS = frozenset({"", "missing", "unknown", "not_available", "na", "n/a"})


@dataclass(frozen=True)
class DomainBooleanParsePolicy:
    role: str
    required: bool = True
    true_tokens: frozenset[str] = DEFAULT_TRUE_TOKENS
    false_tokens: frozenset[str] = DEFAULT_FALSE_TOKENS
    missing_tokens: frozenset[str] = DEFAULT_MISSING_TOKENS
    invalid_behavior: str | None = None

    def __post_init__(self) -> None:
        behavior = self.invalid_behavior or ("fail" if self.required else "warn_as_missing")
        if behavior not in {"fail", "warn_as_missing"}:
            raise ValueError("invalid_behavior must be 'fail' or 'warn_as_missing'")
        object.__setattr__(self, "invalid_behavior", behavior)
        object.__setattr__(self, "true_tokens", _normalize_token_set(self.true_tokens))
        object.__setattr__(self, "false_tokens", _normalize_token_set(self.false_tokens))
        object.__setattr__(self, "missing_tokens", _normalize_token_set(self.missing_tokens))


@dataclass(frozen=True)
class ParsedBooleanSeries:
    true_mask: pd.Series
    false_mask: pd.Series
    missing_mask: pd.Series
    invalid_mask: pd.Series
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def counts(self) -> dict[str, int]:
        return {
            "true": int(self.true_mask.sum()),
            "false": int(self.false_mask.sum()),
            "missing_unknown": int(self.missing_mask.sum()),
            "invalid": int(self.invalid_mask.sum()),
        }

    @property
    def valid_mask(self) -> pd.Series:
        return self.true_mask | self.false_mask

    def as_nullable_boolean(self) -> pd.Series:
        values = pd.Series(pd.NA, index=self.true_mask.index, dtype="boolean")
        values.loc[self.true_mask] = True
        values.loc[self.false_mask] = False
        return values


def parse_domain_boolean_series(
    values: pd.Series | Iterable[Any],
    policy: DomainBooleanParsePolicy,
    *,
    source_column: str | None = None,
) -> ParsedBooleanSeries:
    series = values if isinstance(values, pd.Series) else pd.Series(list(values))
    classifications = series.map(lambda value: _classify_domain_boolean(value, policy))
    true_mask = classifications.eq("true")
    false_mask = classifications.eq("false")
    base_missing_mask = classifications.eq("missing")
    invalid_mask = classifications.eq("invalid")
    role_text = f"role {policy.role}"
    if source_column:
        role_text = f"{role_text} column {source_column}"
    invalid_messages = [
        f"Invalid boolean token for {role_text} at row {index}: {series.loc[index]!r}"
        for index in series.index[invalid_mask]
    ]
    if policy.invalid_behavior == "warn_as_missing":
        missing_mask = base_missing_mask | invalid_mask
        return ParsedBooleanSeries(
            true_mask=true_mask,
            false_mask=false_mask,
            missing_mask=missing_mask,
            invalid_mask=invalid_mask,
            warnings=invalid_messages,
            errors=[],
        )
    return ParsedBooleanSeries(
        true_mask=true_mask,
        false_mask=false_mask,
        missing_mask=base_missing_mask,
        invalid_mask=invalid_mask,
        warnings=[],
        errors=invalid_messages,
    )


def parse_domain_boolean_scalar(value: Any, policy: DomainBooleanParsePolicy | None = None) -> bool | None:
    policy = policy or DomainBooleanParsePolicy(role="domain_boolean", required=False)
    classification = _classify_domain_boolean(value, policy)
    if classification == "true":
        return True
    if classification == "false":
        return False
    return None


def _classify_domain_boolean(value: Any, policy: DomainBooleanParsePolicy) -> str:
    if _is_missing_scalar(value):
        return "missing"
    if isinstance(value, (bool, np.bool_)):
        return "true" if bool(value) else "false"
    if isinstance(value, (int, float, np.integer, np.floating)) and not isinstance(value, bool):
        numeric = float(value)
        if numeric == 1.0:
            return "true"
        if numeric == 0.0:
            return "false"
        return "invalid"
    token = _normalize_token(str(value))
    if token in policy.true_tokens:
        return "true"
    if token in policy.false_tokens:
        return "false"
    if token in policy.missing_tokens:
        return "missing"
    return "invalid"


def _is_missing_scalar(value: Any) -> bool:
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _normalize_token(value: str) -> str:
    return value.strip().lower()


def _normalize_token_set(tokens: Iterable[str]) -> frozenset[str]:
    return frozenset(_normalize_token(str(token)) for token in tokens)


__all__ = [
    "DEFAULT_FALSE_TOKENS",
    "DEFAULT_MISSING_TOKENS",
    "DEFAULT_TRUE_TOKENS",
    "DomainBooleanParsePolicy",
    "ParsedBooleanSeries",
    "parse_domain_boolean_scalar",
    "parse_domain_boolean_series",
]
