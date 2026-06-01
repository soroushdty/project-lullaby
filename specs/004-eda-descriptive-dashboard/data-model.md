---
id: PLAN-004A-DATA-MODEL
title: Visualization Foundation and Schema Registry Data Model
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-004A, PLAN-004A]
implements: [P3, P5, P7, P10]
supersedes: null
superseded_by: null
related: [SPEC-001, SPEC-004B, SPEC-005, SPEC-006, SPEC-007]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Data Model: Visualization Foundation and Schema Registry

## EntitySpec

Represents one canonical visualization entity.

**Fields**:
- `name`: canonical entity name such as `participants`, `daily_vitals`, `alerts`,
  `staff_contacts`, `clinical_outcomes`, `environment`, `recruitment`, `model_predictions`,
  or `model_metrics`
- `status`: `current`, `optional`, or `future_optional`
- `source_filenames`: ordered local filenames accepted for this entity, with repository-root
  `data/lullaby_*.csv` names before canonical synthetic filenames when both apply
- `primary_key_roles`: semantic roles that uniquely identify records when available
- `participant_role`: semantic role linking to a participant, or null for participant entity
- `datetime_roles`: date or timestamp roles available for temporal plots
- `required_roles`: roles required for the entity to be usable
- `optional_roles`: roles that may warn when absent but do not fail validation
- `display_labels`: human-facing labels by semantic role
- `units`: unit labels by semantic role when applicable
- `ranges`: hard impossible bounds and capture-worthy bounds by semantic role
- `missingness_policy`: how absence should be represented in validation and visualization
- `default_aggregation`: default dashboard aggregation for repeated records
- `aliases`: ordered accepted source columns by semantic role

**Validation rules**:
- Current entities must define at least one source filename and all required roles.
- Optional/future entities may define no physical source file until producer specs land.
- Alias ordering is deterministic.
- Unknown source columns are allowed and preserved.

## SemanticRole

Stable business meaning consumed by dashboard code instead of raw source column names.

**Fields**:
- `role_id`: dotted identifier, for example `participant.id`, `vital.systolic_bp`,
  `alert.level`, `contact.completed`, or `outcome.event_date`
- `entity`: owning entity name
- `required`: whether absence is a validation error for current entities
- `value_type`: expected logical type such as `string`, `number`, `date`, `datetime`,
  `boolean`, or `category`
- `label`: display label
- `unit`: optional unit label
- `accepted_columns`: ordered source column names
- `hard_range`: optional impossible lower and upper bounds
- `capture_worthy_range`: optional plausible extreme bounds that should be flagged but kept
- `categories`: optional allowed categories for clinically meaningful categorical roles

**Validation rules**:
- Required roles must resolve for current entities.
- Optional roles produce structured warnings when unresolved.
- Multiple matching columns are errors unless the registry declares a priority winner.

## RoleResolution

Result of resolving one role against one DataFrame.

**Fields**:
- `role_id`
- `entity`
- `column`: resolved source column, or null
- `match_type`: `exact`, `alias`, `missing`, or `ambiguous`
- `candidates`: matching source columns in deterministic order
- `required`
- `warning`: optional warning text
- `error`: optional error text

**State transitions**:
- `unresolved` -> `resolved` when exactly one column is selected
- `unresolved` -> `warning` when optional and missing
- `unresolved` -> `error` when required and missing or ambiguous

## ValidationResult

Structured output from visualization schema validation.

**Fields**:
- `status`: `pass`, `warn`, or `fail`
- `data_dir`: data directory validated
- `report_path`: `artifacts/validation-report.json`
- `entities`: per-entity validation details
- `resolved_roles`: list of `RoleResolution`
- `warnings`: optional-role, future-entity, no-data, or manifest warnings
- `errors`: required-role failures, ambiguous aliases, missing required source files, or
  malformed manifest entries
- `range_violations`: values outside hard impossible bounds
- `capture_worthy_values`: plausible extremes preserved for downstream review
- `extra_columns`: unknown source columns preserved as context
- `generated_at_utc`: ISO-8601 timestamp for the validation run

**Validation rules**:
- Source rows are never dropped by validation.
- Missing values are never imputed.
- Hard range violations are reported without mutating source frames.
- Plausible extremes are labeled capture-worthy unless hard bounds are violated.

## SchemaValidationError

Raised only when validation cannot proceed because required structure is absent or ambiguous.

**Fields**:
- `entity`
- `role_id`
- `source_filename`
- `message`
- `candidates`
- `remediation`

## VisualizationStyle

Shared static figure style for dashboard-grade artifacts.

**Fields**:
- `figure_background`
- `panel_background`
- `text_color`
- `muted_text_color`
- `grid_color`
- `warning_color`
- `capture_worthy_color`
- `palette`
- `font_family`
- `dpi`
- `min_width_px`
- `min_height_px`
- `format`
- `non_color_encodings`

**Validation rules**:
- Minimum saved canvas is 1600x900 pixels at 220 DPI unless an explicit test override is used.
- Clinically meaningful categories must use at least one non-color encoding.
- Warning and no-data panels must render without requiring source data.

## FigureArtifactManifest

Traceability document at `outputs/figures/manifest.json`.

**Fields**:
- `schema_version`
- `manifest_path`
- `entries`: sorted list of `FigureArtifact`
- `warnings`

**Validation rules**:
- Empty manifests are valid.
- Manifest path is repository-relative and defaults to `outputs/figures/manifest.json`.
- Entries are sorted by `artifact_id`.
- Missing required entry fields fail manifest validation.

## FigureArtifact

One generated figure record.

**Fields**:
- `artifact_id`
- `path`
- `title`
- `spec`
- `inputs`
- `required_roles`
- `optional_roles_used`
- `warnings`
- `created_at_utc`
- `deterministic`

**Validation rules**:
- `path` must be repository-relative and under `outputs/figures/`.
- `spec` must identify the producing spec.
- `deterministic` is true only when the artifact is generated from local inputs and stable
  configuration.
- Warnings produced during rendering are preserved on the entry.

## VisualizationConfig

Project-level visualization settings.

**Fields**:
- `output_root`: default `outputs/figures`
- `manifest_path`: default `outputs/figures/manifest.json`
- `validation_report_path`: default `artifacts/validation-report.json`
- `data_dir`: default `data`
- `image`: DPI, minimum pixel dimensions, and format
- `style`: font, palette, units, direct labels
- `eda`: defaults that later EDA specs may consume
- `missingness`: explicit missingness and gap cluster rendering preferences

**Validation rules**:
- Defaults must support clone-to-run without network access.
- Paths must remain repository-relative unless a caller explicitly passes an alternate local path.
- Config loading must not be required for tests that instantiate defaults directly.
