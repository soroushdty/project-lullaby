---
id: TASKS-010
title: Relationships, Heat Exposure, Archetypes, and Recruitment Dashboards Tasks
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-010, PLAN-010, DATA-010, RESEARCH-010]
implements: [P3, P5, P7, P10]
supersedes: null
superseded_by: null
related: [SPEC-001, SPEC-004, SPEC-006, SPEC-007, SPEC-009]
description: "Executable implementation task list for relationship, heat/environment, archetype, and recruitment EDA dashboard PNGs, CLI routing, manifest registration, and focused tests."
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Tasks: Relationships, Heat Exposure, Archetypes, and Recruitment Dashboards

**Input**: Design documents from `specs/010-relationships-heat-archetypes-recruitment-dashboards/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/`

**Tests**: Included because SPEC-010 requires focused tests in `tests/test_eda_relationships_outputs.py`.

**Organization**: Tasks are grouped by user story so each SPEC-010 panel can be implemented and verified independently after the shared EDA foundation is complete.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files or independent fixtures
- **[Story]**: Maps the task to a SPEC-010 user story
- Each task names the exact source, test, artifact, or documentation path to change

## Phase 1: Setup

**Purpose**: Prepare the SPEC-010 EDA file structure, exports, and focused test fixtures.

- [ ] T001 [P] Create reusable SPEC-010 canonical table fixture builders in `tests/test_eda_relationships_outputs.py`.
- [ ] T002 [P] Add module skeleton for shared SPEC-010 loading and Panel 10 in `src/visualization/eda_relationships.py`.
- [ ] T003 [P] Add module skeleton for Panel 11 in `src/visualization/eda_environment.py`.
- [ ] T004 [P] Add module skeleton for Panels 12 and 13 in `src/visualization/eda_archetypes.py`.
- [ ] T005 Export SPEC-010 public APIs from `src/visualization/__init__.py`.
- [ ] T006 Confirm accepted environment, recruitment, participant, vital, outcome, and alert roles in `src/visualization/schema_registry.py`.

---

## Phase 2: Foundational SPEC-010 Loading, CLI, and Manifest Behavior

**Purpose**: Implement shared behavior that blocks every SPEC-010 dashboard panel.

**Blocking rule**: No user story implementation should start until T007-T019 are complete.

### Tests for Foundational Behavior

- [ ] T007 Add CLI success tests for `--panels relationships` and `--panels all` in `tests/test_eda_relationships_outputs.py`.
- [ ] T008 Add four-artifact manifest registration assertions for SPEC-010 artifact ids in `tests/test_eda_relationships_outputs.py`.
- [ ] T009 Add required table and required semantic role preflight failure tests for `participants` and `daily_vitals` in `tests/test_eda_relationships_outputs.py`.
- [ ] T010 Add repo-relative registration and outside-repository warning coverage for SPEC-010 outputs in `tests/test_eda_relationships_outputs.py`.
- [ ] T011 Add artifact dimension assertions for `10_relationships.png`, `11_heat_environment.png`, `12_archetype_explorer.png`, and `13_recruitment_timeline.png` in `tests/test_eda_relationships_outputs.py`.

### Implementation for Foundational Behavior

- [ ] T012 Define `SPEC_ID = "SPEC-010"`, panel filenames, artifact ids, `RelationshipEDATables`, `RelationshipPanelResult`, and `RelationshipInputError` in `src/visualization/eda_relationships.py`.
- [ ] T013 Implement canonical table loading for participants, daily vitals, clinical outcomes, environment, recruitment, and alerts in `src/visualization/eda_relationships.py`.
- [ ] T014 Implement `data/raw` to `data/` fallback resolution and source-path error formatting in `src/visualization/eda_relationships.py`.
- [ ] T015 Implement required entity and semantic-role preflight validation before output directory creation in `src/visualization/eda_relationships.py`.
- [ ] T016 Implement study-day derivation and shared role lookup helpers in `src/visualization/eda_relationships.py`.
- [ ] T017 Implement repo-relative `FigureArtifact` registration, artifact-id suffixing for alternate output dirs, and JSON-safe metadata serialization in `src/visualization/eda_relationships.py`.
- [ ] T018 Extend `src/visualization/generate_eda.py` to accept `--panels relationships`, route to `generate_relationship_dashboards()`, and print success output.
- [ ] T019 Extend `src/visualization/generate_eda.py` to accept `--panels all` and run core, longitudinal, and relationships panel sets in order.

