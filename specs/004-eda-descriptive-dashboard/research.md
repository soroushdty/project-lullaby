---
id: PLAN-004-RESEARCH
title: Visualization Foundation and Schema Registry Research
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-004, PLAN-004]
implements: [P1, P2, P3, P5, P7, P10]
supersedes: null
superseded_by: null
related: [SPEC-001, SPEC-005, SPEC-006, SPEC-007, SPEC-008]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Research: Visualization Foundation and Schema Registry

## Decision: Add a visualization-specific semantic registry beside the SPEC-001 schema contract

**Rationale**: The existing `src/schemas` contract defines ingestion-ready table shape, primary
keys, timestamps, and Pandera validation. SPEC-004 needs additional visualization semantics:
role aliases, display labels, units, valid ranges, missingness policy, default aggregation, and
future optional entities. A dedicated visualization registry can reference SPEC-001 as the
canonical baseline without forcing ingestion contracts to grow dashboard concerns.

**Alternatives considered**:
- Extend `TableContract` directly. Rejected because it would mix ingestion validation with
  visualization-only concerns and risk breaking SPEC-001 tests.
- Hardcode plotting columns in each dashboard. Rejected by SPEC-004 and P3.

## Decision: Support canonical entity names with ordered source filename aliases

**Rationale**: The clarified default validation target is repository-root `data/`, whose files
use `lullaby_*.csv` names and richer source columns. The synthetic fixtures under
`data/synthetic/` use canonical table filenames. Entity specs will declare a preferred default
source filename plus ordered aliases so `participants` can load from `lullaby_participants.csv`
or `participants.csv` without changing downstream semantic roles.

**Alternatives considered**:
- Rename or move bundled files into `data/raw/`. Rejected by clarification.
- Treat `data/synthetic/` as the default. Rejected by clarification.
- Require every command to pass `--data-dir`. Rejected by clarification.

## Decision: Resolve roles by deterministic exact-name and alias priority

**Rationale**: Role resolution must be stable across runs and source variants. Each semantic
role declares ordered accepted column names. Resolution checks exact role column names first,
then aliases in declared order. If more than one accepted source column is present and the
registry does not declare a priority winner, validation reports an ambiguity instead of guessing.

**Alternatives considered**:
- Fuzzy matching. Rejected because clinical and dashboard semantics should not depend on
  unstable similarity scores.
- First DataFrame column wins. Rejected because source column order is not a semantic contract.

## Decision: Return structured validation results without mutating source frames

**Rationale**: P5 requires preserving missingness and clinically plausible extremes. Validation
therefore returns errors, warnings, range violations, capture-worthy values, extra columns, and
resolved-role metadata as separate structured results. It does not impute, drop, coerce, or
rewrite caller-provided frames.

**Alternatives considered**:
- Normalize source data during validation. Rejected because validation would corrupt evidence.
- Fail on all range warnings. Rejected because plausible extremes are meaningful and must remain
  available for downstream review.

## Decision: Use matplotlib as the only new visualization dependency

**Rationale**: SPEC-004 requires static dashboard-grade figures with DPI, canvas-size, labels,
warning panels, no-data panels, and non-color encodings. Matplotlib provides deterministic
static image generation, integrates well with pytest smoke tests, and avoids a browser, server,
or notebook dependency.

**Alternatives considered**:
- Seaborn. Rejected for SPEC-004 foundation because it adds another style abstraction while
  matplotlib already satisfies the required contract.
- Plotly or browser-rendered figures. Rejected because SPEC-004 requires reproducible static
  artifacts without a web runtime.
- Notebook-only rendering. Rejected by the spec.

## Decision: Make `outputs/figures/manifest.json` valid when empty

**Rationale**: Later dashboard specs need one deterministic registration target. Creating a
valid empty manifest during foundation validation proves the path and schema exist before any
figure generator lands. Entries will be sorted by `artifact_id`; paths will be repository
relative; generated timestamps are UTC run metadata and are not used as deterministic identity.

**Alternatives considered**:
- Create the manifest only after the first artifact. Rejected by clarification.
- Let every dashboard choose its own manifest path. Rejected because it weakens traceability.

## Decision: Keep validation command output dual-purpose

**Rationale**: Contributors need a concise terminal summary, while tests and later specs need a
machine-readable contract. The command prints summary counts and writes deterministic JSON to
`artifacts/validation-report.json`, matching the existing SPEC-001 artifact convention.

**Alternatives considered**:
- JSON-only output. Rejected because clone-to-run should be legible without opening artifacts.
- Human-only output. Rejected because later specs need structured validation reuse.

## Decision: Add a focused visualization foundation CLI instead of changing SPEC-001 behavior

**Rationale**: The existing `src.cli.validate_schema` validates canonical ingestion tables. SPEC-004
has a different boundary: visualization semantic roles over richer source data. A focused command
under `src/cli/validate_visualization_foundation.py` can default to `data/`, create the figure
manifest, and write the shared report while preserving the existing SPEC-001 CLI behavior.

**Alternatives considered**:
- Overload `src.cli.validate_schema` to cover both ingestion and visualization validation.
  Rejected because it would blur two different validation contracts.
- Place the CLI under `src/schema/`. Rejected because this repo already uses `src/schemas`
  and `src/cli` conventions.
