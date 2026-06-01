---
id: TASKS-007
title: Core Descriptive EDA Dashboards Tasks
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-007, PLAN-007, DATA-007, RESEARCH-007]
implements: [P3, P5, P7, P10]
supersedes: null
superseded_by: null
related: [SPEC-001, SPEC-004, SPEC-005, SPEC-006]
description: "Executable implementation task list for the core descriptive EDA dashboard PNGs, CLI, manifest registration, missingness behavior, and schema-driven capture-worthy value handling."
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Tasks: Core Descriptive EDA Dashboards

**Input**: Design documents from `specs/007-core-descriptive-eda-dashboards/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/`

**Tests**: Included because SPEC-007 requires focused EDA tests in `tests/test_eda_core_outputs.py` and `tests/test_eda_missingness_policy.py`.

**Organization**: Tasks are grouped by user story so each panel can be implemented and verified independently after the shared EDA foundation is complete.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files or independent fixtures
- **[Story]**: Maps the task to a SPEC-007 user story
- Each task names the exact source, test, artifact, or documentation path to change

## Phase 1: Setup

**Purpose**: Confirm the existing visualization foundation is ready for the core EDA panel work.

- [X] T001 Verify Python 3.11, pandas, numpy, matplotlib, PyYAML, and pytest dependencies for EDA generation in `pyproject.toml`.
- [X] T002 Export the public core EDA generation API from `src/visualization/__init__.py`.
- [X] T003 [P] Add reusable core EDA table fixture helpers in `tests/test_eda_core_outputs.py`.
- [X] T004 [P] Add reusable missingness and optional-role fixture helpers in `tests/test_eda_missingness_policy.py`.

---

## Phase 2: Foundational EDA Loading, CLI, and Manifest Behavior

**Purpose**: Implement shared behavior that blocks every dashboard panel.

**Blocking rule**: No user story implementation should start until T005-T013 are complete.

### Tests for Foundational Behavior

- [X] T005 [P] Add CLI success, synthetic run, and required-failure contract tests in `tests/test_eda_core_outputs.py`.
- [X] T006 [P] Add manifest registration assertions for SPEC-007 artifact entries in `tests/test_eda_core_outputs.py`.
- [X] T007 [P] Add required table and required semantic role preflight failure tests in `tests/test_eda_core_outputs.py`.
- [X] T008 [P] Add optional-role warning and unavailable-section regression tests in `tests/test_eda_missingness_policy.py`.

### Implementation for Foundational Behavior

- [X] T009 Define `SPEC_ID = "SPEC-007"`, `PANEL_FILENAMES`, `EDATables`, `PanelResult`, and `EDAInputError` in `src/visualization/eda_core.py`.
- [X] T010 Implement canonical table loading and `data/raw` to `data/` fallback resolution in `src/visualization/eda_core.py`.
- [X] T011 Implement required entity and semantic-role preflight validation before output directory creation in `src/visualization/eda_core.py`.
- [X] T012 Implement repo-relative `FigureArtifact` upsert registration with SPEC-007 metadata in `src/visualization/eda_core.py`.
- [X] T013 Implement `--data-dir`, `--out-dir`, `--panels core`, `--manifest`, stdout success output, and stderr failure output in `src/visualization/generate_eda.py`.

**Checkpoint**: Core EDA runs can load canonical inputs, fail before writes on required problems, and register generated repo-relative artifacts.

---

## Phase 3: User Story 1 - Review Cohort Composition (Priority: P1) MVP

**Goal**: Generate a Table 1-style cohort overview with participant count, demographics, equity context, baseline risk indicators, psychosocial measures, and optional clinical outcome context.

**Independent Test**: Generate the cohort overview panel from canonical `participants` data with optional `clinical_outcomes`, including fixtures where optional roles are missing.

### Tests for User Story 1

- [X] T014 [P] [US1] Add cohort overview artifact existence and 1600 x 900 dimension tests in `tests/test_eda_core_outputs.py`.
- [X] T015 [P] [US1] Add participant N, age median/range, and available Table 1 field assertion tests in `tests/test_eda_core_outputs.py`.
- [X] T016 [P] [US1] Add optional cohort field unavailable-card warning tests in `tests/test_eda_missingness_policy.py`.
- [X] T017 [P] [US1] Add low-count race/ethnicity and insurance category preservation tests in `tests/test_eda_core_outputs.py`.

### Implementation for User Story 1