**Checkpoint**: SPEC-010 EDA runs can load canonical inputs, fail before writes on required problems, generate four default artifacts, and register repo-relative outputs.

---

## Phase 3: User Story 1 - Review Descriptive Relationships (Priority: P1) MVP

**Goal**: Generate Panel 10 with descriptive correlations, targeted bivariate views, observed pair counts, heat-index relationships, and CV-vs-heat discriminator annotations.

**Independent Test**: Generate Panel 10 from canonical `daily_vitals` with optional `environment` and assert schema labels, observed-pair metadata, pairwise N annotations, heat-source metadata, and descriptive-only wording.

### Tests for User Story 1

- [ ] T020 [P] [US1] Add Panel 10 artifact existence, 1600 x 900 dimension, and manifest metadata tests in `tests/test_eda_relationships_outputs.py`.
- [ ] T021 [P] [US1] Add observed-pair policy and pairwise N regression tests for the correlation heatmap in `tests/test_eda_relationships_outputs.py`.
- [ ] T022 [P] [US1] Add body-water direction versus BP, HR, and skin-temperature coverage tests in `tests/test_eda_relationships_outputs.py`.
- [ ] T023 [P] [US1] Add environment heat-index and daily-vitals heat-index proxy source tests in `tests/test_eda_relationships_outputs.py`.
- [ ] T024 [P] [US1] Add CV-risk-like and heat-strain-like discriminator metadata tests in `tests/test_eda_relationships_outputs.py`.
- [ ] T025 [P] [US1] Add no-causality and no-imputation language guard tests for Panel 10 metadata in `tests/test_eda_relationships_outputs.py`.

### Implementation for User Story 1

- [ ] T026 [US1] Implement Panel 10 numeric vital role selection with schema labels and units in `src/visualization/eda_relationships.py`.
- [ ] T027 [US1] Implement observed-pair correlation matrix and pairwise N matrix preparation in `src/visualization/eda_relationships.py`.
- [ ] T028 [US1] Implement descriptive correlation heatmap rendering with pairwise N annotations in `src/visualization/eda_relationships.py`.
- [ ] T029 [US1] Implement body-water direction delta preparation for BP, HR, and skin temperature in `src/visualization/eda_relationships.py`.
- [ ] T030 [US1] Implement targeted body-water bivariate panels with observed pair counts and descriptive correlation labels in `src/visualization/eda_relationships.py`.
- [ ] T031 [US1] Implement environment-first heat-index preparation with daily-vitals proxy fallback labeled as Panel 10-only in `src/visualization/eda_relationships.py`.
- [ ] T032 [US1] Implement heat-index versus HR and skin-temperature bivariate rendering in `src/visualization/eda_relationships.py`.
- [ ] T033 [US1] Implement CV-risk-like and heat-strain-like discriminator interval counts and annotation panel in `src/visualization/eda_relationships.py`.
- [ ] T034 [US1] Implement `render_relationships_dashboard()` layout and artifact save path for `outputs/figures/eda/10_relationships.png` in `src/visualization/eda_relationships.py`.
- [ ] T035 [US1] Add Panel 10 observed-data policy, heat source, pairwise N, and discriminator metadata to the SPEC-010 manifest entry in `src/visualization/eda_relationships.py`.

**Checkpoint**: User Story 1 is independently functional and Panel 10 can be generated and reviewed without Panels 11-13.

---

## Phase 4: User Story 2 - Audit Heat Exposure and Environmental Context (Priority: P1)

**Goal**: Generate Panel 11 with real environment trends, high-heat shading, AC-access context, high-heat versus non-high-heat vital summaries, missing environment data, and explicit unavailable behavior.

