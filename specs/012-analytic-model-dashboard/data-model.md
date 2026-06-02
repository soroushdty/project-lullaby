---
id:            DATA-MODEL-012
title:         Analytic Dashboard for Model Outputs — Data Model
status:        complete
version:       0.1.0
created:       2026-06-01
updated:       2026-06-01
author:        Soroush Dianaty
related:       [PLAN-012, SPEC-012, SPEC-011]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Data Model: Analytic Dashboard for Model Outputs

## Input Artifacts (read-only, produced by SPEC-011)

### `predictions_oof.csv`

| Column | Type | Notes |
|--------|------|-------|
| `participant_id` | str | unique participant identifier |
| `observation_id` | str | defaults to participant_id in participant-level mode |
| `fold` | int | outer CV fold index |
| `repeat` | int | CV repeat index |
| `model_id` | str | candidate model name |
| `y_true` | int (0/1) | true event label |
| `y_score` | float | predicted probability-like score |
| `y_pred_default_threshold` | int (0/1) | prediction at model default threshold |
| `y_pred_selected_threshold` | int (0/1) | prediction at selected operating threshold |
| `selected_threshold` | float | threshold value used for selected-threshold column |

Optional columns used by Panels 6, 7, 9 (absent → affected panel renders unavailable or warning state):

| Column | Panel | Notes |
|--------|-------|-------|
| `body_water_direction` | 6 | categorical: rising / falling / stable |
| `bp_trend` | 6 | categorical |
| `hr_trend` | 6 | categorical |
| `skin_temp_trend` | 6 | categorical |
| `heat_index_c` | 6 | float, optional environment proxy |
| `days_before_event` | 7 | int; rows with this column are the lead-time cohort |
| `race_ethnicity` | 9 | categorical |
| `insurance` | 9 | categorical |
| `ac_access` | 9 | bool / categorical |
| `health_literacy` | 9 | categorical |

---

### `metrics_summary.csv`

| Column | Type | Notes |
|--------|------|-------|
| `model_id` | str | |
| `metric` | str | e.g. `auprc`, `recall_at_precision`, `brier`, `auroc` |
| `mean` | float | |
| `sd` | float | |
| `ci_lower` | float | bootstrap CI lower bound |
| `ci_upper` | float | bootstrap CI upper bound |
| `n_folds` | int | |
| `n_repeats` | int | |
| `primary_metric` | bool | True for AUPRC, recall_at_precision, brier |
| `notes` | str | nullable |

---

### `metrics_by_fold.csv`

| Column | Type | Notes |
|--------|------|-------|
| `model_id` | str | |
| `fold` | int | |
| `repeat` | int | |
| `metric` | str | |
| `value` | float | |
| `notes` | str | nullable |

---

### `calibration_table.csv`

| Column | Type | Notes |
|--------|------|-------|
| `model_id` | str | |
| `bin_lower` | float | calibration bin lower edge |
| `bin_upper` | float | calibration bin upper edge |
| `n_observations` | int | samples in bin |
| `observed_fraction` | float | empirical positive rate in bin |
| `mean_predicted` | float | mean predicted score in bin |
| `brier_score` | float | model-level; repeated per row or in summary row |
| `calibration_intercept` | float | nullable |
| `calibration_slope` | float | nullable |
| `notes` | str | nullable |

**Sparsity rule**: Panel 2 switches to sparse-data warning when `n_non_empty_bins < 3` or `min(n_observations where n_observations > 0) < 10`.

---

### `decision_curve.csv`

| Column | Type | Notes |
|--------|------|-------|
| `model_id` | str | |
| `threshold` | float | probability threshold |
| `net_benefit` | float | model net benefit |
| `net_benefit_treat_all` | float | nullable |
| `net_benefit_treat_none` | float | always 0.0 |

---

### `operating_points.csv`

| Column | Type | Notes |
|--------|------|-------|
| `model_id` | str | |
| `threshold` | float | |
| `precision` | float | |
| `recall` | float | |
| `specificity` | float | |
| `false_positive_rate` | float | |
| `alerts_per_100_participant_days` | float | |
| `number_needed_to_alert` | float | |
| `estimated_calls` | float | |

---

### `feature_importance.csv` (optional)

| Column | Type | Notes |
|--------|------|-------|
| `model_id` | str | |
| `feature` | str | |
| `importance` | float | |
| `method` | str | e.g. `shap`, `permutation`, `model_native` |

---

### `local_explanations.csv` (optional)

| Column | Type | Notes |
|--------|------|-------|
| `participant_id` | str | |
| `model_id` | str | |
| `feature` | str | |
| `shap_value` | float | or equivalent local attribution |
| `method` | str | |

