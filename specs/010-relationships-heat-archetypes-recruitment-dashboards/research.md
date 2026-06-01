---
id: RESEARCH-010
title: Relationships, Heat Exposure, Archetypes, and Recruitment Dashboards Research
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-010, SPEC-001, SPEC-004, SPEC-007, SPEC-009]
implements: [P3, P5, P7, P10]
supersedes: null
superseded_by: null
related: [SPEC-004, SPEC-005, SPEC-006, SPEC-007, SPEC-009]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Research: Relationships, Heat Exposure, Archetypes, and Recruitment Dashboards

## Decision: Extend The Existing EDA CLI With `relationships` And `all`

**Decision**: Add `relationships` and `all` as supported `--panels` values in
`src/visualization/generate_eda.py`. `relationships` generates panels 10 through 13; `all`
generates panels 1 through 13 through existing panel-set generators.

**Rationale**: SPEC-007 and SPEC-009 already established a single EDA CLI, output directory,
manifest path, and failure behavior. Extending the existing entry point keeps dashboard
generation reproducible and avoids split orchestration.

**Alternatives considered**:
- A second CLI for SPEC-010: rejected because manifest registration and user commands would
  drift.
- Only support `all`: rejected because SPEC-010 requires independent generation for panels
  10 through 13.
- Fold all panels into `eda_core.py`: rejected because these panels have distinct optional
  environment, archetype, and recruitment behavior.

## Decision: Render Static PNG Dashboards With Matplotlib

**Decision**: Implement panels 10 through 13 as deterministic Matplotlib figures under
`src/visualization/eda_relationships.py`, `src/visualization/eda_environment.py`, and
`src/visualization/eda_archetypes.py`.

**Rationale**: The feature requires static PNG artifacts with minimum dimensions. Matplotlib is
already used by the visualization foundation and prior EDA specs, works offline, and supports
shared layout helpers.

**Alternatives considered**:
- Plotly or browser-native dashboards: rejected because acceptance is static PNG-based.
- Notebook-generated figures: rejected because notebook state weakens reproducibility.
- SVG dashboards: rejected because the established artifact contract and tests center on PNGs.

## Decision: Use Observed Pairs For Relationship Views

**Decision**: Panel 10 uses pairwise complete observations for correlations and bivariate
views, annotates pairwise N, and records the observed-data policy in manifest metadata.

**Rationale**: Relationship EDA must preserve missingness and avoid imputation. Pairwise
denominators make correlation and bivariate plots interpretable when vital variables have
different missingness patterns.

**Alternatives considered**:
- Listwise deletion across all vital variables: rejected because it can discard too much data
  and obscure per-pair denominators.
- Mean imputation before correlations: rejected because SPEC-010 forbids imputation.
- Hiding N in metadata only: rejected because the dashboard itself must make observed pairs
  clear.

## Decision: Permit A Panel 10-Only Daily-Vitals Heat Proxy

**Decision**: Panel 10 uses `environment.heat_index_c` when available; if no environment table
exists, it may use observed `daily_vitals.heat_index_c` as a clearly labeled Panel 10-only
proxy.

**Rationale**: Some canonical raw data include observed heat-index columns on daily vitals even
when no standalone environment table exists. Relationship EDA can use those observed values
without weakening Panel 11's stricter source requirements.

**Alternatives considered**:
- Require `environment.csv` for Panel 10 heat bivariates: rejected because it hides observed
  heat-index values already present in canonical daily vitals.
- Let Panel 11 use daily-vitals heat proxy too: rejected because Panel 11 is specifically an
  environment-source dashboard and must not fabricate environment coverage.

## Decision: Keep Panel 11 Environment-Table Strict

**Decision**: Panel 11 renders a visible unavailable panel when no `environment` table exists.
It never creates environment trends, heat waves, or missing environment rows from
`daily_vitals` columns.

