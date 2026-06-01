---
id: SPEC-007
title: Core Descriptive EDA Dashboards
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-001, SPEC-004, SPEC-005]
implements: [P3, P5, P7, P10]
supersedes: null
superseded_by: null
related: [SPEC-004, SPEC-005, SPEC-006]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Feature Specification: Core Descriptive EDA Dashboards

**Feature Branch**: `007-core-descriptive-eda-dashboards`

**Created**: 2026-06-01

**Status**: Draft

**Input**: User description: "Generate the first set of high-quality descriptive dashboards from canonical tables. These dashboards present data only. They do not predict outcomes and do not impute missing values."

## Clarifications

### Session 2026-06-01

- Q: How should the CLI behave when a requested panel's required canonical input table is missing? → A: Missing required panel input tables fail the CLI before writing affected artifacts.
- Q: When should Panel 2 annotate the 15/200 or 7.5% target event rate? → A: Annotate when observed CV event prevalence is 6.5% to 8.5%.
- Q: What source defines Panel 3 capture-worthy and impossible value thresholds? → A: Use schema registry `capture_worthy_range` and `hard_range`; if absent, do not flag that variable.
- Q: How should Panel 4 compute funnel conversion percentages? → A: Conversion equals current stage count divided by the immediately prior stage count; missing states are shown but not counted as attempted or completed.
- Q: How should the CLI behave when a requested panel is missing a required semantic role? → A: Missing required semantic roles fail before writing affected artifacts or manifest entries.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review Cohort Composition (Priority: P1)

A dashboard reviewer needs a Table 1-style cohort overview that summarizes participants, demographics, equity-relevant context, baseline risk indicators, and optional clinical outcome context from canonical tables.

**Why this priority**: The first descriptive dashboard must establish who is represented in the cohort before outcome, distribution, or engagement patterns are interpreted.

**Independent Test**: Generate the cohort overview panel from canonical `participants` data with optional `clinical_outcomes`, including fixtures where optional roles are missing.

**Acceptance Scenarios**:

1. **Given** canonical participants are available, **when** the cohort overview renders, **then** it displays participant N, age distribution with median/range annotation, PIH severity, insurance, race/ethnicity, AC availability, household size, parity, risk indicators, and available BHLS, MSPSS, EPDS, and PASS measures.
2. **Given** optional cohort fields are absent, **when** the dashboard renders, **then** the missing sections appear as labeled unavailable cards rather than causing crashes.
3. **Given** equity-relevant fields are present, **when** the panel is composed, **then** those fields are grouped visually instead of scattered across unrelated sections.
4. **Given** low-count categories exist, **when** the dashboard renders, **then** categories are not suppressed.

---

### User Story 2 - Inspect Outcome Prevalence and Class Imbalance (Priority: P1)

A reviewer needs outcome prevalence counts and rare-event imbalance to be explicit before any modeling or interpretation work.

**Why this priority**: Project Lullaby has rare outcomes; prevalence and class imbalance must be shown plainly so downstream model performance is interpreted honestly.

**Independent Test**: Generate the outcome prevalence panel from canonical `clinical_outcomes` data and assert count/percent labels, rare-outcome warning text, and class imbalance display are present.

**Acceptance Scenarios**:

1. **Given** clinical outcomes are available, **when** the panel renders, **then** CV event, ED visit, hospitalization, and heat illness counts and percentages are displayed.
2. **Given** observed CV event prevalence is 6.5% to 8.5%, **when** the class imbalance panel renders, **then** the 15/200 or 7.5% target-rate relationship is directly annotated.
3. **Given** the CV outcome is rare, **when** the dashboard renders, **then** it includes the warning text: `Rare outcome: interpret model performance with precision-recall metrics and uncertainty intervals.`
4. **Given** positive and negative CV event classes are shown, **when** the panel renders, **then** both classes are visually countable or directly labeled.

---

### User Story 3 - Examine Distributions and Capture-Worthy Extremes (Priority: P1)

A clinical analyst needs distribution cards for daily vitals and a concise list of capture-worthy values that may deserve review without being mislabeled as errors.

**Why this priority**: Descriptive EDA must preserve physiologic variation, missingness, and clinically plausible extremes rather than imputing, discarding, or overcorrecting source data.

