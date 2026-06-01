---
id: SPEC-004
title: Visualization Foundation and Schema Registry
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-001]
implements: [P3, P5, P7, P10]
supersedes: null
superseded_by: null
related: [SPEC-001, SPEC-005, SPEC-006, SPEC-007, SPEC-008]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Feature Specification: Visualization Foundation and Schema Registry

**Feature Branch**: `004-eda-descriptive-dashboard`

**Created**: 2026-06-01

**Status**: Draft

**Input**: User description: "SPEC-004 - Visualization Foundation and Schema Registry — create shared infrastructure for high-quality, schema-driven, deterministic visualization artifacts. Establish the schema registry, validation behavior, visualization design system, artifact manifest contract, visualization configuration, and root commands that later EDA, simulator, model bake-off, and analytic dashboard specs depend on."

## Clarifications

### Session 2026-06-01

- Q: Which bundled data directory is the default validation target for SPEC-004 root commands? -> A: Default to repository-root `data/` CSV files, with `--data-dir` available for alternate directories.
- Q: Should SPEC-004 require a concrete default artifact manifest file or only define the manifest schema/contract? -> A: Require `outputs/figures/manifest.json` as the default manifest path, created with an empty valid manifest when no figures exist yet.
- Q: What output contract should the repository-root schema validation command provide? -> A: Print a concise human-readable summary and also produce deterministic JSON validation results at `artifacts/validation-report.json`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Resolve Canonical Data Semantics (Priority: P1)

A visualization author wants to build dashboard figures without hardcoding raw column names. They ask the registry which entity and semantic role corresponds to a DataFrame column, confirm which required roles are present, and receive structured warnings for optional roles that are missing.

**Why this priority**: Later dashboard specs depend on schema-driven plotting. Without a registry that resolves semantic roles, every visualization risks drifting back to raw-file assumptions and brittle column-name checks.

**Independent Test**: Load the bundled cohort tables, resolve required participant, vital, alert, contact, outcome, and optional future roles, and verify required roles resolve or fail with explicit validation errors while optional roles produce warnings.

**Acceptance Scenarios**:

1. **Given** a participants table with accepted column aliases, **when** a caller requests `participant.id`, **then** the registry returns the matching DataFrame column and the participant entity metadata.
2. **Given** a table missing a required role, **when** validation runs, **then** a clear schema validation error identifies the missing role and entity.
3. **Given** a table missing an optional role, **when** validation runs, **then** the result includes a structured warning and visualization callers can continue.
4. **Given** a table with unknown extra columns, **when** validation runs, **then** the extra columns are allowed and reported only as available source context.

---

### User Story 2 - Validate Data Without Corrupting It (Priority: P1)

A data analyst checks whether bundled or newly generated tables are safe to use for dashboard generation. The validation layer flags missing required fields, optional-column gaps, and range violations without imputing values or discarding physiologic extremes that may be clinically meaningful.

**Why this priority**: Project Lullaby treats missingness and physiologic extremes as meaningful evidence. The validation foundation must fail loud on truly invalid structure while preserving capture-worthy observations for downstream review.

**Independent Test**: Run the schema validation command against bundled data and injected invalid examples; assert hard structural failures raise, optional missingness warns, extra columns pass, and range violations are reported without row removal.

**Acceptance Scenarios**:

1. **Given** a daily vitals table missing a required systolic blood pressure role, **when** validation runs, **then** validation fails with an error naming the role and source table.
2. **Given** an optional heat exposure field is absent, **when** validation runs, **then** validation returns a warning that can be rendered in a dashboard panel.
3. **Given** an impossible physiologic value outside a hard bound, **when** validation runs, **then** the result reports a range violation and does not silently drop the row.
4. **Given** a plausible but extreme physiologic value, **when** validation runs, **then** the value is labeled capture-worthy rather than removed or imputed.

---

### User Story 3 - Render Consistent Dashboard-Grade Figures (Priority: P2)

A dashboard author creates a static figure and wants it to match Project Lullaby's visual quality baseline. The shared design system provides consistent style, accessible palettes, labels, warning panels, no-data panels, and size/DPI enforcement.

**Why this priority**: The foundation must make later dashboards look coherent and accessible by default, but it depends on the schema validation behaviors that determine what each panel can safely show.

**Independent Test**: Generate sample figure panels with title, subtitle, card styling, labels, warning/no-data panels, and save attempts; assert figure dimensions, DPI, labels, and non-color category encodings meet the contract.

**Acceptance Scenarios**:

1. **Given** a figure generated through the shared design system, **when** it is saved, **then** the output meets the minimum dashboard canvas and DPI requirements.
2. **Given** a tiny/default figure, **when** saving is attempted without an explicit test override, **then** saving is rejected with a clear error.
3. **Given** a chart that displays clinically meaningful categories, **when** it is styled, **then** it uses non-color encodings such as labels, markers, line styles, hatches, or direct annotations.
4. **Given** required roles are unavailable, **when** a panel is rendered, **then** a no-data or warning panel explains the missing roles instead of crashing.

---

### User Story 4 - Register Deterministic Figure Artifacts (Priority: P2)

A maintainer needs every generated figure to be traceable to its inputs, spec, required roles, optional warnings, and output path. The artifact manifest records deterministic metadata for generated figures so later dashboard specs can verify completeness.

**Why this priority**: Honest evaluation and reproducibility require a manifest that explains what each artifact used, where it was written, and which warnings were encountered.

**Independent Test**: Confirm `outputs/figures/manifest.json` exists as a valid empty manifest before figures are generated, then register a sample artifact entry and assert it includes artifact id, path, title, spec id, input entities, required roles, optional roles used, warnings, UTC creation time, and deterministic status.

**Acceptance Scenarios**:

1. **Given** no figures have been generated yet, **when** the foundation is initialized or validated, **then** `outputs/figures/manifest.json` exists and validates as an empty manifest.
2. **Given** a generated dashboard artifact, **when** it is registered, **then** the default manifest contains the artifact metadata required for traceability.
3. **Given** an optional role warning was produced during rendering, **when** the artifact is registered, **then** the warning is preserved in the manifest entry.
4. **Given** the manifest is read back, **when** entries are validated, **then** missing required manifest fields are reported as contract failures.

---

### User Story 5 - Provide Clone-to-Run Foundation Commands (Priority: P3)

A new contributor clones the repository and wants to verify that the visualization foundation is ready before implementing later EDA dashboards. They run a schema validation command and the focused foundation tests from the repository root with no network access.

**Why this priority**: Reproducible root commands are the handoff point to later specs, but they are useful only after the registry, validation, design, and manifest contracts exist.

**Independent Test**: From a clean repository checkout with bundled repository-root `data/` CSV files only, run the schema validation command and focused foundation tests; both complete without network calls, and validation produces both a concise human-readable summary and deterministic JSON results at `artifacts/validation-report.json`.

**Acceptance Scenarios**:

1. **Given** bundled repository-root `data/` CSV files, **when** the schema validation command runs from the repository root without an explicit data directory, **then** validation uses `data/` by default and completes with a concise summary plus structured JSON results at `artifacts/validation-report.json` or clear validation errors.
2. **Given** the focused foundation tests, **when** they run from the repository root, **then** registry and visualization contract tests pass without network access.

### Edge Cases

- Optional future entities (`environment`, `recruitment`, `model_predictions`, `model_metrics`) may not exist yet; the registry MUST describe them as optional/future-capable and validation MUST not require them until their producer specs land.
- Bundled data defaults to repository-root `data/` CSV files; commands MUST also expose a `--data-dir` override for alternate local data directories.
- Column aliases may map multiple source columns to one semantic role; resolution MUST be deterministic and report ambiguous matches.
- Missing optional roles MUST be renderable as warning or no-data panels, not uncaught exceptions.
- Unknown extra columns MUST remain available to callers and MUST NOT be dropped by validation.
- Range violations MUST be reported while preserving source rows.
- The default artifact manifest may have zero entries; an empty manifest MUST still be valid and deterministic.
- Schema validation command output MUST remain readable for contributors while exposing deterministic JSON at `artifacts/validation-report.json` for automation and tests.
- Generated figure saves MUST fail clearly when the canvas is below the minimum dashboard size unless a test override is explicitly used.
- Runtime MUST avoid network calls and notebook-only flows.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST define a schema registry that describes canonical entities, including participants, daily vitals, alerts, staff contacts, clinical outcomes, and future optional environment, recruitment, model prediction, and model metric entities.
- **FR-002**: Each entity specification MUST include source filename, primary key columns, participant id column when applicable, date/time columns, required columns, optional columns, semantic roles, display labels, units, known valid ranges, missingness policy, default aggregation, and column aliases.
- **FR-003**: The registry MUST resolve semantic roles to DataFrame columns using exact names and configured aliases without requiring visualization code to hardcode raw column names.
- **FR-004**: The registry MUST expose role availability checks that distinguish required-role failures from optional-role warnings.
- **FR-005**: Validation MUST raise a clear schema validation error when required roles or required columns are missing.
- **FR-006**: Validation MUST return structured warnings for missing optional columns or roles and MUST allow callers to continue when required data is present.
- **FR-007**: Validation MUST allow unknown extra columns without dropping them.
- **FR-008**: Validation MUST report range violations without automatically removing rows.
- **FR-009**: Validation and visualization flows MUST NOT impute missing values in EDA contexts.
- **FR-010**: Plausible physiologic extremes MUST be labeled as capture-worthy unless they violate explicit hard impossible bounds.
- **FR-011**: The visualization design system MUST centralize figure background, panel background, text, muted text, grid, warning, and capture-worthy styling.
- **FR-012**: All figures using the design system MUST use a colorblind-safe palette and consistent typography, spacing, card/tile styling, gridlines, subtitles, legends, and annotations.
- **FR-013**: Saved figures MUST support at least 220 DPI and MUST reject tiny/default dashboard figures below the configured minimum size unless an explicit test override is used.
- **FR-014**: Charts that encode clinically meaningful categories MUST include non-color encodings such as labels, markers, line styles, hatches, or direct annotations.
- **FR-015**: The design system MUST provide warning and no-data panel behavior for missing required or optional roles.
- **FR-016**: The system MUST use `outputs/figures/manifest.json` as the default artifact manifest path, MUST create it as a valid empty manifest when no figures exist yet, and MUST record each generated figure's artifact id, path, title, source spec, input entities, required roles, optional roles used, warnings, UTC creation time, and deterministic status.
- **FR-017**: Manifest validation MUST detect missing required manifest fields.
- **FR-018**: A repository-root schema validation command MUST default to validating repository-root `data/` CSV files, MUST allow callers to override the target with `--data-dir`, MUST print a concise human-readable summary, and MUST produce deterministic JSON success, warning, and failure results at `artifacts/validation-report.json`.
- **FR-019**: Focused registry and visualization contract tests MUST run from the repository root without network access.
- **FR-020**: Existing participant visualization outputs MUST continue to render or be replaced by equivalent dashboard-grade artifacts using the shared foundation.

