---
id:            PLAN-008
title:         Implementation Acceptance and Provenance Remediation — Plan
status:        draft
version:       0.1.0
created:       2026-06-01
updated:       2026-06-01
author:        Gemini CLI
depends_on:    [SPEC-000, SPEC-001, SPEC-002, SPEC-003, SPEC-004, SPEC-005, SPEC-006, SPEC-007]
implements:    [P1, P2, P3, P4, P5, P10]
supersedes:    null
superseded_by: null
related:       [SPEC-000, SPEC-001, SPEC-002, SPEC-003, SPEC-004, SPEC-005, SPEC-006, SPEC-007]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Implementation Plan: Acceptance Remediation

**Branch**: `008-implementation-acceptance-remediation` | **Date**: 2026-06-01 | **Spec**: [specs/008-implementation-acceptance-remediation/spec.md]

**Input**: Feature specification from `/specs/008-implementation-acceptance-remediation/spec.md`

## Summary

This plan addresses repository-wide implementation gaps, provenance failures, and visual readability issues identified during the acceptance audit. We will fix `CHANGELOG.md` validity, complete skipped integration tests for SPEC-002 adapters using Docker Compose emulators, harden boolean semantics in modeling and simulation, and perform a major revision of visualization elements to ensure dashboard PNGs are readable and free of text overlap.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: pytest, pandas, matplotlib, docker compose, tenacity

**Storage**: Filesystem, Docker (MinIO, Azurite, fake-gcs-server, MySQL)

**Testing**: pytest with integration and contract markings.

**Target Platform**: Linux / Docker

**Project Type**: Infrastructure & Remediation Suite

**Performance Goals**: CI test suite completes in < 5 minutes (including emulators).

**Constraints**: No PHI; zero network access during tests; high-resolution PNG outputs (>= 220 DPI).

## Constitution Check

- **P1 Specification-Driven**: PASS. Remediates code-spec drift.
- **P2 Reproducibility**: PASS. Ensures all integration tests pass on bundled emulators.
- **P4 Source-Agnostic**: PASS. Completes S3/Azure/GCS/MySQL adapter acceptance.
- **P5 Resilience**: PASS. Hardens boolean parsing logic.
- **P10 Equity-Centered**: PASS. Fixes dashboard text overlap for better accessibility.

## Project Structure

### Documentation (this feature)

```text
specs/008-implementation-acceptance-remediation/
├── plan.md              # This file
├── research.md          # Phase 0 summary
├── data-model.md        # Acceptance ledger schema
├── quickstart.md        # Audit and remediation steps
├── contracts/
│   ├── visual-revision-contract.md
│   └── boolean-hardening-contract.md
└── tasks.md             # To be created by speckit.tasks
```

### Source Code

```text
src/
├── modeling/
│   └── metrics.py       # Fix .astype(bool)
├── simulation/
│   └── environment.py   # Fix .astype(bool)
├── visualization/
│   ├── design.py        # Spacing/readability helpers
│   ├── eda_core.py      # Panel-specific visual fixes
│   └── analytic_dashboard.py # Panel-specific visual fixes
└── tools/
    ├── changelog_validator.py # Audit fixes
    └── generate_acceptance_ledger.py # New tool
```

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Docker Compose in CI | Needed for SPEC-002 cloud adapter acceptance | Local mocking is insufficient to prove real protocol compliance. |
| Major visual revision | Fixed offsets in matplotlib are brittle | Hardcoding new offsets would only shift the problem; adaptive helpers are required. |
