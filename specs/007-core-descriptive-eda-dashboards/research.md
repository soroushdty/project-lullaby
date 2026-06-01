---
id: RESEARCH-007
title: Core Descriptive EDA Dashboards Research
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-007, SPEC-001, SPEC-004, SPEC-005, SPEC-006]
implements: [P3, P5, P7, P10]
supersedes: null
superseded_by: null
related: [SPEC-004, SPEC-005, SPEC-006, SPEC-008]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Research: Core Descriptive EDA Dashboards

## Decision: Render Static PNG Dashboards With Matplotlib

**Decision**: Implement the four core panels as deterministic Matplotlib figures under
`src/visualization/eda_core.py`.

**Rationale**: SPEC-007 requires static PNG artifacts with minimum dimensions, titles,
subtitles, labels, units, and annotations. Matplotlib is already a project dependency from the
visualization foundation and works offline in CI and local clone-to-run workflows.

**Alternatives considered**:
- Plotly or a browser dashboard: rejected because SPEC-007 requires static PNG artifacts and no
  runtime web stack.
- Notebook-generated figures: rejected because notebook state would weaken reproducibility.
- Separate per-panel scripts: rejected because shared validation, manifest registration, and
  styling would drift.

## Decision: Keep Canonical Role Resolution in the Schema Registry

**Decision**: Load entities through `src/visualization/schema_registry.py` and resolve semantic
roles before rendering.

**Rationale**: Project Lullaby is schema-driven and multi-tenant. The same dashboard should
work against conforming institution data when column aliases map to the registered semantic
roles.

**Alternatives considered**:
- Hardcode current CSV column names: rejected because it would violate schema-driven
  extensibility.
- Require callers to pre-rename every column: rejected because alias resolution already exists
  in the visualization foundation.

## Decision: Preflight Required Panel Inputs Before Writes

**Decision**: Validate all required core-panel entities and required roles before creating PNGs
or manifest entries for a requested core run.

**Rationale**: A missing required table or role means the affected dashboard cannot support its
claim. Failing before writes avoids stale or misleading acceptance artifacts.

**Alternatives considered**:
- Render warning PNGs for missing required inputs: rejected because a generated artifact can be
  mistaken for success.
- Generate unaffected panels and fail later: rejected because the core panel set is the
  acceptance unit in SPEC-007.

## Decision: Optional Context Degrades Visibly

**Decision**: Missing optional fields, optional entities, or optional parse problems render
labeled unavailable or warning sections and collect warnings for manifest metadata.

**Rationale**: Optional context improves interpretation but should not prevent the reviewer from
seeing the valid descriptive evidence that is present. Visible degradation also prevents silent
omission of equity, psychosocial, or engagement context.

**Alternatives considered**:
- Fail on missing optional roles: rejected because canonical datasets may not contain every
  enrichment field.
- Hide unavailable sections: rejected because hidden context makes missingness invisible.

## Decision: Use Schema-Declared Physiologic Ranges Only

**Decision**: Panel 3 flags capture-worthy and impossible values only when the schema registry
declares `capture_worthy_range` or `hard_range` for the semantic role.

**Rationale**: Capture-worthy values are clinical and schema semantics, not dashboard-local
statistics. This preserves physiologic extremes without mislabeling them as errors and avoids
inventing unreviewed thresholds.

**Alternatives considered**:
- IQR or percentile outlier rules: rejected because they may flag rare but expected physiology
  and are explicitly out of scope.
- Min/max-only local rules: rejected because they are untraceable to the schema registry.

## Decision: Expose Rare Outcome Imbalance Explicitly

**Decision**: Panel 2 shows positive and negative CV event counts, percentages, missing counts,
and the required rare-outcome warning text. It annotates the `15/200` or `7.5%` target-rate
relationship only when observed prevalence is 6.5% to 8.5%.

**Rationale**: The project evaluates rare events downstream. The descriptive dashboard must make
class imbalance obvious before any model interpretation appears.

**Alternatives considered**:
- Show only percentages: rejected because counts are necessary for rare-event interpretation.
- Always annotate the target prevalence: rejected because SPEC-007 limits the annotation to the
  clarified observed-prevalence window.

## Decision: Preserve Low-Count and Overflow Categories

**Decision**: Low-count categories remain displayed. When alert trigger reasons exceed readable
chart space, rendered overflow must preserve all hidden category counts in manifest metadata or
a visible companion table.

**Rationale**: Rare demographic categories and rare alert reasons may be clinically or
equity-relevant. Readability should not come at the cost of silent suppression.

**Alternatives considered**:
- Suppress low-count categories: rejected by SPEC-007 and the equity-centered constitution.
- Draw every category regardless of readability: rejected because labels can become unreadable
  in a static 1600 x 900 artifact.

## Decision: Register Repo-Relative Outputs in the Default Manifest

**Decision**: Register the four default EDA artifacts in `outputs/figures/manifest.json` with
repo-relative paths, required roles, optional roles used, warnings, and deterministic metadata.

**Rationale**: The manifest is the audit trail connecting generated dashboard artifacts to the
spec and canonical inputs.

**Alternatives considered**:
- Leave generated PNGs unregistered: rejected because SPEC-007 requires manifest entries.
- Store absolute artifact paths: rejected because absolute paths are machine-specific and not
  reproducible.

## Decision: Keep Synthetic Longitudinal Run Optional

**Decision**: Support `data/synthetic/longitudinal` as an optional CLI input and allow a
repo-relative output directory such as `outputs/figures/eda_synthetic`.

**Rationale**: SPEC-005 provides a richer synthetic data run, useful for demo and regression
evidence, but SPEC-007 acceptance centers the four default artifacts under
`outputs/figures/eda/`.

**Alternatives considered**:
- Require synthetic longitudinal data for every default run: rejected because the repo already
  includes bundled canonical CSVs under `data/`.
- Skip synthetic support: rejected because SPEC-007 says the CLI should support a synthetic run.
