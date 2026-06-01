---
id: SPEC-010
title: Relationships, Heat Exposure, Archetypes, and Recruitment Dashboards
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-001, SPEC-004, SPEC-007, SPEC-009]
implements: [P3, P5, P7, P10]
supersedes: null
superseded_by: null
related: [SPEC-004, SPEC-005, SPEC-006, SPEC-007, SPEC-009]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Feature Specification: Relationships, Heat Exposure, Archetypes, and Recruitment Dashboards

**Feature Branch**: `010-relationships-heat-archetypes-recruitment-dashboards`

**Created**: 2026-06-01

**Status**: Draft

**Input**: User description: "SPEC-004D, renamed as SPEC-010: generate the remaining descriptive EDA dashboards for relationships, heat exposure, participant archetypes, and enrollment/recruitment timelines. Depends on SPEC-001, SPEC-004A, SPEC-004B, and SPEC-004C renamed; implements P3, P5, P7, P10."

## Scope

SPEC-010 completes the descriptive EDA dashboard series with panels 10 through 13. These dashboards remain descriptive only: they summarize observed relationships, heat exposure context, participant archetype segments, and recruitment/enrollment timing without prediction, causal claims, imputation, or ground-truth assertions for provisional clusters.

## Clarifications

### Session 2026-06-01

- Q: How should SPEC-010 define “high heat” when an explicit `heat_wave` flag is not available? → A: Use `heat_wave == true`; else `heat_exposure_level in high/extreme`; else observed `heat_index_c >= 75th percentile`.
- Q: Panel 12 requires alert burden, but the listed inputs did not include `alerts`. How should alert burden be handled? → A: Load optional `alerts`; compute alert burden from alerts when present; mark unavailable when absent.
- Q: For Panel 10, may heat-index bivariate views use `daily_vitals.heat_index_c` when no standalone `environment` table exists? → A: Use `environment.heat_index_c` when available; else use observed `daily_vitals.heat_index_c` as a labeled proxy for Panel 10 only.
- Q: How should Panel 12 handle explicit archetype labels that are not one of the five required segment names or known aliases? → A: Normalize known aliases; preserve unknown explicit labels as additional rows and metadata.
- Q: When explicit archetype labels are absent and provisional rules match multiple archetypes for the same participant, what rule priority should Panel 12 use? → A: Priority order: true emergency → heat-stressed → silent decliner → overwhelmed mom → diligent monitor.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review Descriptive Relationships (Priority: P1)

A reviewer needs one dashboard that summarizes pairwise relationships among observed vital variables and highlights descriptive CV-risk-like versus heat-strain-like trajectory patterns.

**Why this priority**: Relationship patterns are central to interpreting whether vital trajectories look more consistent with cardiovascular burden, heat strain, or neither. The reviewer needs pairwise denominators and descriptive labels before using these views in any analysis discussion.

**Independent Test**: Generate Panel 10 from `daily_vitals`, `participants`, optional `environment`, and optional `clinical_outcomes`; assert the artifact exists, includes descriptive correlation metadata, records observed pair counts, and avoids causal wording.

**Acceptance Scenarios**:

1. **Given** numeric daily vital variables are available, **when** Panel 10 renders, **then** it shows a descriptive correlation heatmap using observed pairs only.
2. **Given** body-water, BP, HR, and skin-temperature observations are available, **when** Panel 10 renders, **then** it shows targeted bivariate direction views for body-water direction versus BP, HR, and skin temperature.
3. **Given** heat-index data are available from an environment table or from observed `daily_vitals.heat_index_c`, **when** Panel 10 renders, **then** it shows heat-index versus HR and skin-temperature views with observed pair counts and labels daily-vitals heat index as a Panel 10-only proxy when no environment table exists.
4. **Given** trajectory direction data are available, **when** Panel 10 renders, **then** it labels body water rising with BP/HR rising as a CV-risk-like descriptive trajectory and body water falling with HR/skin temperature rising as a heat-strain-like descriptive trajectory without implying causality.

---

### User Story 2 - Audit Heat Exposure and Environmental Context (Priority: P1)

A dashboard reviewer needs a heat exposure panel showing ambient temperature, heat index, heat-wave periods, AC-access context, vital responses during high heat, and missing environment data.

**Why this priority**: Heat exposure is a core contextual driver for participant interpretation. The dashboard must never silently fabricate weather data and must make missing environment coverage explicit.

**Independent Test**: Generate Panel 11 with and without an `environment` table; assert the available-data path renders heat context and the unavailable path renders a visible unavailable panel with a manifest warning.

**Acceptance Scenarios**:

