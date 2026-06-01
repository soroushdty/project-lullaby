---
id:            TASKS-001
title:         Canonical Schema & Validation Tasks
status:        draft
version:       0.1.0
created:       2026-06-01
updated:       2026-06-01
author:        Soroush Dianaty
depends_on:    [PLAN-001, SPEC-001]
implements:    [P1, P2, P3, P5]
supersedes:    null
superseded_by: null
related:       [PLAN-001, SPEC-001]
description:   "Executable task list for canonical schema ABC, LullabySchema, Pandera validation engine, ingestion pipeline, and CI gate"
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Tasks: Canonical Schema & Validation

**Input**: Design documents from `/specs/001-canonical-schema-validation/`

**Prerequisites**: plan.md (required), spec.md (required), data-model.md, contracts/schema-interface.md, contracts/validation-contract.md, quickstart.md

**Tests**: Included because spec and quickstart require CI/test verification of schema validation.

**Organization**: Tasks are grouped by user story to enable independent implementation and validation.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create all source and test file scaffolds before any logic is written.

- [X] T001 Create source module scaffolds with empty stubs in src/schemas/base.py, src/schemas/lullaby.py, src/schemas/registry.py
- [X] T002 Create validation module scaffolds in src/validation/pandera_models.py, src/validation/engine.py
- [X] T003 Create ingestion module scaffolds in src/ingestion/pipeline.py, src/ingestion/adapters/csv_adapter.py
- [X] T004 Create CLI entrypoint scaffold with argparse in src/cli/validate_schema.py
- [X] T005 Create unit test module scaffolds in tests/unit/test_lullaby_schema.py and tests/unit/test_pandera_models.py
- [X] T006 Create contract test module scaffolds in tests/contract/test_schema_interface.py and tests/contract/test_validation_contract.py
- [X] T007 Create integration test module scaffold in tests/integration/test_ingestion_validation_pipeline.py
- [X] T008 Create GitHub Actions workflow scaffold in .github/workflows/validate-schema.yml
- [X] T009 Generate bundled synthetic dataset (five CSVs for all canonical tables) in data/synthetic/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement schema ABC, TableContract, exception types, registry, and Pandera utilities required by all user stories.

**⚠️ CRITICAL**: No user story work begins until this phase is complete.

- [X] T010 Implement SchemaContract ABC (name, version, table_names, table_contract, pandera_schema, data_dictionary) in src/schemas/base.py
- [X] T011 Implement TableContract dataclass (required_columns, optional_columns, primary_key, timestamp_column, constraints) in src/schemas/base.py
- [X] T012 Implement custom exception types (SchemaContractError, SchemaTableMissingError, SchemaValidationConfigError) in src/schemas/base.py
- [X] T013 [P] Implement schema registry with alias and dotted-import-path resolution in src/schemas/registry.py
- [X] T014 [P] Implement Pandera base utilities and shared UTC-timezone check helper in src/validation/pandera_models.py

**Checkpoint**: SchemaContract ABC, TableContract, exceptions, registry, and Pandera utilities are ready for story-level implementation.

---

## Phase 3: User Story 1 - Ingest Bundled Data (Priority: P1) 🎯 MVP

**Goal**: A developer clones the repo and runs ingestion against bundled synthetic data; all five tables pass schema validation.

**Independent Test**: Running CLI on bundled synthetic data exits 0 and emits a report; deliberate violation exits non-zero with table/column/constraint detail.

### Tests for User Story 1

- [X] T015 [P] [US1] Add unit tests for LullabySchema table contracts (column lists, PKs, timestamp column for all five tables) in tests/unit/test_lullaby_schema.py
- [X] T016 [P] [US1] Add unit tests for Pandera model field types, nullability, and constraint definitions in tests/unit/test_pandera_models.py
- [X] T017 [US1] Add contract tests asserting all six SchemaContract interface methods and five-table requirement from schema-interface.md in tests/contract/test_schema_interface.py
- [X] T018 [US1] Add contract tests asserting validation boundary success/failure payload shape and non-imputation rule from validation-contract.md in tests/contract/test_validation_contract.py
- [X] T019 [US1] Add integration test: bundled synthetic data passes full pipeline with exit code 0 and five-table report in tests/integration/test_ingestion_validation_pipeline.py
- [X] T020 [US1] Add integration test: deliberate schema violation (missing required column) fails fast with table, column, and constraint in error payload in tests/integration/test_ingestion_validation_pipeline.py

### Implementation for User Story 1

- [X] T021 [US1] Implement LullabySchema for participants table (TableContract + Pandera schema) in src/schemas/lullaby.py
- [X] T022 [US1] Implement LullabySchema for daily_vitals table in src/schemas/lullaby.py
- [X] T023 [US1] Implement LullabySchema for alerts table in src/schemas/lullaby.py
- [X] T024 [US1] Implement LullabySchema for clinical_outcomes table in src/schemas/lullaby.py
- [X] T025 [US1] Implement LullabySchema for staff_contacts table in src/schemas/lullaby.py
- [X] T026 [US1] Implement validation engine: run Pandera schema per table, reject whole table on any violation, return structured error payload in src/validation/engine.py
- [X] T027 [US1] Implement UTC-normalization and ingestion state machine (raw_loaded -> normalized -> schema_validated/schema_rejected) in src/ingestion/pipeline.py
- [X] T028 [US1] Implement CSV adapter for loading raw CSVs from input directory keyed by table name in src/ingestion/adapters/csv_adapter.py
- [X] T029 [US1] Implement CLI entrypoint: --schema, --input flags; emit report to artifacts/validation-report.json; exit 0 on pass, non-zero on failure in src/cli/validate_schema.py

