---
id: SPEC-005
title: Synthetic Longitudinal Physiologic Data Simulator
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-001, SPEC-004A]
implements: [P2, P3, P5, P7, P8, P9]
supersedes: null
superseded_by: null
related: [SPEC-004A, SPEC-004B, SPEC-006, SPEC-007]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Feature Specification: Synthetic Longitudinal Physiologic Data Simulator

**Feature Branch**: `005-synthetic-longitudinal-simulator`

**Created**: 2026-06-01

**Status**: Draft

**Input**: User description: "SPEC-005 - Synthetic Longitudinal Physiologic Data Simulator. Replace or extend the current flat MEOWS-style synthetic generator with a seeded longitudinal cohort simulator that produces schema-conforming tables for descriptive and analytic dashboards. The simulator must encode cardiovascular-risk, heat-strain, overlap, adherence, missingness, and event-rate structure while preserving raw missing values and validating against the schema registry."

## Clarifications

### Session 2026-06-01

- Q: What default study duration should the simulator use? -> A: 84 study days, matching a true 12-week postpartum window.
- Q: What temperature units should exported synthetic tables use? -> A: Export temperature and heat-index columns in Celsius; Fahrenheit scenario defaults are converted in effective configuration and summary reporting.
- Q: What should happen when generated artifacts fail schema validation? -> A: Export the artifacts for debugging, mark the summary failed/not ready, and return a non-zero status.
- Q: What row grain should daily vitals exports use? -> A: Use a full participant-day grid for the configured study window; nulls mark missed observations and dropout.
- Q: What should happen when required target diagnostics miss tolerance? -> A: Keep artifacts inspectable, mark the run failed/not ready, and return a non-zero status.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Reproducible Longitudinal Cohorts (Priority: P1)

A maintainer needs a canonical synthetic cohort generator that creates a multi-day postpartum monitoring dataset for all dashboard and modeling specs. The generated package includes participants, daily observations, alerts, contacts, outcomes, environment, recruitment, the effective configuration, and a run summary under stable artifact names.

**Why this priority**: Reproducible synthetic data is the base material for descriptive dashboards, analytic dashboards, and honest model evaluation. Without a deterministic longitudinal package, later specs cannot share one source of truth.

**Independent Test**: Generate the default cohort twice with the same seed and configuration, then verify the exported table contents match exactly except for explicitly allowed run metadata, and verify the package validates against the schema registry.

**Acceptance Scenarios**:

1. **Given** the default simulator settings, **when** a contributor generates a cohort, **then** the output package contains `participants.csv`, `daily_vitals.csv`, `alerts.csv`, `staff_contacts.csv`, `clinical_outcomes.csv`, `environment.csv`, `recruitment.csv`, `simulation_config_used.yaml`, and `simulation_summary.json`.
2. **Given** the same seed and same configuration, **when** the cohort is generated twice, **then** all exported table contents are identical except for explicitly allowed timestamp metadata.
3. **Given** the generated output package, **when** schema validation runs, **then** every required current table and column role validates successfully.
4. **Given** the generated daily vitals table, **when** its row count is checked, **then** it contains one row per participant-day across the configured study window.
5. **Given** downstream dashboard or model specs request synthetic data, **when** no alternate generator is selected, **then** this longitudinal simulator is treated as the canonical synthetic source.

---

### User Story 2 - Encode Clinically Plausible Physiologic Signals (Priority: P1)

A clinical analyst needs synthetic observations that reflect postpartum cardiovascular risk, heat strain, and their difficult overlap cases. Cardiovascular trajectories show gradual blood pressure, heart rate, and body-water increase; heat-strain days show acute heart-rate and skin-temperature increase with body-water decrease; overlap cases contain both alert-like signal families without becoming perfectly separable.

**Why this priority**: Project Lullaby's central analytic question depends on distinguishing cardiovascular deterioration from heat strain without oversimplifying the synthetic physiology.

