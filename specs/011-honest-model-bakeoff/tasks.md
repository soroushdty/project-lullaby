---
id: TASKS-011
title: Honest Model Bake-off Under Severe Class Imbalance Tasks
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-011, PLAN-011, DATA-011, RESEARCH-011]
implements: [P7, P8]
supersedes: null
superseded_by: null
related: [SPEC-001, SPEC-004, SPEC-005, SPEC-006, SPEC-009, SPEC-010]
description: "Executable implementation task list for participant-level modeling bake-off, grouped CV leakage protection, fold-local pipelines, rare-event metrics, calibration, operating points, and required artifacts."
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Tasks: Honest Model Bake-off Under Severe Class Imbalance

**Input**: Design documents from `specs/011-honest-model-bakeoff/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/`

**Tests**: Included because SPEC-011 explicitly requires focused tests in `tests/test_grouped_cv_no_leakage.py`, `tests/test_resampling_inside_fold.py`, `tests/test_bakeoff_outputs.py`, and `tests/test_model_metrics_ci.py`.

**Organization**: Tasks are grouped by user story so each modeling capability can be implemented and verified independently after the shared modeling foundation is complete.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files or independent test areas
- **[Story]**: Maps the task to a SPEC-011 user story
- Each task names the exact source, test, config, script, artifact, or documentation path to change

## Phase 1: Setup

**Purpose**: Prepare the SPEC-011 dependency, config, package, script, and test structure.

- [X] T001 Add `scikit-learn>=1.5` to runtime dependencies in `pyproject.toml`.
- [X] T002 Create default SPEC-011 modeling configuration in `config/modeling.yaml`.
- [X] T003 [P] Create modeling package exports in `src/modeling/__init__.py`.
- [X] T004 [P] Create dataset module skeleton and shared exceptions in `src/modeling/datasets.py`.
- [X] T005 [P] Create split module skeleton in `src/modeling/splits.py`.
- [X] T006 [P] Create model factory module skeleton in `src/modeling/models.py`.
- [X] T007 [P] Create metric module skeleton in `src/modeling/metrics.py`.
- [X] T008 [P] Create calibration module skeleton in `src/modeling/calibration.py`.
- [X] T009 [P] Create bake-off orchestration module skeleton in `src/modeling/bakeoff.py`.
- [X] T010 [P] Create explanation module skeleton in `src/modeling/explainability.py`.
- [X] T011 Create CLI wrapper skeleton in `scripts/run_model_bakeoff.py`.

---

## Phase 2: Foundational Modeling Dataset and Config

**Purpose**: Implement shared config parsing, input loading, role/alias resolution, participant-level feature construction, and leakage-guard windows that block every user story.

**Blocking rule**: No user story work should start until T012-T027 are complete.

### Tests for Foundational Behavior

- [X] T012 [P] Add config default and CLI seed override tests in `tests/test_bakeoff_outputs.py`.
- [X] T013 [P] Add canonical and synthetic CSV role-resolution tests in `tests/test_bakeoff_outputs.py`.
- [X] T014 [P] Add participant-level modeling dataset shape tests in `tests/test_bakeoff_outputs.py`.
- [X] T015 [P] Add leakage-guard feature-window tests for event and non-event participants in `tests/test_bakeoff_outputs.py`.
- [X] T016 [P] Add one-class and missing required-role validation tests in `tests/test_bakeoff_outputs.py`.

### Implementation for Foundational Behavior