**Checkpoint**: US1 is independently functional; bundled ingestion passes and violation detection is tested.

---

## Phase 4: User Story 2 - Swap Schema Implementation (Priority: P2)

**Goal**: A data engineer injects a conforming alternate schema object and runs the pipeline without code edits.

**Independent Test**: Conforming alternate schema passes ingestion; non-conforming injection raises SchemaContractError.

### Tests for User Story 2

- [X] T030 [P] [US2] Add unit tests for registry alias (lullaby) and dotted-import-path resolution in tests/unit/test_lullaby_schema.py
- [X] T031 [US2] Add integration test: conforming alternate schema injected via --schema flag runs pipeline successfully in tests/integration/test_ingestion_validation_pipeline.py
- [X] T032 [US2] Add integration test: non-conforming alternate schema injection raises SchemaContractError with actionable message in tests/integration/test_ingestion_validation_pipeline.py

### Implementation for User Story 2

- [X] T033 [US2] Register lullaby alias and wire CLI --schema flag to registry resolution in src/schemas/registry.py and src/cli/validate_schema.py
- [X] T034 [US2] Create conforming alternate schema test fixture class in tests/conftest.py

**Checkpoint**: US2 schema injection is independently functional and both conforming/non-conforming paths are tested.

---

## Phase 5: CI Gate (Priority: P3)

**Goal**: Block merges when schema validation fails; enforce pinned Python and dependency versions.

**Independent Test**: validate-schema workflow fails on invalid data and passes on valid bundled data using the required CLI command.

### Tests for CI Gate

- [X] T035 [US3] Add integration test for CLI exit code 0 (valid bundled data) and non-zero (invalid data) in tests/integration/test_ingestion_validation_pipeline.py

### Implementation for CI Gate

- [X] T036 [US3] Implement validate-schema GitHub Actions workflow: pin Python 3.11 and dependency major versions, run CLI against data/synthetic/ in .github/workflows/validate-schema.yml
- [X] T037 [US3] Configure workflow to publish artifacts/validation-report.json as a GitHub Actions artifact on every run in .github/workflows/validate-schema.yml

**Checkpoint**: CI gate blocks merges on validation failures and publishes the validation report artifact.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final hardening and documentation alignment across all stories.

- [X] T038 [P] Write data dictionary (column name, type, unit, nullable, description) for all five canonical tables in schemas/data-dictionary.md
- [X] T039 [P] Run full test suite from quickstart (pytest -q) and adjust any failing expectations in tests/
- [X] T040 Add spec-001 CHANGELOG.md entry with all required fields (Date, Spec, Summary, Rationale, Impact, Targets) following changelog policy

---

## Dependencies & Execution Order

### Phase Dependencies

- Setup (Phase 1) has no dependencies.
- Foundational (Phase 2) depends on Setup and blocks all user stories.
- User Story phases (Phase 3–5) depend on Foundational completion.
- Polish (Phase 6) depends on completion of all user stories.

### User Story Dependencies

- US1 (P1) starts immediately after Foundational and defines MVP.
- US2 (P2) starts after Foundational; reuses registry and validation engine from US1.
- US3 (CI gate) starts after US1 CLI is functional; can proceed in parallel with US2.

### Within Each User Story

- Tests are authored before implementation and should fail before fixes.
- Validation logic lands before CLI and workflow integration.
- Story is complete only when its independent test criteria pass.

### Parallel Opportunities

- Phase 2: T013 and T014 can run in parallel after T012.
- US1 tests: T015 and T016 can run in parallel; T017 and T018 can run in parallel.
- US2 tests: T030 can run in parallel with T031.
- CI gate: T036 and T037 are sequential (T037 extends T036).
- Polish: T038 and T039 can run in parallel.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 (US1).
3. Validate US1 independent test criteria before expanding scope.

### Incremental Delivery

1. Deliver US1 as baseline: bundled ingestion passes, violations fail loud.
2. Add US2 for pluggable schema injection.
3. Add CI gate (US3) to enforce validation on every PR.
4. Finalize data dictionary and full test run in Polish.

### Parallel Team Strategy

1. Team aligns on Phase 1 and Phase 2.
2. After foundation: split US2 tests while US1 implementation lands.
3. Rejoin for CI gate and Polish.

---

## Notes

- [P] tasks are safe to run concurrently when dependencies are satisfied.
- [USn] labels provide traceability from tasks to story outcomes.
- Every task includes an explicit file path to remain LLM-executable.
- Validation failure policy: reject the whole table — no partial acceptance, no silent imputation.
- Timestamps: normalize to UTC at ingestion; missing or invalid timezone metadata is a hard validation error.
