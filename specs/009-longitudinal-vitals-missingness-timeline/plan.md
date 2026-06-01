---
id: PLAN-009
title: Longitudinal Vitals, Missingness, Signal Quality, and Patient Timeline Implementation Plan
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

# Implementation Plan: Longitudinal Vitals, Missingness, Signal Quality, and Patient Timeline

**Branch**: `009-longitudinal-vitals-missingness-timeline` | **Date**: 2026-06-01 | **Spec**: `specs/009-longitudinal-vitals-missingness-timeline/spec.md`

**Input**: Feature specification from `specs/009-longitudinal-vitals-missingness-timeline/spec.md`

## Summary

Implement longitudinal descriptive EDA panels 5 through 9: vital trajectories, missingness and
adherence, one-participant clinical timeline, data-quality scorecard, and missingness-mechanism
diagnostics. The technical approach is to extend the existing SPEC-007 EDA CLI and
visualization foundation with `src/visualization/eda_longitudinal.py` and
`src/visualization/patient_view.py`, reuse schema-registry role resolution and manifest
registration, preserve missingness as visible gaps, and write five static PNG artifacts under
`outputs/figures/eda/`.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**:
- Existing runtime: pandas, numpy, matplotlib, PyYAML, pandera, pydantic
- Existing validation and visualization modules under `src/validation/` and
  `src/visualization/`
- Existing test tooling: pytest
- No new runtime dependency planned; static dashboard layout should remain Matplotlib-based

**Storage**:
- Local canonical CSV inputs under `data/` by default; `data/raw` is accepted by the CLI and
  may resolve to `data/` when a literal `data/raw` directory is absent
- Optional synthetic longitudinal inputs under `data/synthetic/longitudinal/`
- Static PNG outputs under `outputs/figures/eda/`
- Figure artifact manifest at `outputs/figures/manifest.json`
- Focused pytest fixtures may use temporary input, output, and manifest directories

**Testing**: pytest focused on `tests/test_eda_longitudinal_outputs.py` and
`tests/test_patient_timeline.py`, with supporting coverage from the existing visualization
foundation, schema registry, semantic parsing, and artifact manifest tests

**Target Platform**: Local Linux/macOS developer environments and GitHub Actions CI; offline
static artifact generation only

**Project Type**: Single Python package with a CLI entry point and deterministic static figure
generation

**Performance Goals**:
- Generate the five longitudinal PNG artifacts from bundled local or synthetic data in under 3
  minutes on a normal developer machine
- Focused longitudinal EDA tests complete in under 2 minutes from the repository root
- Each required PNG is at least 1600 x 900 pixels and readable at the configured static output
  size
- Missingness matrix rendering remains readable for large cohorts by downsampling displayed
  rows when participant count exceeds 250 while computing metrics on all rows

**Constraints**:
- Dashboards are descriptive only and must not predict outcomes, rank clinical risk, or impute
  missing values
- Missing required input tables fail before affected artifact files or manifest entries are
  written
- Missing required semantic roles fail before affected artifact files or manifest entries are
  written
- Optional entities and roles render labeled unavailable or warning sections instead of
  crashing
- Missing longitudinal observations remain visible as line gaps, missing matrix states,
  denominators, and warning annotations
- `--week-start` and `--week-end` are inclusive, 1-based study-week filters derived from
  study-day values
- `--overlay-environment` defaults to `false`; setting it to `true` never makes environment a
  required table
- Automatic participant selection is deterministic and records score components in the
  manifest
- Data-quality score components are normalized 0-1; unavailable components are excluded with
  redistributed weights and manifest warnings
- Missingness-mechanism diagnostics are labeled as exploratory signals consistent with MCAR,
  MAR, or MNAR hypotheses, never proof
- All data remains synthetic or bundled local demonstration data; no real PHI path is
  introduced

**Scale/Scope**:
- Six canonical or optional entities: participants, daily_vitals, alerts, staff_contacts,
  clinical_outcomes, environment
- Five required dashboard artifacts:
  `05_vital_trajectories.png`, `06_missingness_adherence.png`,
  `07_patient_timeline.png`, `08_data_quality_scorecard.png`,
  `09_missingness_mechanism.png`