**Independent Test**: Generate the distribution panel from canonical `daily_vitals` and assert vital distributions, observed/missing denominators, schema units, and capture-worthy outlier labeling.

**Acceptance Scenarios**:

1. **Given** daily vitals are available, **when** the panel renders, **then** it includes distribution cards for SBP, DBP, HR, RR, skin temperature, weight, body water, sleep, and steps.
2. **Given** units are defined in the schema registry, **when** each card renders, **then** shared schema units are shown.
3. **Given** missing values are present, **when** a distribution card renders, **then** observed N and missing counts are displayed in denominator annotations.
4. **Given** an observed value is outside the schema registry `capture_worthy_range` but within the `hard_range`, **when** the outlier table renders, **then** it is labeled `capture-worthy` rather than an error.
5. **Given** an observed value is outside the schema registry `hard_range`, **when** the outlier table renders, **then** it is labeled `impossible by schema`.
6. **Given** a variable has no schema registry `capture_worthy_range` or `hard_range`, **when** the outlier detection step runs, **then** that variable is not flagged by dashboard-local or statistical outlier rules.
7. **Given** capture-worthy values are listed, **when** the table renders, **then** each row includes participant id, study day, value, unit, and a context link label.

---

### User Story 4 - Understand Alerts and Engagement Funnel (Priority: P2)

An operations reviewer needs alert volume, trigger reasons, survey status, staff-contact status, and conversion between engagement stages.

**Why this priority**: Alert and engagement descriptive views show whether monitoring generates actionable follow-up and where response pathways lose participants or staff contact.

**Independent Test**: Generate the alert engagement funnel panel from canonical `alerts` and `staff_contacts`, including fixtures with missing survey/contact states.

**Acceptance Scenarios**:

1. **Given** alert rows are available, **when** the panel renders, **then** it displays alert count by level and trigger reason.
2. **Given** survey states include completed, dismissed, abandoned, or missing values, **when** the funnel renders, **then** each state remains explicit.
3. **Given** staff contact state is missing, **when** completion counts are computed, **then** completion is not inferred from missing state.
4. **Given** all engagement stages are present, **when** the funnel renders, **then** it shows counts and conversion percentages for alert generated, survey completed/dismissed/abandoned, staff call attempted, and staff contact completed.
5. **Given** alerting participants exist, **when** the summary tiles render, **then** they include total alerts, alerting participants, median alerts per alerting participant, and completed-call rate.
6. **Given** funnel conversion percentages are shown, **when** a stage has a prior stage, **then** its percentage is calculated as current stage count divided by the immediately prior stage count.
7. **Given** survey or contact state is missing, **when** attempted or completed stages are counted, **then** missing states are displayed separately and are not counted as attempted or completed.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST create `src/visualization/eda_core.py` for core EDA dashboard rendering.
- **FR-002**: The system MUST create `src/visualization/generate_eda.py` as the CLI entry point for EDA generation.
- **FR-003**: The system MUST create or update `tests/test_eda_core_outputs.py` and `tests/test_eda_missingness_policy.py`.
- **FR-004**: The system MUST generate `outputs/figures/eda/01_cohort_overview.png`.
- **FR-005**: The system MUST generate `outputs/figures/eda/02_outcome_prevalence.png`.
- **FR-006**: The system MUST generate `outputs/figures/eda/03_distribution_outliers.png`.
- **FR-007**: The system MUST generate `outputs/figures/eda/04_alert_engagement_funnel.png`.
- **FR-008**: Every generated dashboard artifact MUST be registered in `outputs/figures/manifest.json`.
- **FR-009**: Every dashboard artifact MUST be at least 1600 x 900 pixels and include a title, subtitle, labels, units where available, and direct annotations where feasible.
- **FR-010**: Dashboards MUST present descriptive data only and MUST NOT predict outcomes or impute missing values.
- **FR-011**: Missing optional roles MUST render visible warning or unavailable panels rather than crashes.
- **FR-012**: Missing values MUST be counted and displayed where relevant.
- **FR-013**: Panel 1 MUST include participant N, age distribution with median/range annotation, PIH severity, insurance, race/ethnicity, AC availability, household size, parity, comorbidities/risk indicators, and available BHLS, MSPSS, EPDS, and PASS measures.
- **FR-014**: Panel 1 MUST group equity-relevant fields visually and MUST NOT suppress low-count categories.
- **FR-015**: Panel 2 MUST show CV event, ED visit, hospitalization, and heat illness counts and percentages.
- **FR-016**: Panel 2 MUST make CV class imbalance visually explicit, including positive and negative counts.
- **FR-017**: Panel 2 MUST annotate the 15/200 or 7.5% target event-rate relationship when observed CV event prevalence is 6.5% to 8.5%, and MUST include the rare-outcome warning text.
- **FR-018**: Panel 3 MUST show distribution cards for SBP, DBP, HR, RR, skin temperature, weight, body water, sleep, and steps.
- **FR-019**: Panel 3 MUST use schema-registry units, preserve missing-count denominators, and label values outside schema registry `capture_worthy_range` as `capture-worthy` unless they are outside `hard_range`, in which case they MUST be labeled `impossible by schema`.
- **FR-020**: Panel 3 MUST include a top capture-worthy values table/card with participant id, study day, value, unit, and context link label.
- **FR-021**: Panel 4 MUST show alert count by level and trigger reason.
- **FR-022**: Panel 4 MUST show a funnel from alert generated to survey completed/dismissed/abandoned to staff call attempted to staff contact completed.
- **FR-023**: Panel 4 MUST show both counts and conversion percentages at funnel stages, with each conversion percentage calculated as the current stage count divided by the immediately prior stage count.
- **FR-024**: Panel 4 MUST make missing survey/contact states explicit and MUST NOT infer completion when state is missing.
- **FR-025**: The CLI MUST support `python -m src.visualization.generate_eda --data-dir data/raw --out-dir outputs/figures/eda --panels core`.
- **FR-026**: The CLI SHOULD support a synthetic run using `data/synthetic/longitudinal` and a repo-relative output directory such as `outputs/figures/eda_synthetic`.
- **FR-027**: When a requested panel's required canonical input table is missing, the CLI MUST fail with an actionable validation error before writing that panel artifact or registering it in the manifest; optional input tables or roles continue to render visible unavailable/warning sections.
- **FR-028**: Panel 3 MUST NOT apply dashboard-local clinical thresholds, IQR rules, percentile rules, or min/max-only rules for capture-worthy flagging when the schema registry does not define `capture_worthy_range` or `hard_range` for a variable.
- **FR-029**: When a requested panel's required semantic role is missing from an available input table, the CLI MUST fail with an actionable validation error before writing that panel artifact or registering it in the manifest; optional roles continue to render visible unavailable/warning sections.