1. **Given** an environment table is available, **when** Panel 11 renders, **then** it shows ambient temperature and heat index over calendar date or study day.
2. **Given** heat-wave or high-heat periods are available or can be transparently derived from observed environment fields, **when** Panel 11 renders, **then** those periods are shaded or annotated using the ordered high-heat definition: `heat_wave == true`, else `heat_exposure_level` high/extreme, else observed `heat_index_c` at or above the 75th percentile.
3. **Given** participant AC-access data are available, **when** Panel 11 renders, **then** vital response summaries are stratified or overlaid by AC access.
4. **Given** high-heat and non-high-heat days can be identified, **when** Panel 11 renders, **then** HR and skin-temperature response summaries compare high-heat versus non-high-heat observations.
5. **Given** the environment table is absent, **when** Panel 11 renders, **then** it creates an explicit unavailable panel explaining that environment data must come from SPEC-005 synthetic generation or a real environment source and does not fabricate environment data.

---

### User Story 3 - Explore Participant Archetype Segments (Priority: P2)

A reviewer needs a participant-archetype explorer summarizing five interpretable segments with adherence, missingness, alert burden, event prevalence, AC access, and PIH severity.

**Why this priority**: Archetype summaries help reviewers understand cohort heterogeneity and operational patterns, but provisional segments must be clearly separated from explicit synthetic labels or known labels.

**Independent Test**: Generate Panel 12 with explicit archetype labels, without explicit labels, and with optional `alerts`; assert explicit labels are used when present, provisional labels are marked as provisional when inferred, all five required segments are represented, and alert burden is computed only from observed alert rows.

**Acceptance Scenarios**:

1. **Given** explicit archetype labels exist in `participants` or `daily_vitals`, **when** Panel 12 renders, **then** the dashboard uses those labels and records the label source.
2. **Given** explicit archetype labels are absent, **when** Panel 12 renders, **then** the dashboard assigns provisional descriptive clusters using transparent rules and labels them as provisional.
3. **Given** explicit archetype labels include known aliases, **when** Panel 12 renders, **then** known aliases are normalized to the five canonical segments.
4. **Given** explicit archetype labels include unknown labels, **when** Panel 12 renders, **then** unknown labels are preserved as additional explicit rows and recorded in metadata while the five required segments remain visible.
5. **Given** multiple provisional archetype rules match the same participant, **when** Panel 12 assigns provisional labels, **then** it uses the deterministic priority order true emergency, heat-stressed, silent decliner, overwhelmed mom, then diligent monitor.
6. **Given** segment metrics can be computed, **when** Panel 12 renders, **then** it summarizes N, adherence, missingness, alert burden, event prevalence, AC access, and PIH severity for each segment.
7. **Given** alert data are available, **when** Panel 12 renders, **then** alert burden is computed from observed alert rows.
8. **Given** alert data are unavailable, **when** Panel 12 renders, **then** alert burden is marked unavailable rather than inferred from other fields.

---

### User Story 4 - Review Recruitment and Enrollment Timeline (Priority: P2)

An operations reviewer needs a calendar-aware timeline of recruitment/enrollment, observation windows, delivery dates, enrolled participant counts, and cohort observation density.

**Why this priority**: Recruitment timing and observation density determine whether cohort coverage overlaps with heat seasons and whether analyses are calendar-aware.

**Independent Test**: Generate Panel 13 with and without a `recruitment` table; assert the panel uses recruitment dates when present, infers from participant and observation dates when absent, and renders an unavailable panel when no parseable dates exist.

**Acceptance Scenarios**:

1. **Given** recruitment or participant enrollment dates are available, **when** Panel 13 renders, **then** it shows enrollment dates over calendar time.
2. **Given** observation start/end dates or daily-vitals date bounds are available, **when** Panel 13 renders, **then** it shows participant observation windows.
3. **Given** delivery dates are available, **when** Panel 13 renders, **then** it marks delivery dates on the timeline.
4. **Given** environment data are available, **when** Panel 13 renders, **then** it overlays summer heat or high-heat periods.
5. **Given** recruitment data are absent but participant enrollment or observation dates are available, **when** Panel 13 renders, **then** it infers the recruitment timeline and records the inference in warnings or metadata.
6. **Given** required date fields are missing or unparseable, **when** Panel 13 renders, **then** it creates an unavailable panel and manifest warning.

### Edge Cases

