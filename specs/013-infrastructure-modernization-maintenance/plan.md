---
id:            PLAN-013
title:         Infrastructure Modernization and Maintenance — Plan
status:        draft
version:       0.1.0
created:       2026-06-01
updated:       2026-06-01
author:        Gemini CLI
depends_on:    [SPEC-013]
implements:    [P1, P2, P5, P6, P10]
supersedes:    null
superseded_by: null
related:       [SPEC-008, SPEC-004]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Implementation Plan: Infrastructure Modernization

**Branch**: `013-infrastructure-modernization` | **Date**: 2026-06-01 | **Spec**: [specs/013-infrastructure-modernization-maintenance/spec.md]

**Input**: Feature specification from `/specs/013-infrastructure-modernization-maintenance/spec.md`

## Summary

This plan addresses repository health issues found during the June 2026 audit. We will modernize `pandera` usage, optimize the emulated integration test tier using healthy-wait patterns, eliminate baseline test warnings, and update specification templates to align with the v1.0.0 Constitution.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: pandera (pandas namespace), pytest, matplotlib, docker-py (optional for health checks)

**Testing**: Pytest with focus on integration test runtime and warning suppression.

**Target Platform**: Linux / CI

**Project Type**: Maintenance & DevOps

**Performance Goals**: Integration test tier completes in < 2 minutes.

## Constitution Check

- **P1 Specification-Driven**: PASS. This maintenance work is itself spec-driven.
- **P2 Reproducibility**: PASS. Improves reliability of integration tests across environments.
- **P6 Distribution Integrity**: PASS. Templates ensure consistent provenance across all forms.
- **P10 Equity-Centered**: PASS. Updates templates to explicitly check for equity-centered design.

## Project Structure

### Documentation (this feature)

```text
specs/013-infrastructure-modernization-maintenance/
├── plan.md              # This file
├── research.md          # Audit findings (from previous scan)
├── contracts/
│   └── template-standards-contract.md
└── tasks.md             # To be created by speckit.tasks
```

### Source Code

```text
.specify/templates/      # Update templates
src/
├── validation/
│   ├── pandera_models.py # Update imports
│   └── engine.py        # Update imports
├── schemas/
│   └── lullaby.py       # Update imports
├── visualization/
│   ├── eda_core.py      # Fix registration warnings and date formats
│   └── design.py        # Fix date formats
tests/
├── conftest.py          # Fix MPLCONFIGDIR and shared fixtures
└── integration/         # Optimize cloud adapter tests
```

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Overhauling test timing | Current tests take 8 minutes | Mocking is too high-level; we need real emulator tests but they must be efficient. |
| Template logic update | Constitution v1.0.0 is more strict | Keeping old templates would lead to non-conforming new specs. |