**Independent Test**: Inspect generated participant-day trajectories and summary diagnostics to confirm cardiovascular cases, heat-strain days, and overlap cases meet the expected directional patterns while retaining ambiguous examples.

**Acceptance Scenarios**:

1. **Given** a participant with a true or emerging cardiovascular event and enough pre-event observations, **when** the seven days before the event are summarized, **then** the median body-water slope is positive.
2. **Given** a heat-strain day, **when** same-day physiologic deltas are summarized, **then** body-water decrease occurs more often than body-water increase alongside heart-rate and skin-temperature increase.
3. **Given** a hot day for a participant with pregnancy-induced hypertension or elevated baseline cardiovascular risk, **when** alerts and physiologic values are reviewed, **then** both cardiovascular-like and heat-like signals may appear.
4. **Given** overlap cases, **when** body-water direction is evaluated, **then** it remains informative but imperfect and does not make the cohort trivially separable.

---

### User Story 3 - Represent Adherence and Missingness Mechanisms (Priority: P2)

A data scientist needs missing data to behave like participant burden, heat exposure, access to cooling, adherence decline, and worsening health state rather than random noise alone. The simulator preserves missing cells and clustered observation gaps in raw exports so dashboards can show meaningful missingness.

**Why this priority**: Missingness is source evidence in Project Lullaby. Treating missing values as merely random would hide the participant-context constraints that the product is meant to surface.

**Independent Test**: Generate a cohort and verify aggregate adherence declines over study time, missingness differs by archetype and heat exposure, dropout increases with late-study burden or worsening physiologic state, and raw exports keep missing values missing.

**Acceptance Scenarios**:

1. **Given** participants with declining adherence archetypes, **when** wear hours and scale adherence are summarized by study week, **then** adherence declines over time in aggregate.
2. **Given** hot afternoons and participants without reliable cooling access, **when** missingness is summarized, **then** hot-afternoon gaps occur more often than on non-hot comparison periods.
3. **Given** worsening physiologic state, **when** dropout and partial observation rates are summarized, **then** worsening state is associated with increased missingness.
4. **Given** raw synthetic tables, **when** missing observations are exported, **then** they remain missing rather than being imputed or replaced by sentinel values.

---

### User Story 4 - Configure Cohort Mix, Events, and Heat Context (Priority: P2)

A maintainer needs the simulator to be configurable for cohort size, study length, random seed, archetype mix, event rates, heat season behavior, adherence parameters, missingness mechanisms, physiologic effect sizes, and alert follow-up behavior.

**Why this priority**: Later dashboards and modeling experiments need repeatable scenario variants without changing the feature contract or breaking schema conformance.

**Independent Test**: Run the simulator with default and modified settings, then verify event rates, archetype proportions, heat exposure patterns, and adherence summaries move toward configured targets within the documented tolerance.

**Acceptance Scenarios**:

1. **Given** archetype weights that do not sum to one, **when** a cohort is generated, **then** the weights are normalized and the run summary records the effective proportions.
2. **Given** a configured cardiovascular event rate, heat illness rate, emergency department visit rate, and hospitalization rate, **when** the default-size cohort is generated, **then** observed rates match targets within the documented tolerance for that cohort size.
3. **Given** heat-season settings, **when** environment observations are generated, **then** hot days, heat waves, and heat-index variation reflect the configured scenario.
4. **Given** alert follow-up settings, **when** alerts and contacts are generated, **then** survey and call completion rates are reflected in the output package and summary.

---

### User Story 5 - Publish Diagnostics for Downstream Trust (Priority: P3)

A dashboard author or model evaluator needs a concise run summary that explains whether the synthetic dataset achieved its target structure before relying on it. The summary reports schema validation status, event rates, archetype mix, adherence trends, missingness diagnostics, and physiologic directional checks.

**Why this priority**: Diagnostics make the generated data auditable and help downstream specs avoid silently using a malformed or misleading cohort.

**Independent Test**: Generate a cohort and confirm the summary reports all target checks, flags any target misses, and identifies whether the output is ready for downstream descriptive and analytic dashboards.

