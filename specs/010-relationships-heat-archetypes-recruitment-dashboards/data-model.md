---
id: DATA-010
title: Relationships, Heat Exposure, Archetypes, and Recruitment Dashboards Data Model
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-010, SPEC-001, SPEC-004, SPEC-007, SPEC-009]
implements: [P3, P5, P7, P10]
supersedes: null
superseded_by: null
related: [SPEC-004, SPEC-005, SPEC-006, SPEC-007, SPEC-009]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Data Model: Relationships, Heat Exposure, Archetypes, and Recruitment Dashboards

## RelationshipEDATables

Represents the canonical table bundle used by a SPEC-010 dashboard run.

**Fields**:
- `data_dir`: caller-supplied input path
- `resolved_data_dir`: actual directory used after default fallback resolution
- `participants`: canonical participants table
- `daily_vitals`: canonical participant-day vitals table with derived `__study_day` where
  needed
- `clinical_outcomes`: optional participant outcome table
- `environment`: optional calendar-day environment table
- `recruitment`: optional recruitment table
- `alerts`: optional alert table for archetype alert burden
- `load_warnings`: optional table or role warnings collected during loading

**Validation rules**:
- Required panel-set tables (`participants`, `daily_vitals`) must exist before requested
  SPEC-010 artifacts are written.
- Required semantic roles must resolve before requested artifacts are written.
- Optional table or role absence is recorded as a warning and rendered visibly where relevant.
- Required boolean-like roles use shared semantic parsing.

## RelationshipPanelResult

Represents one required dashboard artifact in the SPEC-010 panel set.

**Fields**:
- `artifact_id`
- `path`
- `title`
- `warnings`
- `metadata`

**Validation rules**:
- Output path is repo-relative for default manifest registration.
- Saved image is at least 1600 x 900 pixels.
- Title, subtitle, labels, units where available, and direct annotations are present.
- Missing values are explicit and are never imputed.

## RelationshipsDashboard

Panel 10 artifact showing descriptive correlations, targeted bivariate views, and
CV-vs-heat discriminator counts.

**Required entities and roles**:
- `daily_vitals`
- `vital.participant_id`
- `vital.date`
- `vital.systolic_bp`

**Optional roles and entities**:
- Other numeric vital roles including DBP, HR, RR, skin temperature, weight, body water,
  sleep, steps, and active minutes
- Optional `environment.heat_index_c`
- Optional `vital.heat_index_c` as Panel 10-only proxy when environment is absent
- Optional `participants`
- Optional `clinical_outcomes`

**Derived fields**:
- `correlation_matrix`
- `pairwise_n_matrix`
- `body_water_delta`
- `vital_delta`
- `heat_index_source`
- `heat_index_pairwise_n`
- `cv_risk_like_intervals`
- `heat_strain_like_intervals`

**Validation rules**:
- Correlations and bivariate views use observed pairs only.
- Pairwise N is visible in the panel and stored in metadata.
- Daily-vitals heat-index proxy is labeled as a Panel 10-only proxy.
- Labels use schema registry labels and units.
- Correlations are descriptive and do not imply causality.

## HeatEnvironmentDashboard

Panel 11 artifact showing real environment coverage, heat trends, high-heat periods, AC
context, vital response summaries, and missing environment data.

**Required entities and roles for available-data rendering**:
- `environment`
- `environment.date` or `environment.study_day`
- `environment.ambient_temp_c` or `environment.heat_index_c`

**Optional roles and entities**:
- `environment.heat_wave`
- `environment.heat_exposure_level`
- `participants`
- `participant.has_ac`
- `daily_vitals`
- `vital.heart_rate`
- `vital.skin_temperature_c`

**Derived fields**:
- `environment_axis`
- `ambient_temperature_series`
- `heat_index_series`
- `high_heat_flag`
- `high_heat_definition`
- `environment_missingness_summary`
- `ac_access_strata`
- `vital_response_rows`

**Validation rules**:
- If no environment table exists, render an explicit unavailable panel.
- Panel 11 does not use daily-vitals heat columns as environment source data.
- High-heat definition follows the clarified fallback order.
- Missing environment rows and date gaps are explicitly summarized.
- Vital response summaries use observed daily-vitals rows aligned to observed environment
  rows.

## ArchetypeExplorer

Panel 12 artifact summarizing participant archetype segments and segment-level context.

**Required entities and roles**:
- `participants`
- `participant.id`
- `daily_vitals`
- `vital.participant_id`
- `vital.date`

**Optional roles and entities**:
- `participant.archetype`
- Daily-vitals `archetype` source labels
- `alerts`, `alert.participant_id`, `alert.level`
- `clinical_outcomes`
- `participant.has_ac`
- `participant.pih_severity`
- `vital.sensor_wear_hours`
- `vital.scale_used`
- Other vital roles used by provisional rules

**Derived fields**:
- `label_source`
- `canonical_archetype`
- `unknown_explicit_archetype_labels`
- `provisional_rule_summary`
- `provisional_priority_order`
- `segment_n`
- `adherence`
- `missingness`
- `alert_burden`
- `event_prevalence`
- `ac_access`
- `pih_severity`

**Validation rules**:
- Five canonical rows are present: diligent monitor, overwhelmed mom, heat-stressed, true
  emergency, silent decliner.
- Explicit labels are used when present.
- Known aliases normalize to canonical labels.
- Unknown explicit labels are preserved as additional rows and metadata.
- Provisional labels are visibly marked provisional and are not ground truth.
- Provisional rule conflicts resolve to one label by the clarified priority order.
- Alert burden is computed from optional alerts rows when available and is unavailable when
  alerts are absent.

## RecruitmentTimeline

Panel 13 artifact showing calendar-aware recruitment, enrollment, observation windows,
delivery dates, cumulative enrollment, heat overlay, and observation density.

**Required entities and roles**:
- `participants`
- `participant.id`

**Optional roles and entities**:
- `recruitment`
- `recruitment.participant_id`
- `recruitment.date`
- `recruitment.enrolled`
- `participant.enrollment_date`
- `participant.delivery_date`
- `participant.observation_start_date`
- `daily_vitals`, `vital.participant_id`, `vital.date`
- `environment`

**Derived fields**:
- `timeline_enrollment_date`
- `recruitment_source`
- `observation_start`
- `observation_end`
- `delivery_marker`
- `cumulative_enrollment`
- `observation_density`
- `heat_overlay`
- `display_downsample_metadata`

**Validation rules**:
- Recruitment table dates take precedence when present and parseable.
- Participant enrollment, observation, and daily-vitals date bounds provide fallback dates.
- If all date sources are missing or unparseable, render an unavailable panel and manifest
  warning.
- Heat overlay renders only from observed environment data.
- Display rows may be downsampled deterministically while metrics remain full-cohort.

## Manifest Metadata

Represents audit information that cannot fully fit in the static PNG.

**Fields**:
- `observed_data_policy`
- `pairwise_n`
- `heat_source`
- `high_heat_definition`
- `environment_available`
- `environment_data_fabricated`
- `environment_missingness`
- `label_source`
- `label_source_detail`
- `provisional`
- `rule_summary`
- `unknown_explicit_labels`
- `recruitment_source`
- `calendar_aware`
- `display_downsampled`

**Validation rules**:
- Metadata must be JSON-serializable.
- Metadata must distinguish explicit and provisional archetype labels.
- Metadata must identify unavailable panels and optional-data warnings.
- Metadata must not store PHI or any real-data path beyond local demonstration source paths.
