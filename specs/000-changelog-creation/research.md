---
id:            PLAN-000-RESEARCH
title:         Research Notes - Changelog Creation Requirement
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

# Research

## Decision: Enforce changelog policy via required CI status check
Rationale: CI is auditable, centralized, and mandatory for merges, unlike local hooks.
Alternatives considered: Pre-commit hooks only (optional by environment), manual review checklist only (error-prone).

## Decision: Machine-parseable `Targets` format
Rationale: `path | +added -removed` is simple to validate and compare.
Alternatives considered: free-form text (ambiguous), embedded unified diff snippets (verbose and unstable).

## Decision: One changelog entry per `spec-id`
Rationale: Prevents duplicate provenance records and simplifies traceability.
Alternatives considered: one entry per PR (duplicates for same spec), one per release (weak linkage to spec implementation).

## Decision: Use Python stdlib parser/validator
Rationale: No extra dependencies, deterministic behavior, easy CI execution.
Alternatives considered: markdown parser dependency (extra maintenance), shell-only validation (harder diagnostics).

## Decision: Changelog `Date` equals merge date policy
Rationale: Reflects when implementation actually entered mainline history.
Alternatives considered: spec publication date (not implementation timestamp), first commit date (can drift during rebases/cherry-picks).