- One CLI panel set: `--panels longitudinal`
- Four longitudinal static-render flags: `--participant-id`, `--week-start`, `--week-end`,
  and `--overlay-environment true|false`
- One default manifest updated with deterministic metadata for each repo-relative artifact
- Two focused EDA test files named in SPEC-009

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **P1 Specification-Driven Development**: PASS. This plan maps directly to SPEC-009 and its
  2026-06-01 clarification record.
- **P2 Reproducibility by Default**: PASS. Inputs, commands, outputs, participant selection,
  and manifest paths are local and deterministic.
- **P3 Schema-Driven Extensibility**: PASS. Tables and columns are resolved through the
  visualization schema registry and semantic roles, with small registry extensions for missing
  participant context roles if needed.
- **P5 Resilience / Graceful Degradation**: PASS. Required inputs fail loud before writes;
  optional context degrades to visible unavailable or warning sections.
- **P7 Honest Evaluation**: PASS. The feature remains descriptive, avoids imputation, and
  labels missingness-mechanism diagnostics as exploratory evidence rather than proof.
- **P8 Clinical Fidelity & Participant Safety**: PASS. Timeline thresholds are used only when
  schema or reference sources exist; capture-worthy extremes are preserved rather than hidden.
- **P9 Privacy & Synthetic-Data Transparency**: PASS. The workflow uses bundled local or
  synthetic data only and adds no PHI ingestion path.
- **P10 Equity-Centered & Accessible Design**: PASS. Participant timeline context includes AC
  access, insurance, PIH severity, parity, health literacy, and psychosocial fields where
  available; missing/present states do not rely on color alone.
- **Provenance / Traceability**: PASS. Planning artifacts carry frontmatter and link to
  SPEC-009 and dependency specs.

## Project Structure

### Documentation (this feature)

```text
specs/009-longitudinal-vitals-missingness-timeline/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- cli-contract.md
|   |-- longitudinal-artifacts-contract.md
|   |-- manifest-contract.md
|   `-- quality-missingness-contract.md
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
    |-- schema_registry.py       # Existing roles plus optional longitudinal context roles
    |-- validation.py            # Existing role and schema range validation helpers
    |-- eda_core.py              # Existing SPEC-007 panels 1-4
    |-- eda_longitudinal.py      # New SPEC-009 panels 5, 6, 8, and 9
    |-- patient_view.py          # New SPEC-009 patient timeline panel 7
    `-- generate_eda.py          # Extended CLI entry point for core and longitudinal panels

tests/
|-- test_eda_core_outputs.py
|-- test_eda_missingness_policy.py
|-- test_eda_longitudinal_outputs.py
|-- test_patient_timeline.py
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
        |-- 04_alert_engagement_funnel.png
        |-- 05_vital_trajectories.png
        |-- 06_missingness_adherence.png
        |-- 07_patient_timeline.png
        |-- 08_data_quality_scorecard.png
        `-- 09_missingness_mechanism.png
```

**Structure Decision**: Use the existing single Python package. Add longitudinal rendering
beside the existing core EDA renderer, keep patient-specific layout in a focused helper module,
extend the current CLI rather than creating a second entry point, and preserve the established
manifest and static PNG output paths.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Post-Design Constitution Check

- **P1**: PASS. Research, data model, contracts, and quickstart trace to SPEC-009 requirements
  and clarifications.
- **P2**: PASS. Quickstart uses clone-to-run local commands and deterministic output paths.
- **P3**: PASS. Contracts keep required/optional roles, units, ranges, and participant context
  in the schema registry or optional-role metadata.
- **P5**: PASS. Contracts require pre-write failure for required inputs and visible
  degradation for optional roles.
- **P7**: PASS. Missingness diagnostics are exploratory, not proof; no prediction or
  imputation is introduced.
- **P8**: PASS. Timeline thresholds and capture-worthy labels are reference-driven and preserve
  observed safety-relevant extremes.
- **P9**: PASS. No real-data pathway or PHI handling is added.
- **P10**: PASS. Missing/present states are not color-only, equity-relevant context is visible,
  and large-cohort displays remain readable through deterministic downsampling.
