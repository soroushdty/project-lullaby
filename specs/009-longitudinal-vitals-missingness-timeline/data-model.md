---
id: DATA-009
title: Longitudinal Vitals, Missingness, Signal Quality, and Patient Timeline Data Model
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-009, SPEC-001, SPEC-004, SPEC-007]
implements: [P3, P5, P7, P10]
supersedes: null
superseded_by: null
related: [SPEC-004, SPEC-005, SPEC-006, SPEC-007]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Data Model: Longitudinal Vitals, Missingness, Signal Quality, and Patient Timeline

## LongitudinalEDATables

Represents the canonical table bundle used by a longitudinal dashboard run.

**Fields**:
- `data_dir`: caller-supplied input path
- `resolved_data_dir`: actual directory used after default fallback resolution
- `participants`: canonical participants table, optional for Panel 5 and required for Panels 7
  and 9
- `daily_vitals`: canonical participant-day vitals table
- `alerts`: canonical alert table, optional for Panels 5 and 6 and required for Panel 7
- `staff_contacts`: canonical staff contact table
- `clinical_outcomes`: canonical participant outcome table, optional for Panel 5 and required
  for Panel 7
- `environment`: optional environment table
- `load_warnings`: optional table or role warnings collected during loading

**Validation rules**:
- Required panel tables must exist before affected artifacts are written.
- Required semantic roles for requested panels must resolve before affected artifacts are
  written.
- Optional table or role absence is recorded as a warning and rendered visibly where relevant.
- Required boolean-like roles use shared semantic parsing.

## LongitudinalEDAPanel

Represents one required dashboard artifact in the longitudinal panel set.

**Fields**:
- `panel_id`: stable logical identifier
- `artifact_id`: manifest artifact identifier
- `filename`: required PNG filename
- `title`: dashboard title
- `required_entities`
- `optional_entities`
- `required_roles`
- `optional_roles_used`
- `warnings`
- `metadata`

**Validation rules**:
- Output path is repo-relative for default manifest registration.
- Saved image is at least 1600 x 900 pixels.
- Title, subtitle, labels, units where available, and direct annotations are present.
- Missing values are explicit and are never imputed.

## SelectedParticipantContext

Represents the participant used for static participant-focused rendering.

**Fields**:
- `participant_id`
- `selection_mode`: `provided` or `automatic`
- `observed_vital_days`
- `distinct_alert_days`
- `distinct_outcome_events`
- `observed_vital_variable_count`
- `selection_score`
- `tie_breakers_applied`

**Validation rules**:
- Supplied participant ids must exist in at least one required participant-scoped table for the
  affected panel.
- Automatic selection is deterministic and uses the clarified score rule.
- Selected participant context is recorded in the manifest for Panel 5 and Panel 7.

## VitalTrajectoryPanel

Panel 5 artifact showing cohort aggregate and selected-participant vital trajectories.

**Required entities and roles**:
- `daily_vitals`
- `vital.participant_id`
- `vital.date`
- `vital.systolic_bp`

**Optional roles and entities**:
- `vital.study_day`
- `vital.week`
- `vital.diastolic_bp`
- `vital.heart_rate`
- `vital.respiratory_rate`
- `vital.skin_temperature_c`
- `vital.weight_kg`
- `vital.body_water_pct`
- `vital.sleep_hours`
- `vital.steps`
- `vital.sensor_wear_hours`
- `vital.scale_used`
- optional `participants`
- optional `alerts`
- optional `clinical_outcomes`
- optional `environment`

**Derived fields**:
- `study_day`
- `study_week`
- `observed_day_denominator`
- `cohort_aggregate_series`
- `selected_participant_series`
- `missing_day_gaps`
- `environment_overlay_series`

**Validation rules**:
- Week filters are inclusive 1-based study-week filters.
- Missing days render as gaps, not interpolated values.
- Cohort aggregate calculations use observed values only and include observed denominators.
- Environment overlay renders only when requested and available.

## MissingnessAdherencePanel

Panel 6 artifact showing participant-day presence, wear, scale adherence, variable missingness,
and gap patterns.

**Required entities and roles**:
- `daily_vitals`
- `vital.participant_id`
- `vital.date`
- `staff_contacts`
- `contact.type`

**Optional roles and entities**:
- `vital.study_day`
- `vital.sensor_wear_hours`
- `vital.scale_used`
- `alert.participant_id`
- `alert.date`
- `alert.hour`
- optional `alerts`

