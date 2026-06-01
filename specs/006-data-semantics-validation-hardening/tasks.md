---
id: TASKS-006
title: Data Semantics and Validation Hardening Tasks
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-006, PLAN-006, DATA-006, RESEARCH-006]
implements: [P3, P5, P7, P10]
supersedes: null
superseded_by: null
related: [SPEC-001, SPEC-003, SPEC-004A, SPEC-005]
description: "Implementation task list for data semantics, missingness, validation, manifest, simulator diagnostic, and category-completeness hardening."
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Tasks: Data Semantics and Validation Hardening

**Input**: Design documents from `specs/006-data-semantics-validation-hardening/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/`

**Tests**: Tests are required by SPEC-006 and its contracts. Write the tests for each story before implementation and confirm they fail against the current behavior where applicable.

**Organization**: Tasks are grouped by user story so each story can be implemented and verified independently after the shared parser foundation is complete.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files or independent test cases
- **[Story]**: Maps the task to a SPEC-006 user story
- Each task names the exact source or test path to change

## Phase 1: Setup

**Purpose**: Add the shared semantic parsing surface and focused test entry points.

- [X] T001 Create `src/validation/semantics.py` with exported names for domain boolean parsing, parsed counts, warnings, and errors.
- [X] T002 Update `src/validation/__init__.py` to expose the shared semantics helpers to ingestion, simulation, visualization, and tests.
- [X] T003 [P] Create `tests/unit/test_boolean_semantics.py` with token-matrix fixture helpers for true, false, missing, and invalid values.
- [X] T004 [P] Add reusable EDA fixture helpers for missingness and required-input cases in `tests/test_eda_missingness_policy.py`.

---

## Phase 2: Foundational Parser

**Purpose**: Implement the parser that blocks all user stories.

**Blocking rule**: No user story implementation should start until T005-T010 are complete.

- [X] T005 Implement `DomainBooleanParsePolicy`, `ParsedBooleanSeries`, and `parse_domain_boolean_series()` in `src/validation/semantics.py`.
- [X] T006 Implement deterministic scalar normalization for native booleans, numeric flags, common string flags, blanks, nulls, and invalid tokens in `src/validation/semantics.py`.
- [X] T007 [P] Add accepted-token tests for native, numeric, string, blank, and null values in `tests/unit/test_boolean_semantics.py`.
- [X] T008 [P] Add required-role invalid token failure tests in `tests/unit/test_boolean_semantics.py`.
- [X] T009 [P] Add optional-role invalid token warning-as-missing tests in `tests/unit/test_boolean_semantics.py`.
- [X] T010 Add a regression guard in `tests/unit/test_boolean_semantics.py` that fails on generic `.astype(bool)` use for domain boolean fields in `src/ingestion/`, `src/simulation/`, and `src/visualization/`.

**Checkpoint**: Shared boolean parsing is testable and ready for callers.

---

## Phase 3: User Story 1 - Preserve Missingness as Evidence (Priority: P1)

**Goal**: EDA panels and diagnostic summaries distinguish true, false, and missing/unknown instead of converting missing values to false.

**Independent Test**: Focused EDA fixtures with true, false, blank, null, unknown, and invalid optional values render explicit missing/unknown counts and warnings.

### Tests for User Story 1

- [X] T011 [P] [US1] Add outcome prevalence fixture tests in `tests/test_eda_missingness_policy.py` for positive, negative, missing/unknown, denominator, and class-imbalance counts.
- [X] T012 [P] [US1] Add risk-indicator fixture tests in `tests/test_eda_missingness_policy.py` for yes, no, and missing/unknown counts.
- [X] T013 [P] [US1] Add alert funnel fixture tests in `tests/test_eda_missingness_policy.py` for missing survey, call, and contact states.
- [X] T014 [P] [US1] Add optional invalid boolean warning tests in `tests/test_eda_missingness_policy.py` that verify invalid optional values render as `Missing/Unknown`.

### Implementation for User Story 1

- [X] T015 [US1] Replace `_outcome_series()` and `_heat_illness_series()` in `src/visualization/eda_core.py` with parser-backed tri-state outcome helpers.
- [X] T016 [US1] Update `render_outcome_prevalence()`, `_class_imbalance_panel()`, `_prevalence_panel()`, and `_outcome_context_panel()` in `src/visualization/eda_core.py` to display positive, negative, missing/unknown, denominator, and warning annotations.
- [X] T017 [US1] Update `_risk_indicator_panel()`, `_boolean_bar()`, and `_optional_outcome_context()` in `src/visualization/eda_core.py` to count yes, no, and missing/unknown separately.
- [X] T018 [US1] Update `_survey_states()`, `_completion_series()`, `_call_attempted_count()`, `_call_completed_count()`, `_contact_state_panel()`, and `_funnel_panel()` in `src/visualization/eda_core.py` to keep missing states explicit and use only explicit completed states.
- [X] T019 [US1] Propagate optional-role parser warnings into `PanelResult.warnings` in `src/visualization/eda_core.py`.

