---
id: SPEC-011
title: Honest Model Bake-off Under Severe Class Imbalance
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-001, SPEC-004, SPEC-005]
implements: [P7, P8]
supersedes: null
superseded_by: null
related: [SPEC-004, SPEC-005, SPEC-006, SPEC-007, SPEC-009, SPEC-010]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Feature Specification: Honest Model Bake-off Under Severe Class Imbalance

**Feature Branch**: `011-honest-model-bakeoff`

**Created**: 2026-06-01

**Status**: Draft

**Input**: User description: "SPEC-006 renamed to 11: train and compare candidate models under severe class imbalance without participant leakage. Report uncertainty and calibration. Treat results as signal characterization, not validated clinical performance. Depends on SPEC-001, SPEC-004A, and optionally SPEC-005; implements P7 and P8."

## Scope

SPEC-011 adds a reproducible modeling bake-off for postpartum cardiovascular event signal characterization. The feature trains and compares a transparent MEOWS-rules logistic baseline, at least one classic machine-learning model, and a neural-style model using participant-grouped cross-validation, imbalance-aware headline metrics, fold-level uncertainty, calibration, and explicitly selected operating points.

This feature is not a clinical validation claim. All outputs must be framed as synthetic-data or exploratory signal characterization when run on bundled synthetic data, and as candidate-model characterization when run on conforming non-synthetic data.

## Clarifications

### Session 2026-06-01

- Q: How should the pasted "SPEC-006 renamed to 11" be represented in this repository, given an existing SPEC-006 already exists? -> A: Create this as SPEC-011 and treat the old "SPEC-006" label as a source-note rather than a supersession.
- Q: How should the pasted dependency `SPEC-004A` map to the current repository? -> A: Interpret it as the existing EDA/dashboard foundation represented by SPEC-004, with related downstream EDA specs listed as related.
- Q: Is SPEC-005 required? -> A: SPEC-005 is optional for synthetic longitudinal inputs; the bake-off must also accept canonical raw data when available.
- Q: May existing MEOWS code be reused? -> A: Yes, if present; otherwise implement a compatible baseline that consumes the canonical schema and emits conforming predictions.
- Q: What is the primary modeling unit for SPEC-011 outputs? -> A: Participant-level primary modeling: one row per participant, target is `outcome.cv_event`; `observation_id` defaults to participant id.
- Q: How should longitudinal features respect `leakage_guard_days_before_event`? -> A: Event participants use features observed before `cv_event_date - guard_days`; non-event participants use the full observed window.
- Q: How should `threshold_selection: inner_cv` choose selected thresholds? -> A: Maximize recall subject to precision >= configured minimum; break ties by higher precision, then higher threshold.
- Q: How should bootstrap confidence intervals in `metrics_summary.csv` be computed? -> A: Bootstrap over available fold/repeat metric values per model and metric.
- Q: What fallback applies when no inner-CV threshold satisfies the configured minimum precision? -> A: Select the threshold with highest precision; break ties by higher recall, then higher threshold, and mark precision target unmet.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run a Reproducible Bake-off (Priority: P1)

A researcher needs a single command that loads canonical Lullaby data, applies a checked modeling configuration, trains all enabled candidate models, and writes a complete set of modeling artifacts to a chosen output directory.

**Why this priority**: The bake-off only supports honest evaluation if another reviewer can reproduce the same folds, predictions, metrics, thresholds, and summaries from the same seed and inputs.

**Independent Test**: Run the required CLI on synthetic longitudinal data with a fixed seed; assert the required artifacts exist, include the expected schemas, and are reproducible across repeated runs with the same seed.

**Acceptance Scenarios**:

1. **Given** a canonical data directory and `config/modeling.yaml`, **when** the bake-off command runs with seed `20260601`, **then** it writes the required modeling artifacts under the requested output directory.
2. **Given** the same data, configuration, and seed are used twice, **when** the bake-off command is rerun, **then** cross-validation assignments, out-of-fold predictions, selected thresholds, and summary metrics are reproducible.
3. **Given** the run uses bundled synthetic data, **when** summary outputs are written, **then** limitations are framed as synthetic-data signal characterization rather than validated clinical performance.
4. **Given** a caller supplies a custom output directory, **when** artifacts are written, **then** outputs are rooted in that directory and the used configuration is saved there.

---

### User Story 2 - Verify No Participant Leakage (Priority: P1)

A methods reviewer needs to confirm that no participant contributes records to both training and validation data in any fold or repeat.

**Why this priority**: Participant leakage would invalidate every reported model comparison, especially in longitudinal monitoring where repeated observations from one participant are highly correlated.

**Independent Test**: Generate grouped stratified cross-validation splits and assert each participant id appears in either train or validation for a fold, never both.

**Acceptance Scenarios**:

1. **Given** records contain `participant.id`, **when** cross-validation splits are created, **then** no participant id appears in both train and validation within the same fold.
2. **Given** the target event rate is severely imbalanced, **when** grouped stratification is possible, **then** validation folds preserve event-label representation as well as the group constraint permits.
3. **Given** grouped stratification cannot place a positive class in every fold, **when** folds are generated, **then** the system records a warning and still preserves participant-group isolation.
4. **Given** repeated cross-validation is configured, **when** repeats are generated, **then** leakage checks apply independently to every repeat and fold.

---

### User Story 3 - Compare Imbalance-Appropriate Models (Priority: P1)

A modeling reviewer needs to compare at least three candidate models using rare-event-appropriate headline metrics and fold-level variance rather than accuracy.

**Why this priority**: Severe class imbalance makes accuracy misleading. The model comparison must emphasize AUPRC, recall at fixed precision, Brier score, calibration, and uncertainty.

**Independent Test**: Run the bake-off with baseline, classic ML, and MLP models enabled; assert each model has per-fold and summary values for AUPRC, recall at fixed precision, Brier score, and confidence intervals.

**Acceptance Scenarios**:

1. **Given** default modeling configuration is used, **when** the bake-off runs, **then** it compares at least `baseline_meows_logistic`, one classic ML model, and `mlp`.
2. **Given** a candidate model emits prediction scores, **when** metrics are computed, **then** AUPRC, recall at fixed precision, and Brier score are present for every model and fold.
3. **Given** AUROC is computed, **when** summaries are written, **then** AUROC is secondary and is not marked as a headline or primary metric.
4. **Given** accuracy is computed or derivable, **when** summaries are written, **then** accuracy is not marked as a headline metric.
5. **Given** confidence intervals are enabled, **when** metric summaries are written, **then** mean, standard deviation, CI bounds, fold count, repeat count, primary-metric flag, and notes are present.

---

### User Story 4 - Keep Fold-Local Training Operations Honest (Priority: P1)

A reviewer needs assurance that preprocessing, scaling, imputation, feature selection, resampling, and threshold tuning are learned only from training data inside each fold.

**Why this priority**: Any preprocessing or tuning learned before the split can leak validation information and inflate performance.

**Independent Test**: Enable fold-level pipelines and, where resampling is configured, assert resampling is instantiated only inside the training fold pipeline after splitting.

**Acceptance Scenarios**:

1. **Given** a model requires imputation or scaling, **when** the fold is trained, **then** the operation is fit on training rows only and applied to validation rows through the fold pipeline.
2. **Given** resampling is configured, **when** the bake-off runs, **then** resampling happens only after the train/validation split and only within the training fold.
3. **Given** threshold selection is configured as `inner_cv`, **when** thresholds are selected, **then** validation labels from the outer fold are not used to tune the threshold.
4. **Given** raw EDA data are loaded for modeling, **when** imputation is performed, **then** raw EDA tables are never modified.

---

### User Story 5 - Audit Calibration, Operating Points, and Explanations (Priority: P2)

