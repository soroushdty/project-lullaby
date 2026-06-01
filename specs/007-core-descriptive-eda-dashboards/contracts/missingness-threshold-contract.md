---
id: CONTRACT-007-MISSINGNESS
title: Core Descriptive EDA Missingness and Threshold Contract
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-007, SPEC-004, SPEC-006]
implements: [P3, P5, P7, P8, P10]
supersedes: null
superseded_by: null
related: [CONTRACT-006-BOOLEAN, CONTRACT-004-REGISTRY]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Contract: Missingness, Boolean Semantics, and Thresholds

## Missingness

- Missing values are counted and displayed where relevant.
- Missing values are not imputed.
- Missing optional roles render unavailable or warning sections.
- Missing required tables or roles fail before affected artifact writes.
- Missing survey/contact state remains visible and is not counted as attempted or completed.

## Boolean-Like Fields

- Required boolean-like roles use shared semantic parsing.
- Invalid required tokens fail validation with role and source context.
- Optional invalid tokens warn and render as `Missing/Unknown`.
- `False`, `0`, `no`, and equivalent false tokens are never treated as true merely because
  they are non-empty strings.

## Capture-Worthy and Impossible Values

- A value outside a role's `hard_range` is labeled `impossible by schema`.
- A value inside `hard_range` but outside `capture_worthy_range` is labeled
  `capture-worthy`.
- A role without `hard_range` or `capture_worthy_range` is not flagged by Panel 3.
- Dashboard-local IQR, percentile, min/max-only, or unregistered clinical thresholds are not
  allowed for capture-worthy flagging.

## Outcome Prevalence Target Annotation

- CV event prevalence is calculated as CV positives divided by the clinical outcome
  denominator after semantic parsing.
- The `15/200` or `7.5%` target relationship is annotated only when observed CV prevalence is
  6.5% to 8.5%.
- The rare-outcome warning text is always present on the outcome prevalence panel.

## Engagement Funnel Conversion

- Conversion percentage equals current stage count divided by the immediately prior stage
  count.
- Survey completed, dismissed, abandoned, and missing/unknown states are explicit.
- Staff contact completion requires explicit completed state.
- Missing staff contact state is never inferred as completed.
