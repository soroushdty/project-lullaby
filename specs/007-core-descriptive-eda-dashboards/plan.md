---
id: PLAN-007
title: Core Descriptive EDA Dashboards Implementation Plan
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

# Implementation Plan: Core Descriptive EDA Dashboards

**Branch**: `006-core-descriptive-eda-dashboards` | **Date**: 2026-06-01 | **Spec**: `specs/007-core-descriptive-eda-dashboards/spec.md`

**Input**: Feature specification from `specs/007-core-descriptive-eda-dashboards/spec.md`

**Planning note**: `.specify/feature.json` pins the feature directory to
`specs/007-core-descriptive-eda-dashboards`, while the current Git branch reported by
`.specify/scripts/bash/setup-plan.sh --json` is `006-core-descriptive-eda-dashboards`.
The implementation should keep generated artifacts under the pinned `007` spec directory and
avoid renaming branches as part of this plan.

## Summary

Implement the first set of high-quality descriptive EDA dashboards from canonical tables:
cohort overview, outcome prevalence and class imbalance, distributions with
capture-worthy values, and alert engagement funnel. The technical approach is to reuse the
SPEC-004 visualization foundation and SPEC-006 semantic hardening, keeping rendering in
`src/visualization/eda_core.py`, exposing generation through
`src/visualization/generate_eda.py`, writing four static PNG artifacts, and registering every
repo-relative output in `outputs/figures/manifest.json`. The feature presents data only: no
prediction, no imputation, and no dashboard-local outlier rules outside the schema registry.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**:
- Existing runtime: pandas, numpy, matplotlib, PyYAML, pandera, pydantic
- Existing test tooling: pytest
- No new runtime dependency planned; image dimension checks should use available local image
  reading support without adding a web, notebook, or JavaScript dashboard stack

**Storage**:
- Local canonical CSV inputs under `data/` by default; `data/raw` is accepted by the CLI and
  may resolve to `data/` when a literal `data/raw` directory is absent
- Optional synthetic longitudinal inputs under `data/synthetic/longitudinal/`
- Static PNG outputs under `outputs/figures/eda/`
- Figure artifact manifest at `outputs/figures/manifest.json`
- Focused pytest fixtures may use temporary directories and manifests

**Testing**: pytest focused on `tests/test_eda_core_outputs.py` and
`tests/test_eda_missingness_policy.py`, with supporting contract/unit coverage from the
existing visualization foundation and semantic parsing layers

**Target Platform**: Local Linux/macOS developer environments and GitHub Actions CI; offline
static artifact generation only

**Project Type**: Single Python package with a CLI entry point and deterministic static figure
generation

**Performance Goals**:
- Generate the four core PNG artifacts from bundled local data in under 2 minutes on a normal
  developer machine
- Focused EDA tests complete in under 2 minutes from the repository root
- Each required PNG is at least 1600 x 900 pixels and readable at the configured static output
  size

**Constraints**:
- Dashboards are descriptive only and must not predict outcomes, train models, score risk, or
  impute missing values
- Missing required input tables fail before affected artifact files or manifest entries are
  written
- Missing required semantic roles fail before affected artifact files or manifest entries are
  written
- Optional entities and roles render labeled unavailable or warning sections instead of
  crashing
- Missing values remain explicit in counts, denominators, and funnel state annotations
- Panel 2 annotates the `15/200` or `7.5%` target event-rate relationship only when observed
  CV event prevalence is 6.5% to 8.5%
- Panel 3 flags values only from schema registry `capture_worthy_range` and `hard_range`;
  dashboard-local IQR, percentile, clinical threshold, and min/max rules are out of scope
- Values outside `capture_worthy_range` but inside `hard_range` are labeled `capture-worthy`;
  values outside `hard_range` are labeled `impossible by schema`
- Low-count demographic and equity-relevant categories are not suppressed
- Engagement funnel percentages use current stage count divided by the immediately prior stage
  count
- Missing survey/contact state is displayed separately and never inferred as attempted or
  completed
- All data remains synthetic or bundled local demonstration data; no real PHI path is
  introduced

**Scale/Scope**:
- Five current canonical entities: participants, daily_vitals, clinical_outcomes, alerts,
  staff_contacts
- Four required dashboard artifacts:
  `01_cohort_overview.png`, `02_outcome_prevalence.png`,
  `03_distribution_outliers.png`, `04_alert_engagement_funnel.png`
