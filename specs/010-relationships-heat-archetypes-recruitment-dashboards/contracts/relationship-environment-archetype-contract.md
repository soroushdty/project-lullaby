---
id: CONTRACT-010-SEMANTICS
title: Relationship, Heat, Archetype, and Recruitment Semantics Contract
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-010, SPEC-004, SPEC-006, SPEC-007, SPEC-009]
implements: [P3, P5, P7, P10]
supersedes: null
superseded_by: null
related: [CONTRACT-004-REGISTRY, CONTRACT-006-BOOLEAN, CONTRACT-009-QUALITY-MISSINGNESS]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Contract: Relationship, Heat, Archetype, and Recruitment Semantics

## Observed Relationship Policy

- Relationship calculations use observed pairs only.
- Missing values are not imputed.
- Pairwise N must be visible in Panel 10 and stored in manifest metadata.
- Correlations are descriptive and non-causal.
- Bivariate direction plots use observed within-participant differences only when both
  variables have observed consecutive values.

## Heat Source Rules

- Panel 10 heat bivariates prefer `environment.heat_index_c`.
- Panel 10 may use observed `daily_vitals.heat_index_c` as a clearly labeled Panel 10-only
  proxy when no environment table exists.
- Panel 11 requires a real `environment` table for environment trends, heat-wave periods, and
  missing environment coverage.
- Panel 11 must not use daily-vitals heat columns as fabricated environment data.

## High-Heat Definition

Use the following ordered fallback:

1. `environment.heat_wave == true`
2. `environment.heat_exposure_level` in `high` or `extreme`
3. observed `environment.heat_index_c >= 75th percentile`

Rules:

- Later fallbacks are used only when earlier fields are unavailable or contain no positive
  high-heat periods.
- The chosen definition is stored in manifest metadata.
- High-heat classification uses observed environment rows only.

## Archetype Label Rules

Canonical segment labels:

- diligent monitor
- overwhelmed mom
- heat-stressed
- true emergency
- silent decliner

Explicit label rules:

- Use explicit labels from `participants` first when available.
- Use explicit labels from `daily_vitals` only when participant-level labels are unavailable.
- Normalize known aliases to canonical segment names.
- Preserve unknown explicit labels as additional rows and metadata.
- Do not treat unknown explicit labels as invalid.

Provisional label rules:

- Assign provisional labels only when no explicit labels exist.
- Provisional labels are review aids, not ground truth.
- Each participant receives exactly one provisional label.
- If multiple provisional rules match, use priority order: true emergency, heat-stressed,
  silent decliner, overwhelmed mom, diligent monitor.
- The rule summary and provisional status are visible in Panel 12 or metadata.

## Segment Metrics

- `N`: count of participants assigned to the segment.
- `adherence`: participant-day observed vital coverage using observed expected-day denominator.
- `missingness`: missing vital share across available vital roles.
- `alert_burden`: mean or count of observed alert rows from optional `alerts`; unavailable when
  alerts are absent.
- `event_prevalence`: share with observed positive clinical outcome signal when outcomes are
  available.
- `AC access`: share with explicit AC access when participant AC role is available.
- `PIH severity`: visible distribution or dominant category when participant PIH severity is
  available.

## Recruitment Timeline Rules

- Recruitment table dates take precedence when present and parseable.
- Participant enrollment dates, observation dates, and daily-vitals date bounds are fallback
  sources.
- The source of timeline dates is recorded in warnings or metadata.
- Calendar-aware panels require parseable calendar dates.
- If no date source is parseable, Panel 13 renders an unavailable panel and manifest warning.
- Heat overlay uses observed environment high-heat periods only.

## Descriptive-Only Guardrails

- No prediction, model scoring, clinical risk score, or causal attribution is performed.
- No missing value is imputed for visualization, scoring, or relationship calculation.
- CV-risk-like and heat-strain-like language is descriptive and must not be presented as a
  diagnosis or causal mechanism.
- Provisional archetypes are not labels for training targets or ground-truth outcome classes.
