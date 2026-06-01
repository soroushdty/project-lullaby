---
id: TASKS-009
title: Longitudinal Vitals, Missingness, Signal Quality, and Patient Timeline Tasks
status: complete
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-009, PLAN-009, DATA-009, RESEARCH-009]
implements: [P3, P5, P7, P10]
supersedes: null
superseded_by: null
related: [SPEC-001, SPEC-004, SPEC-006, SPEC-007]
description: "Executable implementation task list for longitudinal EDA dashboard PNGs, CLI flags, manifest registration, patient timeline, quality scoring, and missingness-mechanism diagnostics."
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Tasks: Longitudinal Vitals, Missingness, Signal Quality, and Patient Timeline

**Input**: Design documents from `specs/009-longitudinal-vitals-missingness-timeline/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/`

**Tests**: Included because SPEC-009 requires focused tests in `tests/test_eda_longitudinal_outputs.py` and `tests/test_patient_timeline.py`.

**Organization**: Tasks are grouped by user story so each longitudinal panel can be implemented and verified independently after the shared EDA foundation is complete.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files or independent fixtures
- **[Story]**: Maps the task to a SPEC-009 user story
- Each task names the exact source, test, artifact, or documentation path to change

## Phase 1: Setup

**Purpose**: Prepare the longitudinal EDA file structure and focused test fixtures.

- [X] T001 [P] Create reusable longitudinal canonical table fixture builders in `tests/test_eda_longitudinal_outputs.py`.
- [X] T002 [P] Create reusable patient timeline fixture builders in `tests/test_patient_timeline.py`.
- [X] T003 [P] Add module skeleton and public imports for longitudinal EDA generation in `src/visualization/eda_longitudinal.py` and `src/visualization/__init__.py`.
- [X] T004 [P] Add module skeleton and public imports for patient timeline rendering in `src/visualization/patient_view.py` and `src/visualization/__init__.py`.

---

## Phase 2: Foundational Longitudinal Loading, CLI, and Manifest Behavior

**Purpose**: Implement shared behavior that blocks every SPEC-009 dashboard panel.

**Blocking rule**: No user story implementation should start until T005-T017 are complete.

### Tests for Foundational Behavior

- [X] T005 Add CLI contract tests for `--panels longitudinal`, `--participant-id`, `--week-start`, `--week-end`, and `--overlay-environment` in `tests/test_eda_longitudinal_outputs.py`.
- [X] T006 Add five-artifact manifest registration assertions for SPEC-009 artifact ids in `tests/test_eda_longitudinal_outputs.py`.
- [X] T007 Add required table and required semantic role preflight failure tests, including Panel 7 event-marker date roles, in `tests/test_eda_longitudinal_outputs.py`.
- [X] T008 Add invalid week range, invalid participant id, and invalid overlay argument tests in `tests/test_eda_longitudinal_outputs.py`.
- [X] T009 Add optional environment, optional participant context, and optional diagnostic stratifier warning tests in `tests/test_eda_longitudinal_outputs.py`.

### Implementation for Foundational Behavior

- [X] T010 Extend `src/visualization/schema_registry.py` with optional longitudinal participant context roles where needed, including insurance, parity, and archetype aliases.
- [X] T011 Define `SPEC_ID = "SPEC-009"`, panel filenames, artifact ids, `LongitudinalRunConfig`, `LongitudinalEDATables`, `LongitudinalPanelResult`, and `LongitudinalInputError` in `src/visualization/eda_longitudinal.py`.
- [X] T012 Implement canonical table loading, optional environment loading, and `data/raw` to `data/` fallback resolution in `src/visualization/eda_longitudinal.py`.
- [X] T013 Implement required entity and semantic-role preflight validation before output directory creation in `src/visualization/eda_longitudinal.py`.
- [X] T014 Implement study-day derivation, inclusive 1-based week filtering, and week-range validation in `src/visualization/eda_longitudinal.py`.
- [X] T015 Implement deterministic selected-participant resolution with manifest-ready score components in `src/visualization/eda_longitudinal.py`.
- [X] T016 Implement repo-relative `FigureArtifact` registration for the five SPEC-009 panels in `src/visualization/eda_longitudinal.py`.
- [X] T017 Extend `src/visualization/generate_eda.py` to accept `--panels longitudinal`, participant/week/environment flags, success stdout, and failure stderr behavior.