**Acceptance Scenarios**:

1. **Given** a successful generation run, **when** the summary is opened, **then** it reports event rates, archetype proportions, adherence decline, missingness diagnostics, physiologic directional checks, and schema validation status.
2. **Given** a generation run that misses a required configured tolerance, **when** the run completes, **then** the artifacts remain available for inspection, the summary marks the run failed/not ready, and the generation command reports failure.
3. **Given** generated artifacts fail schema validation, **when** the run completes, **then** the artifacts remain available for debugging, the summary marks the run failed/not ready, and the generation command reports failure.
4. **Given** downstream specs depend on synthetic data, **when** they inspect the run summary, **then** they can determine whether the cohort is suitable for dashboard or modeling use.

### Edge Cases

- Archetype weights may not sum to 1.0; effective weights MUST be normalized and reported.
- Small cohorts may show sampling noise; documented tolerances MUST distinguish the default cohort size from larger runs.
- Required target diagnostics that miss tolerance MUST keep artifacts available for inspection while marking the run failed/not ready.
- Participants may have too few observed pre-event days because of dropout or missingness; directional checks MUST report denominator counts rather than pretending every case is fully observed.
- Heat strain and cardiovascular risk may co-occur; the simulator MUST preserve ambiguous overlap cases.
- Body-water direction is important but MUST NOT become a perfect label proxy across all generated days.
- Missingness may remove values needed for some daily deltas; diagnostics MUST use available observations and disclose coverage.
- Raw exports MUST preserve missing values even when summaries compute aggregate diagnostics.
- Daily vitals exports MUST retain participant-day rows after missed observations and dropout, with unobserved values left null.
- If schema validation fails after generation, artifacts MUST remain available for debugging while the summary marks the run failed/not ready.
- Heat-season behavior may be disabled or modified; environment outputs MUST remain schema-conforming.
- Legacy flat synthetic data may remain for backward compatibility, but this simulator is the canonical source for new descriptive and analytic dashboard workflows.
- Generated data is synthetic and MUST NOT be presented as real participant data.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST generate a seeded longitudinal synthetic postpartum cohort across a configurable number of participants and study days.
- **FR-002**: The system MUST produce identical exported table contents for repeated runs with the same seed and effective configuration, except for explicitly allowed run metadata.
- **FR-003**: The generated output package MUST default to `data/synthetic/longitudinal/` and MUST include `participants.csv`, `daily_vitals.csv`, `alerts.csv`, `staff_contacts.csv`, `clinical_outcomes.csv`, `environment.csv`, `recruitment.csv`, `simulation_config_used.yaml`, and `simulation_summary.json`.
- **FR-004**: Generated tabular artifacts MUST validate against the schema registry before the output package is considered ready for downstream use.
- **FR-004A**: If generated artifacts fail schema validation, the system MUST leave the generated artifacts available for debugging, mark the simulation summary as failed/not ready, and report generation failure to the caller.
- **FR-005**: The simulator MUST support the archetypes diligent monitor, overwhelmed mom, heat stressed, true emergency, and silent decliner, each with configurable target weight, adherence behavior, missingness pattern, and physiologic risk profile; default target weights MUST be 0.30, 0.30, 0.15, 0.06, and 0.14 respectively before normalization.
- **FR-006**: Archetype target weights MUST be normalized when configured weights do not sum to 1.0, and the effective weights MUST be recorded in the run summary.
- **FR-007**: The default configuration MUST define seed 20260601, 200 participants, 84 study days (12 weeks), event-rate targets for cardiovascular events, heat illness, emergency department visits, and hospitalization, summer heat behavior, adherence decline, missingness behavior, physiologic effect ranges, and alert follow-up probabilities.
- **FR-008**: Default event-rate targets MUST be 0.075 for cardiovascular events, 0.05 for heat illness, 0.10 for emergency department visits, and 0.04 for hospitalization.
- **FR-009**: Default summer heat settings MUST be enabled from 2026-06-01, with baseline temperature 94 F, heat-wave probability 0.20, heat-wave temperature 108 F, and heat-index noise standard deviation 4 F; exported temperature and heat-index table columns MUST use Celsius to align with the schema registry.
- **FR-010**: Default adherence settings MUST start wear hours around 18 hours per day, decline by 0.8 hours per week, start scale adherence probability at 0.85, and decline scale adherence probability by 0.08 per week.
- **FR-011**: Default missingness settings MUST include random cell missingness rate 0.03, participant dropout rate 0.08, clustered gap probability 0.15, and hot-afternoon gap multiplier 2.0.
- **FR-012**: Default physiologic effect ranges MUST include cardiovascular blood-pressure slope 0.6 to 1.4 per day, cardiovascular heart-rate slope 0.2 to 0.8 per day, cardiovascular body-water slope 0.05 to 0.20 per day, heat heart-rate spike 10 to 28, heat skin-temperature spike 1.0 F to 4.0 F, and heat body-water drop 0.3 to 1.5; exported skin-temperature effects MUST be represented in Celsius.
- **FR-013**: Default alert follow-up probabilities MUST include survey completion probability 0.65 and call completion probability 0.55.
- **FR-014**: For each participant-day, the simulator MUST represent latent baseline risk, archetype, pregnancy-induced hypertension severity, cooling access, environmental heat exposure, adherence probability, missingness probability, and event risk.
- **FR-015**: Daily vitals exports MUST contain one row per participant-day across the configured study window, and daily observations MUST include systolic blood pressure, diastolic blood pressure, heart rate, respiratory rate, skin temperature, weight, body water, sleep, steps, wear hours, and scale adherence when observed.
- **FR-015A**: Missed observations and post-dropout participant-days MUST remain present in daily vitals exports with unobserved values left null.
- **FR-016**: Cardiovascular-risk trajectories MUST encode gradual multi-day increases in systolic blood pressure, diastolic blood pressure, heart rate, and body water.
- **FR-017**: Heat-strain days MUST encode acute heart-rate and skin-temperature increases, normal or low blood pressure behavior, and body-water decrease more often than increase.
- **FR-018**: For true or emerging cardiovascular cases with enough observed pre-event data, the median body-water slope in the seven days before event MUST be positive.
- **FR-019**: In overlap cases, cardiovascular-like and heat-like signals MUST be able to appear together, and body-water direction MUST remain informative but imperfect.
- **FR-020**: The simulator MUST avoid making cardiovascular risk and heat strain trivially separable by any single generated measure.
- **FR-021**: Missingness MUST include low-rate random cell missingness, missingness associated with observed context, missingness associated with worsening physiologic state, clustered gaps, and late-study adherence decline.
- **FR-022**: Clustered gaps MUST include overnight, feeding or morning, hot-afternoon, and late-study adherence-decline patterns.
- **FR-023**: Missing values in raw synthetic exports MUST remain missing and MUST NOT be silently imputed or replaced.
- **FR-024**: The simulator MUST generate alerts, staff contacts, and completion outcomes that reflect configured alert thresholds and follow-up probabilities.
- **FR-025**: The run summary MUST report event rates, archetype proportions, adherence trends, missingness diagnostics, physiologic directional checks, effective configuration, and schema validation status.
- **FR-026**: Event-rate and archetype diagnostics MUST compare observed results to configured targets using documented tolerances that account for cohort size.
- **FR-026A**: Required target diagnostic failures MUST leave generated artifacts inspectable, mark the simulation summary as failed/not ready, and report generation failure to the caller.
- **FR-027**: A clone-to-run local generation command MUST allow a contributor to choose configuration, output location, and seed without editing source files.
- **FR-028**: The existing flat synthetic generator MAY remain for backward compatibility, but new descriptive and analytic dashboard workflows MUST use this longitudinal simulator as the canonical synthetic source.