**Independent Test**: Generate Panel 11 with and without an `environment` table; assert available-data rendering, high-heat fallback metadata, missing environment summaries, and unavailable-panel behavior.

### Tests for User Story 2

- [ ] T036 [P] [US2] Add Panel 11 artifact existence, 1600 x 900 dimension, and manifest metadata tests in `tests/test_eda_relationships_outputs.py`.
- [ ] T037 [P] [US2] Add environment-unavailable panel tests proving daily-vitals heat columns are not treated as an environment table in `tests/test_eda_relationships_outputs.py`.
- [ ] T038 [P] [US2] Add high-heat fallback order tests for heat-wave flag, heat exposure level, and heat-index percentile in `tests/test_eda_relationships_outputs.py`.
- [ ] T039 [P] [US2] Add missing environment row, missing field, and calendar gap metadata tests in `tests/test_eda_relationships_outputs.py`.
- [ ] T040 [P] [US2] Add AC-access stratification and high-heat versus non-high-heat vital response tests in `tests/test_eda_relationships_outputs.py`.

### Implementation for User Story 2

- [ ] T041 [US2] Implement `prepare_environment_frame()` with date or study-day axis support in `src/visualization/eda_environment.py`.
- [ ] T042 [US2] Implement high-heat classification fallback order in `src/visualization/eda_environment.py`.
- [ ] T043 [US2] Implement missing environment row, missing field, and date-gap summaries in `src/visualization/eda_environment.py`.
- [ ] T044 [US2] Implement environment time-series rendering with ambient temperature, heat index, and high-heat shading in `src/visualization/eda_environment.py`.
- [ ] T045 [US2] Implement participant AC access parsing and daily-vitals alignment to environment rows in `src/visualization/eda_environment.py`.
- [ ] T046 [US2] Implement high-heat versus non-high-heat HR and skin-temperature response summaries in `src/visualization/eda_environment.py`.
- [ ] T047 [US2] Implement explicit unavailable panel behavior when `environment.csv` is absent or unusable in `src/visualization/eda_environment.py`.
- [ ] T048 [US2] Implement `render_heat_environment()` layout and artifact save path for `outputs/figures/eda/11_heat_environment.png` in `src/visualization/eda_environment.py`.
- [ ] T049 [US2] Add Panel 11 environment availability, high-heat definition, fabricated-data flag, vital response rows, and missingness metadata to the SPEC-010 manifest entry in `src/visualization/eda_environment.py`.

**Checkpoint**: User Story 2 is independently functional and Panel 11 never fabricates environment data.

---

## Phase 5: User Story 3 - Explore Participant Archetype Segments (Priority: P2)

**Goal**: Generate Panel 12 with five canonical archetype segments, explicit-label handling, provisional rule-derived labels, alert burden from optional alerts, and segment summaries.

**Independent Test**: Generate Panel 12 with explicit labels, unknown explicit labels, no explicit labels, optional alerts, and missing alerts; assert label source metadata, provisional status, rule priority, and segment metrics.

### Tests for User Story 3

- [ ] T050 [P] [US3] Add Panel 12 artifact existence, 1600 x 900 dimension, and manifest metadata tests in `tests/test_eda_relationships_outputs.py`.
- [ ] T051 [P] [US3] Add explicit archetype label source and known-alias normalization tests in `tests/test_eda_relationships_outputs.py`.
- [ ] T052 [P] [US3] Add unknown explicit label preservation tests in `tests/test_eda_relationships_outputs.py`.
- [ ] T053 [P] [US3] Add provisional label assignment, visible provisional metadata, and no-ground-truth tests in `tests/test_eda_relationships_outputs.py`.
- [ ] T054 [P] [US3] Add provisional rule priority-order tests for overlapping rules in `tests/test_eda_relationships_outputs.py`.
- [ ] T055 [P] [US3] Add optional alert burden computed-from-alerts and alerts-unavailable tests in `tests/test_eda_relationships_outputs.py`.
- [ ] T056 [P] [US3] Add segment summary tests for N, adherence, missingness, event prevalence, AC access, and PIH severity in `tests/test_eda_relationships_outputs.py`.

