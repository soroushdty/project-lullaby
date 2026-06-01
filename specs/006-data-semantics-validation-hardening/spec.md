---
id: SPEC-006
title: Data Semantics and Validation Hardening
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-001, SPEC-003, SPEC-004A, SPEC-005]
implements: [P3, P5, P7, P10]
supersedes: null
superseded_by: null
related: [SPEC-003, SPEC-004A, SPEC-005]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Feature Specification: Data Semantics and Validation Hardening

**Feature Branch**: `006-data-semantics-validation-hardening`

**Created**: 2026-06-01

**Status**: Draft

**Input**: User description: "Create a deferred bugfix spec from repo-wide findings covering missing-value semantics, boolean parsing, schema failure visibility, alert funnel state handling, simulator diagnostics, and EDA category completeness."

## Clarifications

### Session 2026-06-01

- Q: When a requested dashboard panel has an invalid required input, should generation fail before writing/registering artifacts or continue partially? -> A: Fail before writing/registering requested dashboard artifacts if any required input for requested panels is invalid.
- Q: How should invalid boolean-like tokens be handled in required versus optional roles? -> A: Fail invalid tokens in required roles; warn and treat invalid optional-role tokens as `Missing/Unknown`.
- Q: How should generated artifacts outside `outputs/figures/**` be registered? -> A: Register every generated artifact with a repo-relative path in the default manifest; warn clearly for outputs outside the repo.
- Q: How should descriptive category charts handle too many clinically meaningful categories for readable labels? -> A: Show all categories when readable; otherwise use an explicit overflow table or manifest record preserving every category and count.
- Q: Should hardening changes require regenerating existing tracked dashboard artifacts and the manifest? -> A: Regenerate affected tracked dashboard artifacts and `outputs/figures/manifest.json` after fixes.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Preserve Missingness as Evidence (Priority: P1)

A dashboard author needs EDA panels and diagnostic summaries to distinguish true negative values from missing or unknown values. Missing outcomes, risk indicators, call states, and contact states must not be silently treated as false.

**Why this priority**: Project Lullaby treats missingness as meaningful source evidence. Treating missing values as negative can understate risk, inflate denominators, and make dashboards look more certain than the data supports.

**Independent Test**: Run EDA generation and focused unit tests with fixture tables containing true, false, missing, unknown, and blank values for outcomes, risk indicators, survey states, call states, and contact states.

**Acceptance Scenarios**:

1. **Given** clinical outcome fields with missing event values, **when** outcome prevalence is rendered, **then** positive, negative, and missing/unknown counts are displayed separately.
2. **Given** participant risk indicators with missing values, **when** the cohort overview renders comorbidities and risk indicators, **then** missing/unknown values are counted explicitly and not included as "No".
3. **Given** alerts or contacts with missing call or completion state, **when** the engagement funnel is computed, **then** missing state is displayed as its own category and is not inferred as incomplete.
4. **Given** the dashboard denominator includes records with missing values, **when** a percentage is shown, **then** the numerator, denominator, and missing count are directly visible or annotated.

---

### User Story 2 - Parse Boolean-Like Values Consistently (Priority: P1)

A maintainer needs ingestion, simulation diagnostics, EDA panels, and tests to parse boolean-like values consistently across in-memory tables and CSV-loaded tables.

**Why this priority**: Pandas truthiness treats non-empty strings such as "False" and "0" as true when `.astype(bool)` is used. That can corrupt pending-ingestion filters, event-rate diagnostics, adherence checks, and test assertions.

**Independent Test**: Exercise the shared boolean parsing behavior against booleans, numeric flags, common string flags, blanks, nulls, and invalid values across ingestion, simulator diagnostics, EDA, and tests.

**Acceptance Scenarios**:

1. **Given** a stream queue contains `processed` values of `true`, `false`, `1`, `0`, `yes`, `no`, blanks, and nulls, **when** pending records are selected, **then** only explicitly unprocessed or missing-policy-eligible rows are selected.
2. **Given** simulator diagnostic inputs contain object or string boolean columns, **when** event rates and adherence rates are computed, **then** "False" and "0" are parsed as false rather than true.
3. **Given** tests load exported CSV tables, **when** boolean metrics are asserted, **then** the same explicit parser used by production code is used by the test expectation.
4. **Given** an invalid boolean-like token appears in a required boolean role, **when** validation runs, **then** the result reports a clear data-quality error instead of guessing.
5. **Given** an invalid boolean-like token appears only in an optional boolean role, **when** validation and rendering run, **then** the result emits a structured warning and downstream displays treat the value as `Missing/Unknown`.

---

### User Story 3 - Fail Clearly on Required Schema Problems (Priority: P2)

A contributor running dashboards or diagnostics needs required-table and required-role failures to be visible. Optional inputs may degrade to unavailable panels, but required inputs must not silently become empty tables.

