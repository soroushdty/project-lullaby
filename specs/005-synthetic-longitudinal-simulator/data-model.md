---
id: PLAN-005-DATA-MODEL
title: Synthetic Longitudinal Physiologic Data Simulator Data Model
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-005, PLAN-005]
implements: [P2, P3, P5, P7, P8, P9]
supersedes: null
superseded_by: null
related: [SPEC-001, SPEC-004, SPEC-006, SPEC-007, SPEC-008]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Data Model: Synthetic Longitudinal Physiologic Data Simulator

## SimulationConfig

Effective configuration for one generation run.

**Fields**:
- `seed`: integer root seed
- `n_participants`: participant count
- `study_days`: number of participant-day rows per participant
- `output_dir`: default `data/synthetic/longitudinal`
- `event_rate`: target rates for `cv_event`, `heat_illness`, `ed_visit`, `hospitalization`
- `summer_heat`: heat season settings with F scenario defaults and C export conversion
- `adherence`: initial wear hours, weekly decline, scale-use probability and decline
- `missingness`: random cell rate, dropout rate, clustered gap probability, heat gap multiplier
- `physiology`: CV slopes, heat spikes, and body-water effects
- `alerts`: threshold config path plus survey and call completion probabilities
- `archetypes`: named `ArchetypeConfig` entries

**Validation rules**:
- `seed`, `n_participants`, and `study_days` are required and positive.
- Default `study_days` is 84.
- Archetype weights are normalized when their raw sum is not 1.0.
- The effective normalized configuration is exported to `simulation_config_used.yaml`.

## ArchetypeConfig

Configurable participant behavior and risk pattern.

**Fields**:
- `name`
- `target_weight`
- `normalized_weight`
- `adherence_level`: `high`, `moderate`, `declining`, or `variable`
- `missingness_pattern`: `low_random`, `clustered_overnight_and_feeding`,
  `hot_afternoon_gaps`, `variable`, or `increasing_dropout`
- `physiologic_risk`: `low_to_moderate`, `moderate`, `heat_strain`, `cv_event`, or
  `gradual_cv_decline`

**Validation rules**:
- Default archetypes are diligent monitor, overwhelmed mom, heat stressed, true emergency,
  and silent decliner.
- Observed default proportions must match target weights within tolerance for default N=200.

## Participant

Synthetic postpartum participant profile.

**Fields**:
- `participant_id`
- `site_code`
- `enrollment_date`
- `delivery_date`
- `observation_start_date`
- `archetype`
- `baseline_cv_risk`
- `pih_severity`
- `has_ac`
- `gestational_diabetes`
- `health_literacy`
- `social_support`
- `depression`
- `anxiety`
- `synthetic_data`: true

**Relationships**:
- One participant has exactly `study_days` participant-day records.
- One participant has zero or more alerts and staff contacts.
- One participant has one clinical outcome summary record.

## EnvironmentDay

Calendar heat and exposure context.

**Fields**:
- `date`
- `study_day`
- `ambient_temp_c`
- `heat_index_c`
- `heat_wave`
- `heat_exposure_level`
- `synthetic_data`: true

**Validation rules**:
- Temperature and heat index are exported in Celsius.
- Heat season may be disabled, but the environment table remains schema-conforming.

## ParticipantDay

Latent and observed state for one participant on one study day.

**Fields**:
- `participant_id`
- `date`
- `study_day`
- `week`
- `archetype`
- `latent_cv_risk`
- `latent_heat_exposure`
- `latent_adherence_probability`
- `latent_missingness_probability`
- `dropout_active`
- `cv_event_window`
- `heat_strain_day`
- `overlap_day`
- `systolic_bp`
- `diastolic_bp`
- `heart_rate`
- `respiratory_rate`
- `skin_temperature_c`
- `weight_kg`
- `body_water_pct`
- `sleep_hours`
- `steps`
- `active_minutes`
- `sensor_wear_hours`
- `scale_used`
- `missingness_reasons`

**Validation rules**:
- Raw export uses one row per participant-day.
- Unobserved values remain null.
- Post-dropout participant-days remain present with null observed values and dropout metadata.
- CV cases with enough observed pre-event days must show positive seven-day body-water slope.
- Heat-strain days must show body-water decrease with HR/temp increase more often than not.

## Alert

Generated alert-like signal derived from participant-day physiology and configured thresholds.

**Fields**:
- `alert_id`
- `participant_id`
- `date`
- `alert_hour`
- `alert_level`: `yellow`, `red`, or `composite-red`
- `trigger_reasons`
- `classification`: `cv_like`, `heat_like`, `overlap`, or `other`
- `called_nurse`
- `survey_completed`
- `synthetic_data`: true

**Validation rules**:
- Alert IDs are deterministic and unique.
- Alert thresholds come from explicit safety-critical configuration.

## StaffContact

Generated follow-up contact or survey attempt.

**Fields**:
- `contact_id`
- `participant_id`
- `contact_date`
- `contact_type`: `survey`, `nurse_call`, or `follow_up`
- `contact_week`
- `completed`
- `reason`
- `related_alert_id`
- `synthetic_data`: true

## ClinicalOutcome

Participant-level outcome indicators and event dates.

**Fields**:
- `participant_id`
- `cv_event`
- `cv_event_type`
- `cv_event_date`
- `heat_illness`
- `heat_illness_date`
- `ed_visit`
- `hospitalized`
- `synthetic_data`: true

**Validation rules**:
- Observed event rates are compared to configured targets with cohort-size-aware tolerances.
- Outcome indicators align with participant-day latent event windows.

## RecruitmentRecord

Synthetic enrollment and cohort accounting context.

**Fields**:
- `participant_id`
- `recruitment_date`
- `recruitment_source`
- `eligible`
- `enrolled`
- `decline_reason`
- `synthetic_data`: true

## SimulationSummary

Run-level readiness and diagnostics artifact.

**Fields**:
- `status`: `pass`, `warn`, or `fail`
- `ready_for_downstream`: boolean
- `seed`
- `n_participants`
- `study_days`
- `output_dir`
- `schema_validation_status`
- `target_checks`: list of `DiagnosticCheck`
- `warnings`
- `errors`
- `generated_at_utc`: allowed metadata timestamp
- `synthetic_data`: true

**Validation rules**:
- Required schema or target failures set `status=fail` and `ready_for_downstream=false`.
- Failed runs still preserve generated artifacts for inspection.
- Each target check records target, observed, tolerance, denominator, and pass/fail status.

## State Transitions

### Generation Run

1. `configured`
2. `participants_assigned`
3. `environment_generated`
4. `participant_days_generated`
5. `missingness_applied`
6. `events_and_alerts_derived`
7. `artifacts_exported`
8. `schema_validated`
9. `diagnostics_evaluated`
10. `ready` or `failed_not_ready`

**Transition rules**:
- `schema_validated -> failed_not_ready` when required schema validation fails.
- `diagnostics_evaluated -> failed_not_ready` when required target diagnostics miss tolerance.
- Failed runs keep artifacts and summary available.