### Key Entities

- **Core EDA Dashboard Artifact**: A static PNG generated from canonical tables and registered in the figure manifest.
- **Cohort Overview Panel**: The Table 1-style dashboard summarizing participants and optional clinical outcome context.
- **Outcome Prevalence Panel**: The dashboard summarizing outcome rates and CV event class imbalance.
- **Distribution Outliers Panel**: The dashboard summarizing daily vital distributions and capture-worthy extremes.
- **Alert Engagement Funnel Panel**: The dashboard summarizing alerts, survey state, staff-contact state, and conversion stages.
- **Unavailable Card**: A visible dashboard section shown when optional data or roles are absent.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All four required PNG artifacts exist under `outputs/figures/eda/`.
- **SC-002**: Each required PNG artifact is at least 1600 x 900 pixels.
- **SC-003**: Each required artifact has a corresponding entry in `outputs/figures/manifest.json`.
- **SC-004**: Missing optional roles produce visible unavailable or warning panels without command failure.
- **SC-005**: Missing values are counted and displayed where relevant.
- **SC-006**: Outcome prevalence and class imbalance are visually explicit for the CV event.
- **SC-007**: Distribution extremes are labeled `capture-worthy` where appropriate.
- **SC-008**: The focused EDA tests pass: `pytest tests/test_eda_core_outputs.py tests/test_eda_missingness_policy.py`.
- **SC-009**: Missing required input tables or required semantic roles fail before affected PNG artifacts or manifest entries are written.

## Assumptions

- SPEC-001 provides the canonical table baseline.
- SPEC-004 provides the visualization foundation, schema registry, design system, and artifact manifest contract.
- SPEC-005 synthetic longitudinal data is optional input for the synthetic dashboard run.
- This feature presents data only; prediction, imputation, and model evaluation are out of scope.