- [X] T018 [US1] Implement `render_cohort_overview()` layout and artifact save path in `src/visualization/eda_core.py`.
- [X] T019 [US1] Implement participant count, age distribution, PIH severity, insurance, race/ethnicity, AC availability, household size, and parity panels in `src/visualization/eda_core.py`.
- [X] T020 [US1] Implement equity-context grouping, risk indicator counts, and low-count category preservation in `src/visualization/eda_core.py`.
- [X] T021 [US1] Implement BHLS, MSPSS, EPDS, PASS, and optional clinical outcome context sections in `src/visualization/eda_core.py`.
- [X] T022 [US1] Propagate optional cohort unavailable-card warnings into `PanelResult.warnings` and manifest metadata in `src/visualization/eda_core.py`.
- [X] T023 [US1] Generate `outputs/figures/eda/01_cohort_overview.png` through `src/visualization/generate_eda.py`.

**Checkpoint**: User Story 1 is independently functional and the cohort overview panel can be reviewed without the other panels.

---

## Phase 4: User Story 2 - Inspect Outcome Prevalence and Class Imbalance (Priority: P1)

**Goal**: Generate an outcome prevalence panel with CV event, ED visit, hospitalization, heat illness counts, rare-outcome warning text, and explicit positive/negative CV class imbalance.

**Independent Test**: Generate the outcome prevalence panel from canonical `clinical_outcomes` data and assert count/percent labels, rare-outcome warning text, and class imbalance display are present.

### Tests for User Story 2

- [X] T024 [P] [US2] Add outcome artifact existence, 1600 x 900 dimension, CV event, ED visit, hospitalization, and heat illness count/percent tests in `tests/test_eda_core_outputs.py`.
- [X] T025 [P] [US2] Add positive, negative, and missing/unknown CV event class count tests in `tests/test_eda_missingness_policy.py`.
- [X] T026 [P] [US2] Add 6.5% to 8.5% target-rate annotation fixture tests in `tests/test_eda_core_outputs.py`.
- [X] T027 [P] [US2] Add rare-outcome warning text assertion tests in `tests/test_eda_core_outputs.py`.

### Implementation for User Story 2

- [X] T028 [US2] Implement parser-backed `_outcome_series()` and `_heat_illness_series()` helpers in `src/visualization/eda_core.py`.
- [X] T029 [US2] Implement `render_outcome_prevalence()` metric cards and prevalence chart in `src/visualization/eda_core.py`.
- [X] T030 [US2] Implement CV class imbalance positive, negative, missing/unknown, and target-rate annotation behavior in `src/visualization/eda_core.py`.
- [X] T031 [US2] Implement the exact rare-outcome warning text and no-prediction/no-model-label guardrails in `src/visualization/eda_core.py`.
- [X] T032 [US2] Propagate outcome parsing warnings into `PanelResult.warnings` and manifest metadata in `src/visualization/eda_core.py`.
- [X] T033 [US2] Generate `outputs/figures/eda/02_outcome_prevalence.png` through `src/visualization/generate_eda.py`.

**Checkpoint**: User Story 2 is independently functional and rare-event imbalance is visible before modeling work.

---

## Phase 5: User Story 3 - Examine Distributions and Capture-Worthy Extremes (Priority: P1)

**Goal**: Generate daily vital distribution cards with observed/missing denominators, schema units, and schema-driven capture-worthy or impossible value labels.

**Independent Test**: Generate the distribution panel from canonical `daily_vitals` and assert vital distributions, observed/missing denominators, schema units, and capture-worthy outlier labeling.

### Tests for User Story 3

- [X] T034 [P] [US3] Add distribution artifact existence, dimension, and required vital card tests in `tests/test_eda_core_outputs.py`.
- [X] T035 [P] [US3] Add schema unit and observed/missing denominator tests in `tests/test_eda_missingness_policy.py`.
- [X] T036 [P] [US3] Add capture-worthy and impossible-by-schema fixture tests in `tests/test_eda_core_outputs.py`.
- [X] T037 [P] [US3] Add no dashboard-local IQR, percentile, min/max-only, or unregistered-threshold flagging tests in `tests/test_eda_missingness_policy.py`.

### Implementation for User Story 3

