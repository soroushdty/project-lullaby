---
id: SPEC-009
title: Longitudinal Vitals, Missingness, Signal Quality, and Patient Timeline
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-001, SPEC-004, SPEC-007]
implements: [P3, P5, P7, P10]
supersedes: null
superseded_by: null
related: [SPEC-004, SPEC-005, SPEC-006, SPEC-007]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Feature Specification: Longitudinal Vitals, Missingness, Signal Quality, and Patient Timeline

**Feature Branch**: `009-longitudinal-vitals-missingness-timeline`

**Created**: 2026-06-01

**Status**: Draft

**Input**: User description: "SPEC-004C, renamed to SPEC-009: generate dashboard-grade longitudinal EDA artifacts focused on participant trajectories, adherence, signal quality, missingness, and a single-participant clinical timeline. Skip SPEC-008 for now."

## Clarifications

### Session 2026-06-01

- Q: How should `--week-start` and `--week-end` be interpreted? -> A: They are inclusive, 1-based study-week filters derived from study-day values, where study days 1-7 are week 1; omitted week filters render the full observed study-day range.
- Q: How should the default participant be selected when `--participant-id` is omitted? -> A: Select deterministically by `observed_vital_days + distinct_alert_days + distinct_outcome_events`; break ties by observed vital variable count, then lexicographic participant id, and record score components in the manifest.
- Q: What is the default behavior for `--overlay-environment`? -> A: The default is `false`; when set to `true`, environment overlays render only if the environment table and required roles are available, otherwise the artifact renders with a visible unavailable annotation and manifest warning.
- Q: How are data-quality score components normalized? -> A: Each component is normalized to a 0-1 participant-level score against the participant's expected observed study-day denominator when available; components with no valid denominator are unavailable rather than zero.
- Q: How should missingness-mechanism labels be worded? -> A: Panel 9 labels patterns as exploratory "signals consistent with" MCAR, MAR, or MNAR hypotheses; it must not label a mechanism as proven.
- Q: Which roles are required for Panel 7 event markers? -> A: Timeline event markers require participant id and date roles for each event table: `alert.participant_id`, `alert.date`, `alert.level`, `contact.participant_id`, `contact.date`, `contact.type`, `outcome.participant_id`, `outcome.cv_event`, and `outcome.cv_event_date`; missing marker roles fail before Panel 7 writes, while optional label/detail roles render unavailable.

## Scope

SPEC-009 extends the core descriptive EDA dashboards with longitudinal panels 5 through 9. These panels remain descriptive only: they show observed participant trajectories, adherence, signal quality, missingness, and exploratory missingness mechanism evidence without prediction, imputation, or risk ranking.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review Longitudinal Vital Trajectories (Priority: P1)

A dashboard reviewer needs to see cohort-level and participant-level vital trajectories over study time, including visible missing-day gaps and optional heat exposure context.

**Why this priority**: Longitudinal vitals are the main signal source for participant monitoring. Reviewers must understand observed trajectories, gaps, and denominators before interpreting alerts, outcomes, or missingness patterns.

**Independent Test**: Generate the longitudinal panel with canonical `daily_vitals`, optional `environment`, optional `participants`, and CLI participant/week filters; assert required vital tracks, gaps, denominators, and manifest metadata.

**Acceptance Scenarios**:

1. **Given** canonical daily vitals are available, **when** Panel 5 renders, **then** it shows cohort aggregate trajectories by study day or week for SBP, DBP, HR, RR, skin temperature, weight, body water, sleep, and steps.
2. **Given** a participant id is supplied, **when** Panel 5 renders, **then** the static PNG focuses the participant-specific trajectory while preserving cohort context.
3. **Given** no participant id is supplied, **when** Panel 5 renders, **then** the system selects the participant with the richest combination of vitals, alerts, and outcomes, and records that choice in the manifest.
4. **Given** a participant has missing study days, **when** trajectories render, **then** those days appear as visible gaps rather than interpolated values.
5. **Given** environment data are available and environment overlay is enabled, **when** Panel 5 renders, **then** ambient temperature or heat index appears as a clearly labeled overlay.

---

### User Story 2 - Audit Missingness and Adherence (Priority: P1)

A data-quality reviewer needs a participant-by-study-day missingness matrix, adherence trend summaries, and missingness-by-variable summaries to distinguish source coverage from clinical absence.