- [X] T017 Implement `ModelingConfig` loading, validation, and seed override handling in `src/modeling/bakeoff.py`.
- [X] T018 Implement local CSV discovery for participants, daily vitals, alerts, clinical outcomes, and environment tables in `src/modeling/datasets.py`.
- [X] T019 Implement accepted canonical and synthetic role aliases for participant id, target, event date, vitals, alerts, and environment fields in `src/modeling/datasets.py`.
- [X] T020 Implement binary target parsing for `outcome.cv_event` in `src/modeling/datasets.py`.
- [X] T021 Implement participant-level `observation_id == participant_id` dataset construction in `src/modeling/datasets.py`.
- [X] T022 Implement leakage-guard window calculation using `cv_event_date - leakage_guard_days_before_event` in `src/modeling/datasets.py`.
- [X] T023 Implement daily-vitals summary feature aggregation inside the leakage-guard window in `src/modeling/datasets.py`.
- [X] T024 Implement demographic and participant-context feature extraction in `src/modeling/datasets.py`.
- [X] T025 Implement alert-history and environment feature aggregation inside the leakage-guard window in `src/modeling/datasets.py`.
- [X] T026 Implement unavailable feature notes and synthetic-data detection in `src/modeling/datasets.py`.
- [X] T027 Implement required-role, two-class target, and non-mutating raw-data validation helpers in `src/modeling/datasets.py`.

**Checkpoint**: A valid participant-level modeling dataset can be built from `data/synthetic/longitudinal` without post-event feature leakage.

---

## Phase 3: User Story 1 - Run a Reproducible Bake-off (Priority: P1) MVP

**Goal**: Provide the required CLI that loads config and data, runs enabled models through the bake-off, writes required artifacts, and reproduces outputs by seed.

**Independent Test**: Run the CLI on synthetic longitudinal data with seed `20260601`; assert required artifacts exist, expected schemas are present, synthetic framing is included, and repeated runs are deterministic.

### Tests for User Story 1

- [X] T028 [P] [US1] Add CLI synthetic bake-off success test in `tests/test_bakeoff_outputs.py`.
- [X] T029 [P] [US1] Add required artifact existence tests for all non-optional outputs in `tests/test_bakeoff_outputs.py`.
- [X] T030 [P] [US1] Add `predictions_oof.csv`, `metrics_summary.csv`, and `operating_points.csv` schema tests in `tests/test_bakeoff_outputs.py`.
- [X] T031 [P] [US1] Add repeated-run deterministic prediction and metric ordering tests in `tests/test_bakeoff_outputs.py`.
- [X] T032 [P] [US1] Add synthetic signal-characterization limitation tests for `bakeoff_summary.json` in `tests/test_bakeoff_outputs.py`.

### Implementation for User Story 1

- [X] T033 [US1] Implement argparse handling for `--config`, `--data-dir`, `--out-dir`, and `--seed` in `scripts/run_model_bakeoff.py`.
- [X] T034 [US1] Implement `run_bakeoff()` orchestration entry point in `src/modeling/bakeoff.py`.
- [X] T035 [US1] Implement output directory creation and deterministic artifact overwrite behavior in `src/modeling/bakeoff.py`.
- [X] T036 [US1] Implement `bakeoff_config_used.yaml` writing with effective config in `src/modeling/bakeoff.py`.
- [X] T037 [US1] Implement `predictions_oof.csv` and `predictions_by_fold.csv` writing with deterministic row ordering in `src/modeling/bakeoff.py`.
- [X] T038 [US1] Implement `metrics_by_fold.csv`, `metrics_summary.csv`, `operating_points.csv`, `calibration_table.csv`, and `decision_curve.csv` writing in `src/modeling/bakeoff.py`.
- [X] T039 [US1] Implement `bakeoff_summary.json` with seed, counts, models, warnings, limitations, and artifact paths in `src/modeling/bakeoff.py`.
- [X] T040 [US1] Implement CLI exit-code and actionable error behavior in `scripts/run_model_bakeoff.py`.

**Checkpoint**: User Story 1 is independently functional and the synthetic quickstart command writes the complete non-optional artifact set.

---

## Phase 4: User Story 2 - Verify No Participant Leakage (Priority: P1)

**Goal**: Generate repeated grouped stratified cross-validation splits with no participant overlap between train and validation in any fold or repeat.

**Independent Test**: Generate splits from participant ids and imbalanced labels; assert train/validation participant sets are disjoint in every fold and repeat, with stratification warnings only where class counts require them.