**Why this priority**: A dashboard can render attractive but misleading figures if a required source file, required role, or schema-valid table is missing and the loader replaces it with an empty DataFrame.

**Independent Test**: Run dashboard generation with fixtures that omit required entities, omit optional entities, and include schema-invalid entities.

**Acceptance Scenarios**:

1. **Given** a required EDA input table is missing or schema-invalid, **when** dashboard generation runs, **then** the command fails before writing or registering requested dashboard artifacts and reports a clear message naming the entity, path, and validation failure.
2. **Given** an optional EDA input table is missing, **when** dashboard generation runs, **then** the affected section renders a labeled unavailable card and the command continues.
3. **Given** an alternate data directory lacks a required table, **when** generation is requested for a panel that requires that table, **then** the failure is visible in command output and no misleading successful artifact is registered for that panel.
4. **Given** validation produces warnings for optional roles, **when** artifacts are registered, **then** the warnings remain attached to the manifest entry.
5. **Given** a dashboard writes artifacts to an alternate repo-relative output directory, **when** generation succeeds, **then** each generated artifact is registered in the default manifest with its repo-relative path.
6. **Given** a dashboard writes artifacts outside the repository, **when** generation succeeds, **then** the command warns that those outside-repo artifacts are not registered in the default manifest.
7. **Given** a hardening fix changes dashboard semantics, warning behavior, category completeness, or artifact registration, **when** the fix is completed, **then** affected tracked dashboard artifacts and `outputs/figures/manifest.json` are regenerated.

---

### User Story 4 - Keep Descriptive Categories Complete (Priority: P3)

A clinical analyst reviewing descriptive dashboards needs low-count categories and rare trigger reasons to remain visible unless truncation is explicit and auditable.

**Why this priority**: Rare categories may be clinically or operationally important. Descriptive EDA should not hide them through top-N plotting defaults.

**Independent Test**: Render EDA fixtures containing more categories than the default visual space allows, including low-count alert trigger reasons and demographic categories.

**Acceptance Scenarios**:

1. **Given** alert trigger reasons include more than eight categories, **when** the alert trigger panel renders, **then** every category is displayed when readable, or an explicit overflow table or manifest record reports every category and count.
2. **Given** demographic or equity-relevant fields contain low-count categories, **when** cohort overview renders, **then** low-count categories are not suppressed.
3. **Given** a figure uses a grouped "Other" category for visual space, **when** the artifact is generated, **then** the grouped source categories and counts are available in the figure annotation or companion manifest metadata.

### Edge Cases

- Boolean-like values may arrive as native booleans, integers, floats, strings, blanks, nulls, or mixed object columns.
- Invalid boolean-like tokens may appear in required or optional roles; required-role invalids fail, while optional-role invalids warn and render as `Missing/Unknown`.
- Missing outcome values must not be counted as negatives in prevalence or class-imbalance calculations.
- Missing risk indicators must not be counted as absence of risk.
- Missing survey, call, or contact completion states must not be inferred as incomplete or complete.
- Nurse contact outcomes may include future states such as no answer, left voicemail, pending, declined, or completed.
- Optional dashboard roles may be absent; required dashboard roles may not.
- Schema validation errors may indicate missing files, missing columns, invalid values, impossible range violations, or ambiguous aliases.
- CSV-loaded synthetic outputs may infer booleans differently from in-memory generated tables.
- Low-count categories may exceed available visual space; when direct labels would be unreadable, every category and count must remain auditable through an explicit overflow table or manifest record.
- Semantic-only dashboard hardening can still change counts, labels, warnings, or manifest metadata, so affected tracked artifacts must be refreshed even when visual layout changes are small.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST centralize boolean-like value parsing for ingestion, EDA, simulator diagnostics, and tests.
- **FR-002**: The boolean parser MUST distinguish true, false, missing/unknown, and invalid tokens.
- **FR-002A**: Invalid boolean-like tokens in required roles MUST fail validation, while invalid tokens in optional roles MUST produce structured warnings and be represented downstream as `Missing/Unknown`.
- **FR-003**: The boolean parser MUST handle native booleans, numeric flags, common string flags, blanks, and nulls deterministically.
- **FR-004**: The system MUST NOT use generic `.astype(bool)` coercion for domain booleans that may originate from CSV or object-typed inputs.
- **FR-005**: Outcome prevalence dashboards MUST display missing/unknown outcome counts separately from positive and negative counts.
- **FR-006**: Class-imbalance calculations MUST NOT count missing outcome values as negative cases.
- **FR-007**: Cohort risk-indicator panels MUST count yes, no, and missing/unknown values separately.
- **FR-008**: Alert engagement funnels MUST represent missing survey, call, and contact states as explicit categories.
- **FR-009**: Alert engagement funnels MUST NOT infer completion when completion state is missing.
- **FR-010**: Nurse contact completion counts MUST use explicit completed-state mapping rather than any non-null outcome value.
- **FR-011**: Required EDA entities and required semantic roles MUST fail clearly when missing or schema-invalid.
- **FR-011A**: If any required input for a requested dashboard panel is missing or schema-invalid, the command MUST fail before writing or registering requested dashboard artifacts.
- **FR-012**: Optional EDA entities and optional semantic roles MUST render labeled unavailable or warning panels without crashing.
- **FR-013**: Schema failure messages MUST name the affected entity, expected source path when available, and failed role or validation rule.
- **FR-014**: Simulator diagnostics MUST compute event rates, adherence rates, and physiologic checks using explicit domain parsing instead of truthiness.
- **FR-015**: Tests MUST cover CSV-loaded and object-typed boolean columns, not only in-memory native booleans.
- **FR-016**: Descriptive EDA category plots MUST avoid silent top-N truncation for clinically meaningful fields.
- **FR-017**: If direct category labels would be unreadable, the figure MUST use explicit overflow behavior and preserve every omitted or grouped category and count in a visible table or artifact metadata.
- **FR-018**: Artifact registration MUST add every generated artifact with a repo-relative path to the default manifest.
- **FR-018A**: Artifact registration MUST warn clearly when an output path is outside the repository and therefore cannot be registered in the default repo-relative manifest.
- **FR-019**: Hardening changes that affect dashboard semantics, warnings, category completeness, or artifact registration MUST regenerate affected tracked dashboard artifacts and `outputs/figures/manifest.json`.