**Why this priority**: Missingness and adherence drive whether longitudinal signals are usable. Reviewers need explicit present/missing states and summary metrics before trusting downstream dashboards.

**Independent Test**: Generate the missingness and adherence panel from `daily_vitals`, `staff_contacts`, and optional `alerts`; assert matrix rendering, adherence summaries, deterministic downsampling behavior, and no color-only state encoding.

**Acceptance Scenarios**:

1. **Given** daily vitals and staff contacts are available, **when** Panel 6 renders, **then** it includes a participant x study day missingness matrix, wear-hours trend, scale-adherence trend, adherence decline summary, missingness by variable, and gap clustering summary where supported.
2. **Given** timestamps or suitable proxies support gap clustering, **when** Panel 6 renders, **then** it summarizes overnight, feeding/morning, hot afternoon, and late-study decline gap patterns.
3. **Given** more than 250 participants exist, **when** Panel 6 renders, **then** display rows are downsampled deterministically while summary metrics are computed on all participants and the subtitle states this.
4. **Given** present and missing states are shown, **when** a reviewer reads the panel, **then** the states are explicit through labels, legends, symbols, or patterns and are not conveyed by color alone.

---

### User Story 3 - Review A Single-Participant Clinical Timeline (Priority: P1)

A clinical or operations reviewer needs one participant's longitudinal record on a single dashboard page with vitals, alerts, staff contacts, outcomes, missingness, wear, and contextual participant fields aligned to the same study-day axis.

**Why this priority**: The participant timeline is the highest-value review surface for connecting physiology, engagement, events, and context without requiring the reviewer to inspect multiple separate tables.

**Independent Test**: Generate the patient timeline with canonical participant, vital, alert, contact, outcome, and optional environment fixtures; assert aligned tracks, summary card fields, event markers, missingness/wear track, visible vital gaps, and one-page layout.

**Acceptance Scenarios**:

1. **Given** the required canonical inputs are available, **when** Panel 7 renders, **then** it fits one participant's longitudinal record on one dashboard page.
2. **Given** clinical thresholds or reference bands are available, **when** vital tracks render, **then** those bands are displayed without hiding observed gaps.
3. **Given** alerts, staff contacts, and clinical outcomes exist, **when** the timeline renders, **then** each event type appears as a labeled event marker on the shared study-day axis.
4. **Given** wear and missingness data are available, **when** the timeline renders, **then** a bottom track summarizes data availability and wear quality.
5. **Given** participant context fields exist, **when** the timeline renders, **then** the summary card includes PIH severity, AC access, insurance, parity, and baseline psychosocial fields where available.
6. **Given** capture-worthy extremes occur, **when** the timeline renders, **then** the most important extremes are labeled directly.

---

### User Story 4 - Rank Data and Signal Quality (Priority: P2)

A data-quality reviewer needs a transparent per-participant scorecard that ranks participants by data completeness and signal quality rather than by clinical risk.

**Why this priority**: Signal-quality triage helps reviewers identify where monitoring data are complete enough for interpretation and where gaps require caution, while avoiding accidental clinical-risk ranking.

**Independent Test**: Generate the data-quality scorecard from `daily_vitals` and `staff_contacts`; assert component scores, composite formula, missing-component weight redistribution, manifest warnings, and completeness-based ordering.

**Acceptance Scenarios**:

1. **Given** daily vitals and staff contacts are available, **when** Panel 8 renders, **then** it shows per-participant wear completeness, scale adherence, valid-signal hours, number and duration of gaps, and a composite data-quality score.
2. **Given** all score components can be computed, **when** scores are calculated, **then** the formula is `0.40 * wear_completeness + 0.25 * scale_adherence + 0.20 * vital_completeness + 0.15 * contact_traceability`.
3. **Given** one or more score components cannot be computed, **when** scores are calculated, **then** the missing component weights are redistributed across available components and a manifest warning records the adjustment.
4. **Given** participants are ranked, **when** Panel 8 renders, **then** ranking is based on data completeness and signal quality, not clinical risk or outcome severity.

---

### User Story 5 - Explore Missingness Mechanism Evidence (Priority: P2)