**Checkpoint**: Longitudinal EDA runs can load canonical inputs, fail before writes on required problems, parse static-render flags, select a participant deterministically, and register generated repo-relative artifacts.

---

## Phase 3: User Story 1 - Review Longitudinal Vital Trajectories (Priority: P1) MVP

**Goal**: Generate Panel 5 with cohort aggregate trajectories, selected-participant trajectories, observed-day denominators, visible missing-day gaps, week filters, and optional environment overlay.

**Independent Test**: Generate Panel 5 from canonical `daily_vitals` with optional `environment`, optional `participants`, and CLI filters; assert vital tracks, gaps, denominators, participant metadata, and manifest registration.

### Tests for User Story 1

- [X] T018 [US1] Add Panel 5 artifact existence and 1600 x 900 dimension tests in `tests/test_eda_longitudinal_outputs.py`.
- [X] T019 [US1] Add SBP, DBP, HR, RR, skin temperature, weight, body water, sleep, and steps trajectory coverage tests in `tests/test_eda_longitudinal_outputs.py`.
- [X] T020 [US1] Add visible missing-day gap and no-interpolation regression tests in `tests/test_eda_longitudinal_outputs.py`.
- [X] T021 [US1] Add observed-day denominator and inclusive week filter tests in `tests/test_eda_longitudinal_outputs.py`.
- [X] T022 [US1] Add participant-id selection, automatic selection, and manifest score-component tests in `tests/test_eda_longitudinal_outputs.py`.
- [X] T023 [US1] Add environment overlay default-false, enabled-overlay, and unavailable-warning tests in `tests/test_eda_longitudinal_outputs.py`.

### Implementation for User Story 1

- [X] T024 [US1] Implement the Panel 5 vital role list and schema unit lookup in `src/visualization/eda_longitudinal.py`.
- [X] T025 [US1] Implement cohort aggregate and selected-participant trajectory data preparation with missing-day gaps in `src/visualization/eda_longitudinal.py`.
- [X] T026 [US1] Implement observed-day denominator calculations and direct annotations in `src/visualization/eda_longitudinal.py`.
- [X] T027 [US1] Implement ambient temperature and heat index overlay preparation in `src/visualization/eda_longitudinal.py`.
- [X] T028 [US1] Implement `render_vital_trajectories()` layout and artifact save path for `outputs/figures/eda/05_vital_trajectories.png` in `src/visualization/eda_longitudinal.py`.
- [X] T029 [US1] Add Panel 5 warnings and metadata to the SPEC-009 manifest entry in `src/visualization/eda_longitudinal.py`.

**Checkpoint**: User Story 1 is independently functional and Panel 5 can be generated and reviewed without the other longitudinal panels.

---

## Phase 4: User Story 2 - Audit Missingness and Adherence (Priority: P1)

**Goal**: Generate Panel 6 with participant-day missingness matrix, wear-hours and scale-adherence trends, adherence decline summary, missingness by variable, and supported gap clustering.

**Independent Test**: Generate Panel 6 from `daily_vitals`, `staff_contacts`, and optional `alerts`; assert matrix rendering, adherence summaries, deterministic downsampling, non-color-only state encoding, and gap clustering behavior.

### Tests for User Story 2