### Tests for User Story 2

- [X] T041 [P] [US2] Add grouped CV no-overlap tests in `tests/test_grouped_cv_no_leakage.py`.
- [X] T042 [P] [US2] Add repeated split determinism tests by seed in `tests/test_grouped_cv_no_leakage.py`.
- [X] T043 [P] [US2] Add stratification-preserves-positive-events-where-possible tests in `tests/test_grouped_cv_no_leakage.py`.
- [X] T044 [P] [US2] Add infeasible positive-event group warning tests in `tests/test_grouped_cv_no_leakage.py`.
- [X] T045 [P] [US2] Add bake-off integration leakage audit tests in `tests/test_grouped_cv_no_leakage.py`.

### Implementation for User Story 2

- [X] T046 [US2] Implement `SplitAssignment` records and validation helpers in `src/modeling/splits.py`.
- [X] T047 [US2] Implement repeated grouped stratified split generation with seed-controlled repeats in `src/modeling/splits.py`.
- [X] T048 [US2] Implement feasible split-count validation and warning generation for rare positive-event groups in `src/modeling/splits.py`.
- [X] T049 [US2] Implement strict participant-disjoint leakage assertions in `src/modeling/splits.py`.
- [X] T050 [US2] Integrate split assignment metadata and warnings into `src/modeling/bakeoff.py`.

**Checkpoint**: User Story 2 is independently functional and split tests prove no participant leakage across all repeats and folds.

---

## Phase 5: User Story 3 - Compare Imbalance-Appropriate Models (Priority: P1)

**Goal**: Compare at least three model families using rare-event-appropriate headline metrics, per-fold variance, confidence intervals, and non-headline treatment of AUROC and accuracy.

**Independent Test**: Run the bake-off with baseline, classic ML, and MLP enabled; assert every trained model has AUPRC, recall at fixed precision, Brier score, fold-level values, mean, standard deviation, CIs, and primary-metric flags.

### Tests for User Story 3

- [X] T051 [P] [US3] Add enabled model family and configured class-weight behavior tests in `tests/test_bakeoff_outputs.py`.
- [X] T052 [P] [US3] Add model probability-score bounds tests in `tests/test_bakeoff_outputs.py`.
- [X] T053 [P] [US3] Add primary metric presence tests for AUPRC, recall at fixed precision, and Brier score in `tests/test_model_metrics_ci.py`.
- [X] T054 [P] [US3] Add AUROC-secondary and accuracy-not-headline tests in `tests/test_model_metrics_ci.py`.
- [X] T055 [P] [US3] Add bootstrap CI over fold/repeat metric values tests in `tests/test_model_metrics_ci.py`.
- [X] T056 [P] [US3] Add degenerate metric notes tests in `tests/test_model_metrics_ci.py`.

### Implementation for User Story 3

- [X] T057 [US3] Implement MEOWS-style feature transformation and logistic baseline factory with configured `class_weight` support in `src/modeling/models.py`.
- [X] T058 [US3] Implement random forest and gradient boosting model factories with deterministic random states and configured `class_weight` behavior where supported in `src/modeling/models.py`.
- [X] T059 [US3] Implement MLP model factory with scaling-aware deterministic pipeline settings and explicit notes for unsupported `class_weight` behavior in `src/modeling/models.py`.
- [X] T060 [US3] Implement fold-local sklearn pipeline construction with imputation and optional scaling in `src/modeling/models.py`.
- [X] T061 [US3] Implement probability-like score extraction and bounds validation in `src/modeling/models.py`.
- [X] T062 [US3] Implement AUPRC, AUROC secondary, Brier wrapper, and confusion-derived metric helpers in `src/modeling/metrics.py`.
- [X] T063 [US3] Implement recall-at-fixed-precision metric with configured minimum precision in `src/modeling/metrics.py`.
- [X] T064 [US3] Implement fold/repeat metric records and primary-metric flags in `src/modeling/metrics.py`.
- [X] T065 [US3] Implement bootstrap CI resampling over fold/repeat metric values in `src/modeling/metrics.py`.
- [X] T066 [US3] Integrate model training, prediction, and metric collection loops into `src/modeling/bakeoff.py`.