### Implementation for User Story 3

- [ ] T057 [US3] Define canonical archetype labels, known aliases, and provisional priority order in `src/visualization/eda_archetypes.py`.
- [ ] T058 [US3] Implement participant-level adherence, missingness, late missingness, vital severity, high-heat day, event, AC, and PIH metric preparation in `src/visualization/eda_archetypes.py`.
- [ ] T059 [US3] Implement explicit archetype label detection from participants first and daily vitals second in `src/visualization/eda_archetypes.py`.
- [ ] T060 [US3] Implement known-alias normalization and unknown explicit label preservation in `src/visualization/eda_archetypes.py`.
- [ ] T061 [US3] Implement provisional descriptive rule assignment with deterministic priority order in `src/visualization/eda_archetypes.py`.
- [ ] T062 [US3] Implement optional alert burden calculation from `alerts` rows and unavailable behavior when alerts are absent in `src/visualization/eda_archetypes.py`.
- [ ] T063 [US3] Implement segment summary aggregation for N, adherence, missingness, alert burden, event prevalence, AC access, and PIH severity in `src/visualization/eda_archetypes.py`.
- [ ] T064 [US3] Implement Panel 12 summary table, count chart, adherence/missingness chart, alert/event chart, and rule annotation panel in `src/visualization/eda_archetypes.py`.
- [ ] T065 [US3] Implement `render_archetype_explorer()` artifact save path for `outputs/figures/eda/12_archetype_explorer.png` in `src/visualization/eda_archetypes.py`.
- [ ] T066 [US3] Add Panel 12 label source, provisional flag, rule summary, unknown label, alert source, and segment metadata to the SPEC-010 manifest entry in `src/visualization/eda_archetypes.py`.

**Checkpoint**: User Story 3 is independently functional and Panel 12 distinguishes explicit labels from provisional review aids.

---

## Phase 6: User Story 4 - Review Recruitment and Enrollment Timeline (Priority: P2)

**Goal**: Generate Panel 13 with calendar-aware recruitment/enrollment dates, observation windows, delivery markers, heat overlay, cumulative enrollment, observation density, and unavailable behavior when dates are absent.

**Independent Test**: Generate Panel 13 with recruitment dates, without recruitment dates, with environment heat overlay, and with all date sources missing; assert source metadata, calendar awareness, and unavailable-panel behavior.

### Tests for User Story 4

- [ ] T067 [P] [US4] Add Panel 13 artifact existence, 1600 x 900 dimension, and manifest metadata tests in `tests/test_eda_relationships_outputs.py`.
- [ ] T068 [P] [US4] Add recruitment-table date precedence tests in `tests/test_eda_relationships_outputs.py`.
- [ ] T069 [P] [US4] Add participant enrollment, observation, and daily-vitals date fallback tests in `tests/test_eda_relationships_outputs.py`.
- [ ] T070 [P] [US4] Add no-parseable-date unavailable panel and manifest warning tests in `tests/test_eda_relationships_outputs.py`.
- [ ] T071 [P] [US4] Add environment heat overlay and high-heat shading tests for Panel 13 in `tests/test_eda_relationships_outputs.py`.
- [ ] T072 [P] [US4] Add participant display downsampling with full-cohort metadata tests in `tests/test_eda_relationships_outputs.py`.

### Implementation for User Story 4

- [ ] T073 [US4] Implement recruitment date extraction with enrolled-state handling in `src/visualization/eda_archetypes.py`.
- [ ] T074 [US4] Implement participant enrollment, delivery, observation, and daily-vitals date fallback preparation in `src/visualization/eda_archetypes.py`.
- [ ] T075 [US4] Implement no-parseable-date detection and unavailable panel metadata in `src/visualization/eda_archetypes.py`.
- [ ] T076 [US4] Implement environment high-heat overlay preparation for timeline panels in `src/visualization/eda_archetypes.py`.
- [ ] T077 [US4] Implement participant observation-window panel with deterministic display downsampling in `src/visualization/eda_archetypes.py`.
- [ ] T078 [US4] Implement cumulative enrollment count panel in `src/visualization/eda_archetypes.py`.
- [ ] T079 [US4] Implement cohort observation density from daily-vitals dates or participant observation windows in `src/visualization/eda_archetypes.py`.
- [ ] T080 [US4] Implement timeline source/warning annotation panel in `src/visualization/eda_archetypes.py`.
- [ ] T081 [US4] Implement `render_recruitment_timeline()` artifact save path for `outputs/figures/eda/13_recruitment_timeline.png` in `src/visualization/eda_archetypes.py`.
- [ ] T082 [US4] Add Panel 13 recruitment source, calendar awareness, display downsampling, date-missing, and observation-density metadata to the SPEC-010 manifest entry in `src/visualization/eda_archetypes.py`.