### Key Entities

- **EntitySpec**: Metadata contract for one canonical entity, including source file, keys, semantic roles, labels, units, ranges, missingness rules, aggregation defaults, and aliases.
- **SemanticRole**: Stable business meaning used by dashboards, such as participant identifier, systolic blood pressure, heat index, alert level, or outcome event date.
- **ValidationResult**: Structured outcome containing resolved roles, missing required roles, optional warnings, range violations, extra columns, and capture-worthy flags.
- **SchemaValidationError**: Clear validation failure raised when required structure is absent.
- **VisualizationStyle**: Shared styling contract for palette, typography, backgrounds, gridlines, warning/capture colors, sizing, and DPI.
- **FigureArtifactManifest**: Deterministic JSON manifest at the default path `outputs/figures/manifest.json` that records generated figure artifacts and their traceability metadata, including the valid empty state before artifacts exist.
- **VisualizationConfig**: Project-level settings for output root, image size/DPI/format, style preferences, EDA defaults, and missingness rendering behavior.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Registry role resolution succeeds for all required semantic roles present in the bundled participants, daily vitals, alerts, staff contacts, and clinical outcomes data.
- **SC-002**: Missing required roles fail with a validation error that names the missing role and entity in 100% of focused validation tests.
- **SC-003**: Missing optional roles produce structured warnings and do not crash visualization contract tests.
- **SC-004**: Range violations are reported without row removal in focused registry tests.
- **SC-005**: A saved dashboard figure produced through the design system meets or exceeds 1600x900 pixels and 220 DPI.
- **SC-006**: Saving a tiny/default figure without explicit override fails in visualization contract tests.
- **SC-007**: The default manifest exists as a valid empty manifest before figures are generated, and manifest entries validate only when all required traceability fields are present.
- **SC-008**: Root commands for schema validation against the default `data/` target and focused registry/visualization tests complete without network access, and schema validation exposes deterministic JSON results at `artifacts/validation-report.json` alongside its contributor-facing summary.
- **SC-009**: Existing participant visualization behavior still renders or has an equivalent dashboard-grade artifact covered by tests.

## Assumptions

- SPEC-001 remains the authoritative canonical schema baseline for currently bundled tables.
- Optional future entities are registry-supported now but are not required to have physical source files until their producer specs land.
- The foundation creates shared contracts and sample validation/design behavior, not the full EDA dashboard suite.
- Missingness is meaningful source evidence and is preserved for later dashboards.
- Figure artifacts are static image outputs for reproducible dashboard-grade reporting.
- The shared artifact manifest has one default location: `outputs/figures/manifest.json`.
- Runtime behavior must work from bundled local data with no network calls.
- Clone-to-run schema validation defaults to repository-root `data/` CSV files; alternate local sources, including synthetic fixtures, are selected explicitly with `--data-dir`.
- Schema validation command results are both human-readable and machine-readable at `artifacts/validation-report.json` so later specs can depend on the same validation outcome.