A researcher needs exploratory diagnostics that show whether missingness appears related to study time, participant context, heat exposure, or recent abnormal vitals, while making clear that the panel does not prove MCAR, MAR, or MNAR mechanisms.

**Why this priority**: Missingness interpretation affects downstream analysis, but mechanism claims are high-risk. The dashboard should surface evidence patterns with clear cautionary labeling and no imputation.

**Independent Test**: Generate the missingness-mechanism panel from `participants`, `daily_vitals`, optional `environment`, and optional `clinical_outcomes`; assert exploratory labels, diagnostic groupings, and absence of imputation.

**Acceptance Scenarios**:

1. **Given** participant and daily vital data are available, **when** Panel 9 renders, **then** it shows missingness rate by study day and exploratory MCAR/MAR/MNAR evidence summaries.
2. **Given** archetype or participant context fields are available, **when** Panel 9 renders, **then** it stratifies missingness by archetype, AC access, insurance, PIH severity, and health literacy where available.
3. **Given** environment data are available, **when** Panel 9 renders, **then** it shows missingness versus heat exposure.
4. **Given** recent abnormal vital signals can be identified from observed data, **when** Panel 9 renders, **then** it shows missingness versus recent abnormal vitals without filling missing values.
5. **Given** diagnostic labels are shown, **when** a reviewer reads the panel, **then** the panel explicitly states that mechanism evidence is exploratory and not proof.

### Edge Cases