**Checkpoint**: Missingness is visible in EDA output and no longer silently counted as false.

---

## Phase 4: User Story 2 - Parse Boolean-Like Values Consistently (Priority: P1)

**Goal**: Ingestion, simulator diagnostics, EDA, and tests share one boolean-like value policy across native and CSV-loaded data.

**Independent Test**: Native boolean, numeric, string, blank, null, and invalid fixtures produce the same counts and rates in stream replay and simulator diagnostics.

### Tests for User Story 2

- [X] T020 [P] [US2] Add `_stream_pending` string and numeric boolean tests in `tests/unit/test_stream_adapter_unit.py`.
- [X] T021 [P] [US2] Add simulator diagnostic equivalence tests for native boolean versus CSV/string boolean inputs in `tests/unit/test_simulation_targets.py`.
- [X] T022 [P] [US2] Add CSV-loaded expectation tests in `tests/unit/test_simulation_schema_validation.py` that use the shared parser instead of `.astype(bool)`.
- [X] T023 [P] [US2] Add invalid required diagnostic token tests in `tests/unit/test_simulation_targets.py` that assert readiness diagnostics fail clearly.

### Implementation for User Story 2

- [X] T024 [US2] Replace `_stream_pending` `.astype(bool)` parsing in `src/ingestion/stream/adapter.py` with the shared domain boolean parser.
- [X] T025 [US2] Replace event-rate, adherence, physiology, and missingness `.astype(bool)` parsing in `src/simulation/export.py` with the shared domain boolean parser.
- [X] T026 [US2] Update boolean-derived expected-rate assertions in `tests/unit/test_simulation_targets.py` to use parser-backed masks.
- [X] T027 [US2] Update boolean-derived expected-set assertions in `tests/unit/test_simulation_schema_validation.py` to use parser-backed masks.
- [X] T028 [US2] Audit `rg "astype\\(bool\\)" src tests --glob '!*.md'` and leave only native/generated-safe uses with explicit tests or comments.

**Checkpoint**: String `"False"` and `"0"` are false everywhere domain booleans are parsed.

---

## Phase 5: User Story 3 - Fail Clearly on Required Schema Problems (Priority: P2)

**Goal**: Required EDA inputs fail before writing or registering requested artifacts, while optional inputs degrade with visible warnings.

**Independent Test**: Missing required tables fail with no new requested PNGs or manifest entries; missing optional tables render unavailable cards; alternate repo-relative outputs are registered.

### Tests for User Story 3

- [X] T029 [P] [US3] Add required table missing test in `tests/test_eda_core_outputs.py` that asserts generation fails before writing requested panel artifacts.
- [X] T030 [P] [US3] Add schema-invalid required role test in `tests/test_eda_core_outputs.py` that asserts the error names the entity, path, and role.
- [X] T031 [P] [US3] Add optional entity missing test in `tests/test_eda_missingness_policy.py` that asserts labeled unavailable cards and warnings.
- [X] T032 [P] [US3] Add repo-relative alternate output registration tests in `tests/unit/test_artifact_manifest.py`.
- [X] T033 [P] [US3] Add outside-repository output warning and no-absolute-path tests in `tests/unit/test_artifact_manifest.py`.
- [X] T034 [P] [US3] Add CLI nonzero exit test for required input failure in `tests/test_eda_core_outputs.py`.

### Implementation for User Story 3

- [X] T035 [US3] Add required and optional panel input preflight helpers in `src/visualization/eda_core.py`.
- [X] T036 [US3] Replace `_load_entity_or_empty()` in `src/visualization/eda_core.py` with loader behavior that separates required failures from optional unavailable tables.
- [X] T037 [US3] Update `generate_core_dashboards()` in `src/visualization/eda_core.py` to preflight all requested core panels before creating output directories, writing PNGs, or registering artifacts.
- [X] T038 [US3] Update `src/visualization/generate_eda.py` to return nonzero status with actionable messages for required input failures.
- [X] T039 [US3] Update `_register_results()` in `src/visualization/eda_core.py` to register every generated repo-relative artifact and warn for outside-repo outputs.
- [X] T040 [US3] Relax `_validate_entry_path()` in `src/visualization/artifacts.py` so any safe repository-relative artifact path is valid in the default manifest.
- [X] T041 [US3] Ensure optional warnings and required/optional role lists remain attached to each `FigureArtifact` entry in `src/visualization/eda_core.py`.

**Checkpoint**: Required failures are loud and artifact provenance remains accurate.

---

## Phase 6: User Story 4 - Keep Descriptive Categories Complete (Priority: P3)

**Goal**: Low-count and rare descriptive categories remain visible or auditable instead of being silently truncated.

**Independent Test**: Fixtures with more categories than fit directly preserve every category and count through labels, overflow tables, or manifest metadata.