**Checkpoint**: User Story 4 is independently functional and Panel 13 is calendar-aware where dates exist.

---

## Phase 7: Polish and Acceptance Evidence

**Purpose**: Verify the full SPEC-010 implementation and refresh tracked acceptance artifacts.

- [ ] T083 Regenerate all default SPEC-010 EDA artifacts under `outputs/figures/eda/` with `.venv/bin/python -m src.visualization.generate_eda --data-dir data/raw --out-dir outputs/figures/eda --panels relationships`.
- [ ] T084 Verify all SPEC-010 manifest entries, repo-relative paths, warnings, metadata, and required roles in `outputs/figures/manifest.json`.
- [ ] T085 Run synthetic SPEC-010 generation with `.venv/bin/python -m src.visualization.generate_eda --data-dir data/synthetic/longitudinal --out-dir outputs/figures/eda_synthetic --panels relationships`.
- [ ] T086 Run the all-panels smoke command with `.venv/bin/python -m src.visualization.generate_eda --data-dir data/synthetic/longitudinal --out-dir outputs/figures/eda_all_smoke --panels all --participant-id P0001 --overlay-environment true`.
- [ ] T087 Run focused acceptance tests with `.venv/bin/pytest tests/test_eda_relationships_outputs.py`.
- [ ] T088 Run existing EDA regression tests with `.venv/bin/pytest tests/test_eda_core_outputs.py tests/test_eda_longitudinal_outputs.py`.
- [ ] T089 Audit descriptive-only behavior for prediction, model scoring, imputation, and causal wording in `src/visualization/eda_relationships.py`, `src/visualization/eda_environment.py`, and `src/visualization/eda_archetypes.py`.
- [ ] T090 Update implementation evidence and any changed command notes in `specs/010-relationships-heat-archetypes-recruitment-dashboards/quickstart.md`.
- [ ] T091 Add the SPEC-010 implementation entry in `CHANGELOG.md` after acceptance evidence is clean.

---

## Dependencies and Execution Order

### Phase Dependencies

- **Phase 1 Setup**: No dependencies.
- **Phase 2 Foundational SPEC-010 Loading, CLI, and Manifest Behavior**: Depends on Phase 1 and blocks all user stories.
- **Phase 3 US1 Relationships**: Depends on Phase 2 and is the MVP slice.
- **Phase 4 US2 Heat Environment**: Depends on Phase 2 and can run in parallel with US1 after shared loading is complete.
- **Phase 5 US3 Archetype Explorer**: Depends on Phase 2 and can run after or alongside P1 stories if shared participant metrics are stable.
- **Phase 6 US4 Recruitment Timeline**: Depends on Phase 2 and can run after or alongside US3 because it shares `eda_archetypes.py`.
- **Phase 7 Polish**: Depends on all selected user stories.

### User Story Dependencies

- **US1 Review Descriptive Relationships (P1)**: Starts after Phase 2; no dependency on other stories.
- **US2 Audit Heat Exposure and Environmental Context (P1)**: Starts after Phase 2; no dependency on other stories.
- **US3 Explore Participant Archetype Segments (P2)**: Starts after Phase 2; no dependency on US1 or US2, but can reuse shared heat helpers.
- **US4 Review Recruitment and Enrollment Timeline (P2)**: Starts after Phase 2; can reuse high-heat overlay helpers from US2.

### Within Each User Story

