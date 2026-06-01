---
id: DATA-006
title: Data Semantics and Validation Hardening Data Model
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-006, SPEC-001, SPEC-003, SPEC-004, SPEC-005]
implements: [P3, P5, P7, P10]
supersedes: null
superseded_by: null
related: [SPEC-003, SPEC-004, SPEC-005]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Data Model: Data Semantics and Validation Hardening

## DomainBooleanParsePolicy

Represents how one boolean-like semantic role should be parsed.

**Fields**:
- `role`: canonical role or local field name, such as `clinical_outcomes.cv_event`
- `required`: whether invalid tokens fail validation
- `true_tokens`: accepted true values, including native `True`, `1`, `true`, `t`, `yes`, `y`
- `false_tokens`: accepted false values, including native `False`, `0`, `false`, `f`, `no`, `n`
- `missing_tokens`: accepted missing/unknown values, including nulls, blanks, `unknown`, `missing`
- `invalid_behavior`: `fail` for required roles, `warn_as_missing` for optional roles

**Validation rules**:
- Tokens are normalized case-insensitively after trimming whitespace.
- Invalid required-role tokens produce validation errors with role, source column, token, and row
  reference when available.
- Invalid optional-role tokens produce structured warnings and downstream `Missing/Unknown`.

## ParsedBooleanSeries

Represents the parsed result for one boolean-like column.

**Fields**:
- `true_mask`
- `false_mask`
- `missing_mask`
- `invalid_mask`
- `warnings`
- `errors`
- `counts`: true, false, missing/unknown, invalid

**Relationships**:
- Created by `DomainBooleanParsePolicy`.
- Consumed by EDA prevalence panels, alert funnel calculations, simulator diagnostics, and
  ingestion stream pending selection.

## RequiredPanelInputSet

Represents entities and roles that must be valid before a requested dashboard panel may write
artifacts.

**Fields**:
- `panel_id`
- `required_entities`
- `optional_entities`
- `required_roles`
- `optional_roles`
- `validation_errors`
- `warnings`

**Validation rules**:
- Missing or schema-invalid required entities fail before requested artifact writes.
- Optional entities and optional roles degrade to warning or unavailable panels.

## OutcomePrevalenceCount

Represents one outcome prevalence row after tri-state parsing.

**Fields**:
- `label`
- `positive_count`
- `negative_count`
- `missing_unknown_count`
- `denominator`
- `positive_percent`
- `warnings`

**Validation rules**:
- Missing/unknown values are never included in negative counts.
- Percent annotations include denominator and missing/unknown counts.

## AlertFunnelStateCount

Represents engagement funnel states without inferring missing completion.

**Fields**:
- `stage`
- `completed_count`
- `incomplete_count`
- `missing_unknown_count`
- `denominator`
- `conversion_percent`
- `warnings`

**Validation rules**:
- Call/contact completion uses explicit completed states.
- Missing state remains `Missing/Unknown`.

## CategoryCompletenessRecord

Represents preservation of category counts when a chart cannot label every category directly.

**Fields**:
- `artifact_id`
- `field`
- `displayed_categories`
- `overflow_categories`
- `all_category_counts`
- `overflow_rendering`: visible table or manifest metadata

**Validation rules**:
- Every source category and count remains recoverable.
- Truncation is never silent.

## ManifestRegistrationDecision

Represents whether an artifact can be registered in the default manifest.

**Fields**:
- `artifact_id`
- `artifact_path`
- `repo_relative_path`
- `registered`
- `warning`

**Validation rules**:
- Repo-relative artifacts are registered in `outputs/figures/manifest.json`.
- Outside-repo artifacts warn and remain unregistered.
- Absolute paths are not written into manifest entries.

## HardeningAcceptanceEvidence

Represents completion evidence for the hardening implementation.

**Fields**:
- `tests_run`
- `dashboard_artifacts_regenerated`
- `manifest_updated`
- `warnings_reviewed`
- `remaining_risks`

**Validation rules**:
- If dashboard semantics, warnings, category completeness, or registration changed, affected
  tracked PNGs and the default manifest must be regenerated.