- [X] T030 [US2] Add Panel 6 artifact existence, 1600 x 900 dimension, and participant x study day matrix tests in `tests/test_eda_longitudinal_outputs.py`.
- [X] T031 [US2] Add wear-hours trend, scale-adherence trend, adherence decline summary, and missingness-by-variable tests in `tests/test_eda_longitudinal_outputs.py`.
- [X] T032 [US2] Add explicit missing/present legend, label, symbol, or pattern tests so state is not color-only in `tests/test_eda_longitudinal_outputs.py`.
- [X] T033 [US2] Add deterministic display-row downsampling tests for more than 250 participants while metrics use all participants in `tests/test_eda_longitudinal_outputs.py`.
- [X] T034 [US2] Add gap clustering supported and unavailable-warning tests for overnight, feeding/morning, hot afternoon, and late-study decline patterns in `tests/test_eda_longitudinal_outputs.py`.

### Implementation for User Story 2

- [X] T035 [US2] Implement participant-day missingness matrix preparation in `src/visualization/eda_longitudinal.py`.
- [X] T036 [US2] Implement wear-hours, scale-adherence, adherence decline, and missingness-by-variable summaries in `src/visualization/eda_longitudinal.py`.
- [X] T037 [US2] Implement supported gap clustering summaries and unavailable-warning behavior in `src/visualization/eda_longitudinal.py`.
- [X] T038 [US2] Implement deterministic matrix row downsampling with full-cohort metric preservation in `src/visualization/eda_longitudinal.py`.
- [X] T039 [US2] Implement `render_missingness_adherence()` layout and artifact save path for `outputs/figures/eda/06_missingness_adherence.png` in `src/visualization/eda_longitudinal.py`.
- [X] T040 [US2] Add Panel 6 downsampling, gap-clustering, and missing-state metadata to the SPEC-009 manifest entry in `src/visualization/eda_longitudinal.py`.

**Checkpoint**: User Story 2 is independently functional and Panel 6 makes adherence and missingness interpretable before any patient timeline review.

---

## Phase 5: User Story 3 - Review A Single-Participant Clinical Timeline (Priority: P1)

**Goal**: Generate Panel 7 with one participant's aligned vital trajectories, alerts, staff contacts, outcomes, missingness/wear track, optional environment overlay, summary card, and capture-worthy labels.

**Independent Test**: Generate the patient timeline with canonical participant, vital, alert, contact, outcome, and optional environment fixtures; assert aligned tracks, summary card fields, event markers, missingness/wear track, visible vital gaps, and one-page layout.

### Tests for User Story 3

- [X] T041 [US3] Add Panel 7 artifact existence, 1600 x 900 dimension, one-page layout, and selected participant tests in `tests/test_patient_timeline.py`.
- [X] T042 [US3] Add aligned vital trajectory and visible gap tests in `tests/test_patient_timeline.py`.
- [X] T043 [US3] Add alert, staff contact, clinical outcome event marker, and missing marker-role failure tests in `tests/test_patient_timeline.py`.
- [X] T044 [US3] Add missingness/wear bottom track and optional environment overlay tests in `tests/test_patient_timeline.py`.
- [X] T045 [US3] Add PIH severity, AC access, insurance, parity, and baseline psychosocial summary-card tests in `tests/test_patient_timeline.py`.
- [X] T046 [US3] Add clinical reference band and capture-worthy direct-label tests where schema ranges are available in `tests/test_patient_timeline.py`.

### Implementation for User Story 3

- [X] T047 [US3] Implement selected-participant timeline input preparation in `src/visualization/patient_view.py`.
- [X] T048 [US3] Implement shared study-day axis alignment for vital, event, outcome, environment, and missingness tracks in `src/visualization/patient_view.py`.
- [X] T049 [US3] Implement alert, staff contact, and clinical outcome event marker preparation with required participant id and event-date role validation in `src/visualization/patient_view.py`.
- [X] T050 [US3] Implement participant summary card fields and unavailable optional-field warnings in `src/visualization/patient_view.py`.
- [X] T051 [US3] Implement vital tracks, clinical reference bands where available, visible gaps, and capture-worthy extreme labels in `src/visualization/patient_view.py`.
- [X] T052 [US3] Implement missingness/wear bottom track and optional environment overlay in `src/visualization/patient_view.py`.
- [X] T053 [US3] Implement `render_patient_timeline()` artifact save path for `outputs/figures/eda/07_patient_timeline.png` in `src/visualization/patient_view.py`.
- [X] T054 [US3] Wire Panel 7 rendering and manifest metadata into `generate_longitudinal_dashboards()` in `src/visualization/eda_longitudinal.py`.

