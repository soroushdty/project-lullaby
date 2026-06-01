---
id: TASKS-005
title: Synthetic Longitudinal Physiologic Data Simulator Tasks
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [PLAN-005, SPEC-005, SPEC-001, SPEC-004]
implements: [P1, P2, P3, P5, P7, P8, P9]
supersedes: null
superseded_by: null
related: [SPEC-004, SPEC-006, SPEC-007, SPEC-008]
description: "Executable task list for the seeded longitudinal synthetic cohort simulator"
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Tasks: Synthetic Longitudinal Physiologic Data Simulator

**Input**: Design documents from `specs/005-synthetic-longitudinal-simulator/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md, contracts/

**Tests**: Included because SPEC-005, quickstart.md, and contracts require focused reproducibility, target, schema-validation, and CLI tests.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add dependency, config, package, script, and fixture scaffolding needed by every story.

- [X] T001 Add numpy as an explicit project dependency in pyproject.toml
- [X] T002 Create default simulator configuration in config/simulation.yaml
- [X] T003 Create synthetic MEOWS threshold configuration in config/meows_thresholds.synthetic.yaml
- [X] T004 [P] Create simulation package export scaffold in src/simulation/__init__.py
- [X] T005 [P] Create generator script scaffold in scripts/generate_synthetic.py
- [X] T006 [P] Add temporary simulation output fixtures in tests/conftest.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement configuration, deterministic RNG, core data structures, and schema-registry extensions that all stories depend on.

**CRITICAL**: No user story work should begin until this phase is complete.

### Tests for Foundational Infrastructure

- [X] T007 [P] Add config default, validation, and archetype normalization tests in tests/unit/test_simulation_config.py
- [X] T008 [P] Add schema-registry extension tests for environment, recruitment, and synthetic longitudinal aliases in tests/unit/test_simulation_schema_validation.py

### Implementation for Foundational Infrastructure

- [X] T009 Implement simulation config dataclasses, YAML loading, validation, and effective config serialization helpers in src/simulation/config.py
- [X] T010 Implement deterministic component RNG stream helpers from the root seed in src/simulation/config.py
- [X] T011 Define core cohort, participant-day, output package, and summary data structures in src/simulation/cohort.py
- [X] T012 Extend generated environment/recruitment entities and daily-vitals aliases in src/visualization/schema_registry.py
- [X] T013 Export the public simulation config and cohort APIs from src/simulation/__init__.py

**Checkpoint**: Config loading, RNG streams, core structures, and registry extensions are ready for story-level work.

---

## Phase 3: User Story 1 - Generate Reproducible Longitudinal Cohorts (Priority: P1) MVP

**Goal**: Generate the canonical output package deterministically with a full participant-day grid and schema-valid tables.

**Independent Test**: Generate the default cohort twice with the same seed and configuration, compare CSV content byte-for-byte, verify required files exist, verify `daily_vitals.csv` row count equals participants times study days, and validate against the schema registry.

### Tests for User Story 1

- [X] T014 [P] [US1] Add same-seed CSV reproducibility tests in tests/unit/test_simulation_reproducibility.py
- [X] T015 [P] [US1] Add output package, required-file, full-grid row-count, and schema validation tests in tests/unit/test_simulation_schema_validation.py
- [X] T016 [P] [US1] Add generator CLI happy-path contract test in tests/integration/test_simulation_cli.py

### Implementation for User Story 1

- [X] T017 [US1] Implement deterministic participant ID, baseline profile, and archetype assignment generation in src/simulation/cohort.py
- [X] T018 [US1] Implement full participant-day grid construction with stable date, study-day, and week columns in src/simulation/cohort.py
- [X] T019 [US1] Implement baseline environment, recruitment, clinical outcome, alert, and contact table placeholders needed for a schema-valid package in src/simulation/cohort.py
- [X] T020 [US1] Implement deterministic CSV/YAML/JSON output writing with stable row and column ordering in src/simulation/export.py
- [X] T021 [US1] Integrate SPEC-004 schema validation and failed/not-ready handling into the export flow in src/simulation/export.py
- [X] T022 [US1] Implement generator orchestration entry point for config, generation, export, validation, and summary writing in src/simulation/export.py
- [X] T023 [US1] Implement argparse command wrapper with `--config`, `--out-dir`, and `--seed` in scripts/generate_synthetic.py
- [X] T024 [US1] Wire public `generate_synthetic` or equivalent orchestration export in src/simulation/__init__.py

**Checkpoint**: User Story 1 is independently functional and clone-to-run generation produces a deterministic schema-valid package.

---

## Phase 4: User Story 2 - Encode Clinically Plausible Physiologic Signals (Priority: P1)

**Goal**: Add cardiovascular, heat-strain, and overlap physiology that satisfies directional constraints without making labels trivially separable.

**Independent Test**: Generate trajectories and verify CV cases have positive seven-day pre-event body-water slopes when enough data exists, heat-strain days more often show body-water decrease with HR/temp increase, and overlap examples remain imperfectly separable.

### Tests for User Story 2

- [X] T025 [P] [US2] Add CV pre-event slope, heat-strain delta, and overlap nonseparability tests in tests/unit/test_simulation_targets.py
- [X] T026 [P] [US2] Add alert and clinical outcome alignment tests for CV, heat, and overlap cases in tests/unit/test_simulation_schema_validation.py

### Implementation for User Story 2

- [X] T027 [US2] Implement cardiovascular trajectory slope helpers for BP, HR, and body-water changes in src/simulation/physiology.py
- [X] T028 [US2] Implement heat-strain spike helpers with Celsius export conversion in src/simulation/physiology.py
- [X] T029 [US2] Implement overlap-case physiology with imperfect body-water discrimination in src/simulation/physiology.py
- [X] T030 [US2] Integrate physiology generation into participant-day observed values in src/simulation/cohort.py
- [X] T031 [US2] Implement alert trigger, alert classification, and clinical outcome derivation from physiologic states in src/simulation/cohort.py

**Checkpoint**: User Stories 1 and 2 are independently functional, and physiologic target tests pass without relying on missingness mechanisms.

---

## Phase 5: User Story 3 - Represent Adherence and Missingness Mechanisms (Priority: P2)

**Goal**: Apply adherence decline, contextual missingness, dropout, and clustered gaps while preserving nulls in raw exports.

**Independent Test**: Generate a cohort and verify aggregate wear hours and scale adherence decline, missingness differs by archetype and heat exposure, worsening state increases dropout or partial observation, and raw CSV values remain missing.

### Tests for User Story 3

- [X] T032 [P] [US3] Add adherence decline and non-random missingness diagnostic tests in tests/unit/test_simulation_targets.py
- [X] T033 [P] [US3] Add raw null preservation and post-dropout full-grid tests in tests/unit/test_simulation_schema_validation.py

### Implementation for User Story 3

- [X] T034 [US3] Implement wear-hour and scale-adherence trajectories by archetype and study week in src/simulation/missingness.py
- [X] T035 [US3] Implement MCAR, MAR, MNAR-proxy, and clustered gap masks in src/simulation/missingness.py
- [X] T036 [US3] Integrate missingness masks, dropout metadata, and missingness reasons into participant-day generation in src/simulation/cohort.py
- [X] T037 [US3] Preserve missing observed values as null/empty CSV cells during serialization in src/simulation/export.py

**Checkpoint**: Missingness is explicit and raw exports retain full participant-day rows with null observations.

---

## Phase 6: User Story 4 - Configure Cohort Mix, Events, and Heat Context (Priority: P2)

**Goal**: Make cohort size, seed, archetypes, event rates, heat season, adherence, missingness, physiology, and alert follow-up configurable.

**Independent Test**: Run default and modified configurations, then verify observed event rates, archetype proportions, heat exposure patterns, and follow-up rates move toward configured targets within tolerance.

### Tests for User Story 4

- [X] T038 [P] [US4] Add custom config and CLI override tests in tests/unit/test_simulation_config.py
- [X] T039 [P] [US4] Add event-rate, archetype-proportion, heat-wave, and follow-up probability tests in tests/unit/test_simulation_targets.py

### Implementation for User Story 4

- [X] T040 [US4] Implement deterministic event assignment against configured target rates in src/simulation/cohort.py
- [X] T041 [US4] Implement summer heat, heat-wave, heat-index, and Fahrenheit-to-Celsius conversion logic in src/simulation/environment.py
- [X] T042 [US4] Integrate generated environment context into participant-day physiology and missingness in src/simulation/cohort.py
- [X] T043 [US4] Implement survey, nurse-call, and follow-up contact completion from alert settings in src/simulation/cohort.py
- [X] T044 [US4] Write normalized effective configuration to `simulation_config_used.yaml` in src/simulation/export.py
- [X] T045 [US4] Apply CLI seed and output-directory overrides to effective configuration in scripts/generate_synthetic.py

**Checkpoint**: Scenario variants can be generated without source edits and still satisfy schema and target checks.

---

## Phase 7: User Story 5 - Publish Diagnostics for Downstream Trust (Priority: P3)

**Goal**: Produce an auditable `simulation_summary.json` that gates downstream readiness on schema validation and target diagnostics.

**Independent Test**: Generate passing and controlled-failing cohorts, confirm every required diagnostic records target, observed value, tolerance, denominator, and status, and confirm failures leave artifacts inspectable while returning non-zero status.

### Tests for User Story 5

- [X] T046 [P] [US5] Add simulation summary shape and required diagnostic check tests in tests/unit/test_simulation_targets.py
- [X] T047 [P] [US5] Add schema-failure and target-failure exit-code tests in tests/integration/test_simulation_cli.py

### Implementation for User Story 5

- [X] T048 [US5] Implement event-rate, archetype, adherence, and scale-use diagnostic checks in src/simulation/export.py
- [X] T049 [US5] Implement physiology, heat-strain, overlap, and missingness diagnostic checks in src/simulation/export.py
- [X] T050 [US5] Implement summary readiness status, warnings, errors, and denominator/coverage reporting in src/simulation/export.py
- [X] T051 [US5] Propagate failed schema or target diagnostics to CLI exit code and concise stdout/stderr summary in scripts/generate_synthetic.py

**Checkpoint**: Downstream users can trust the summary to decide whether a generated cohort is ready.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Verify end-to-end behavior, documentation, performance, and compatibility.

- [X] T052 [P] Update README simulator usage and canonical synthetic source notes in README.md
- [X] T053 [P] Add simulation public API docstrings and import coverage in src/simulation/__init__.py
- [X] T054 Run focused simulation tests from specs/005-synthetic-longitudinal-simulator/quickstart.md
- [X] T055 Run default generation command from specs/005-synthetic-longitudinal-simulator/quickstart.md
- [X] T056 Run visualization schema validation against data/synthetic/longitudinal from specs/005-synthetic-longitudinal-simulator/quickstart.md
- [X] T057 Verify generated default run completes within the plan performance target in specs/005-synthetic-longitudinal-simulator/plan.md
- [X] T058 Review generated data and docs for synthetic-data transparency and no-PHI wording in data/synthetic/longitudinal/simulation_summary.json
- [X] T059 Run git diff validation for generated artifacts, unintended CSV churn, and whitespace in specs/005-synthetic-longitudinal-simulator/tasks.md

---

## Dependencies & Execution Order

### Phase Dependencies

- Setup (Phase 1) has no dependencies.
- Foundational (Phase 2) depends on Setup and blocks all user stories.
- US1 and US2 are both P1. US1 should land first because it creates the package, CLI, and export path that US2 enriches.
- US3 depends on US1 and benefits from US2 because missingness uses physiologic state.
- US4 depends on US1 and should run after US2/US3 so configurable event, heat, and adherence settings drive real mechanisms.
- US5 depends on US1 through US4 because diagnostics summarize their generated outputs.
- Polish depends on all selected user stories.

### User Story Dependencies

- US1 (P1): Starts after Foundational. Provides deterministic package generation and validation MVP.
- US2 (P1): Starts after Foundational and US1 export skeleton. Adds physiologic signal fidelity.
- US3 (P2): Starts after US1 and preferably after US2. Adds adherence and missingness evidence.
- US4 (P2): Starts after US1 and integrates with US2/US3 mechanisms. Adds scenario configurability.
- US5 (P3): Starts after US1 through US4. Adds readiness diagnostics and failure gates.

### Within Each User Story

- Tests are written before implementation and should fail before fixes.
- Data structures and pure generation helpers come before export and CLI integration.
- Schema validation and target diagnostics are readiness gates, not optional warnings.
- Each story is complete only when its independent tests pass from the repository root.

### Parallel Opportunities

- Setup tasks T004 through T006 can run in parallel after T001 through T003 are underway.
- Foundational tests T007 and T008 can run in parallel.
- US1 tests T014 through T016 can run in parallel.
- US2 tests T025 and T026 can run in parallel.
- US3 tests T032 and T033 can run in parallel.
- US4 tests T038 and T039 can run in parallel.
- US5 tests T046 and T047 can run in parallel.
- Polish documentation tasks T052 and T053 can run in parallel.

---

## Parallel Example: User Story 1

```bash
# Launch independent US1 tests together:
Task: "T014 Add same-seed CSV reproducibility tests in tests/unit/test_simulation_reproducibility.py"
Task: "T015 Add output package, required-file, full-grid row-count, and schema validation tests in tests/unit/test_simulation_schema_validation.py"
Task: "T016 Add generator CLI happy-path contract test in tests/integration/test_simulation_cli.py"
```

## Parallel Example: User Story 4

```bash
# Launch independent US4 tests together:
Task: "T038 Add custom config and CLI override tests in tests/unit/test_simulation_config.py"
Task: "T039 Add event-rate, archetype-proportion, heat-wave, and follow-up probability tests in tests/unit/test_simulation_targets.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: US1 deterministic package generation.
4. Stop and validate: same-seed CSV reproducibility, required files, full-grid row count, and schema validation.

### Incremental Delivery

1. Add US1 to establish deterministic schema-valid output.
2. Add US2 to make physiology clinically meaningful.
3. Add US3 to preserve adherence and missingness mechanisms.
4. Add US4 to unlock configurable scenarios.
5. Add US5 to gate downstream trust with summary diagnostics.

### Validation Gates

1. `pytest tests/unit/test_simulation_reproducibility.py tests/unit/test_simulation_targets.py tests/unit/test_simulation_schema_validation.py tests/integration/test_simulation_cli.py tests/unit/test_simulation_config.py`
2. `python scripts/generate_synthetic.py --config config/simulation.yaml --out-dir data/synthetic/longitudinal --seed 20260601`
3. `python -m src.cli.validate_visualization_foundation --data-dir data/synthetic/longitudinal`
