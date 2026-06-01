---
id: RESEARCH-009
title: Longitudinal Vitals, Missingness, Signal Quality, and Patient Timeline Research
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-009, SPEC-001, SPEC-004, SPEC-007]
implements: [P3, P5, P7, P10]
supersedes: null
superseded_by: null
related: [SPEC-004, SPEC-005, SPEC-006, SPEC-007]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Research: Longitudinal Vitals, Missingness, Signal Quality, and Patient Timeline

## Decision: Extend The Existing EDA CLI

**Decision**: Add `longitudinal` as a supported `--panels` value in
`src/visualization/generate_eda.py` and route it to a new longitudinal generator.

**Rationale**: SPEC-007 already established the EDA CLI, output directory, manifest path, and
static PNG conventions. Extending the existing entry point keeps clone-to-run behavior simple
and avoids two incompatible dashboard generation paths.

**Alternatives considered**:
- A second CLI module for longitudinal dashboards: rejected because manifest registration,
  argument parsing, and failure behavior would drift.
- Fold all logic into `eda_core.py`: rejected because panels 5 through 9 have distinct
  longitudinal and patient-timeline responsibilities.

## Decision: Render Static PNG Dashboards With Matplotlib

**Decision**: Implement longitudinal panels as deterministic Matplotlib figures under
`src/visualization/eda_longitudinal.py` and `src/visualization/patient_view.py`.

**Rationale**: The feature requires static PNG artifacts with minimum dimensions. Matplotlib is
already used by the visualization foundation and SPEC-007, works offline, and supports shared
layout helpers.

**Alternatives considered**:
- Plotly or a browser dashboard: rejected because SPEC-009 acceptance is based on static PNGs.
- Notebook-generated figures: rejected because notebook state weakens reproducibility.
- Generated SVG dashboards: rejected because the existing design and acceptance checks center
  on PNG artifacts.

## Decision: Preserve Gaps By Construction

**Decision**: Represent study-day missingness explicitly and render vital trajectories as
line segments that break at missing days.

**Rationale**: SPEC-009 repeatedly forbids interpolation. Reindexing to the expected
participant-day axis with missing values preserved allows Matplotlib to break lines while
keeping observed-day denominators accurate.

**Alternatives considered**:
- Forward-fill, backfill, rolling averages, or interpolation: rejected because they alter the
  observed record.
- Drop missing study days from the x-axis: rejected because it hides adherence and signal gaps.

## Decision: Deterministic Default Participant Selection

**Decision**: When no participant id is supplied, select the participant with the highest
`observed_vital_days + distinct_alert_days + distinct_outcome_events` score, breaking ties by
observed vital variable count and then lexicographic participant id.

**Rationale**: Static PNGs need one participant for trajectory and timeline views. The
clarified rule chooses the richest review record without manual input and is reproducible in
CI.

**Alternatives considered**:
- Select a random participant: rejected because outputs would not be reproducible.
- Select the highest clinical-risk participant: rejected because SPEC-009 forbids clinical
  risk ranking.
- Select the first row: rejected because it may produce an uninformative timeline.

## Decision: Keep Environment Overlay Optional And Off By Default

**Decision**: `--overlay-environment` defaults to `false`; when true, the overlay renders only
if environment data and required roles are available.

**Rationale**: Heat context is valuable, but environment is an optional future entity in the
current registry. A default-off toggle prevents accidental visual clutter while preserving a
clear path for heat exposure review.

**Alternatives considered**:
- Make environment required for longitudinal generation: rejected because SPEC-009 lists it as
  optional.
- Always overlay environment when available: rejected because static panels can become hard to
  read with too many axes.

## Decision: Downsample Missingness Matrix Display Rows Only

**Decision**: For more than 250 participants, deterministically downsample displayed matrix
rows while computing all adherence and missingness metrics on the full cohort.

**Rationale**: The missingness matrix must remain readable in a static 1600 x 900 artifact, but
summary metrics must remain complete and honest.

**Alternatives considered**:
- Compute metrics only on displayed rows: rejected because it would bias cohort summaries.
- Render every row regardless of size: rejected because labels and cells become unreadable.
- Random downsampling: rejected because it is not deterministic.

## Decision: Normalize Quality Components And Redistribute Missing Weights

**Decision**: Normalize wear completeness, scale adherence, vital completeness, and contact
traceability to participant-level 0-1 components. If a component has no valid denominator,
exclude it and redistribute its weight proportionally across available components.

**Rationale**: The required formula combines unlike measures. Normalized components make the
formula transparent, while unavailable-component handling avoids treating absent optional data
as poor participant behavior.

**Alternatives considered**:
- Treat unavailable components as zero: rejected because it penalizes missing data sources.
- Omit the composite score whenever a component is unavailable: rejected because the spec
  requires redistribution and manifest warning.
- Use clinical outcomes in the score: rejected because ranking must be by completeness, not
  clinical risk.

## Decision: Label Missingness Mechanism Evidence As Exploratory

**Decision**: Panel 9 uses labels such as exploratory "signals consistent with" MCAR, MAR, or
MNAR hypotheses and does not claim proof.

**Rationale**: Static descriptive diagnostics can show associations with study day,
participant context, heat exposure, or recent abnormal vitals, but cannot prove the
missingness mechanism. The wording aligns with honest evaluation and avoids overclaiming.

**Alternatives considered**:
- Classify each variable as MCAR, MAR, or MNAR: rejected because mechanism proof is outside
  descriptive EDA.
- Hide mechanism terminology entirely: rejected because the spec explicitly asks for
  MCAR/MAR/MNAR exploratory diagnostics.

## Decision: Register Rich Longitudinal Metadata In The Manifest

**Decision**: Each generated longitudinal artifact records required roles, optional roles used,
warnings, selected participant context, week filters, environment overlay state, score formula
metadata, downsampling metadata, and missingness diagnostic caveats where applicable.

**Rationale**: The static PNGs cannot show every implementation choice. Manifest metadata is
the audit trail connecting the artifact to the spec and clarifications.

**Alternatives considered**:
- Store only artifact paths in the manifest: rejected because acceptance requires formula,
  warnings, and participant selection metadata.
- Write sidecar metadata files per panel: rejected because the existing figure manifest is the
  project-level artifact registry.