**Checkpoint**: User Story 3 is independently functional and a reviewer can inspect one participant's longitudinal record on a single dashboard page.

---

## Phase 6: User Story 4 - Rank Data and Signal Quality (Priority: P2)

**Goal**: Generate Panel 8 with per-participant wear completeness, scale adherence, valid-signal hours, gap counts/durations, composite quality score, and completeness-based ranking.

**Independent Test**: Generate the data-quality scorecard from `daily_vitals` and `staff_contacts`; assert component scores, composite formula, missing-component redistribution, manifest warnings, and completeness-based ordering.

### Tests for User Story 4

- [X] T055 [US4] Add Panel 8 artifact existence and 1600 x 900 dimension tests in `tests/test_eda_longitudinal_outputs.py`.
- [X] T056 [US4] Add 0-1 component normalization and required formula tests in `tests/test_eda_longitudinal_outputs.py`.
- [X] T057 [US4] Add unavailable component weight redistribution and manifest warning tests in `tests/test_eda_longitudinal_outputs.py`.
- [X] T058 [US4] Add valid-signal hours, gap count, and gap duration tests in `tests/test_eda_longitudinal_outputs.py`.
- [X] T059 [US4] Add participant ranking tests proving ordering is by data completeness and not clinical risk in `tests/test_eda_longitudinal_outputs.py`.

### Implementation for User Story 4

- [X] T060 [US4] Implement participant expected-day denominator calculation for score components in `src/visualization/eda_longitudinal.py`.
- [X] T061 [US4] Implement wear completeness, scale adherence, vital completeness, and contact traceability component calculations in `src/visualization/eda_longitudinal.py`.
- [X] T062 [US4] Implement valid-signal hours, gap count, and gap duration calculations in `src/visualization/eda_longitudinal.py`.
- [X] T063 [US4] Implement quality-score formula, unavailable-component redistribution, and adjusted formula metadata in `src/visualization/eda_longitudinal.py`.
- [X] T064 [US4] Implement completeness-based participant ranking and `render_data_quality_scorecard()` layout for `outputs/figures/eda/08_data_quality_scorecard.png` in `src/visualization/eda_longitudinal.py`.
- [X] T065 [US4] Add Panel 8 formula, component availability, and ranking metadata to the SPEC-009 manifest entry in `src/visualization/eda_longitudinal.py`.

**Checkpoint**: User Story 4 is independently functional and data quality can be ranked without clinical-risk ordering.

---

## Phase 7: User Story 5 - Explore Missingness Mechanism Evidence (Priority: P2)

**Goal**: Generate Panel 9 with exploratory missingness diagnostics by study day, participant context, heat exposure, and recent abnormal vitals, clearly labeled as evidence patterns rather than proof.

**Independent Test**: Generate the missingness-mechanism panel from `participants`, `daily_vitals`, optional `environment`, and optional `clinical_outcomes`; assert exploratory labels, diagnostic groupings, and absence of imputation.

### Tests for User Story 5

- [X] T066 [US5] Add Panel 9 artifact existence, 1600 x 900 dimension, and missingness-by-study-day tests in `tests/test_eda_longitudinal_outputs.py`.
- [X] T067 [US5] Add archetype, AC access, insurance, PIH severity, and health literacy stratifier tests with unavailable warnings in `tests/test_eda_longitudinal_outputs.py`.
- [X] T068 [US5] Add heat exposure diagnostic tests for optional environment data in `tests/test_eda_longitudinal_outputs.py`.
- [X] T069 [US5] Add recent abnormal vital diagnostic tests using schema ranges and observed values only in `tests/test_eda_longitudinal_outputs.py`.
- [X] T070 [US5] Add exploratory "signals consistent with" label tests and no-proof/no-imputation language guards in `tests/test_eda_longitudinal_outputs.py`.

