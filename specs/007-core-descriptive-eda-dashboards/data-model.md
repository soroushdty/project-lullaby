---
id: DATA-007
title: Core Descriptive EDA Dashboards Data Model
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-007, SPEC-001, SPEC-004, SPEC-005, SPEC-006]
implements: [P3, P5, P7, P10]
supersedes: null
superseded_by: null
related: [SPEC-004, SPEC-005, SPEC-006, SPEC-008]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Data Model: Core Descriptive EDA Dashboards

## EDATables

Represents the canonical table bundle used by a core dashboard run.

**Fields**:
- `data_dir`: caller-supplied input path
- `resolved_data_dir`: actual directory used after default fallback resolution
- `participants`: canonical participants table
- `daily_vitals`: canonical participant-day vitals table
- `clinical_outcomes`: canonical participant outcome table
- `alerts`: canonical alert table
- `staff_contacts`: canonical staff contact table
- `load_warnings`: optional table or role warnings collected during loading

**Validation rules**:
- Required core tables must exist before any requested core artifact is written.
- Required semantic roles for requested panels must resolve before any requested core artifact
  is written.
- Optional table or role absence is recorded as a warning and rendered visibly where relevant.

## CoreEDAPanel

Represents one required dashboard artifact in the core panel set.

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

## CohortOverviewPanel

Table 1-style descriptive dashboard for cohort composition.

**Required entities and roles**:
- `participants`
- `participant.id`

**Optional fields and roles**:
- Age, PIH severity, insurance, race/ethnicity, AC availability, household size, parity,
  comorbidities/risk indicators, BHLS, MSPSS, EPDS, PASS
- Optional `clinical_outcomes` context

**Validation rules**:
- Participant N must be shown.
- Age shows median and range when available.
- Equity-relevant fields are grouped visually.
- Low-count categories are not suppressed.
- Missing optional fields render unavailable cards.

## OutcomePrevalencePanel

Descriptive dashboard for outcome rates and rare-event class imbalance.

**Required entities and roles**:
- `clinical_outcomes`
- `outcome.participant_id`
- `outcome.cv_event`

**Optional roles**:
- `outcome.ed_visit`
- `outcome.hospitalized`
- `outcome.heat_illness`

**Derived fields**:
- `positive_count`
- `negative_count`
- `missing_unknown_count`
- `denominator`
- `positive_percent`
- `target_rate_annotation`

**Validation rules**:
- CV event positive and negative classes are visually countable or directly labeled.
- Missing/unknown values are not counted as negative.
- The rare-outcome warning text is present exactly as specified.
- The `15/200` or `7.5%` annotation appears only when observed CV prevalence is 6.5% to
  8.5%.

## DistributionOutliersPanel

Descriptive dashboard for daily vital distributions and schema-driven capture-worthy values.

**Required entities and roles**:
- `daily_vitals`
- `vital.participant_id`
- `vital.date`
- `vital.systolic_bp`

**Optional distribution roles**:
- `vital.diastolic_bp`
- `vital.heart_rate`
- `vital.respiratory_rate`
- `vital.skin_temperature_c`
- `vital.weight_kg`
- `vital.body_water_pct`
- `vital.sleep_hours`
- `vital.steps`
- `vital.study_day`

**Derived fields**:
- `observed_count`
- `missing_count`
- `unit`
- `capture_worthy_rows`
- `impossible_by_schema_rows`

**Validation rules**:
- Units come from the schema registry when available.
- Missing values remain in denominators.
- Capture-worthy flags require schema registry `capture_worthy_range`.
- Impossible flags require schema registry `hard_range`.
- Variables without registry ranges are not flagged by local statistical rules.
- Each listed row includes participant id, study day, value, unit, and context link label.

## AlertEngagementFunnelPanel

Descriptive dashboard for alert volume, trigger reasons, survey state, staff contact state,
and conversion between engagement stages.

**Required entities and roles**:
- `alerts`
- `alert.id`
- `alert.participant_id`
- `alert.level`
- `staff_contacts`
- `contact.type`

**Optional roles**:
- `alert.trigger_reasons`
- `alert.called_nurse`
- `contact.completed`

**Derived fields**:
- `total_alerts`
- `alerting_participants`
- `median_alerts_per_alerting_participant`
- `completed_call_rate`
- `survey_state_counts`
- `staff_contact_state_counts`
- `funnel_stage_counts`
- `conversion_percentages`

**Validation rules**:
- Alert levels and trigger reasons are counted.
- Survey states completed, dismissed, abandoned, and missing/unknown remain explicit.
- Staff contact completion is based only on explicit completed states.
- Missing survey/contact state is shown separately and not counted as attempted or completed.
- Each funnel conversion is current stage count divided by the immediately prior stage count.

## EDAManifestEntry

Represents one generated dashboard entry in `outputs/figures/manifest.json`.

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
- `spec` references SPEC-007 for core descriptive EDA dashboard artifacts.
- Duplicate artifact ids are upserted only when metadata intentionally replaces the previous
  run output.
- Warnings preserve optional missingness and category overflow evidence.