### Tests for User Story 4

- [X] T042 [P] [US4] Add alert trigger reason fixture tests with more than eight categories in `tests/test_eda_core_outputs.py`.
- [X] T043 [P] [US4] Add low-count demographic and equity category tests in `tests/test_eda_core_outputs.py`.
- [X] T044 [P] [US4] Add overflow metadata assertion tests for grouped categories in `tests/test_eda_core_outputs.py`.

### Implementation for User Story 4

- [X] T045 [US4] Remove silent `.head(8)` truncation from `_trigger_reason_panel()` in `src/visualization/eda_core.py`.
- [X] T046 [US4] Add category overflow rendering or `CategoryCompletenessRecord` metadata support in `src/visualization/eda_core.py`.
- [X] T047 [US4] Update cohort overview category panels in `src/visualization/eda_core.py` so low-count demographic and equity-relevant categories are not suppressed.
- [X] T048 [US4] Propagate grouped or overflow category counts into artifact warnings or manifest metadata in `src/visualization/eda_core.py`.

**Checkpoint**: Descriptive categories are complete and auditable.

---

## Phase 7: Polish and Acceptance Evidence

**Purpose**: Verify the full hardening pass and refresh tracked acceptance artifacts.

- [X] T049 Run focused hardening tests from `specs/006-data-semantics-validation-hardening/quickstart.md`.
- [X] T050 Run `rg "astype\\(bool\\)" src tests --glob '!*.md'` and confirm domain boolean parsing has no unsafe truthiness paths.
- [X] T051 Regenerate default EDA artifacts with `.venv/bin/python -m src.visualization.generate_eda --data-dir data/raw --out-dir outputs/figures/eda --panels core`.
- [X] T052 Run optional synthetic EDA generation with `.venv/bin/python -m src.visualization.generate_eda --data-dir data/synthetic/longitudinal --out-dir outputs/figures/eda_synthetic --panels core`.
- [X] T053 Verify regenerated PNG dimensions and manifest entries for affected artifacts in `outputs/figures/eda/` and `outputs/figures/manifest.json`.
- [X] T054 Run the full local test suite with `.venv/bin/pytest`.
- [X] T055 Update `CHANGELOG.md` with the completed SPEC-006 hardening entry after tests and regenerated artifacts pass.

---

## Dependencies and Execution Order

### Phase Dependencies

- **Phase 1 Setup**: No dependencies.
- **Phase 2 Foundational Parser**: Depends on Phase 1 and blocks all user stories.
- **Phase 3 US1**: Depends on Phase 2 and is the MVP for preserving missingness in dashboards.
- **Phase 4 US2**: Depends on Phase 2 and may run in parallel with US1 after parser completion.
- **Phase 5 US3**: Depends on Phase 2 and should land before artifact regeneration.
- **Phase 6 US4**: Depends on Phase 2 and can run after or alongside US3.
- **Phase 7 Polish**: Depends on all selected user stories.

### User Story Dependencies

- **US1 Preserve Missingness**: Requires parser foundation only.
- **US2 Boolean Consistency**: Requires parser foundation only.
- **US3 Required Schema Failures**: Requires parser foundation and should integrate US1 warning behavior.
- **US4 Category Completeness**: Requires parser foundation and should integrate US3 manifest warning behavior.

### Within Each User Story

- Write story tests first and confirm they fail for the current bug class.
- Implement source changes only after the failing tests capture the intended behavior.
- Run the story's focused tests before starting acceptance artifact regeneration.

## Parallel Opportunities

- T003 and T004 can run in parallel after T001/T002 are understood.
- T007, T008, and T009 can run in parallel after T005/T006.
- T011-T014 can run in parallel because they cover separate EDA missingness behaviors.
- T020-T023 can run in parallel because they target separate ingestion and simulator tests.
- T029-T034 can run in parallel because they target independent required-input, CLI, and manifest behaviors.
- T042-T044 can run in parallel because they target separate category completeness fixtures.

## Parallel Example: User Story 2

```text
Task: "T020 [US2] Add _stream_pending string and numeric boolean tests in tests/unit/test_stream_adapter_unit.py"
Task: "T021 [US2] Add simulator diagnostic equivalence tests for native boolean versus CSV/string boolean inputs in tests/unit/test_simulation_targets.py"
Task: "T022 [US2] Add CSV-loaded expectation tests in tests/unit/test_simulation_schema_validation.py"
Task: "T023 [US2] Add invalid required diagnostic token tests in tests/unit/test_simulation_targets.py"
```

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete US1 so dashboard missingness is honest.
3. Run the focused EDA missingness tests.
4. Continue with US2, US3, and US4 in priority order.

### Acceptance Finish

1. Run focused tests from `quickstart.md`.
2. Regenerate affected tracked EDA artifacts and `outputs/figures/manifest.json`.
3. Run the full test suite.
4. Add the final `CHANGELOG.md` entry once acceptance evidence is clean.