---

### `learning_curve.csv` (optional, Panel 10)

| Column | Type | Notes |
|--------|------|-------|
| `model_id` | str | |
| `training_n` | int | number of training participants |
| `n_events` | int | number of positive-class training participants |
| `auprc_mean` | float | |
| `auprc_ci_lower` | float | |
| `auprc_ci_upper` | float | |
| `recall_at_precision_mean` | float | |
| `recall_at_precision_ci_lower` | float | |
| `recall_at_precision_ci_upper` | float | |

Panel 10 probes for `{model_dir}/learning_curve.csv`. Absent → explicit unavailable panel.

---

### `novelty_scores.csv` (optional, Panel 11)

| Column | Type | Notes |
|--------|------|-------|
| `participant_id` | str | unique participant identifier |
| `study_day` | int | day within participant observation window |
| `observation_date` | str | ISO-8601 date, nullable |
| `novelty_score` | float | higher = more anomalous |
| `source_description` | str | human-readable label of the contributing signal, nullable |

Panel 11 probes for `{model_dir}/novelty_scores.csv`. Absent → explicit unavailable panel. High-score points are labeled "capture-worthy" in all rendered text.

**Sparsity rule**: No sparsity gate. All rows are rendered; the panel title states the number of observations shown.

---

### `bakeoff_summary.json`

Key fields consumed by model card generator:

| Field | Type | Notes |
|-------|------|-------|
| `data_source` | str | `"synthetic"` triggers synthetic-data caveat |
| `seed` | int | |
| `run_timestamp` | str | ISO-8601 |
| `models_trained` | list[str] | |
| `n_participants` | int | |
| `n_events` | int | |

---

### `bakeoff_config_used.yaml`

Passed verbatim into the model card as the reproducibility section. Must exist for a complete card; absent → model card notes the missing config file.

---

## Cost Configuration (`config/costs.yaml`)

```yaml
currency: USD
nurse_hotline:
  cost_per_call: float
  minutes_per_call: int
  nurse_hourly_cost: float
alert_workflow:
  survey_review_minutes: int
  false_positive_call_probability: float
  true_positive_call_probability: float
volume_assumptions:
  participants: int
  participant_days: int
  alerts_to_calls_multiplier: float
sensitivity:
  cost_per_call: list[float]
  false_positive_call_probability: list[float]
```

Absent file → Panel 4 renders unavailable/error panel; CLI exits 0.

---

## Output Artifacts

### Panel PNGs (`outputs/figures/analytic/`)

| File | Required | Fallback |
|------|----------|---------|
| `01_model_leaderboard.png` | Yes | n/a (requires `metrics_summary.csv`) |
| `02_calibration_decision_curve.png` | Yes | unavailable if both source files missing |
| `03_threshold_explorer.png` | Yes | unavailable if `operating_points.csv` missing |
| `04_alarm_cost.png` | Yes | unavailable/error if `costs.yaml` absent |
| `05_explainability.png` | Yes | unavailable if no explanation files |
| `06_cv_vs_heat_discrimination.png` | Yes | unavailable if trajectory columns absent |
| `07_lead_time_analysis.png` | Yes | unavailable if no event records |
| `08_grouped_cv_variance.png` | Yes | unavailable if fold/repeat columns missing |
| `09_subgroup_fairness_audit.png` | Yes | unavailable if subgroup columns absent |
| `10_label_efficiency_learning_curve.png` | Yes | unavailable if `learning_curve.csv` absent |
| `11_novelty_anomaly_view.png` | Yes | unavailable if `novelty_scores.csv` absent |

All PNGs: minimum 1600 × 900 px, `"type": "analytic"` in manifest.

### `model_card_tripod_ai.md`

Generated by `model_cards.py`. Registered in manifest as `"type": "analytic"`.

---

## Manifest Entry Schema (analytic)

Each SPEC-012 entry in `outputs/figures/manifest.json`:

```json
{
  "path": "outputs/figures/analytic/01_model_leaderboard.png",
  "type": "analytic",
  "panel": 1,
  "width_px": 1920,
  "height_px": 1080,
  "available": true,
  "warning": null
}
```

Unavailable panel entry:

```json
{
  "path": "outputs/figures/analytic/10_label_efficiency_learning_curve.png",
  "type": "analytic",
  "panel": 10,
  "width_px": 1600,
  "height_px": 900,
  "available": false,
  "warning": "learning_curve.csv not found in model_dir; re-run bake-off with learning-curve generation enabled"
}
```
