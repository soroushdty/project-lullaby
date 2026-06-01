---
id:            PLAN-000-CONTRACT-002
title:         Validation Gate Contract
status:        draft
version:       0.1.0
created:       2026-06-01
updated:       2026-06-01
author:        Soroush Dianaty
depends_on:    [SPEC-000]
implements:    [P2, P5]
supersedes:    null
superseded_by: null
related:       [PLAN-000]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Validation Gate Contract

## Execution contract
Validator command:
- `python3 tools/changelog_validator.py --changelog CHANGELOG.md --spec-dir specs`

## Output contract
On success:
- Exit code `0`
- Summary: number of checked entries and spec ids

On failure:
- Non-zero exit code
- Actionable diagnostics including: violation code, field, and failing `spec-id` when available

## Required CI behavior
- Workflow name: `changelog-policy`
- Trigger: pull requests targeting protected branches
- Must be marked as required status check before merge
- Merge blocked on non-zero validator exit

## Required validations
- Required fields present per entry
- `spec-id` uniqueness
- `Targets` line grammar (`path | +added -removed`)
- `Date` field parseable ISO date and merge-date policy gate (where metadata is available)