**Checkpoint**: User Story 3 is independently functional and the bake-off compares baseline, classic ML, and MLP with honest headline metrics and CIs.

---

## Phase 6: User Story 4 - Keep Fold-Local Training Operations Honest (Priority: P1)

**Goal**: Ensure imputation, scaling, optional resampling, feature selection, model fitting, and threshold tuning happen only inside training folds.

**Independent Test**: Enable fold-level pipelines and configured resampling checks; assert preprocessing is fit only on training rows, resampling never happens before split, and selected thresholds never use outer validation labels.

### Tests for User Story 4

- [X] T067 [P] [US4] Add fold-local imputation and scaling tests in `tests/test_resampling_inside_fold.py`.
- [X] T068 [P] [US4] Add raw EDA dataframe immutability tests in `tests/test_resampling_inside_fold.py`.
- [X] T069 [P] [US4] Add no-resampling-before-split tests in `tests/test_resampling_inside_fold.py`.
- [X] T070 [P] [US4] Add unsupported resampling mode validation tests in `tests/test_resampling_inside_fold.py`.
- [X] T071 [P] [US4] Add inner-CV threshold selection does-not-use-outer-validation-labels tests in `tests/test_resampling_inside_fold.py`.
- [X] T072 [P] [US4] Add threshold fallback precision-target-unmet tests in `tests/test_resampling_inside_fold.py`.

### Implementation for User Story 4

- [X] T073 [US4] Implement fold-local preprocessing fit/transform boundaries in `src/modeling/models.py`.
- [X] T074 [US4] Implement `resampling: none` handling and explicit validation for unsupported non-default resampling in `src/modeling/models.py`.
- [X] T075 [US4] Implement training-fold-only threshold candidate generation in `src/modeling/metrics.py`.
- [X] T076 [US4] Implement inner-CV threshold selection maximizing recall subject to minimum precision in `src/modeling/metrics.py`.
- [X] T077 [US4] Implement selected-threshold fallback choosing highest precision, then higher recall, then higher threshold in `src/modeling/metrics.py`.
- [X] T078 [US4] Integrate selected thresholds, threshold notes, and default-threshold predictions into `src/modeling/bakeoff.py`.
- [X] T079 [US4] Record threshold target-met status and fallback notes in `predictions_by_fold.csv` from `src/modeling/bakeoff.py`.

**Checkpoint**: User Story 4 is independently functional and fold-local tests prove preprocessing, resampling checks, and threshold tuning do not leak validation information.

---

## Phase 7: User Story 5 - Audit Calibration, Operating Points, and Explanations (Priority: P2)

**Goal**: Write calibration diagnostics, explicit operating points, decision-curve rows, and optional explanation artifacts or unavailability notes.

**Independent Test**: Run the bake-off and assert calibration, decision curve, operating points, feature importance where available, and local-explanation availability notes are present and tied to explicit thresholds.

### Tests for User Story 5

- [X] T080 [P] [US5] Add calibration table schema and estimability tests in `tests/test_model_metrics_ci.py`.
- [X] T081 [P] [US5] Add operating point explicit-threshold and alert-burden schema tests in `tests/test_bakeoff_outputs.py`.
- [X] T082 [P] [US5] Add decision curve schema and exploratory-notes tests in `tests/test_bakeoff_outputs.py`.
- [X] T083 [P] [US5] Add feature importance available-or-noted tests in `tests/test_bakeoff_outputs.py`.
- [X] T084 [P] [US5] Add local explanations available-or-noted tests in `tests/test_bakeoff_outputs.py`.
- [X] T085 [P] [US5] Add non-clinical-validation language tests for calibration and operating-point notes in `tests/test_bakeoff_outputs.py`.

### Implementation for User Story 5