A clinical-safety reviewer needs calibrated score diagnostics, explicitly selected thresholds, and optional feature-level explanations to understand alert burden and model behavior.

**Why this priority**: Candidate model scores and thresholds need clinical interpretation, especially when alert burden and false positives affect participant safety and staff workload.

**Independent Test**: Run the bake-off and assert calibration, decision-curve, operating-point, optional feature-importance, and optional local-explanation outputs are present or explicitly marked unavailable.

**Acceptance Scenarios**:

1. **Given** a model emits probability-like scores, **when** calibration metrics are estimable, **then** calibration intercept, slope, Brier score, and expected calibration error where implemented are reported.
2. **Given** a selected threshold is available, **when** predictions are written, **then** default-threshold and selected-threshold predictions are both included with the selected threshold value.
3. **Given** operating points are evaluated, **when** the operating-points artifact is written, **then** precision, recall, specificity, false-positive rate, alert burden, number needed to alert, and estimated calls are reported.
4. **Given** a model can expose feature importance, **when** the bake-off completes, **then** `feature_importance.csv` is written.
5. **Given** local explanations can be generated, **when** the bake-off completes, **then** `local_explanations.csv` is written.
6. **Given** feature importance or local explanations are unavailable for a model, **when** summaries are written, **then** the output notes clearly mark the explanation as unavailable rather than fabricating values.

### Edge Cases