- If a required input for the SPEC-010 panel set is missing (`participants` or `daily_vitals`), the CLI fails before writing requested artifacts.
- If optional `environment`, `clinical_outcomes`, `alerts`, or `recruitment` tables are absent, affected panels render explicit unavailable or warning states rather than silently inferring missing source data.
- If `environment.csv` is absent, Panel 11 MUST NOT use `daily_vitals` ambient or heat-index columns as a fabricated environment table.
- If explicit archetype labels are absent, provisional segment labels MUST be visibly marked provisional in the panel and manifest metadata.
- If explicit archetype labels contain labels outside the five required segments, the panel MUST normalize known aliases, preserve unknown source labels as additional explicit rows and metadata, and still include rows for the five required segments.
- If multiple provisional archetype rules match one participant, the panel MUST assign exactly one provisional label using the deterministic priority order true emergency, heat-stressed, silent decliner, overwhelmed mom, then diligent monitor.
- If recruitment dates are absent but observation dates exist, Panel 13 uses observation/enrollment fallback dates and records the source of inference.
- If all calendar dates are missing or unparseable for Panel 13, the timeline renders an unavailable panel and manifest warning.
- If more participants exist than can be legibly displayed in timeline-style panels, display rows may be downsampled deterministically while metrics remain full-cohort.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST create or update `src/visualization/eda_relationships.py`.
- **FR-002**: The system MUST create or update `src/visualization/eda_environment.py`.
- **FR-003**: The system MUST create or update `src/visualization/eda_archetypes.py`.
- **FR-004**: The system MUST create or update `tests/test_eda_relationships_outputs.py`.
- **FR-005**: The system MUST generate `outputs/figures/eda/10_relationships.png`.
- **FR-006**: The system MUST generate `outputs/figures/eda/11_heat_environment.png`.
- **FR-007**: The system MUST generate `outputs/figures/eda/12_archetype_explorer.png`.
- **FR-008**: The system MUST generate `outputs/figures/eda/13_recruitment_timeline.png`.
- **FR-009**: Every generated repo-relative SPEC-010 artifact MUST be registered in `outputs/figures/manifest.json`; outside-repository output paths MUST warn and remain unregistered.
- **FR-010**: Every SPEC-010 artifact MUST be at least 1600 x 900 pixels and include a title, subtitle, labels, units where available, and direct annotations where feasible.
- **FR-011**: Panel 10 MUST use semantic labels and units from the schema registry.
- **FR-012**: Panel 10 MUST use observed pairs only for correlations and bivariate relationships, annotate pairwise N, and record the observed-data policy in metadata.
- **FR-013**: Panel 10 MUST label correlations as descriptive and MUST NOT imply causality.
- **FR-014**: Panel 10 MUST show a numeric vital correlation heatmap and targeted bivariate views for body-water direction versus BP, HR, and skin temperature.
- **FR-015**: Panel 10 MUST show heat-index versus HR and skin temperature when environment heat-index data are available; if no environment table exists, Panel 10 MAY use observed `daily_vitals.heat_index_c` as a clearly labeled Panel 10-only proxy.
- **FR-016**: Panel 10 MUST highlight the descriptive CV-vs-heat discriminator: body water rising with BP/HR rising versus body water falling with HR/skin temperature rising.
- **FR-017**: Panel 11 MUST use a real `environment` table when rendering ambient temperature, heat index, or heat-wave periods.
- **FR-018**: Panel 11 MUST NOT fabricate environment data during EDA.
- **FR-019**: Panel 11 MUST render an explicit unavailable panel when no environment table exists, explaining that environment data must come from SPEC-005 synthetic generation or a real environment source.
- **FR-020**: Panel 11 MUST show ambient temperature and heat index over calendar date or study day when environment data are available.
- **FR-021**: Panel 11 MUST shade or annotate heat-wave or high-heat periods when supported by observed environment fields, using `heat_wave == true`; if unavailable, `heat_exposure_level in high/extreme`; if unavailable, observed `heat_index_c >= 75th percentile`.
- **FR-022**: Panel 11 MUST show AC-access stratification or overlay when participant AC data are available.
- **FR-023**: Panel 11 MUST summarize observed HR and skin-temperature responses during high-heat versus non-high-heat days.
- **FR-024**: Panel 11 MUST explicitly show missing environment rows, missing environment date gaps, or missing environment field counts.
- **FR-025**: Panel 12 MUST include the five required archetype segments: diligent monitor, overwhelmed mom, heat-stressed, true emergency, and silent decliner.
- **FR-026**: Panel 12 MUST use explicit archetype labels when available, record the label source in metadata, normalize known aliases to canonical segment names, and preserve unknown explicit labels as additional rows and metadata.
- **FR-027**: Panel 12 MUST assign provisional descriptive clusters when explicit labels are unavailable, using transparent rules, visibly labeling them provisional, and resolving multiple rule matches by deterministic priority order: true emergency, heat-stressed, silent decliner, overwhelmed mom, then diligent monitor.
- **FR-028**: Panel 12 MUST NOT present provisional archetypes as ground truth.
- **FR-029**: Panel 12 MUST summarize N, adherence, missingness, alert burden, event prevalence, AC access, and PIH severity for each segment; alert burden MUST be computed from optional `alerts` rows when available and marked unavailable when `alerts` are absent.
- **FR-030**: Panel 13 MUST show enrollment dates, observation windows, delivery dates when available, participant count enrolled over time, and cohort observation density over calendar time.
- **FR-031**: Panel 13 MUST overlay summer heat or high-heat periods when environment data are available.
- **FR-032**: Panel 13 MUST use the recruitment table when present and infer from participant enrollment, observation, and daily-vitals dates when recruitment data are absent.
- **FR-033**: Panel 13 MUST render an unavailable panel and manifest warning when no parseable date source exists.
- **FR-034**: The CLI MUST support `python -m src.visualization.generate_eda --data-dir data/raw --out-dir outputs/figures/eda --panels relationships`.
- **FR-035**: The CLI MUST support `python -m src.visualization.generate_eda --data-dir data/raw --out-dir outputs/figures/eda --panels all`.
- **FR-036**: SPEC-010 dashboards MUST remain descriptive only and MUST NOT perform prediction, model scoring, imputation, or causal attribution.
- **FR-037**: Missing optional roles MUST render visible unavailable or warning sections rather than crashes.

