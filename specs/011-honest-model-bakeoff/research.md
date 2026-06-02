---
id: RESEARCH-011
title: Honest Model Bake-off Under Severe Class Imbalance Research
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

# Research: Honest Model Bake-off Under Severe Class Imbalance

## Decision: Add A Dedicated Modeling Package

**Decision**: Implement SPEC-011 under `src/modeling/` with a thin script wrapper at
`scripts/run_model_bakeoff.py`.

**Rationale**: Modeling has separate concerns from visualization: grouped CV, fold-local
pipelines, metrics, calibration, and artifact writing. A dedicated package keeps those
contracts testable without turning EDA modules into model orchestration code.

**Alternatives considered**:
- Put modeling in `src/visualization/`: rejected because the bake-off is not a figure
  generator and must avoid mixing descriptive EDA with prediction.
- Put all logic in one script: rejected because the required tests target splits,
  resampling, metrics, and outputs independently.

## Decision: Use scikit-learn For Core Estimators And Pipelines

**Decision**: Add scikit-learn as a runtime dependency and use it for logistic regression,
random forest, gradient boosting, MLP, preprocessing pipelines, and metric primitives.

**Rationale**: SPEC-011 requires random forest, gradient boosting, and MLP-style models.
scikit-learn provides deterministic seeded estimators, pipelines, imputation, scaling, and
well-tested metric functions without introducing a deep-learning framework for this MVP.

**Alternatives considered**:
- Hand-roll estimators: rejected because it increases correctness risk and weakens metric
  reproducibility.
- Add PyTorch/TensorFlow now: rejected because the sequence tensor model is explicitly
  disabled until implemented and testable.
- Add imbalanced-learn: rejected for the default plan because `resampling: none` is the
  configured default; non-default resampling can be added as a fold-local extension later.

## Decision: Build Participant-Level Features By Default

**Decision**: Build one modeling row per participant with `observation_id == participant_id`
and target `outcome.cv_event`.

**Rationale**: The clarified spec names participant-level modeling as the primary unit and
the config enables daily-vitals summaries rather than sequence tensors. This keeps grouped
CV exact: each participant contributes one row to exactly one validation fold per repeat.

**Alternatives considered**:
- Participant-day rows: rejected for SPEC-011 because the target window definition would
  require additional temporal labeling choices and repeated observations per participant.
- Support both modes in the first implementation: rejected because participant-level output
  is enough to satisfy acceptance and reduces leakage risk.

## Decision: Apply The Leakage Guard During Feature Aggregation

**Decision**: For event participants, summarize longitudinal vitals, alerts, and environment
only from observations strictly before `cv_event_date - leakage_guard_days_before_event`.
For non-event participants, use the full observed window.

**Rationale**: The target is a participant-level outcome, so post-event observations would
leak information about the event. Applying the guard before feature aggregation makes the
rule auditable and testable.

**Alternatives considered**:
- Use all observations: rejected because post-event data can leak outcome information.
- Use a fixed landmark window for everyone: rejected because the spec selected pre-event
  truncation and full non-event windows.

## Decision: Repeated Grouped Stratified Splits With Deterministic Fallbacks

**Decision**: Use repeated grouped stratified fold assignment where each participant group is
kept intact and event-label balance is approximated across folds. If class counts cannot
support requested splits, reduce to the maximum valid split count or mark the condition
unavailable while preserving group isolation.

**Rationale**: Participant leakage is the top validity risk. Stratification is important but
secondary to group isolation under severe imbalance.

**Alternatives considered**:
- Plain StratifiedKFold: rejected because it can split participant records across folds in
  future observation-level modes.
- Plain GroupKFold without stratification: rejected because positive events can concentrate
  in too few folds under severe imbalance.

## Decision: Use Fold-Local sklearn Pipelines

**Decision**: Each model is fit through a fold-local pipeline containing imputation,
optional scaling, estimator fitting, and any future resampling/feature selection extension.

**Rationale**: Pipelines make it natural to fit preprocessing on training rows only and then
apply it to validation rows without mutating raw dataframes.

**Alternatives considered**:
- Precompute imputed features globally: rejected because it leaks validation distribution.
- Let each model handle raw missing values ad hoc: rejected because MLP and logistic
  regression need consistent preprocessing and tests need one fold-local contract.

## Decision: Thresholds Are Selected Inside Training Folds

**Decision**: For `threshold_selection: inner_cv`, choose the threshold inside the training
fold that maximizes recall subject to configured minimum precision. Break ties by higher
precision, then higher threshold. If no threshold meets the precision target, choose the
highest-precision threshold, breaking ties by higher recall then higher threshold, and mark
the target unmet.

**Rationale**: This aligns selected-threshold predictions with the primary recall-at-fixed-
precision metric while preventing outer validation labels from influencing thresholds.

**Alternatives considered**:
- Default threshold 0.50: rejected because probability calibration differs by model and the
  spec requires explicit selected thresholds.
- F1 optimization: rejected because it ignores the fixed-precision safety constraint.

## Decision: Bootstrap Metric Summary CIs Over Fold/Repeat Values

**Decision**: Compute `metrics_summary.csv` confidence intervals by bootstrap-resampling the
available fold/repeat metric values per model and metric.

**Rationale**: `metrics_summary.csv` summarizes `metrics_by_fold.csv`; bootstrapping those
values keeps the CI source aligned with the reported mean, standard deviation, fold count,
and repeat count.

**Alternatives considered**:
- Participant-level prediction bootstrap: rejected because it estimates a different target
  and complicates grouped repeated-CV dependence.
- Analytic normal intervals only: rejected because severe imbalance can make metric
  distributions non-normal.

## Decision: Write All Required Artifacts As Simple Local Files

**Decision**: Write CSV files for tabular predictions, metrics, calibration, operating
points, decision curve, and explanations; write YAML for the used config; write JSON for the
summary.

**Rationale**: File artifacts match the spec, are easy for tests to inspect, and keep the
workflow offline and clone-to-run.

**Alternatives considered**:
- Store results in a database: rejected because the repo uses local artifact conventions.
- Generate a model report only: rejected because acceptance criteria require specific file
  schemas.

## Decision: Explanations Are Best-Effort And Explicitly Optional

**Decision**: Emit `feature_importance.csv` for models with native or derived global feature
importance, and emit `local_explanations.csv` only when a lightweight conforming method is
available. Otherwise, record unavailability in notes.

**Rationale**: The spec marks explanation artifacts conditional. Fabricating local
explanations would be worse than transparently marking them unavailable.

**Alternatives considered**:
- Add SHAP now: rejected because it is a new heavyweight dependency not required for
  acceptance.
- Require every model to expose explanations: rejected because MLP and calibrated pipelines
  may not expose stable feature importances.

## Decision: Frame Outputs As Signal Characterization

**Decision**: `bakeoff_summary.json` and metric notes must include synthetic-data or
exploratory signal-characterization language when the input data indicate synthetic status or
the data directory is the bundled synthetic path.

**Rationale**: P7 and P9 require honest limitations and synthetic-data transparency. The
model bake-off must not imply validated clinical performance.

**Alternatives considered**:
- Put limitations only in documentation: rejected because artifact consumers may inspect
  outputs without reading the spec.
- Suppress model comparisons on synthetic data: rejected because synthetic bake-off is a
  required acceptance path.