**Rationale**: SPEC-010 explicitly requires no silent fabrication in the EDA step. A standalone
environment table is the evidence source for environmental coverage and missing environment
data.

**Alternatives considered**:
- Derive environment from daily-vitals heat columns: rejected because it would make participant
  measurements look like complete environment coverage.
- Fail the whole panel set when environment is absent: rejected because the spec requires an
  unavailable panel, not a command failure.

## Decision: High-Heat Fallback Order

**Decision**: Identify high-heat periods with `heat_wave == true`; if absent, use
`heat_exposure_level` high/extreme; if absent, use observed `heat_index_c >= 75th percentile`.

**Rationale**: The order respects source-provided semantics first, then transparent categorical
labels, then a deterministic observed-data fallback when only numeric heat index is present.

**Alternatives considered**:
- Use only explicit heat-wave flags: rejected because synthetic and real environment sources
  may provide heat exposure levels without a boolean heat-wave field.
- Use a fixed Celsius threshold: rejected because local synthetic or real sources may encode
  different heat-index distributions and the spec did not define a clinical threshold.
- Always use top quartile: rejected because it ignores explicit heat-wave or exposure fields.

## Decision: Archetype Label Source Determines Behavior

**Decision**: Panel 12 uses explicit archetype labels when available. Known aliases normalize
to canonical segment names; unknown explicit labels are preserved as additional explicit rows
and metadata. When labels are absent, transparent provisional rules assign exactly one segment.

**Rationale**: Explicit labels may be synthetic source truth or externally curated labels and
should not be overwritten. Unknown labels remain visible instead of being forced into the five
canonical segments. Provisional labels are review aids, not ground truth.

**Alternatives considered**:
- Force every explicit label into one of five segments: rejected because it can distort source
  semantics.
- Drop unknown labels: rejected because it hides source data.
- Multi-label provisional assignment: rejected because the required dashboard summarizes five
  segments and needs deterministic per-participant denominators.

## Decision: Provisional Archetype Priority Order

**Decision**: When multiple provisional rules match, assign one label by priority: true
emergency, heat-stressed, silent decliner, overwhelmed mom, diligent monitor.

**Rationale**: This deterministic order surfaces the most review-critical descriptive pattern
first and avoids ambiguous multi-label counts in a static summary table.

**Alternatives considered**:
- Largest normalized deviation from cohort median: rejected because it is harder to explain in
  panel annotations and tests.
- Multi-label segments: rejected because segment N and prevalence denominators become harder
  to interpret.
- Mark ambiguous participants unavailable: rejected because it reduces utility when rules
  overlap naturally.

## Decision: Recruitment Timeline Fallbacks Are Calendar-First

**Decision**: Panel 13 uses recruitment table dates when present, otherwise participant
enrollment/observation dates and daily-vitals date bounds. If all date sources are missing or
unparseable, it renders an unavailable panel and manifest warning.

**Rationale**: The operations view needs calendar awareness, but recruitment may be a future
optional table. Transparent fallback preserves usefulness while recording inference.

**Alternatives considered**:
- Require recruitment table: rejected because the spec allows inference from participant and
  observation dates.
- Use study day only: rejected because the panel's main value is calendar overlap with heat
  exposure.
- Fabricate dates from row order: rejected because it violates reproducibility and honest
  evaluation.

## Decision: Register Rich SPEC-010 Metadata In The Manifest

**Decision**: Each generated SPEC-010 artifact records required roles, optional roles used,
warnings, observed-pair denominators, heat source, high-heat definition, archetype label
source, rule summary, recruitment source, and unavailable-panel metadata where applicable.

**Rationale**: Static PNGs cannot show every source and fallback decision. Manifest metadata is
the audit trail connecting artifacts to the spec and clarifications.

**Alternatives considered**:
- Store only artifact paths in the manifest: rejected because acceptance requires source,
  warning, and policy metadata.
- Write separate sidecar metadata files per panel: rejected because the existing figure
  manifest is the project artifact registry.