**Derived fields**:
- `participant_day_matrix`
- `wear_hours_by_day`
- `scale_adherence_by_day`
- `adherence_decline_summary`
- `missingness_by_variable`
- `gap_cluster_summary`
- `display_downsample_metadata`

**Validation rules**:
- Missing and present states are explicit through labels, legends, symbols, or patterns.
- Participant matrix display rows are downsampled deterministically above 250 participants.
- Metrics use all participants even when display rows are downsampled.
- Gap clustering is unavailable, not guessed, when timestamps or proxies are absent.

## PatientTimelinePanel

Panel 7 artifact showing one participant's aligned longitudinal record.

**Required entities and roles**:
- `participants`, `participant.id`
- `daily_vitals`, `vital.participant_id`, `vital.date`, `vital.systolic_bp`
- `alerts`, `alert.participant_id`, `alert.date`, `alert.level`
- `staff_contacts`, `contact.participant_id`, `contact.date`, `contact.type`
- `clinical_outcomes`, `outcome.participant_id`, `outcome.cv_event`, `outcome.cv_event_date`

**Optional roles and entities**:
- Other vital roles listed for Panel 5
- `alert.trigger_reasons`
- `contact.completed`
- `outcome.cv_event_type`
- `participant.pih_severity`
- `participant.has_ac`
- `participant.health_literacy`
- `participant.social_support`
- `participant.depression`
- `participant.anxiety`
- Optional participant context columns or roles for insurance and parity
- optional `environment`

**Derived fields**:
- `selected_participant_context`
- `aligned_study_day_axis`
- `vital_tracks`
- `event_markers`
- `missingness_wear_track`
- `summary_card_fields`
- `capture_worthy_extreme_labels`

**Validation rules**:
- Timeline fits on one dashboard page.
- All tracks align on the same study-day x-axis.
- Vital gaps remain gaps.
- Clinical thresholds or reference bands render only when available.
- Summary card omits no available required context silently; absent optional fields are marked
  unavailable.

## DataQualityScorecard

Panel 8 artifact ranking participants by completeness and signal quality.

**Required entities and roles**:
- `daily_vitals`
- `vital.participant_id`
- `vital.date`
- `staff_contacts`
- `contact.type`

**Optional roles**:
- `vital.study_day`
- `vital.sensor_wear_hours`
- `vital.scale_used`
- `contact.participant_id`
- `contact.date`
- `contact.completed`

**Derived fields**:
- `wear_completeness`
- `scale_adherence`
- `vital_completeness`
- `contact_traceability`
- `valid_signal_hours`
- `gap_count`
- `gap_duration_days`
- `quality_score`
- `adjusted_formula`

**Validation rules**:
- Each score component is normalized to 0-1 against the participant's expected observed
  study-day denominator when available.
- Components with no valid denominator are unavailable rather than zero.
- Missing component weights are redistributed proportionally across available components.
- Ranking is by completeness and signal quality, not clinical risk.

## MissingnessMechanismDiagnostics

Panel 9 artifact showing exploratory missingness mechanism evidence.

**Required entities and roles**:
- `participants`, `participant.id`
- `daily_vitals`, `vital.participant_id`, `vital.date`, `vital.systolic_bp`

**Optional roles and entities**:
- `vital.study_day`
- other vital roles listed for Panel 5
- `participant.pih_severity`
- `participant.has_ac`
- `participant.health_literacy`
- optional participant context columns or roles for archetype and insurance
- optional `environment`
- optional `clinical_outcomes`

**Derived fields**:
- `missingness_rate_by_study_day`
- `missingness_by_participant_context`
- `missingness_by_heat_exposure`
- `missingness_after_recent_abnormal_vitals`
- `exploratory_mechanism_labels`

**Validation rules**:
- Diagnostics are labeled as exploratory signals consistent with MCAR, MAR, or MNAR
  hypotheses.
- No imputation is performed.
- Missing optional stratifiers are shown as unavailable and recorded in warnings.

## LongitudinalManifestEntry

Represents one generated longitudinal dashboard entry in `outputs/figures/manifest.json`.

**Fields**:
- `artifact_id`
- `path`
- `title`
- `spec`
- `inputs`
- `required_roles`
- `optional_roles_used`
- `warnings`
- `metadata`
- `created_at_utc`
- `deterministic`

**Validation rules**:
- `path` is repository-relative.
- `spec` references `SPEC-009` for longitudinal dashboard artifacts.
- Duplicate artifact ids are upserted only when metadata intentionally replaces the previous
  run output.
- `metadata` stores selected participant context, week filters, overlay state, downsampling
  metadata, adjusted quality formulas, and diagnostic caveats where applicable.