### Key Entities *(include if feature involves data)*

- **Simulation Configuration**: The effective set of seed, cohort size, study duration, event-rate targets, heat settings, adherence settings, missingness settings, physiologic effect ranges, alert settings, and archetype weights used for a generation run.
- **Archetype**: A configurable participant pattern describing expected prevalence, adherence behavior, missingness pattern, and physiologic risk tendency.
- **Participant**: A synthetic postpartum participant with baseline risk, pregnancy-induced hypertension context, cooling access, and demographic or support attributes needed by downstream dashboards.
- **Participant-Day**: One daily monitoring state for a participant for every day in the configured study window, including latent risk, observed vitals when present, activity, sleep, adherence, dropout, and missingness.
- **Environment Day**: Heat and exposure context for calendar days used to distinguish heat strain from cardiovascular risk and to drive heat-related missingness.
- **Alert**: A generated alert-like event with level, trigger reasons, classification context, and follow-up relationship to participant-day observations.
- **Staff Contact**: A generated survey, nurse call, or follow-up contact with completion status and reason.
- **Clinical Outcome**: A participant-level or date-specific cardiovascular event, heat illness, emergency department visit, or hospitalization indicator.
- **Recruitment Record**: Synthetic enrollment context needed for descriptive dashboards and cohort accounting.
- **Simulation Summary**: Auditable diagnostics describing whether the run achieved configured targets and is suitable for downstream dashboard or modeling use.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Running the generator twice with the same seed and effective configuration produces identical exported table contents, except for explicitly allowed timestamp metadata.
- **SC-002**: Generated tabular artifacts validate against the schema registry with no required-role failures.
- **SC-002A**: When schema validation fails in a controlled test, the generated artifacts remain inspectable, the summary reports failed/not ready status, and the generation command reports failure.
- **SC-002B**: The daily vitals table row count equals participant count multiplied by configured study days, with missed or post-dropout observations represented by null values.
- **SC-003**: For a 200-participant default cohort, configured cardiovascular event, heat illness, emergency department visit, and hospitalization rates match targets within absolute tolerance 0.03; larger cohorts use tighter documented tolerance.
- **SC-004**: For a 200-participant default cohort, observed archetype proportions match target weights within absolute tolerance 0.05.
- **SC-005**: Aggregate wear hours and scale adherence decline over study time in the generated cohort.
- **SC-006**: True or emerging cardiovascular cases with enough observed pre-event data show positive seven-day pre-event body-water trend more often than non-cases, and required true-event directional checks pass.
- **SC-007**: Heat-strain days show body-water decrease with heart-rate and skin-temperature increase more often than not.
- **SC-008**: Missingness diagnostics identify non-random missingness patterns by archetype, heat exposure, adherence, and worsening physiologic state.
- **SC-009**: Raw exported tables retain missing values in cells where observations were not generated or not observed.
- **SC-010**: Overlap diagnostics demonstrate that body-water direction is useful but imperfect and that cardiovascular and heat-strain examples are not perfectly separable by one raw measure.
- **SC-011**: The default generation run produces a summary that reports all target checks, observed values, tolerances, and pass/fail status for downstream dashboard readiness.
- **SC-011A**: When a controlled run misses a required target tolerance, artifacts remain inspectable, the summary reports failed/not ready status, and the generation command reports failure.

## Assumptions

- SPEC-001 remains the authoritative canonical schema baseline, and SPEC-004A provides the schema registry used to validate generated exports.
- The default study window is 84 days (12 weeks), with future specs able to extend the window through configuration.
- Generated data is wholly synthetic and contains no real participant records or protected health information.
- The simulator generates raw synthetic tables and diagnostics; downstream feature engineering for modeling remains the responsibility of later analytic specs.
- Alert threshold definitions are treated as safety-critical configuration and are not casually changed by this feature.
- Small default cohorts are expected to have sampling variability, so event-rate and archetype checks use explicit tolerances.
- Environment and recruitment tables are required outputs for this simulator even if some downstream dashboards initially use only participant, vitals, alert, contact, and outcome tables.
