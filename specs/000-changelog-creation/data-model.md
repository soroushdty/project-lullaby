---
id:            PLAN-000-DATA-MODEL
title:         Data Model - Changelog Entry Policy
status:        draft
version:       0.1.0
created:       2026-06-01
updated:       2026-06-01
author:        Soroush Dianaty
depends_on:    [SPEC-000]
implements:    [P1, P2, P5]
supersedes:    null
superseded_by: null
related:       [PLAN-000]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Data Model

## Entity: ChangelogEntry
Fields:
- `spec_id: str` (required, unique)
- `date: str` (required, ISO 8601, merge date policy)
- `spec_link: str` (required, path or URL)
- `summary: str` (required)
- `rationale: str` (required)
- `impact: str` (required)
- `targets: list[TargetDelta]` (required, non-empty)
- `status: str` (optional; values: draft|accepted|implemented|deprecated)

Validation rules:
- `spec_id` must match known spec identifier format (`SPEC-\d+` or accepted aliasing policy).
- `date` must be parseable ISO date.
- Exactly one entry per `spec_id` across `CHANGELOG.md`.

## Entity: TargetDelta
Fields:
- `path: str` (required)
- `added: int` (required, >=0)
- `removed: int` (required, >=0)

Validation rules:
- Serialized line MUST match `path | +added -removed`.
- `path` must be non-empty and repository-relative.

## Entity: ValidationReport
Fields:
- `ok: bool`
- `errors: list[ValidationError]`
- `checked_entries: int`
- `checked_spec_ids: list[str]`

## Entity: ValidationError
Fields:
- `code: str`
- `message: str`
- `entry_index: int | null`
- `spec_id: str | null`
- `field: str | null`

State transitions:
1. `raw_changelog_loaded`
2. `entries_parsed`
3. `entries_validated`
4. `ci_pass` or `ci_fail`

Transition rule:
- Any parse or validation error transitions directly to `ci_fail` with explicit diagnostics.
