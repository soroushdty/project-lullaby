---
id: CONTRACT-009-ARTIFACTS
title: Longitudinal EDA Dashboard Artifact Contract
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-009, SPEC-004, SPEC-007]
implements: [P5, P7, P10]
supersedes: null
superseded_by: null
related: [CONTRACT-007-DASHBOARDS]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Contract: Longitudinal EDA Dashboard Artifacts

## Common Artifact Requirements

Every longitudinal dashboard artifact must:

- Be a PNG file.
- Be at least 1600 x 900 pixels.
- Include a title and source/date-range subtitle.
- Include labels and schema units where units are available.
- Include direct count, denominator, or warning annotations where feasible.
- Preserve missing values in gaps, denominators, matrix cells, and annotations.
- Avoid prediction, model scores, clinical risk ranking, and imputation.
- Record relevant optional-data warnings in the manifest.

## Required Artifacts

| Panel | Filename | Required inputs |
|-------|----------|-----------------|
| Vital trajectories | `05_vital_trajectories.png` | `daily_vitals`, `vital.participant_id`, `vital.date`, `vital.systolic_bp` |
| Missingness and adherence | `06_missingness_adherence.png` | `daily_vitals`, `vital.participant_id`, `vital.date`, `staff_contacts`, `contact.type` |
| Patient timeline | `07_patient_timeline.png` | `participants`, `participant.id`, `daily_vitals`, `vital.participant_id`, `vital.date`, `vital.systolic_bp`, `alerts`, `alert.participant_id`, `alert.date`, `alert.level`, `staff_contacts`, `contact.participant_id`, `contact.date`, `contact.type`, `clinical_outcomes`, `outcome.participant_id`, `outcome.cv_event`, `outcome.cv_event_date` |
| Data-quality scorecard | `08_data_quality_scorecard.png` | `daily_vitals`, `vital.participant_id`, `vital.date`, `staff_contacts`, `contact.type` |
| Missingness mechanism | `09_missingness_mechanism.png` | `participants`, `participant.id`, `daily_vitals`, `vital.participant_id`, `vital.date`, `vital.systolic_bp` |

## Panel 5: Vital Trajectories

- Shows cohort aggregate trajectory by study day or study week.
- Shows selected-participant trajectory when a participant id is supplied or automatically
  selected.
- Includes SBP, DBP, HR, RR, skin temperature, weight, body water, sleep, and steps when roles
  are present.
- Shows observed-day denominators.
- Renders missing days as visible line gaps.
- Never connects missing days with interpolated values.
- Shows ambient temperature or heat index overlay only when requested and available.

## Panel 6: Missingness and Adherence

- Shows a participant x study day missingness matrix.
- Shows wear-hours over time when `vital.sensor_wear_hours` is present.
- Shows scale-adherence over time when `vital.scale_used` is present.
- Shows adherence decline summary.
- Shows missingness by variable.
- Shows gap clustering for overnight, feeding/morning, hot afternoon, and late-study decline
  only when timestamps or suitable proxies exist.
- Makes present and missing states explicit without relying on color alone.
- Downsamples display rows deterministically for cohorts above 250 participants while
  computing metrics on all participants.

## Panel 7: Single-Participant Clinical Timeline

- Fits one participant's longitudinal record on one dashboard page.
- Aligns vital trajectories, event markers, environment overlay, and missingness/wear track on
  the same study-day x-axis.
- Shows vital trajectories with clinical thresholds or reference bands where available.
- Shows alerts, staff contacts, and clinical outcomes as labeled event markers.
- Requires participant id and event date roles for alert, staff-contact, and clinical-outcome
  marker tables before writing the timeline artifact.
- Shows missingness/wear as a bottom track when available.
- Shows heat index or ambient temperature overlay when requested and available.
- Shows a participant summary card with PIH severity, AC access, insurance, parity, and
  baseline psychosocial fields where available.
- Labels capture-worthy extremes directly where feasible.

## Panel 8: Data-Quality Scorecard

- Shows per-participant wear completeness.
- Shows per-participant scale adherence.
- Shows valid-signal hours.
- Shows number and duration of gaps.
- Shows transparent component weights and composite data-quality score.
- Ranks participants by data completeness and signal quality, not clinical risk.

## Panel 9: Missingness-Mechanism Diagnostics

- Shows missingness rate by study day.
- Shows missingness by archetype when available.
- Shows missingness by AC access, insurance, PIH severity, and health literacy where
  available.
- Shows missingness versus heat exposure when environment data are available.
- Shows missingness versus recent abnormal vitals when recent abnormal vital context can be
  derived from observed values.
- Labels results as exploratory signals consistent with MCAR, MAR, or MNAR hypotheses and not
  proof.
- Does not impute missing data.