### Implementation for User Story 5

- [X] T071 [US5] Implement missingness rate by study day calculations in `src/visualization/eda_longitudinal.py`.
- [X] T072 [US5] Implement missingness by archetype, AC access, insurance, PIH severity, and health literacy where available in `src/visualization/eda_longitudinal.py`.
- [X] T073 [US5] Implement missingness versus heat exposure diagnostics for optional environment data in `src/visualization/eda_longitudinal.py`.
- [X] T074 [US5] Implement recent abnormal vital diagnostics using observed values and schema registry ranges only in `src/visualization/eda_longitudinal.py`.
- [X] T075 [US5] Implement exploratory MCAR/MAR/MNAR hypothesis labels and no-proof wording in `src/visualization/eda_longitudinal.py`.
- [X] T076 [US5] Implement `render_missingness_mechanism()` layout and artifact save path for `outputs/figures/eda/09_missingness_mechanism.png` in `src/visualization/eda_longitudinal.py`.
- [X] T077 [US5] Add Panel 9 diagnostic caveats, stratifier availability, and no-imputation metadata to the SPEC-009 manifest entry in `src/visualization/eda_longitudinal.py`.

**Checkpoint**: User Story 5 is independently functional and missingness mechanism evidence is visible without overclaiming.

---

## Phase 8: Polish and Acceptance Evidence

**Purpose**: Verify the full SPEC-009 implementation and refresh tracked acceptance artifacts.

- [X] T078 Regenerate all default longitudinal EDA artifacts under `outputs/figures/eda/` with `.venv/bin/python -m src.visualization.generate_eda --data-dir data/raw --out-dir outputs/figures/eda --panels longitudinal` and record whether generation meets the under-3-minute target.
- [X] T079 Regenerate a participant-specific overlay run with `.venv/bin/python -m src.visualization.generate_eda --data-dir data/raw --out-dir outputs/figures/eda --panels longitudinal --participant-id PARTICIPANT_ID --overlay-environment true`.
- [X] T080 Regenerate an inclusive week-filter run with `.venv/bin/python -m src.visualization.generate_eda --data-dir data/raw --out-dir outputs/figures/eda --panels longitudinal --week-start 1 --week-end 6`.
- [X] T081 Verify all SPEC-009 entries, repo-relative paths, warnings, selected participant metadata, quality-score metadata, and required roles in `outputs/figures/manifest.json`.
- [X] T082 Run focused acceptance tests with `.venv/bin/pytest tests/test_eda_longitudinal_outputs.py tests/test_patient_timeline.py` and record whether the focused run meets the under-2-minute target.
- [X] T083 Run full local validation for `tests/` with `.venv/bin/pytest`.
- [X] T084 Audit descriptive-only behavior for prediction, clinical risk ranking, and imputation language in `src/visualization/eda_longitudinal.py` and `src/visualization/patient_view.py`.
- [X] T085 Update implementation evidence and any changed command notes in `specs/009-longitudinal-vitals-missingness-timeline/quickstart.md`.
- [X] T086 Add the SPEC-009 implementation entry in `CHANGELOG.md` after acceptance evidence is clean.

---

## Dependencies and Execution Order

### Phase Dependencies

- **Phase 1 Setup**: No dependencies.
- **Phase 2 Foundational Longitudinal Loading, CLI, and Manifest Behavior**: Depends on Phase 1 and blocks all user stories.
- **Phase 3 US1 Vital Trajectories**: Depends on Phase 2 and is the MVP slice.
- **Phase 4 US2 Missingness and Adherence**: Depends on Phase 2 and can run in parallel with US1 after shared loading is complete.
- **Phase 5 US3 Patient Timeline**: Depends on Phase 2 and can run in parallel with US1 and US2 once selected-participant helpers are stable.
- **Phase 6 US4 Data-Quality Scorecard**: Depends on Phase 2 and can run after or alongside P1 stories if shared missingness helpers are stable.
- **Phase 7 US5 Missingness Mechanism**: Depends on Phase 2 and benefits from US2/US4 missingness helpers but must remain independently testable.
- **Phase 8 Polish**: Depends on all selected user stories.

