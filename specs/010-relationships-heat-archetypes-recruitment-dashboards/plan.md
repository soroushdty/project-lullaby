---
id: PLAN-010
title: Relationships, Heat Exposure, Archetypes, and Recruitment Dashboards Implementation Plan
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

# Implementation Plan: Relationships, Heat Exposure, Archetypes, and Recruitment Dashboards

**Branch**: `010-relationships-heat-archetypes-recruitment-dashboards` | **Date**: 2026-06-01 | **Spec**: `specs/010-relationships-heat-archetypes-recruitment-dashboards/spec.md`

**Input**: Feature specification from `specs/010-relationships-heat-archetypes-recruitment-dashboards/spec.md`

## Summary

Implement the remaining descriptive EDA panels 10 through 13: relationships, heat/environment
context, participant archetype exploration, and recruitment/enrollment timelines. The
technical approach is to extend the existing EDA CLI with a `relationships` panel set and
`all` aggregate panel set, add focused renderer modules under `src/visualization/`, reuse the
schema registry, design helpers, and manifest upsert behavior, and write four static PNG
artifacts under `outputs/figures/eda/`.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**:
- Existing runtime: pandas, numpy, matplotlib, PyYAML, pandera, pydantic
- Existing visualization foundation under `src/visualization/`
- Existing semantic parsing under `src/validation/semantics.py`
- Existing test tooling: pytest and Pillow for PNG dimension assertions
- No new runtime dependency planned

**Storage**:
- Local canonical CSV inputs under `data/` by default; `data/raw` is accepted by the CLI and
  may resolve to `data/` when a literal `data/raw` directory is absent
- Optional synthetic longitudinal inputs under `data/synthetic/longitudinal/`
- Static PNG outputs under `outputs/figures/eda/`
- Figure artifact manifest at `outputs/figures/manifest.json`
- Focused pytest fixtures may use temporary input, output, and manifest directories

**Testing**: pytest focused on `tests/test_eda_relationships_outputs.py`, with regression
coverage from existing core and longitudinal EDA tests

**Target Platform**: Local Linux/macOS developer environments and GitHub Actions CI; offline
static artifact generation only

**Project Type**: Single Python package with a CLI entry point and deterministic static figure
generation

**Performance Goals**:
- Generate the four SPEC-010 PNG artifacts from bundled local data in under 3 minutes on a
  normal developer machine
- Focused SPEC-010 EDA tests complete in under 2 minutes from the repository root
- `--panels all` generates panels 1 through 13 in under 6 minutes on a normal developer
  machine
- Each required PNG is at least 1600 x 900 pixels and readable at the configured static output
  size

**Constraints**:
- Dashboards are descriptive only and must not predict outcomes, model scores, impute missing
  values, or imply causality
- Missing required input tables fail before requested artifacts or manifest entries are
  written
- Missing optional entities and roles render visible unavailable or warning sections rather
  than crashing
- Panel 11 requires a real `environment` table and must not fabricate environment data from
  daily-vitals columns
- Panel 10 may use observed `daily_vitals.heat_index_c` as a clearly labeled Panel 10-only
  proxy when no environment table exists
- High-heat periods use the clarified fallback order: `heat_wave == true`, else
  `heat_exposure_level` high/extreme, else observed `heat_index_c >= 75th percentile`
- Panel 12 alert burden uses optional `alerts` rows when available and is unavailable when
  alerts are absent
- Panel 12 explicit archetype labels are used when available; known aliases normalize to
  canonical labels, unknown explicit labels are preserved as additional rows and metadata
- Panel 12 provisional labels are transparent, visibly provisional, and resolved by priority:
  true emergency, heat-stressed, silent decliner, overwhelmed mom, diligent monitor
- Panel 13 is calendar-aware when parseable dates exist and renders unavailable when all date
  sources are missing
- All data remains synthetic or bundled local demonstration data; no real PHI path is
  introduced

**Scale/Scope**:
- Six canonical or optional entities: participants, daily_vitals, clinical_outcomes,
  environment, recruitment, alerts
- Four required dashboard artifacts:
  `10_relationships.png`, `11_heat_environment.png`,
  `12_archetype_explorer.png`, `13_recruitment_timeline.png`
