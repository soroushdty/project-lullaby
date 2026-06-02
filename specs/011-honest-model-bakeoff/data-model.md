---
id: DATA-011
title: Honest Model Bake-off Under Severe Class Imbalance Data Model
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-011, SPEC-001, SPEC-004, SPEC-005]
implements: [P7, P8]
supersedes: null
superseded_by: null
related: [SPEC-004, SPEC-005, SPEC-006, SPEC-007, SPEC-009, SPEC-010]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Data Model: Honest Model Bake-off Under Severe Class Imbalance

## ModelingConfig

Represents the parsed and validated `config/modeling.yaml` used for one bake-off run.

**Fields**:
- `seed`: integer random seed
- `target`: semantic target role, default `outcome.cv_event`
- `participant_id_role`: semantic participant role, default `participant.id`
- `cv`: cross-validation settings
- `features`: enabled feature groups and leakage guard
- `imbalance`: class weight, resampling, and threshold-selection settings
- `metrics`: primary metric and bootstrap-CI settings
- `models`: enabled model settings

**Validation rules**:
- `seed` is required and integer-like.
- `cv.strategy` must be `stratified_group_kfold` for the default run.
- `cv.n_splits` and `cv.n_repeats` must be positive integers.
- `imbalance.resampling_allowed_inside_fold_only` must be true when resampling is not `none`.
- `threshold_selection` must be `inner_cv` for selected-threshold outputs.
- At least three required model families are enabled by default: baseline, classic ML, and
  MLP.

## ModelingDataBundle

Represents the raw loaded tables for a bake-off run.

**Fields**:
- `data_dir`
- `participants`
- `daily_vitals`
- `alerts`
- `clinical_outcomes`
- `environment`
- `load_warnings`
- `synthetic_detected`

**Validation rules**:
- `participants`, `daily_vitals`, and `clinical_outcomes` are required for the default
  participant-level bake-off.
- Required roles must resolve through canonical names or accepted aliases before training.
- Optional table absence is recorded in warnings and disables only affected feature groups.
- Raw loaded tables are not modified by imputation, scaling, or model pipelines.

## ModelingDataset

Represents the participant-level supervised table consumed by splitters and model pipelines.

**Fields**:
- `participant_id`
- `observation_id`
- `y`
- `event_date`
- `feature_columns`
- `feature_frame`
- `feature_group_metadata`
- `unavailable_feature_notes`

**Validation rules**:
- One row per participant.
- `observation_id` defaults to `participant_id`.
- `y` is binary and derived from `outcome.cv_event`.
- At least two target classes must be present before model training.
- Feature columns must exclude target, event-date, and post-event leakage fields.
- Participants with unavailable longitudinal summaries remain in the dataset with missing
  feature values handled only by fold-local imputation.

## LeakageGuardWindow

Represents the observation window used when aggregating longitudinal features.

**Fields**:
- `participant_id`
- `has_event`
- `cv_event_date`
- `guard_days`
- `feature_window_start`
- `feature_window_end`
- `no_pre_event_observations`

**Validation rules**:
- Event participants use observations strictly before `cv_event_date - guard_days`.
- Non-event participants use the full observed window.
- Event participants with no eligible observations must not use post-event observations.
- Guard behavior applies consistently to vitals, alerts, and environment-derived summaries
  that depend on longitudinal dates.

## SplitAssignment

Represents one train/validation partition for one repeat and fold.

**Fields**:
- `repeat`
- `fold`
- `train_indices`
- `validation_indices`
- `train_participant_ids`
- `validation_participant_ids`
- `class_counts`
- `warnings`

**Validation rules**:
- `train_participant_ids` and `validation_participant_ids` are disjoint.
- Every validation row belongs to exactly one validation fold per repeat.
- Stratification is attempted by target label while preserving participant groups.
- If requested splits exceed feasible positive-event groups, the split is reduced or rejected
  with warnings while preserving participant isolation.

## ModelCandidate

Represents one configured estimator family.

**Fields**:
- `model_id`
- `family`
- `enabled`
- `estimator`
- `requires_scaling`
- `supports_predict_proba`
- `supports_feature_importance`
- `random_state`
- `notes`

**Validation rules**:
- Enabled candidates must emit probability-like scores in `[0, 1]`.
- `baseline_meows_logistic`, at least one classic ML model, and `mlp` must be available for
  the default run.