- One CLI panel set: `--panels core`
- One default manifest updated with deterministic metadata for each repo-relative artifact
- Two focused EDA test files named in SPEC-007

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **P1 Specification-Driven Development**: PASS. This plan maps directly to SPEC-007 and its
  2026-06-01 clarification record.
- **P2 Reproducibility by Default**: PASS. Inputs, commands, outputs, and manifest paths are
  local and deterministic.
- **P3 Schema-Driven Extensibility**: PASS. Tables and columns are resolved through the
  visualization schema registry and semantic roles instead of hardcoding one tenant's column
  names.
- **P5 Resilience / Graceful Degradation**: PASS. Required inputs fail loud before writes;
  optional context degrades to visible unavailable or warning sections.
- **P7 Honest Evaluation**: PASS. Outcome prevalence, class imbalance, and rare-outcome
  warnings expose counts, percentages, and missingness without model claims.
- **P8 Clinical Fidelity & Participant Safety**: PASS. Alert/funnel semantics avoid inferring
  follow-up completion from missing state and retain safety-relevant red/yellow/composite-red
  alert categories.
- **P9 Privacy & Synthetic-Data Transparency**: PASS. The workflow uses bundled local or
  synthetic data only and adds no PHI ingestion path.
- **P10 Equity-Centered & Accessible Design**: PASS. Cohort context groups equity-relevant
  fields, preserves low-count categories, uses direct labels/units, and keeps missing context
  visible.
- **Provenance / Traceability**: PASS. Planning artifacts carry frontmatter and link to
  SPEC-007 and dependency specs.

## Project Structure

### Documentation (this feature)

```text
specs/007-core-descriptive-eda-dashboards/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- cli-contract.md
|   |-- dashboard-artifacts-contract.md
|   |-- manifest-contract.md
|   `-- missingness-threshold-contract.md
`-- tasks.md             # Phase 2 output (/speckit.tasks - NOT created here)
```

### Source Code (repository root)

```text
src/
|-- validation/
|   `-- semantics.py             # Existing shared boolean/missingness parsing from SPEC-006
`-- visualization/
    |-- __init__.py
    |-- artifacts.py             # FigureArtifact and manifest read/write/upsert behavior
    |-- design.py                # Shared static dashboard style and save guard
    |-- schema_registry.py       # Canonical entities, semantic roles, units, ranges
    |-- validation.py            # Role and schema range validation helpers
    |-- eda_core.py              # Core EDA table loading, rendering, manifest registration
    `-- generate_eda.py          # CLI entry point for EDA generation

tests/
|-- test_eda_core_outputs.py
|-- test_eda_missingness_policy.py
|-- contract/
|   |-- test_artifact_manifest_contract.py
|   |-- test_visualization_design_contract.py
|   `-- test_visualization_registry_contract.py
`-- unit/
    |-- test_boolean_semantics.py
    |-- test_visualization_schema_registry.py
    |-- test_visualization_style.py
    `-- test_visualization_validation.py

outputs/
`-- figures/
    |-- manifest.json
    `-- eda/
        |-- 01_cohort_overview.png
        |-- 02_outcome_prevalence.png
        |-- 03_distribution_outliers.png
        `-- 04_alert_engagement_funnel.png
```

**Structure Decision**: Use the existing single Python package. Keep schema and validation
behavior in the established `src/visualization/` and `src/validation/` modules, add or update
only the core EDA renderer/CLI and focused tests needed for SPEC-007, and store generated
acceptance artifacts in the existing `outputs/figures/` manifest path.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Post-Design Constitution Check

- **P1**: PASS. Research, data model, contracts, and quickstart trace to SPEC-007 requirements
  and clarifications.
- **P2**: PASS. Quickstart uses clone-to-run local commands and deterministic output paths.
- **P3**: PASS. Contracts keep required/optional roles, units, and capture-worthy ranges in the
  schema registry.
- **P5**: PASS. Contracts require pre-write failure for required inputs and visible degradation
  for optional roles.
- **P7**: PASS. Outcome prevalence and class imbalance contracts require counts, percentages,
  missing denominators, and rare-outcome warning text.
- **P8**: PASS. Alert/contact completion remains explicit and never inferred from missing
  state.
- **P9**: PASS. No real-data pathway or PHI handling is added.
- **P10**: PASS. Cohort and funnel contracts preserve equity-relevant categories, direct labels,
  units, missingness, and readable static figures.