- One new CLI panel set: `--panels relationships`
- One aggregate CLI panel set: `--panels all`
- One default manifest updated with deterministic metadata for each repo-relative artifact
- One focused EDA test file named in SPEC-010

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **P1 Specification-Driven Development**: PASS. This plan maps directly to SPEC-010 and its
  2026-06-01 clarification record.
- **P2 Reproducibility by Default**: PASS. Inputs, commands, outputs, high-heat fallback
  order, archetype fallback rules, and manifest paths are deterministic.
- **P3 Schema-Driven Extensibility**: PASS. Tables and columns are resolved through the
  visualization schema registry and semantic roles.
- **P5 Resilience / Graceful Degradation**: PASS. Required inputs fail loud before writes;
  optional context degrades to visible unavailable or warning sections.
- **P7 Honest Evaluation**: PASS. The feature is descriptive, records pairwise denominators,
  avoids imputation, and labels relationships as non-causal.
- **P8 Clinical Fidelity & Participant Safety**: PASS. CV-vs-heat discriminators are framed as
  descriptive trajectory patterns, not clinical decisions.
- **P9 Privacy & Synthetic-Data Transparency**: PASS. The workflow uses bundled local or
  synthetic data only and adds no PHI ingestion path.
- **P10 Equity-Centered & Accessible Design**: PASS. Heat, AC access, missingness, and
  archetype summaries foreground participant context and readable static panels.
- **Provenance / Traceability**: PASS. Planning artifacts carry frontmatter and link to
  SPEC-010 and dependency specs.

## Project Structure

### Documentation (this feature)

```text
specs/010-relationships-heat-archetypes-recruitment-dashboards/
|-- spec.md
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- cli-contract.md
|   |-- dashboard-artifacts-contract.md
|   `-- relationship-environment-archetype-contract.md
`-- tasks.md             # Phase 2 output (/speckit.tasks - NOT created here)
```

### Source Code (repository root)

```text
src/
|-- validation/
|   `-- semantics.py             # Existing shared boolean/missingness parsing
`-- visualization/
    |-- __init__.py
    |-- artifacts.py             # Existing FigureArtifact manifest behavior
    |-- design.py                # Existing static dashboard style and save guard
    |-- schema_registry.py       # Existing canonical semantic roles
    |-- validation.py            # Existing role and schema range validation helpers
    |-- eda_core.py              # Existing SPEC-007 panels 1-4
    |-- eda_longitudinal.py      # Existing SPEC-009 panels 5, 6, 8, and 9
    |-- patient_view.py          # Existing SPEC-009 patient timeline panel 7
    |-- eda_relationships.py     # New SPEC-010 shared loader and Panel 10
    |-- eda_environment.py       # New SPEC-010 Panel 11
    |-- eda_archetypes.py        # New SPEC-010 Panels 12 and 13
    `-- generate_eda.py          # Extended CLI entry point

tests/
|-- test_eda_core_outputs.py
|-- test_eda_longitudinal_outputs.py
|-- test_patient_timeline.py
|-- test_eda_relationships_outputs.py
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
        |-- ...
        |-- 09_missingness_mechanism.png
        |-- 10_relationships.png
        |-- 11_heat_environment.png
        |-- 12_archetype_explorer.png
        `-- 13_recruitment_timeline.png
```

**Structure Decision**: Use the existing single Python package. Add SPEC-010 renderers beside
the existing EDA modules, keep shared table loading and manifest registration in the
relationships module, and preserve the established output and manifest paths.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Post-Design Constitution Check

- **P1**: PASS. Research, data model, contracts, and quickstart trace to SPEC-010 requirements
  and clarifications.
- **P2**: PASS. Quickstart uses clone-to-run local commands and deterministic output paths.
- **P3**: PASS. Contracts keep required/optional roles, source tables, units, and metadata
  schema-driven through the registry.
- **P5**: PASS. Contracts require pre-write failure for required inputs and visible
  degradation for optional roles.
- **P7**: PASS. Relationship panels use observed pairs only and explicitly avoid causal
  interpretation.
- **P8**: PASS. CV-risk-like and heat-strain-like labels are descriptive discriminator
  annotations, not clinical decisions or risk scores.
- **P9**: PASS. No real-data pathway or PHI handling is added.
- **P10**: PASS. Heat, AC access, missingness, and archetype summaries remain visible and
  annotated in static panels.