- [X] T038 [US3] Implement the SBP, DBP, HR, RR, skin temperature, weight, body water, sleep, and steps vital spec list in `src/visualization/eda_core.py`.
- [X] T039 [US3] Implement schema-role column resolution and distribution card rendering with schema units in `src/visualization/eda_core.py`.
- [X] T040 [US3] Implement observed and missing denominator annotations without imputation in `src/visualization/eda_core.py`.
- [X] T041 [US3] Implement capture-worthy and impossible value row extraction using only `capture_worthy_range` and `hard_range` from `src/visualization/schema_registry.py`.
- [X] T042 [US3] Implement the top capture-worthy values table with participant id, study day, value, unit, and context link label in `src/visualization/eda_core.py`.
- [X] T043 [US3] Ensure hard-range daily vital values render as `impossible by schema` instead of blocking the CLI in `src/visualization/eda_core.py`.
- [X] T044 [US3] Generate `outputs/figures/eda/03_distribution_outliers.png` through `src/visualization/generate_eda.py`.

**Checkpoint**: User Story 3 is independently functional and physiologic extremes are preserved rather than discarded or statistically over-labeled.

---

## Phase 6: User Story 4 - Understand Alerts and Engagement Funnel (Priority: P2)

**Goal**: Generate alert volume, trigger reason, survey state, staff contact state, and engagement funnel views with prior-stage conversion percentages.

**Independent Test**: Generate the alert engagement funnel panel from canonical `alerts` and `staff_contacts`, including fixtures with missing survey/contact states.

### Tests for User Story 4

- [X] T045 [P] [US4] Add alert-funnel artifact existence, 1600 x 900 dimension, alert level, trigger reason, and summary tile tests in `tests/test_eda_core_outputs.py`.
- [X] T046 [P] [US4] Add survey completed/dismissed/abandoned/missing state tests in `tests/test_eda_missingness_policy.py`.
- [X] T047 [P] [US4] Add staff contact missing-state and explicit-completion tests in `tests/test_eda_missingness_policy.py`.
- [X] T048 [P] [US4] Add prior-stage funnel conversion percentage tests in `tests/test_eda_missingness_policy.py`.
- [X] T049 [P] [US4] Add trigger reason overflow category completeness tests in `tests/test_eda_core_outputs.py`.

### Implementation for User Story 4

- [X] T050 [US4] Implement `render_alert_engagement_funnel()` summary tiles and artifact save path in `src/visualization/eda_core.py`.
- [X] T051 [US4] Implement alert level and trigger reason panels with complete category preservation in `src/visualization/eda_core.py`.
- [X] T052 [US4] Implement survey state normalization for completed, dismissed, abandoned, and missing/unknown values in `src/visualization/eda_core.py`.
- [X] T053 [US4] Implement staff contact completion parsing using explicit completed states only in `src/visualization/eda_core.py`.
- [X] T054 [US4] Implement engagement funnel counts and immediately-prior-stage conversion percentages in `src/visualization/eda_core.py`.
- [X] T055 [US4] Propagate trigger reason overflow and missing contact/survey warnings into `PanelResult.metadata` and manifest entries in `src/visualization/eda_core.py`.
- [X] T056 [US4] Generate `outputs/figures/eda/04_alert_engagement_funnel.png` through `src/visualization/generate_eda.py`.

**Checkpoint**: User Story 4 is independently functional and missing engagement states are not inferred as completed or attempted.

---

## Phase 7: Polish and Acceptance Evidence

**Purpose**: Verify the full SPEC-007 implementation and refresh tracked acceptance artifacts.

- [X] T057 Regenerate all default core EDA artifacts under `outputs/figures/eda/` with `.venv/bin/python -m src.visualization.generate_eda --data-dir data/raw --out-dir outputs/figures/eda --panels core` and record whether generation meets the under-2-minute target.
- [X] T058 Verify all SPEC-007 entries, repo-relative paths, warnings, and required roles in `outputs/figures/manifest.json`.
- [X] T059 Run optional synthetic EDA generation under `outputs/figures/eda_synthetic/` with `.venv/bin/python -m src.visualization.generate_eda --data-dir data/synthetic/longitudinal --out-dir outputs/figures/eda_synthetic --panels core`.
- [X] T060 Run focused acceptance tests with `.venv/bin/pytest tests/test_eda_core_outputs.py tests/test_eda_missingness_policy.py` and record whether the focused run meets the under-2-minute target.
- [X] T061 Run full local validation for `tests/` with `.venv/bin/pytest`.
- [X] T062 Audit descriptive-only behavior for prediction, model scoring, and imputation language in `src/visualization/eda_core.py`.
- [X] T063 Update completion evidence and any changed command notes in `specs/007-core-descriptive-eda-dashboards/quickstart.md`.
- [X] T064 Update the SPEC-007 implementation entry in `CHANGELOG.md`, including the pinned `007` feature directory and current branch naming note if the branch remains `006-core-descriptive-eda-dashboards`.