- Write story tests first and confirm they fail for the missing behavior.
- Implement data preparation helpers before panel layout.
- Save the story artifact and validate its manifest entry after the panel renders.
- A story is complete only when its independent tests pass from the repository root.

## Parallel Opportunities

- T001-T004 can run in parallel during setup because they touch different files.
- T007-T011 can run in parallel before implementation because they add independent tests.
- US1 test tasks T020-T025 can run in parallel.
- US2 test tasks T036-T040 can run in parallel.
- US3 test tasks T050-T056 can run in parallel.
- US4 test tasks T067-T072 can run in parallel.
- US1 and US2 can be implemented in parallel after Phase 2 because they use different modules.
- US3 and US4 share `src/visualization/eda_archetypes.py`, so coordinate edits or sequence implementation tasks within that file.

## Parallel Example: User Story 1

```bash
Task: "T020 [P] [US1] Add Panel 10 artifact existence, 1600 x 900 dimension, and manifest metadata tests in tests/test_eda_relationships_outputs.py"
Task: "T021 [P] [US1] Add observed-pair policy and pairwise N regression tests for the correlation heatmap in tests/test_eda_relationships_outputs.py"
Task: "T022 [P] [US1] Add body-water direction versus BP, HR, and skin-temperature coverage tests in tests/test_eda_relationships_outputs.py"
```

## Parallel Example: User Story 2

```bash
Task: "T041 [US2] Implement prepare_environment_frame() with date or study-day axis support in src/visualization/eda_environment.py"
Task: "T043 [US2] Implement missing environment row, missing field, and date-gap summaries in src/visualization/eda_environment.py"
```

## Parallel Example: User Story 3

```bash
Task: "T051 [P] [US3] Add explicit archetype label source and known-alias normalization tests in tests/test_eda_relationships_outputs.py"
Task: "T052 [P] [US3] Add unknown explicit label preservation tests in tests/test_eda_relationships_outputs.py"
Task: "T055 [P] [US3] Add optional alert burden computed-from-alerts and alerts-unavailable tests in tests/test_eda_relationships_outputs.py"
```

## Parallel Example: User Story 4

```bash
Task: "T068 [P] [US4] Add recruitment-table date precedence tests in tests/test_eda_relationships_outputs.py"
Task: "T069 [P] [US4] Add participant enrollment, observation, and daily-vitals date fallback tests in tests/test_eda_relationships_outputs.py"
Task: "T070 [P] [US4] Add no-parseable-date unavailable panel and manifest warning tests in tests/test_eda_relationships_outputs.py"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational loading, CLI, and manifest behavior.
3. Complete Phase 3: User Story 1 relationships dashboard.
4. Stop and validate Panel 10 independently with `pytest tests/test_eda_relationships_outputs.py -k relationships`.
5. Generate `outputs/figures/eda/10_relationships.png` and inspect its manifest entry.

### Incremental Delivery

1. Complete Setup plus Foundational behavior.
2. Add US1 Panel 10, test independently, and generate artifact.
3. Add US2 Panel 11, test with environment present and absent, and generate artifact.
4. Add US3 Panel 12, test explicit and provisional archetypes, and generate artifact.
5. Add US4 Panel 13, test recruitment/date fallbacks, and generate artifact.
6. Run polish commands and update acceptance evidence.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup plus Foundational tasks together.
2. Developer A implements US1 in `src/visualization/eda_relationships.py`.
3. Developer B implements US2 in `src/visualization/eda_environment.py`.
4. Developer C implements US3 and US4 sequentially in `src/visualization/eda_archetypes.py`.
5. Team reconvenes for Phase 7 manifest, artifact, and regression validation.

## Notes

- [P] tasks touch different files or independent tests and can run in parallel.
- [US1]-[US4] labels map to SPEC-010 user stories.
- Tests are listed before implementation tasks because SPEC-010 explicitly requires focused EDA tests.
- Required-input failures must happen before requested artifact writes or manifest registration.
- Optional context must degrade visibly with warnings rather than becoming silent defaults.
- Do not add prediction, imputation, model scoring, or causal interpretation while implementing these tasks.