- If a requested panel's required canonical input table is missing, the CLI fails with an actionable validation error before writing that panel artifact or registering it in the manifest.
- If optional `environment`, `participants`, `alerts`, or `clinical_outcomes` inputs are missing for a panel that can still render, the panel renders visible unavailable or warning sections and records the condition in metadata.
- If `--participant-id` is omitted for longitudinal participant-focused panels, the system chooses the participant with the richest combination of observed vitals, alerts, and outcomes, then records the selected participant id and selection basis in the manifest.
- If `--participant-id` is supplied but not found, the CLI fails before writing affected participant-specific artifacts.
- If `--week-start` is greater than `--week-end`, the CLI fails with an actionable validation error before writing affected artifacts.
- If the requested week range partially overlaps observed data, the panel renders the available overlap and makes empty or missing ranges visible.
- If more than 250 participants exist for the missingness matrix, display rows are downsampled deterministically, but all summary metrics use the full cohort.
- If timestamps or suitable proxies are absent for gap-clustering summaries, the panel marks those summaries unavailable and records a manifest warning.
- If clinical thresholds, reference bands, schema ranges, or units are unavailable for a vital, the panel renders observed data without inventing thresholds and records the missing reference source when relevant.
- If a data-quality score component cannot be computed, its weight is redistributed across computable components and the adjusted formula is documented in metadata.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST create or update `src/visualization/eda_longitudinal.py` for longitudinal EDA rendering.
- **FR-002**: The system MUST create or update `src/visualization/patient_view.py` for single-participant timeline rendering.
- **FR-003**: The system MUST create or update `tests/test_eda_longitudinal_outputs.py` and `tests/test_patient_timeline.py`.
- **FR-004**: The system MUST generate `outputs/figures/eda/05_vital_trajectories.png`.
- **FR-005**: The system MUST generate `outputs/figures/eda/06_missingness_adherence.png`.
- **FR-006**: The system MUST generate `outputs/figures/eda/07_patient_timeline.png`.
- **FR-007**: The system MUST generate `outputs/figures/eda/08_data_quality_scorecard.png`.
- **FR-008**: The system MUST generate `outputs/figures/eda/09_missingness_mechanism.png`.
- **FR-009**: Every generated repo-relative longitudinal dashboard artifact MUST be registered in `outputs/figures/manifest.json`; outside-repository output paths MUST warn and remain unregistered.
- **FR-010**: Every generated longitudinal dashboard artifact MUST be at least 1600 x 900 pixels and include a title, subtitle, labels, units where available, and direct annotations where feasible.
- **FR-011**: The CLI MUST support `python -m src.visualization.generate_eda --data-dir data/raw --out-dir outputs/figures/eda --panels longitudinal`.
- **FR-012**: The CLI MUST support longitudinal static-render flags `--participant-id`, `--week-start`, `--week-end`, and `--overlay-environment true|false`; week filters MUST be inclusive, 1-based study-week filters derived from study-day values.
- **FR-013**: The CLI MUST support participant-specific longitudinal rendering with `python -m src.visualization.generate_eda --data-dir data/raw --out-dir outputs/figures/eda --panels longitudinal --participant-id PARTICIPANT_ID --overlay-environment true`.
- **FR-014**: If no participant id is supplied for participant-focused longitudinal views, the system MUST choose the participant with the highest deterministic `observed_vital_days + distinct_alert_days + distinct_outcome_events` score, break ties by observed vital variable count and then lexicographic participant id, and MUST record the selected participant id, score components, and selection basis in the manifest.
- **FR-015**: Panel 5 MUST use `daily_vitals`, optional `environment`, and optional `participants` inputs to render cohort aggregate trajectories by study day or week.
- **FR-016**: Panel 5 MUST include SBP, DBP, HR, RR, skin temperature, weight, body water, sleep, and steps.
- **FR-017**: Panel 5 MUST show an observed-day denominator for trajectory data.
- **FR-018**: Panel 5 MUST support an ambient temperature or heat index overlay when environment data are available and `--overlay-environment` is true; the default overlay setting MUST be false.
- **FR-019**: Panel 5 MUST render missing longitudinal observations as visible gaps and MUST NOT interpolate missing days.
- **FR-020**: Panel 6 MUST use `daily_vitals`, `staff_contacts`, and optional `alerts` inputs to render a participant x study day missingness matrix, wear-hours over time, scale-adherence over time, adherence decline summary, missingness by variable, and gap clustering summary where supported.
- **FR-021**: Panel 6 MUST summarize overnight, feeding/morning, hot afternoon, and late-study decline gap clusters if timestamps or suitable proxies exist.
- **FR-022**: Panel 6 MUST make missing/present states explicit with labels, legends, symbols, or patterns and MUST NOT rely on color alone.
- **FR-023**: Panel 6 MUST downsample displayed rows deterministically when more than 250 participants are present, compute metrics on all participants, and state the downsampling behavior in the subtitle.
- **FR-024**: Panel 7 MUST use `participants`, `daily_vitals`, `alerts`, `staff_contacts`, `clinical_outcomes`, and optional `environment` inputs to render one participant's longitudinal record on one dashboard page.
- **FR-025**: Panel 7 MUST include vital trajectories, alert event markers, staff-contact event markers, clinical-outcome event markers, missingness/wear bottom track, and optional heat index or ambient temperature overlay; event markers MUST require participant id and event-date roles for alerts, staff contacts, and clinical outcomes before the timeline artifact is written.
- **FR-026**: Panel 7 MUST show clinical thresholds or reference bands where available and MUST NOT invent thresholds where reference sources are absent.
- **FR-027**: Panel 7 MUST render vital gaps as gaps, align all tracks on the same study-day x-axis, and label capture-worthy extremes directly where feasible.
- **FR-028**: Panel 7 MUST include a participant summary card with PIH severity, AC access, insurance, parity, and baseline psychosocial fields where available.
- **FR-029**: Panel 8 MUST use `daily_vitals` and `staff_contacts` to render per-participant wear completeness, scale adherence, valid-signal hours, number and duration of gaps, and composite data-quality score.
- **FR-030**: Panel 8 MUST calculate `quality_score = 0.40 * wear_completeness + 0.25 * scale_adherence + 0.20 * vital_completeness + 0.15 * contact_traceability` when all components are available.
- **FR-031**: Panel 8 score components MUST be normalized to 0-1 participant-level scores against each participant's expected observed study-day denominator when available; components with no valid denominator MUST be treated as unavailable rather than zero.
- **FR-032**: Panel 8 MUST redistribute unavailable score-component weights across available components and MUST record a warning plus adjusted formula metadata in the manifest.
- **FR-033**: Panel 8 MUST rank participants by data completeness and signal quality, not clinical risk.
- **FR-034**: Panel 9 MUST use `participants`, `daily_vitals`, optional `environment`, and optional `clinical_outcomes` inputs to render exploratory MCAR/MAR/MNAR missingness diagnostics.
- **FR-035**: Panel 9 MUST show missingness rate by study day, by archetype if available, and by AC access, insurance, PIH severity, and health literacy where available.
- **FR-036**: Panel 9 MUST show missingness versus heat exposure when environment data are available.
- **FR-037**: Panel 9 MUST show missingness versus recent abnormal vitals when recent abnormal vital context can be derived from observed values.
- **FR-038**: Panel 9 MUST clearly label mechanism patterns as exploratory "signals consistent with" MCAR, MAR, or MNAR hypotheses and MUST NOT label any mechanism as proven.
- **FR-039**: Longitudinal dashboards MUST present descriptive observed data only and MUST NOT predict outcomes or impute missing values.
- **FR-040**: Missing optional roles MUST render visible unavailable or warning sections rather than crashes.
- **FR-041**: Missing values MUST be counted and displayed where relevant.
- **FR-042**: When a requested longitudinal panel's required semantic role is missing from an available input table, the CLI MUST fail with an actionable validation error before writing that panel artifact or registering it in the manifest; optional roles continue to render visible unavailable or warning sections.

