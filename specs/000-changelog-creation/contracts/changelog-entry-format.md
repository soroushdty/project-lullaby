---
id:            PLAN-000-CONTRACT-001
title:         Changelog Entry Format Contract
status:        draft
version:       0.1.0
created:       2026-06-01
updated:       2026-06-01
author:        Soroush Dianaty
depends_on:    [SPEC-000]
implements:    [P1, P2]
supersedes:    null
superseded_by: null
related:       [PLAN-000]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Changelog Entry Format Contract

## Required entry fields
Each implementation entry in `CHANGELOG.md` MUST include:
- `Date`
- `Spec` (link to canonical spec)
- `Summary`
- `Rationale`
- `Impact`
- `Targets`

## Semantic constraints
- `Date` MUST represent implementation PR merge date (ISO 8601).
- `Spec` MUST contain a resolvable spec identifier/link.
- `spec-id` MUST be unique across changelog entries.

## Targets grammar
One line per affected file:
- `path | +added -removed`

Examples:
- `specs/000-changelog-creation/spec.md | +12 -3`
- `.github/workflows/changelog-policy.yml | +38 -0`

Validation:
- `path` non-empty, repository-relative.
- `added` and `removed` are integers >= 0.
