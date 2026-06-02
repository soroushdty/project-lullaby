---
id: CONTRACT-011-ARTIFACTS
title: Modeling Bake-off Artifact Contract
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-011]
implements: [P7, P8]
supersedes: null
superseded_by: null
related: [CONTRACT-011-CLI]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Contract: Modeling Bake-off Artifacts

## Required Files

The bake-off writes these files under the requested output directory:

```text
predictions_oof.csv
predictions_by_fold.csv
metrics_by_fold.csv
metrics_summary.csv
operating_points.csv
calibration_table.csv
decision_curve.csv
bakeoff_config_used.yaml
bakeoff_summary.json
```

`feature_importance.csv` and `local_explanations.csv` are written only when available.

## `predictions_oof.csv`

Required columns:

```text
participant_id,observation_id,fold,repeat,model_id,y_true,y_score,y_pred_default_threshold,y_pred_selected_threshold,selected_threshold
```

Contract:
- One row per out-of-fold participant prediction per model, repeat, and fold.
- `observation_id` defaults to `participant_id`.
- `y_score` is numeric and bounded in `[0, 1]`.
- `y_pred_default_threshold` uses threshold `0.50`.
- `y_pred_selected_threshold` uses the fold-local selected threshold or documented fallback.
- Row order is deterministic.

## `predictions_by_fold.csv`

Contract:
- Contains at least the `predictions_oof.csv` columns.
- May include fold-local notes such as `threshold_target_met`, `fit_status`, and
  `unavailable_reason`.
- Preserves fold and repeat identity for debugging and leakage audits.

## `metrics_by_fold.csv`

Required minimum columns:

```text
model_id,repeat,fold,metric,value,primary_metric,threshold,notes
```

Contract:
- Includes AUPRC, recall at fixed precision, and Brier score for every estimable trained
  model/fold.
- AUROC is secondary when present.
- Accuracy is not marked as primary.
- Degenerate or unavailable values carry notes.

## `metrics_summary.csv`

Required columns:

```text
model_id,metric,mean,sd,ci_lower,ci_upper,n_folds,n_repeats,primary_metric,notes
```

Contract:
- Summarizes available fold/repeat metric values.
- Bootstrap CIs resample fold/repeat values per model and metric.
- CI fields are blank or unavailable only with explanatory notes.

## `operating_points.csv`

Required columns:

```text
model_id,threshold,precision,recall,specificity,false_positive_rate,alerts_per_100_participant_days,number_needed_to_alert,estimated_calls
```

Contract:
- Every row corresponds to an explicit threshold.
- Selected-threshold rows record whether the configured precision target was met in notes or
  supplemental columns.
- Alert-burden denominators are documented when approximate.

## `calibration_table.csv`

Required minimum columns:

```text
model_id,repeat,fold,brier,calibration_intercept,calibration_slope,expected_calibration_error,estimable,notes
```

Contract:
- Brier score is reported wherever predictions are available.
- Calibration intercept/slope are populated only where estimable.
- ECE is populated if implemented and otherwise marked unavailable.

## `decision_curve.csv`

Required minimum columns:

```text
model_id,threshold,net_benefit,notes
```

Contract:
- Threshold values are explicit.
- Decision-curve values are exploratory and not clinical deployment guidance.

## `bakeoff_config_used.yaml`

Contract:
- Contains the effective configuration after CLI overrides.
- Includes seed, CV settings, feature toggles, imbalance settings, metric settings, and model
  enablement.

## `bakeoff_summary.json`

Required keys:

```text
seed,data_dir,out_dir,synthetic_detected,n_participants,n_events,enabled_models,primary_metrics,warnings,limitations,artifact_paths
```

Contract:
- Synthetic runs include non-clinical-validation limitations.
- Warnings include unavailable optional features, fold reductions, degenerate metrics, and
  unmet precision targets.
- Artifact paths match files written under the output directory.