- Estimators that cannot be fit on a fold are marked unavailable for that fold with notes.

## FoldPipeline

Represents fold-local preprocessing, optional resampling, model fitting, threshold tuning,
and validation prediction.

**Fields**:
- `repeat`
- `fold`
- `model_id`
- `imputer`
- `scaler`
- `resampler`
- `estimator`
- `selected_threshold`
- `threshold_notes`
- `fit_notes`

**Validation rules**:
- Imputation and scaling are fit on training rows only.
- Resampling, when enabled, occurs only after the split and only on training rows.
- Outer validation labels are not used for threshold tuning.
- Raw input tables are not mutated.

## PredictionRecord

Represents one out-of-fold prediction row.

**Required columns**:
- `participant_id`
- `observation_id`
- `fold`
- `repeat`
- `model_id`
- `y_true`
- `y_score`
- `y_pred_default_threshold`
- `y_pred_selected_threshold`
- `selected_threshold`

**Validation rules**:
- `y_score` is probability-like and bounded in `[0, 1]`.
- `y_pred_default_threshold` uses threshold `0.50`.
- `y_pred_selected_threshold` uses the fold-local selected threshold or documented fallback.
- Row ordering is deterministic by `model_id`, `repeat`, `fold`, `participant_id`, and
  `observation_id`.

## MetricRecord

Represents one model metric for one fold and repeat.

**Fields**:
- `model_id`
- `repeat`
- `fold`
- `metric`
- `value`
- `primary_metric`
- `threshold`
- `notes`

**Validation rules**:
- AUPRC, recall at fixed precision, and Brier score are present for every trained model/fold
  where estimable.
- AUROC is marked secondary when present.
- Accuracy is not marked primary.
- Degenerate metrics are marked unavailable with notes rather than fabricated.

## MetricSummary

Represents aggregate metrics across fold/repeat values.

**Required columns**:
- `model_id`
- `metric`
- `mean`
- `sd`
- `ci_lower`
- `ci_upper`
- `n_folds`
- `n_repeats`
- `primary_metric`
- `notes`

**Validation rules**:
- Mean and standard deviation use available fold/repeat metric values.
- Bootstrap CIs resample available fold/repeat values by model and metric.
- CI fields are unavailable with notes when degenerate resamples prevent estimation.

## OperatingPoint

Represents threshold-specific alert and classification behavior.

**Required columns**:
- `model_id`
- `threshold`
- `precision`
- `recall`
- `specificity`
- `false_positive_rate`
- `alerts_per_100_participant_days`
- `number_needed_to_alert`
- `estimated_calls`

**Validation rules**:
- Confusion-derived values are tied to explicit thresholds.
- Selected-threshold rows record whether the configured precision target was met.
- Alert-burden fields use available participant follow-up denominators and are noted when
  denominators are approximate or unavailable.

## CalibrationRecord

Represents calibration diagnostics for one model and optional fold.

**Fields**:
- `model_id`
- `repeat`
- `fold`
- `brier`
- `calibration_intercept`
- `calibration_slope`
- `expected_calibration_error`
- `estimable`
- `notes`

**Validation rules**:
- Brier score is reported wherever predictions and labels are available.
- Calibration intercept/slope are reported only where estimable.
- ECE is reported when implemented and otherwise marked unavailable.

## ExplanationRecord

Represents optional global or local explanation output.

**Fields**:
- `model_id`
- `explanation_type`
- `participant_id`
- `observation_id`
- `feature`
- `value`
- `rank`
- `notes`

**Validation rules**:
- Feature importance is written only when supported by the model/pipeline.
- Local explanations are written only when a conforming method is available.
- Unavailable explanations are documented in summary notes.

## BakeoffSummary

Represents the JSON audit summary for one run.

**Fields**:
- `run_started_at`
- `seed`
- `data_dir`
- `out_dir`
- `synthetic_detected`
- `n_participants`
- `n_events`
- `enabled_models`
- `primary_metrics`
- `warnings`
- `limitations`
- `artifact_paths`

**Validation rules**:
- Synthetic runs include signal-characterization and non-clinical-validation language.
- Warnings include fold reductions, unavailable features, degenerate metrics, and unmet
  precision targets.
- Artifact paths are relative to the requested output directory where possible.