- [X] T086 [US5] Implement Brier, calibration intercept, calibration slope, and expected calibration error helpers in `src/modeling/calibration.py`.
- [X] T087 [US5] Implement non-estimable calibration notes for degenerate labels or scores in `src/modeling/calibration.py`.
- [X] T088 [US5] Implement operating-point precision, recall, specificity, false-positive rate, alerts-per-100-participant-days, number-needed-to-alert, and estimated-calls helpers in `src/modeling/metrics.py`.
- [X] T089 [US5] Implement exploratory decision-curve net-benefit rows in `src/modeling/metrics.py`.
- [X] T090 [US5] Implement global feature importance extraction for supported estimators in `src/modeling/explainability.py`.
- [X] T091 [US5] Implement local explanation unavailability handling and optional conforming rows in `src/modeling/explainability.py`.
- [X] T092 [US5] Integrate `calibration_table.csv`, `operating_points.csv`, `decision_curve.csv`, `feature_importance.csv`, and `local_explanations.csv` output paths in `src/modeling/bakeoff.py`.

**Checkpoint**: User Story 5 is independently functional and audit artifacts are explicit about calibration, threshold operating points, explanation availability, and clinical limitations.

---

## Phase 8: Polish and Acceptance Evidence

**Purpose**: Verify full SPEC-011 acceptance, documentation, dependency metadata, and regression safety.

- [X] T093 Run and record elapsed time for focused SPEC-011 acceptance tests with `.venv/bin/pytest tests/test_grouped_cv_no_leakage.py tests/test_resampling_inside_fold.py tests/test_bakeoff_outputs.py tests/test_model_metrics_ci.py`.
- [X] T094 Run and record elapsed time for the synthetic quickstart command in `specs/011-honest-model-bakeoff/quickstart.md`.
- [X] T095 Inspect `outputs/modeling_synthetic/bakeoff_summary.json` for synthetic signal-characterization limitations.
- [X] T096 Inspect `outputs/modeling_synthetic/metrics_summary.csv` for primary metrics, CI fields, and no headline accuracy.
- [X] T097 Inspect `outputs/modeling_synthetic/predictions_oof.csv` for deterministic row ordering and required prediction columns.
- [X] T098 Run existing focused regression tests with `.venv/bin/pytest tests/unit/test_lullaby_schema.py tests/test_eda_core_outputs.py tests/test_eda_longitudinal_outputs.py tests/test_eda_relationships_outputs.py`.
- [X] T099 Update command notes or expected output text in `specs/011-honest-model-bakeoff/quickstart.md`.
- [X] T100 Add SPEC-011 implementation entry to `CHANGELOG.md` after acceptance evidence is clean.

---

## Dependencies and Execution Order

### Phase Dependencies

- **Phase 1 Setup**: No dependencies.
- **Phase 2 Foundational Modeling Dataset and Config**: Depends on Phase 1 and blocks all user stories.
- **Phase 3 US1 Reproducible Bake-off**: Depends on Phase 2 and is the MVP slice.
- **Phase 4 US2 Participant Leakage**: Depends on Phase 2 and can run in parallel with US1.
- **Phase 5 US3 Model Comparison**: Depends on Phase 2 and integrates with US1 orchestration.
- **Phase 6 US4 Fold-Local Training Operations**: Depends on Phase 2 and should be completed before finalizing US3 metrics.
- **Phase 7 US5 Calibration, Operating Points, and Explanations**: Depends on US1 and US3 outputs.
- **Phase 8 Polish**: Depends on all selected user stories.

### User Story Dependencies

- **US1 Run a Reproducible Bake-off (P1)**: Starts after Phase 2; provides the CLI and artifact shell for the MVP.
- **US2 Verify No Participant Leakage (P1)**: Starts after Phase 2; independent split validation can be completed before full model output.
- **US3 Compare Imbalance-Appropriate Models (P1)**: Starts after Phase 2; depends on model factories and metrics, then integrates with US1.
- **US4 Keep Fold-Local Training Operations Honest (P1)**: Starts after Phase 2; interacts with US3 pipelines and threshold logic.
- **US5 Audit Calibration, Operating Points, and Explanations (P2)**: Starts after US1/US3 because it consumes predictions and model outputs.