### Key Entities

- **Domain Boolean Value**: A field whose source value may represent true, false, missing/unknown, or invalid state and must be parsed without generic truthiness.
- **Missing/Unknown State**: An explicit state for absent, blank, null, or unknown values that must remain distinct from false.
- **Required EDA Entity**: A canonical table required for a requested dashboard panel to make a valid claim.
- **Optional EDA Entity**: A canonical table or role that can enrich a dashboard but may be unavailable without invalidating the panel.
- **Alert Funnel State**: The survey, call, or contact state used to compute engagement progression and conversion percentages.
- **Diagnostic Check**: A simulator summary calculation that reports target rates, adherence behavior, missingness, or physiology and must be robust to CSV-loaded values.
- **Category Completeness Record**: Metadata or visual annotation that preserves low-count or grouped category counts when space-constrained plots require summarization.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Focused boolean parsing tests pass for native booleans, numeric flags, common string flags, blanks, nulls, and invalid tokens.
- **SC-001A**: Invalid-token tests verify required-role invalids fail validation and optional-role invalids warn while rendering as `Missing/Unknown`.
- **SC-002**: Outcome prevalence fixtures with missing outcomes render positive, negative, and missing/unknown counts separately.
- **SC-003**: Risk-indicator fixtures with missing values render missing/unknown counts separately and do not count them as "No".
- **SC-004**: Alert funnel fixtures with missing survey/contact/call states display those states explicitly and do not infer completion.
- **SC-005**: Required-table and required-role dashboard fixtures fail before writing or registering requested dashboard artifacts, with clear validation errors naming the entity and missing role.
- **SC-006**: Optional-table dashboard fixtures render unavailable cards or warnings without command failure.
- **SC-007**: Simulator diagnostic tests produce the same rates for equivalent native-boolean and CSV/string-boolean inputs.
- **SC-008**: Tests fail if production code reintroduces `.astype(bool)` for domain boolean parsing.
- **SC-009**: Category completeness tests demonstrate that low-count clinically meaningful categories are directly visible when readable, or explicitly accounted for with every category and count preserved in overflow output or artifact metadata.
- **SC-010**: Manifest tests verify repo-relative alternate output directories register generated artifacts in the default manifest, while outside-repo outputs produce clear warnings.
- **SC-011**: Acceptance evidence includes regenerated affected tracked dashboard artifacts and an updated `outputs/figures/manifest.json` whenever hardening changes alter dashboard semantics, warnings, category completeness, or artifact registration.

## Assumptions

- SPEC-001 and SPEC-004A remain the authoritative sources for canonical schema roles and visualization validation behavior.
- This spec is intentionally deferred until the current implementation thread is ready to address hardening work.
- Missingness is meaningful evidence and should be preserved unless a later feature explicitly defines imputation behavior.
- Existing synthetic data may remain valid, but diagnostics must also be safe for exported CSVs and external tables that use string or object-typed boolean values.
- The default artifact manifest uses repo-relative paths; outputs outside the repository may remain unregistered but must produce explicit warnings.
- Tracked dashboard artifacts remain acceptance evidence and should match the hardened dashboard semantics after implementation.
