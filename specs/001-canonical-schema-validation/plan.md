---
id:            PLAN-001
title:         Canonical Schema & Validation Implementation Plan
status:        draft
version:       0.1.0
created:       2026-06-01
updated:       2026-06-01
author:        Soroush Dianaty
depends_on:    [SPEC-001]
implements:    [P1, P2, P3, P5]
supersedes:    null
superseded_by: null
related:       [PLAN-001-RESEARCH, PLAN-001-DATA-MODEL]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Implementation Plan: Canonical Schema & Validation

**Branch**: `001-create-spec-branch` | **Date**: 2026-06-01 | **Spec**: `/specs/001-canonical-schema-validation/spec.md`

**Input**: Feature specification from `/specs/001-canonical-schema-validation/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Implement a canonical time-series-first schema system for Project Lullaby as a Python
abstract base class (ABC), with a default `LullabySchema` implementation for five
canonical tables and validation-as-code at ingestion boundaries. The design enforces
schema compliance using Pandera, preserves informative missingness, supports runtime
schema injection for alternate conforming schemas, and runs validation in CI.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.11

**Primary Dependencies**: pandas, pandera, pydantic-settings, PyYAML, pytest

**Storage**: Files (CSV/Parquet) for bundled synthetic data and ingestion artifacts

**Testing**: pytest + CI workflow (`validate-schema`) on bundled synthetic dataset

**Target Platform**: Linux/macOS developer environments + GitHub Actions CI

**Project Type**: Python library + CLI ingestion/validation entrypoint

**Performance Goals**: Validate bundled synthetic dataset in <= 10 minutes end-to-end in CI

**Constraints**: Fail loud on schema errors; no silent imputation at ingestion; cadence as data

**Scale/Scope**: Five canonical tables, one default schema, pluggable custom schema interface

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Gate 1 (P1 Specification-Driven Development): PASS. Work maps directly to SPEC-001.
- Gate 2 (P2 Reproducibility by Default): PASS. CI and deterministic validation paths included.
- Gate 3 (P3 Schema-Driven Extensibility): PASS. ABC + injectable schema object is core design.
- Gate 4 (P5 Resilience / Graceful Degradation): PASS. Validation boundary rejects bad data with precise errors.
- Gate 5 (Provenance / Traceability): PASS. Artifacts include provenance frontmatter.

## Project Structure

### Documentation (this feature)

```text
specs/001-canonical-schema-validation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── schema-interface.md
│   └── validation-contract.md
└── tasks.md
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
src/
├── schemas/
│   ├── base.py
│   ├── lullaby.py
│   └── registry.py
├── validation/
│   ├── pandera_models.py
│   └── engine.py
├── ingestion/
│   ├── adapters/
│   └── pipeline.py
└── cli/
  └── validate_schema.py

tests/
├── contract/
│   ├── test_schema_interface.py
│   └── test_validation_contract.py
├── integration/
│   └── test_ingestion_validation_pipeline.py
└── unit/
  ├── test_lullaby_schema.py
  └── test_pandera_models.py
```

**Structure Decision**: Single Python project with schema, validation, and ingestion
modules under `src/`; contract/integration/unit tests under `tests/`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Post-Design Constitution Check

- P1: PASS. Design artifacts are derived from SPEC-001 only.
- P2: PASS. Quickstart includes deterministic run path and CI gate.
- P3: PASS. Contracts define ABC interface and runtime schema injection.
- P5: PASS. Validation contract requires precise, actionable failures and no ingestion-time imputation.