### Within Each User Story

- Write story tests first and confirm they fail for missing behavior.
- Implement data/model/metric helpers before orchestration integration.
- Integrate artifact writing after helper behavior is covered.
- A story is complete only when its independent test file passes from the repository root.

## Parallel Opportunities

- T003-T010 can run in parallel during setup because they touch different modeling modules.
- T012-T016 can run in parallel because they add independent foundational tests.
- US2 split tests T041-T045 can run in parallel with US1 CLI tests T028-T032 after Phase 2.
- US3 metric tests T053-T056 can run in parallel with model factory tasks T057-T060 after Phase 2.
- US5 audit tests T080-T085 can run in parallel because they cover separate artifacts.
- Implementation tasks touching the same file, especially `src/modeling/bakeoff.py` and `src/modeling/metrics.py`, should be sequenced or coordinated.

## Parallel Example: User Story 1

```bash
Task: "T028 [P] [US1] Add CLI synthetic bake-off success test in tests/test_bakeoff_outputs.py"
Task: "T029 [P] [US1] Add required artifact existence tests for all non-optional outputs in tests/test_bakeoff_outputs.py"
Task: "T032 [P] [US1] Add synthetic signal-characterization limitation tests for bakeoff_summary.json in tests/test_bakeoff_outputs.py"
```

## Parallel Example: User Story 2

```bash
Task: "T041 [P] [US2] Add grouped CV no-overlap tests in tests/test_grouped_cv_no_leakage.py"
Task: "T042 [P] [US2] Add repeated split determinism tests by seed in tests/test_grouped_cv_no_leakage.py"
Task: "T044 [P] [US2] Add infeasible positive-event group warning tests in tests/test_grouped_cv_no_leakage.py"
```

## Parallel Example: User Story 3

```bash
Task: "T057 [US3] Implement MEOWS-style feature transformation and logistic baseline factory in src/modeling/models.py"
Task: "T062 [US3] Implement AUPRC, AUROC secondary, Brier wrapper, and confusion-derived metric helpers in src/modeling/metrics.py"
Task: "T086 [US5] Implement Brier, calibration intercept, calibration slope, and expected calibration error helpers in src/modeling/calibration.py"
```

## Implementation Strategy

### MVP First

1. Complete Phase 1 setup.
2. Complete Phase 2 foundational dataset/config behavior.
3. Complete Phase 3 User Story 1 enough to run the synthetic CLI and write required artifact shells.
4. Complete Phase 4 leakage checks before trusting any reported result.
5. Stop and validate `tests/test_bakeoff_outputs.py` and `tests/test_grouped_cv_no_leakage.py`.

### Incremental Delivery

1. Add dataset/config foundation and validate participant-level feature construction.
2. Add reproducible CLI artifact generation.
3. Add grouped CV leakage protection.
4. Add model families and primary metrics.
5. Add fold-local threshold/resampling guarantees.
6. Add calibration, operating points, and explanations.
7. Run focused acceptance tests and quickstart commands.

### Parallel Team Strategy

With multiple implementers:

1. Complete setup and foundational dataset tasks together.
2. Assign split/leakage work to one implementer and model/metric work to another.
3. Sequence shared `bakeoff.py` integration after helpers and tests stabilize.
4. Finish with one coordinated acceptance pass to avoid artifact/schema drift.

## Notes

- [P] tasks = different files or independent test areas with no dependency on incomplete tasks.
- [Story] label maps task to a SPEC-011 user story for traceability.
- Tests are included because SPEC-011 names required focused test files.
- Verify new tests fail before implementing their target behavior.
- Keep outputs framed as synthetic or exploratory signal characterization when using synthetic data.
- Do not add real-data/PHI handling, adaptive clinical thresholds, or deployment behavior in SPEC-011.