### User Story Dependencies

- **US1 Review Longitudinal Vital Trajectories (P1)**: Starts after Phase 2; no dependency on other stories.
- **US2 Audit Missingness and Adherence (P1)**: Starts after Phase 2; no dependency on other stories.
- **US3 Review A Single-Participant Clinical Timeline (P1)**: Starts after Phase 2; depends only on shared selected-participant helpers.
- **US4 Rank Data and Signal Quality (P2)**: Starts after Phase 2; can reuse missingness helpers but must be verifiable alone.
- **US5 Explore Missingness Mechanism Evidence (P2)**: Starts after Phase 2; can reuse missingness and schema-range helpers but must be verifiable alone.

### Within Each User Story

- Write story tests first and confirm they fail for the missing behavior.
- Implement data preparation helpers before panel layout.
- Save the story artifact and validate its manifest entry after the panel renders.
- A story is complete only when its independent tests pass from the repository root.

## Parallel Opportunities

- T001-T004 can run in parallel after setup context is understood.
- T005-T009 should be coordinated because they share `tests/test_eda_longitudinal_outputs.py`.
- T010 can run in parallel with T011-T012 if registry role names are agreed first.
- US1, US2, and US3 can run in parallel after Phase 2 if contributors coordinate changes to `src/visualization/eda_longitudinal.py`.
- T041-T046 can run in parallel with US1/US2 tests because they are isolated in `tests/test_patient_timeline.py`.
- US4 and US5 can run in parallel after shared missingness helpers are stable.

## Parallel Example: Setup

```text
Task: "T001 Create reusable longitudinal canonical table fixture builders in tests/test_eda_longitudinal_outputs.py"
Task: "T002 Create reusable patient timeline fixture builders in tests/test_patient_timeline.py"
Task: "T003 Add module skeleton and public imports for longitudinal EDA generation in src/visualization/eda_longitudinal.py and src/visualization/__init__.py"
Task: "T004 Add module skeleton and public imports for patient timeline rendering in src/visualization/patient_view.py and src/visualization/__init__.py"
```

## Parallel Example: User Story 3

```text
Task: "T041 [US3] Add Panel 7 artifact existence, 1600 x 900 dimension, one-page layout, and selected participant tests in tests/test_patient_timeline.py"
Task: "T047 [US3] Implement selected-participant timeline input preparation in src/visualization/patient_view.py"
Task: "T054 [US3] Wire Panel 7 rendering and manifest metadata into generate_longitudinal_dashboards() in src/visualization/eda_longitudinal.py"
```

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete US1 to deliver the vital trajectories MVP.
3. Run the US1-focused tests and inspect `outputs/figures/eda/05_vital_trajectories.png`.
4. Continue with US2 and US3, the remaining P1 longitudinal review panels.

### Incremental Delivery

1. Add US1 -> test independently -> review vital trajectories artifact.
2. Add US2 -> test independently -> review missingness and adherence artifact.
3. Add US3 -> test independently -> review patient timeline artifact.
4. Add US4 -> test independently -> review data-quality scorecard artifact.
5. Add US5 -> test independently -> review missingness-mechanism artifact.
6. Run Phase 8 acceptance evidence after the selected stories are complete.

### Acceptance Finish

1. Regenerate tracked longitudinal dashboard artifacts in `outputs/figures/eda/`.
2. Verify `outputs/figures/manifest.json` contains SPEC-009 entries and required metadata.
3. Run focused tests, then the full local test suite.
4. Update `CHANGELOG.md` after acceptance evidence is clean.