### Key Entities

- **Relationships Dashboard Artifact**: Panel 10 static PNG showing descriptive correlation and targeted bivariate relationship summaries.
- **Heat Environment Dashboard Artifact**: Panel 11 static PNG showing environment availability, heat trends, high-heat periods, AC context, vital response summaries, and missing environment data.
- **Archetype Explorer Artifact**: Panel 12 static PNG summarizing explicit or provisional participant segments and segment-level metrics.
- **Recruitment Timeline Artifact**: Panel 13 static PNG summarizing enrollment, recruitment, observation windows, delivery timing, heat overlay, and observation density.
- **Observed Pair Count**: Pairwise denominator used for each descriptive correlation or bivariate view.
- **High-Heat Period**: A calendar or study-day period identified from observed environment fields using `heat_wave == true`; if unavailable, `heat_exposure_level in high/extreme`; if unavailable, observed `heat_index_c >= 75th percentile`.
- **Archetype Label Source**: Metadata identifying whether segment labels came from explicit source labels or provisional descriptive rules.
- **Provisional Archetype Rule**: A transparent, non-ground-truth rule used only when explicit labels are absent; multiple matches resolve to exactly one label by priority order true emergency, heat-stressed, silent decliner, overwhelmed mom, then diligent monitor.
- **Recruitment Timeline Source**: Metadata describing whether dates came from recruitment records or were inferred from participant and observation dates.
- **Manifest Warning**: Structured metadata explaining unavailable optional data, provisional labels, fallback date inference, downsampling, or unsupported environmental context.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All four required PNG artifacts exist under `outputs/figures/eda/`.
- **SC-002**: Each required SPEC-010 PNG artifact is at least 1600 x 900 pixels.
- **SC-003**: Each required SPEC-010 artifact has a corresponding entry in `outputs/figures/manifest.json`.
- **SC-004**: Panel 10 metadata records observed-pair policy and pairwise N for relationship views.
- **SC-005**: Panel 11 renders an explicit unavailable panel when no environment table exists and does not fabricate environment data.
- **SC-006**: Panel 12 metadata distinguishes explicit labels from provisional rule-derived segments.
- **SC-007**: Panel 13 is calendar-aware where parseable dates exist and renders unavailable when all date sources are missing.
- **SC-008**: The CLI command with `--panels relationships` creates four SPEC-010 artifacts.
- **SC-009**: The CLI command with `--panels all` creates panels 1 through 13.
- **SC-010**: The focused SPEC-010 tests pass: `pytest tests/test_eda_relationships_outputs.py`.

## Assumptions

- SPEC-001 provides canonical table validation and semantic role expectations.
- SPEC-004 provides the visualization foundation, schema registry, design system, artifact manifest contract, and missing optional role behavior.
- SPEC-007 provides panels 1 through 4 and the initial EDA CLI.
- SPEC-009 provides panels 5 through 9 and longitudinal EDA conventions.
- SPEC-005 synthetic longitudinal outputs may provide optional environment and recruitment fixtures.
- The pasted dependency names `SPEC-004A`, `SPEC-004B`, and `SPEC-004C` are interpreted as the renamed repository specs SPEC-004, SPEC-007, and SPEC-009.
- Prediction, model scoring, imputation, and causal interpretation are out of scope for SPEC-010.
