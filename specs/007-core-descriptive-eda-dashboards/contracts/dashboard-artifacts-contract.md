---
id: CONTRACT-007-DASHBOARDS
title: Core Descriptive EDA Dashboard Artifact Contract
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-007, SPEC-004, SPEC-006]
implements: [P5, P7, P10]
supersedes: null
superseded_by: null
related: [CONTRACT-004-DESIGN]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Contract: Core Descriptive EDA Dashboard Artifacts

## Common Artifact Requirements

Every core dashboard artifact must:

- Be a PNG file.
- Be at least 1600 x 900 pixels.
- Include a title and source/date-range subtitle.
- Include labels and schema units where units are available.
- Include direct count/percent annotations where feasible.
- Preserve missing values in denominators and annotations.
- Avoid prediction, model scores, risk classification, and imputation.

## Required Artifacts

| Panel | Filename | Required inputs |
|-------|----------|-----------------|
| Cohort overview | `01_cohort_overview.png` | `participants`, `participant.id` |
| Outcome prevalence | `02_outcome_prevalence.png` | `clinical_outcomes`, `outcome.participant_id`, `outcome.cv_event` |
| Distribution outliers | `03_distribution_outliers.png` | `daily_vitals`, `vital.participant_id`, `vital.date`, `vital.systolic_bp` |
| Alert engagement funnel | `04_alert_engagement_funnel.png` | `alerts`, `alert.id`, `alert.participant_id`, `alert.level`, `staff_contacts`, `contact.type` |

## Panel-Specific Requirements

### Cohort Overview

- Displays participant N.
- Shows age median/range when age is available.
- Shows PIH severity, insurance, race/ethnicity, AC availability, household size, parity,
  comorbidities/risk indicators, and available BHLS, MSPSS, EPDS, and PASS measures.
- Groups equity-relevant context visually.
- Does not suppress low-count categories.
- Renders unavailable cards for absent optional fields.

### Outcome Prevalence and Class Imbalance

- Shows CV event, ED visit, hospitalization, and heat illness counts and percentages.
- Shows CV positive and negative class counts directly.
- Shows missing/unknown outcome counts.
- Includes the required rare-outcome warning text:
  `Rare outcome: interpret model performance with precision-recall metrics and uncertainty intervals.`
- Annotates `15/200` or `7.5%` target relationship only when observed CV event prevalence is
  6.5% to 8.5%.

### Distributions and Capture-Worthy Outliers

- Shows distribution cards for SBP, DBP, HR, RR, skin temperature, weight, body water, sleep,
  and steps when the roles are present.
- Shows observed N and missing count for each distribution.
- Uses schema-registry units.
- Lists top capture-worthy or impossible values with participant id, study day, value, unit,
  and context link label.
- Does not apply local statistical outlier rules when schema registry ranges are absent.

### Alerts and Engagement Funnel

- Shows alert count by level and trigger reason.
- Shows total alerts, alerting participants, median alerts per alerting participant, and
  completed-call rate.
- Shows survey completed/dismissed/abandoned/missing states explicitly.
- Shows staff contact completed/not completed/missing states explicitly.
- Shows funnel counts and conversion percentages.
- Uses immediately prior stage as the denominator for each conversion percentage.