### Key Entities

- **Longitudinal EDA Dashboard Artifact**: A static PNG generated from canonical longitudinal tables and registered in the figure manifest.
- **Vital Trajectory Panel**: Panel 5 artifact showing cohort aggregate and selected-participant vital trajectories over study time.
- **Missingness and Adherence Panel**: Panel 6 artifact showing participant-day presence, wear, scale adherence, variable missingness, and gap patterns.
- **Patient Timeline Panel**: Panel 7 artifact showing one participant's aligned vitals, alerts, contacts, outcomes, missingness, wear, environmental context, and participant summary.
- **Data-Quality Scorecard**: Panel 8 artifact ranking participants by completeness and signal-quality components.
- **Missingness Mechanism Diagnostics Panel**: Panel 9 artifact showing exploratory evidence for missingness patterns without making causal or mechanism-proof claims.
- **Selected Participant Context**: Metadata describing the participant id used for participant-focused rendering and whether it was supplied by the user or selected automatically.
- **Quality Score Component**: A normalized component used in the composite score, including wear completeness, scale adherence, vital completeness, and contact traceability.
- **Gap Cluster Summary**: A labeled summary of missingness gaps by timing pattern when timestamps or proxies support classification.
- **Manifest Warning**: Structured metadata explaining unavailable optional data, missing score components, adjusted formulas, downsampling, or unsupported diagnostic summaries.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All five required PNG artifacts exist under `outputs/figures/eda/`.
- **SC-002**: Each required longitudinal PNG artifact is at least 1600 x 900 pixels.
- **SC-003**: Each required longitudinal artifact has a corresponding entry in `outputs/figures/manifest.json`.
- **SC-004**: Missing longitudinal observations appear as visible gaps in trajectory and timeline panels.
- **SC-005**: No longitudinal panel imputes missing observations for visualization, scoring, or diagnostics.
- **SC-006**: The patient timeline fits on one dashboard page and includes vitals, alerts, contacts, outcomes, and a data-quality or missingness/wear track when available.
- **SC-007**: The data-quality score formula is implemented and documented in output metadata.
- **SC-008**: Missing data-quality score components trigger redistributed weights and a manifest warning that documents the adjusted formula.
- **SC-009**: Automatic participant selection records the selected participant id and selection basis in the manifest when no participant id is supplied.
- **SC-010**: Missingness-mechanism diagnostics are labeled as exploratory evidence, not proof.
- **SC-011**: Missing/present states in the adherence panel are understandable without relying on color alone.
- **SC-012**: The focused longitudinal EDA tests pass: `pytest tests/test_eda_longitudinal_outputs.py tests/test_patient_timeline.py`.

## Assumptions

- SPEC-001 provides canonical table expectations and validation behavior for required longitudinal inputs.
- SPEC-004 provides the visualization foundation, schema registry, design system, artifact manifest contract, and missing optional role behavior.
- SPEC-007 provides the core descriptive EDA CLI and artifact numbering context for panels 1 through 4.
- The pasted dependency names `SPEC-004A` and `SPEC-004B` are interpreted as the renamed repository specs SPEC-004 and SPEC-007.
- SPEC-005 synthetic longitudinal data may be used as optional fixtures or quickstart data, but generated dashboards must also support canonical raw data.
- This feature presents observed data only; prediction, clinical risk ranking, imputation, and causal missingness-mechanism claims are out of scope.