- If `participant.id` or the configured participant id role is missing, the bake-off fails before cross-validation or model training.
- If the configured target role is missing, non-binary, or entirely missing, the bake-off fails with an actionable validation error.
- If only one target class is present, the bake-off fails before training and records that rare-event metrics cannot be estimated.
- If the number of participant groups or positive-event groups is too small for the configured `n_splits`, the splitter reduces or rejects the split according to documented validation rules while preserving participant isolation.
- If a model cannot be trained on a fold because the training fold has one class, the fold/model result is marked unavailable with notes rather than silently reporting invalid metrics.
- If recall at precision >= 0.80 is not achievable, recall is reported as 0 or unavailable according to the metric contract, with notes stating the fixed-precision target was not met.
- If no inner-CV threshold satisfies the configured minimum precision, the selected-threshold prediction columns use the threshold with highest precision, breaking ties by higher recall then higher threshold, and metric notes mark the precision target unmet.
- If bootstrap confidence intervals cannot be estimated for a metric/fold summary because of degenerate resamples, CI fields are marked unavailable with notes.
- If calibration intercept or slope is not estimable because predictions or labels are degenerate, calibration fields are marked unavailable with notes.
- If optional environment features are absent, environment-derived feature groups are skipped or marked unavailable without blocking non-environment models.
- If a model lacks probability output, it must be wrapped or rejected before metric computation rather than producing unconstrained scores that masquerade as probabilities.
- If `deep_sequence_model.enabled` remains false, the bake-off must still satisfy the neural/deep requirement with the scikit-learn MLP model.
- If output files already exist, the run overwrites or replaces only the requested output directory contents needed for the bake-off and saves the used configuration for auditability.
- If an event participant has no observations before `cv_event_date - leakage_guard_days_before_event`, that participant remains in the labeled dataset with unavailable longitudinal feature summaries rather than using post-event observations.
- If configuration requests a resampling mode other than `none`, the SPEC-011 MVP fails configuration validation unless that mode is implemented and tested as a fold-local training-only pipeline step.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST create or update `src/modeling/__init__.py`.
- **FR-002**: The system MUST create or update `src/modeling/datasets.py`.
- **FR-003**: The system MUST create or update `src/modeling/splits.py`.
- **FR-004**: The system MUST create or update `src/modeling/models.py`.
- **FR-005**: The system MUST create or update `src/modeling/metrics.py`.
- **FR-006**: The system MUST create or update `src/modeling/calibration.py`.
- **FR-007**: The system MUST create or update `src/modeling/bakeoff.py`.
- **FR-008**: The system MUST create or update `src/modeling/explainability.py`.
- **FR-009**: The system MUST create or update `config/modeling.yaml`.
- **FR-010**: The system MUST create or update `scripts/run_model_bakeoff.py`.
- **FR-011**: The system MUST create or update `tests/test_grouped_cv_no_leakage.py`.
- **FR-012**: The system MUST create or update `tests/test_resampling_inside_fold.py`.
- **FR-013**: The system MUST create or update `tests/test_bakeoff_outputs.py`.
- **FR-014**: The system MUST create or update `tests/test_model_metrics_ci.py`.
- **FR-015**: The modeling configuration MUST default to seed `20260601`, target role `outcome.cv_event`, participant id role `participant.id`, grouped stratified cross-validation, 5 splits, 10 repeats, participant grouping, target stratification, balanced class weights, no resampling, fold-local resampling only, and inner-CV threshold selection.
- **FR-016**: The modeling configuration MUST expose feature-group toggles for demographics, daily vitals summaries, alert history, environment features, and leakage-guard days before event.
- **FR-017**: The default enabled models MUST include `baseline_meows_logistic`, `random_forest`, `gradient_boosting`, and `mlp`; `deep_sequence_model` MUST default to disabled with a note that it is enabled only when sequence tensors are implemented and testable.
- **FR-018**: The bake-off CLI MUST support `python scripts/run_model_bakeoff.py --config config/modeling.yaml --data-dir data/raw --out-dir outputs/modeling --seed 20260601`.
- **FR-019**: The bake-off CLI MUST support `python scripts/run_model_bakeoff.py --config config/modeling.yaml --data-dir data/synthetic/longitudinal --out-dir outputs/modeling_synthetic --seed 20260601`.
- **FR-020**: The bake-off MUST write `predictions_oof.csv`, `predictions_by_fold.csv`, `metrics_by_fold.csv`, `metrics_summary.csv`, `operating_points.csv`, `calibration_table.csv`, `decision_curve.csv`, `bakeoff_config_used.yaml`, and `bakeoff_summary.json` under the requested output directory.
- **FR-021**: The bake-off MUST write `feature_importance.csv` when feature importance is available and MUST otherwise record its unavailability in summary notes.
- **FR-022**: The bake-off MUST write `local_explanations.csv` when local explanations are available and MUST otherwise record their unavailability in summary notes.
- **FR-023**: `predictions_oof.csv` MUST include `participant_id`, `observation_id`, `fold`, `repeat`, `model_id`, `y_true`, `y_score`, `y_pred_default_threshold`, `y_pred_selected_threshold`, and `selected_threshold`.
- **FR-024**: `metrics_summary.csv` MUST include `model_id`, `metric`, `mean`, `sd`, `ci_lower`, `ci_upper`, `n_folds`, `n_repeats`, `primary_metric`, and `notes`.
- **FR-025**: `operating_points.csv` MUST include `model_id`, `threshold`, `precision`, `recall`, `specificity`, `false_positive_rate`, `alerts_per_100_participant_days`, `number_needed_to_alert`, and `estimated_calls`.
- **FR-026**: Cross-validation MUST split by participant group, and no participant may appear in both training and validation within any fold.
- **FR-027**: Cross-validation MUST stratify by event label where the participant-group constraint and class counts permit.
- **FR-028**: Each fold and repeat MUST be reported separately before aggregate summaries are reported.
- **FR-029**: Any resampling, scaling, feature selection, imputation, or threshold tuning MUST happen inside training-fold pipelines only.
- **FR-030**: The SPEC-011 MVP MUST support `resampling: none`; the system MUST NOT resample before the cross-validation split, and non-`none` resampling modes MUST fail configuration validation unless implemented as fold-local training-only pipeline steps with tests.
- **FR-031**: Imputation for modeling MUST occur only inside a modeling pipeline and MUST NOT modify raw EDA data.
- **FR-032**: The baseline model MUST implement a MEOWS-rules logistic-regression baseline or compatible equivalent using canonical schema inputs.
- **FR-033**: The classic ML model set MUST include at least one of random forest, gradient boosting, SVM, or kNN, with random forest and gradient boosting enabled by default.
- **FR-034**: The neural/deep model requirement MUST be satisfied by scikit-learn MLP unless a full deep sequence model is implemented and testable.
- **FR-035**: A future deep sequence model MAY be plugged in only if it consumes the canonical schema and emits conforming prediction outputs.
- **FR-036**: Primary headline metrics MUST include AUPRC, recall at fixed precision, and Brier score.
- **FR-037**: Recall at fixed precision MUST default to minimum precision `0.80`.
- **FR-038**: Calibration reporting MUST include calibration intercept and slope where estimable.
- **FR-039**: Expected calibration error SHOULD be reported when implemented and MUST be marked unavailable when not implemented.
- **FR-040**: Bootstrap confidence intervals MUST be configurable and default to enabled with 1000 bootstrap samples and 0.95 level.
- **FR-041**: AUROC MAY be included as a secondary metric but MUST NOT be the headline metric.
- **FR-042**: Accuracy MUST NOT be a headline metric.
- **FR-043**: Confusion matrices or confusion-derived summaries MUST be tied to explicitly selected thresholds.
- **FR-044**: The bake-off summary MUST state that results are exploratory signal characterization and, when synthetic data are used, not validated clinical performance.
- **FR-045**: The implementation MUST keep backward compatibility where reasonable with existing MEOWS feature generation or threshold logic if those modules exist in the repository.
- **FR-046**: The default modeling dataset MUST use participant-level rows with one record per participant, target `outcome.cv_event`, and `observation_id` equal to the participant id unless a future optional observation-level mode is explicitly configured.
- **FR-047**: For event participants, longitudinal summary features MUST be computed only from observations strictly before `cv_event_date - leakage_guard_days_before_event`; for non-event participants, longitudinal summary features MAY use the full observed window.
- **FR-048**: When `threshold_selection` is `inner_cv`, selected thresholds MUST be chosen inside the training fold by maximizing recall subject to the configured minimum precision; ties MUST break by higher precision, then higher threshold.
- **FR-049**: Bootstrap confidence intervals in `metrics_summary.csv` MUST be computed by resampling available fold/repeat metric values for each model and metric.
- **FR-050**: When no inner-CV threshold satisfies the configured minimum precision, the selected-threshold fallback MUST choose the highest-precision threshold, break ties by higher recall then higher threshold, and record that the precision target was unmet.

