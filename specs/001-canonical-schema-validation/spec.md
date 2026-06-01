---
id: SPEC-001
title: Canonical Schema & Validation
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: []
implements: [P3, P5]
supersedes: null
superseded_by: null
related: []
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Feature Specification: Canonical Schema & Validation

**Feature Branch**: `001-create-spec-branch`

**Created**: 2026-06-01

**Status**: Draft

**Input**: User description: "SPEC-001 · Canonical Schema & Validation"

## Clarifications

### Session 2026-06-01

- Q: Which validation engine is normative for ingestion boundary and CI? -> A: Pandera-only.
- Q: How should timestamps be normalized across heterogeneous sources? -> A: Normalize all event timestamps to UTC at ingestion, store UTC only.
- Q: How should custom schema objects be selected at runtime? -> A: Support alias OR Python import path (`package.module:ClassName`).
- Q: What is validation failure policy at table level? -> A: Reject whole table load if any row violates schema.
- Q: What environment pinning policy should CI enforce? -> A: Pin Python version and validator dependency major versions in CI.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ingest Bundled Data (Priority: P1)
A developer clones the repo and runs the ingestion pipeline against the bundled synthetic cohort.

**Why this priority**: Validates the canonical schema and the validation-as-code pipeline end-to-end.

**Independent Test**: Run the ingestion command on bundled data; pipeline completes and produces expected tables.

**Acceptance Scenarios**:
1. Given the bundled dataset, when ingestion runs, then `participants`, `daily_vitals`, `alerts`, `clinical_outcomes`, and `staff_contacts` tables are created and pass schema validation.
2. Given the bundled dataset with a deliberate schema violation (e.g., missing required column), when ingestion runs, then the pipeline fails fast with a precise validation error referencing the column and row sample.

---

### User Story 2 - Swap Schema Implementation (Priority: P2)
A data engineer provides an alternate schema object implementing the same ABC interface and runs the pipeline without code edits.

**Why this priority**: Ensures schema is pluggable and the product supports multi-tenant onboarding.

**Independent Test**: Replace the default schema object with a conforming alternate and run the ingestion; pipeline succeeds without code changes.

**Acceptance Scenarios**:
1. Given a conforming alternate schema subclass, when injected into the runtime, then ingestion completes successfully and outputs match expected shapes.
2. Given a non-conforming alternate (missing a required field), when injected, then runtime validation rejects the dataset with detailed errors.

---

### Edge Cases
- Late-arriving timestamps out of order must be normalized by ingestion but validated for missingness.
- Cadence carried as data: ingestion accepts `cadence` metadata and does not require code changes when cadence changes.
- Source timezone ambiguity: records missing timezone info MUST fail validation with actionable errors.

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: Schema MUST be time-series-first: all events are timestamped; the canonical tables include `participants`, `daily_vitals`, `alerts`, `clinical_outcomes`, `staff_contacts`.
- **FR-002**: The canonical schema MUST be defined as an abstract base class (ABC) with a documented interface for concrete subclasses.
- **FR-003**: The repository MUST ship a default concrete `LullabySchema` subclass implementing the ABC for the five canonical tables.
- **FR-004**: Users MAY subclass the ABC and inject their own schema object at runtime without editing pipeline code.
- **FR-005**: The data dictionary (column-level descriptions, types, units) is the authoritative reference and must live in `schemas/data-dictionary.md`.
- **FR-006**: Validation-as-code (Pandera-only) MUST run at the ingestion boundary and enforce active schema rules.
- **FR-007**: Informative missingness MUST be preserved at ingestion; the validator may flag but MUST NOT impute missing values.
- **FR-008**: Non-conforming data MUST be rejected with precise, actionable error messages (column, constraint, example rows where possible).
- **FR-009**: CI MUST run validation on the bundled synthetic data and fail the build on validation errors.
- **FR-010**: Ingestion MUST normalize all event timestamps to UTC and persist UTC values only.
- **FR-011**: Inputs with missing or invalid timezone metadata for event timestamps MUST be rejected at validation.
- **FR-012**: Runtime schema selection MUST support either a built-in alias (for bundled schemas) or a Python import path (`package.module:ClassName`) for custom schema classes.
- **FR-013**: If runtime schema resolution fails (missing alias, import failure, or non-conforming class), ingestion MUST fail fast with actionable diagnostics.
- **FR-014**: Validation policy is strict: if any row violates schema in a table, the entire table load MUST be rejected.
- **FR-015**: CI MUST pin Python runtime version and validator dependency major versions to ensure deterministic schema-validation behavior.

## Key Entities
- **Participant**: identifier, enrollment timestamp, demographic metadata.
- **DailyVital**: timestamp, participant_id, vitals (HR, BP, temp...), cadence metadata.
- **DailyVital**: UTC timestamp, participant_id, vitals (HR, BP, temp...), cadence metadata.
- **Alert**: timestamp, participant_id, alert_type, severity, source.
- **ClinicalOutcome**: timestamp, participant_id, outcome_label, adjudication_metadata.
- **StaffContact**: staff_id, role, contact_method, availability windows.

## Success Criteria *(mandatory)*

- **SC-001**: Clone -> run ingestion on bundled data reproduces canonical tables and passes CI validation in <= 10 minutes on a standard dev machine.
- **SC-002**: A conforming alternate schema object can be injected and runs the pipeline unchanged.
- **SC-003**: Non-conforming inputs are rejected with errors that include table, column, and failing constraint.
- **SC-003**: Non-conforming inputs are rejected with errors that include table, column, and failing constraint; no partial table acceptance is allowed.
- **SC-004**: CI executes validation checks on each push and fails on regressions.
- **SC-004**: CI executes validation checks on each push and fails on regressions, using pinned Python and validator major versions.

## Assumptions
- The default `LullabySchema` is sufficient for the bundled synthetic cohort.
- Validation tooling will be implemented using Pandera as the single validation engine.
- Source data provides parseable timestamp and timezone information for event fields.
- Performance and scale targets will be defined in a later plan when real-data targets are considered.
- CI environment uses pinned Python version and pinned validator major versions for reproducibility.

## Implementation Notes
- Place `schemas/` module containing the ABC and `LullabySchema` implementation.
- Add `schemas/data-dictionary.md` to document columns and units.
- Implement `validation/` with Pandera schemas/checks executed at ingestion.
- Expose a runtime injection point (config/env) to select schema subclass.
- Runtime schema selector accepts alias or Python import path (`package.module:ClassName`).

## Acceptance Tests
- Add CI job `validate-schema` that runs ingestion + validation on bundled data and marks PR green only if validation passes.