---

## Dependencies and Execution Order

### Phase Dependencies

- **Phase 1 Setup**: No dependencies.
- **Phase 2 Foundational EDA Loading, CLI, and Manifest Behavior**: Depends on Phase 1 and blocks all user stories.
- **Phase 3 US1 Cohort Overview**: Depends on Phase 2 and is the MVP slice.
- **Phase 4 US2 Outcome Prevalence**: Depends on Phase 2 and can run in parallel with US1 after shared loading is complete.
- **Phase 5 US3 Distributions and Capture-Worthy Extremes**: Depends on Phase 2 and can run in parallel with US1/US2 after shared loading is complete.
- **Phase 6 US4 Alert Engagement Funnel**: Depends on Phase 2 and can run after or alongside the P1 stories if shared helpers are stable.
- **Phase 7 Polish**: Depends on all selected user stories.

### User Story Dependencies

- **US1 Review Cohort Composition (P1)**: Starts after Phase 2; no dependency on other stories.
- **US2 Inspect Outcome Prevalence and Class Imbalance (P1)**: Starts after Phase 2; no dependency on other stories.
- **US3 Examine Distributions and Capture-Worthy Extremes (P1)**: Starts after Phase 2; no dependency on other stories.
- **US4 Understand Alerts and Engagement Funnel (P2)**: Starts after Phase 2; no dependency on other stories, but benefits from shared missingness helpers.

### Within Each User Story

- Write story tests first and confirm they fail for the missing behavior.
- Implement `src/visualization/eda_core.py` helpers before panel orchestration.
- Save the story artifact and validate its manifest entry after the panel renders.
- A story is complete only when its independent tests pass from the repository root.

## Parallel Opportunities

- T003 and T004 can run in parallel after setup context is understood.
- T005-T008 can run in parallel because they add independent foundational test coverage.
- T014-T017 can run in parallel because they target separate cohort behaviors.
- T024-T027 can run in parallel because they target separate outcome prevalence behaviors.
- T034-T037 can run in parallel because they target distribution, missingness, and threshold fixtures separately.
- T045-T049 can run in parallel because they target independent alert/funnel fixtures.
- US1, US2, and US3 can run in parallel after Phase 2 if separate contributors coordinate changes to `src/visualization/eda_core.py`.

## Parallel Example: User Story 3

```text
Task: "T034 [US3] Add distribution artifact existence, dimension, and required vital card tests in tests/test_eda_core_outputs.py"
Task: "T035 [US3] Add schema unit and observed/missing denominator tests in tests/test_eda_missingness_policy.py"
Task: "T036 [US3] Add capture-worthy and impossible-by-schema fixture tests in tests/test_eda_core_outputs.py"
Task: "T037 [US3] Add no dashboard-local IQR, percentile, min/max-only, or unregistered-threshold flagging tests in tests/test_eda_missingness_policy.py"
```

## Parallel Example: User Story 4

```text
Task: "T045 [US4] Add alert level, trigger reason, and summary tile tests in tests/test_eda_core_outputs.py"
Task: "T046 [US4] Add survey completed/dismissed/abandoned/missing state tests in tests/test_eda_missingness_policy.py"
Task: "T047 [US4] Add staff contact missing-state and explicit-completion tests in tests/test_eda_missingness_policy.py"
Task: "T048 [US4] Add prior-stage funnel conversion percentage tests in tests/test_eda_missingness_policy.py"
Task: "T049 [US4] Add trigger reason overflow category completeness tests in tests/test_eda_core_outputs.py"
```

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete US1 to deliver the cohort overview MVP.
3. Run the US1-focused tests and inspect `outputs/figures/eda/01_cohort_overview.png`.
4. Continue with US2 and US3, the remaining P1 descriptive evidence panels.

### Incremental Delivery

1. Add US1 -> test independently -> review cohort composition artifact.
2. Add US2 -> test independently -> review outcome prevalence and imbalance artifact.
3. Add US3 -> test independently -> review distributions and capture-worthy values artifact.
4. Add US4 -> test independently -> review alert engagement funnel artifact.
5. Run Phase 7 acceptance evidence after the selected stories are complete.

### Acceptance Finish

1. Regenerate tracked dashboard artifacts in `outputs/figures/eda/`.
2. Verify `outputs/figures/manifest.json` contains SPEC-007 entries.
3. Run focused tests, then the full local test suite.
4. Update `CHANGELOG.md` after acceptance evidence is clean.