### Configuration Contract

`config/modeling.yaml` MUST default to:

```yaml
seed: 20260601
target: outcome.cv_event
participant_id_role: participant.id
cv:
  strategy: stratified_group_kfold
  n_splits: 5
  n_repeats: 10
  group_by: participant.id
  stratify_by: target
features:
  include_demographics: true
  include_daily_vitals_summary: true
  include_alert_history: true
  include_environment: true
  leakage_guard_days_before_event: 0
imbalance:
  class_weight: balanced
  resampling: none
  resampling_allowed_inside_fold_only: true
  threshold_selection: inner_cv
metrics:
  primary:
    - auprc
    - recall_at_precision
    - brier
  recall_at_precision:
    min_precision: 0.80
  bootstrap_ci:
    enabled: true
    n_bootstrap: 1000
    level: 0.95
models:
  baseline_meows_logistic:
    enabled: true
  random_forest:
    enabled: true
  gradient_boosting:
    enabled: true
  mlp:
    enabled: true
  deep_sequence_model:
    enabled: false
    note: enable only if sequence tensors are implemented and testable
```

### Key Entities

- **Modeling Dataset**: Canonical participant-level feature table with one row per participant, participant ids, observation ids defaulting to participant ids, target labels from `outcome.cv_event`, feature groups, and optional environment context.
- **Leakage Guard Window**: The per-participant observation window used for longitudinal feature summaries; event participants are truncated before `cv_event_date - guard_days`, while non-event participants use the full observed window.
- **Participant Group Split**: A train/validation partition that assigns each participant to exactly one side of a fold.
- **Model Candidate**: A configured estimator that consumes fold-local training features and emits conforming validation prediction scores.
- **MEOWS Logistic Baseline**: A transparent baseline that uses MEOWS-style rules or generated MEOWS features with logistic regression.
- **Fold Pipeline**: The fold-local sequence of imputation, scaling, feature selection, optional resampling, model fitting, and prediction.
- **Prediction Record**: One out-of-fold scored observation with participant id, observation id, fold, repeat, model id, true label, score, default-threshold prediction, selected-threshold prediction, and selected threshold.
- **Metric Summary**: Aggregate metric record with mean, standard deviation, fold/repeat-value bootstrap confidence interval, fold/repeat counts, primary-metric flag, and notes.
- **Operating Point**: Threshold-specific clinical and operations summary with precision, recall, specificity, false-positive rate, alert burden, number needed to alert, estimated calls, and deterministic threshold-selection rationale.
- **Calibration Table**: Model-level or fold-level calibration diagnostics including Brier score, intercept, slope, expected calibration error where implemented, and estimability notes.
- **Decision Curve**: Threshold-indexed estimate of net benefit or decision-curve support used only for exploratory comparison.
- **Explanation Artifact**: Optional feature-importance or local-explanation output generated only when supported by the fitted model and available features.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The required CLI runs successfully on `data/synthetic/longitudinal` with seed `20260601` and writes all required non-optional artifacts under `outputs/modeling_synthetic`.
- **SC-002**: A repeated run with the same seed, data, and configuration produces identical fold assignments and out-of-fold prediction rows.
- **SC-003**: At least three model families are compared: MEOWS logistic baseline, at least one classic ML model, and MLP or deeper neural model.
- **SC-004**: No participant leakage exists in any fold or repeat, as verified by focused tests.
- **SC-005**: AUPRC, recall at fixed precision, Brier score, fold-level values, mean, standard deviation, and confidence intervals are present for every trained model.
- **SC-006**: AUROC and accuracy, if present, are not marked as headline or primary metrics.
- **SC-007**: Resampling, if enabled by configuration, occurs only inside fold-local training pipelines and never before splitting.
- **SC-008**: Calibration output includes Brier score and calibration intercept/slope where estimable, with unavailable cases noted.
- **SC-009**: Operating points are tied to explicit thresholds and include alert-burden fields.
- **SC-010**: `bakeoff_summary.json` and related report notes frame synthetic runs as synthetic signal characterization, not validated clinical performance.
- **SC-011**: The focused SPEC-011 tests pass: `pytest tests/test_grouped_cv_no_leakage.py tests/test_resampling_inside_fold.py tests/test_bakeoff_outputs.py tests/test_model_metrics_ci.py`.

## Assumptions

- SPEC-001 provides canonical schema roles for participants, daily vitals, alerts, environment, and clinical outcomes.
- SPEC-004 provides visualization/reporting conventions and artifact discipline that can be reused for modeling summaries where helpful.
- SPEC-005 may provide synthetic longitudinal data for reproducible bake-off tests, but non-synthetic conforming data directories should use the same CLI and contracts.
- The pasted dependency `SPEC-004A` is interpreted as the repository's existing SPEC-004 foundation, with later EDA specs listed as related context.
- The pasted "SPEC-006 renamed to 11" does not supersede the existing repository SPEC-006; this feature is SPEC-011.
- Severe class imbalance is expected; metric contracts prioritize rare-event performance and calibration over accuracy.
- This spec defines model comparison and signal characterization only. Clinical deployment, validated clinical performance claims, adaptive thresholds, and participant-facing alert interventions are out of scope.
