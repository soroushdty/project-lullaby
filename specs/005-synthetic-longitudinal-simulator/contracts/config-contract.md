---
id: CONTRACT-005-CONFIG
title: Synthetic Simulator Configuration Contract
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-005, PLAN-005]
implements: [P2, P8, P9]
supersedes: null
superseded_by: null
related: [SPEC-001, SPEC-004]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Contract: Synthetic Simulator Configuration

## Default File

`config/simulation.yaml`

## Required Defaults

```yaml
seed: 20260601
n_participants: 200
study_days: 84
event_rate:
  cv_event: 0.075
  heat_illness: 0.05
  ed_visit: 0.10
  hospitalization: 0.04
summer_heat:
  enabled: true
  start_date: "2026-06-01"
  baseline_temp_f: 94
  heat_wave_probability: 0.20
  heat_wave_temp_f: 108
  heat_index_noise_sd: 4
adherence:
  initial_wear_hours_mean: 18
  weekly_decline_hours: 0.8
  scale_initial_probability: 0.85
  scale_weekly_decline: 0.08
missingness:
  random_cell_missing_rate: 0.03
  participant_dropout_rate: 0.08
  clustered_gap_probability: 0.15
  hot_afternoon_gap_multiplier: 2.0
physiology:
  cv_bp_slope_per_day: [0.6, 1.4]
  cv_hr_slope_per_day: [0.2, 0.8]
  cv_body_water_slope_per_day: [0.05, 0.20]
  heat_hr_spike: [10, 28]
  heat_skin_temp_spike_f: [1.0, 4.0]
  heat_body_water_drop: [0.3, 1.5]
alerts:
  meows_thresholds_path: config/meows_thresholds.synthetic.yaml
  survey_completion_probability: 0.65
  call_completion_probability: 0.55
```

## Required Archetypes

| Archetype | Weight | Adherence | Missingness | Physiologic Risk |
|-----------|--------|-----------|-------------|------------------|
| `diligent_monitor` | 0.30 | high | low_random | low_to_moderate |
| `overwhelmed_mom` | 0.30 | declining | clustered_overnight_and_feeding | moderate |
| `heat_stressed` | 0.15 | moderate | hot_afternoon_gaps | heat_strain |
| `true_emergency` | 0.06 | variable | variable | cv_event |
| `silent_decliner` | 0.14 | declining | increasing_dropout | gradual_cv_decline |

## Validation Rules

- Unknown top-level keys are warnings, not failures, unless they collide with required names.
- Missing required sections are config errors.
- Negative rates, probabilities outside `[0, 1]`, and non-positive participant/study sizes are
  config errors.
- Archetype weights are normalized and the effective normalized values are exported.
- Fahrenheit heat settings are accepted in config, but table exports use Celsius.
