---
id: PLAN-004A
title: Visualization Foundation and Schema Registry Implementation Plan
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-004A, SPEC-001]
implements: [P1, P2, P3, P5, P7, P10]
supersedes: null
superseded_by: null
related: [SPEC-001, SPEC-004B, SPEC-005, SPEC-006, SPEC-007]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Implementation Plan: Visualization Foundation and Schema Registry

**Branch**: `004-eda-descriptive-dashboard` | **Date**: 2026-06-01 | **Spec**: `specs/004-eda-descriptive-dashboard/spec.md`

**Input**: Feature specification from `specs/004-eda-descriptive-dashboard/spec.md`

## Summary

Implement a shared visualization foundation for Project Lullaby that maps source columns
to canonical semantic roles, validates visualization-readiness without corrupting source
data, centralizes static dashboard styling, and records deterministic figure metadata in
`outputs/figures/manifest.json`. The implementation keeps the existing SPEC-001 schema
and ingestion modules intact, adding visualization-specific contracts under
`src/visualization/` and a repository-root validation command that defaults to the
clarified `data/` CSV target while still accepting `--data-dir`.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**:
- Existing: pandas, pandera, pydantic, pytest
- Add: matplotlib for deterministic static dashboard-grade figures
- No seaborn, Plotly, notebooks, network services, or runtime web stack required for SPEC-004A

**Storage**:
- Local CSV inputs under `data/` by default, with `--data-dir` override
- JSON validation report at `artifacts/validation-report.json`
- JSON figure manifest at `outputs/figures/manifest.json`
- Static image artifacts under `outputs/figures/`

**Testing**: pytest unit, contract, and integration tests focused on visualization registry,
validation behavior, design helper contracts, artifact manifest behavior, and the root CLI

**Target Platform**: Linux/macOS developer environments and GitHub Actions CI; offline-only
runtime for validation and tests

**Project Type**: Python library + CLI foundation for later dashboard generators

**Performance Goals**:
- Default validation against repository-root `data/` completes in under 2 minutes locally
- Focused registry, style, manifest, and CLI tests complete in under 2 minutes in CI
- Figure save checks avoid heavyweight rendering beyond small contract fixtures

**Constraints**:
- Do not modify, impute, drop, or normalize away source values during visualization validation
- Preserve unknown extra columns for downstream callers
- Treat optional/future entities as registry-supported but not required until producer specs land
- Resolve aliases deterministically and report ambiguity explicitly
- Default data target is `data/`; alternate sources, including `data/synthetic`, require `--data-dir`
- Create a valid empty manifest at `outputs/figures/manifest.json` before figures exist
- Keep command output both human-readable and machine-readable
- Avoid network calls, notebook-only flows, and divergent distribution paths

**Scale/Scope**:
- Five current entities: participants, daily vitals, alerts, staff contacts, clinical outcomes
- Four optional future entity families: environment, recruitment, model predictions, model metrics
- One default visualization config file
- One registry, one validation layer, one design helper module, one artifact manifest module,
  one CLI command, and focused tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **P1 Specification-Driven Development**: PASS. The plan is derived from SPEC-004A and its
  2026-06-01 clarifications.
- **P2 Reproducibility by Default**: PASS. Root commands use local bundled data, deterministic
  JSON reports, a fixed manifest path, and static figure outputs.
- **P3 Schema-Driven Extensibility**: PASS. Visualization code consumes semantic roles and
  entity metadata instead of hardcoding plotting columns.
- **P5 Resilience / Graceful Degradation**: PASS. Required-role failures are loud, optional
  roles warn, extras are preserved, and no imputation occurs.
- **P7 Honest Evaluation**: PASS. Manifest entries preserve source entities, roles, warnings,
  and deterministic status for downstream figure auditability.
- **P10 Equity-Centered & Accessible Design**: PASS. The design contract requires accessible
  palettes, explicit labels, warnings, no-data panels, and non-color encodings.
- **Provenance / Traceability**: PASS. Planning artifacts carry frontmatter and link back to
  SPEC-004A and SPEC-001.

## Project Structure

### Documentation (this feature)

```text
specs/004-eda-descriptive-dashboard/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── artifact-manifest-contract.md
│   ├── schema-registry-contract.md
│   ├── validation-command-contract.md
│   └── visualization-design-contract.md
└── tasks.md             # Phase 2 output (/speckit.tasks - NOT created here)
```

### Source Code (repository root)

```text
config/
└── visualization.yaml

src/
├── cli/
│   └── validate_visualization_foundation.py
├── schemas/
│   ├── base.py          # Existing SPEC-001 schema contract, reused but not redefined
│   └── lullaby.py       # Existing default schema, used as canonical baseline
└── visualization/
    ├── __init__.py
    ├── artifacts.py     # Manifest creation, registration, validation
    ├── config.py        # VisualizationConfig loading/defaults
    ├── design.py        # Matplotlib style, panels, save guard
    ├── schema_registry.py
    └── validation.py

tests/
├── contract/
│   ├── test_artifact_manifest_contract.py
│   ├── test_validation_command_contract.py
│   ├── test_visualization_design_contract.py
│   └── test_visualization_registry_contract.py
├── integration/
│   └── test_visualization_foundation_cli.py
└── unit/
    ├── test_artifact_manifest.py
    ├── test_visualization_schema_registry.py
    ├── test_visualization_style.py
    └── test_visualization_validation.py
```

**Structure Decision**: Single Python project. Keep ingestion/schema validation under the
existing `src/schemas`, `src/validation`, and `src/ingestion` modules. Add a dedicated
`src/visualization/` package for semantic-role registry, visualization validation, design
helpers, config, and manifest behavior. Add the CLI under `src/cli/` to match existing
command placement.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Post-Design Constitution Check

- **P1**: PASS. Research, data model, contracts, and quickstart map to SPEC-004A requirements
  and clarifications.
- **P2**: PASS. Quickstart uses local commands only and records expected deterministic output
  locations.
- **P3**: PASS. Contracts center semantic roles, aliases, entity specs, and pluggable data
  directory selection.
- **P5**: PASS. Validation state preserves source rows, missingness, extras, and physiologic
  extremes while failing clearly on absent required roles.
- **P7**: PASS. Manifest contract records inputs, roles, warnings, source spec, UTC timestamp,
  and deterministic status for every figure artifact.
- **P10**: PASS. Design contract requires labels, palettes, warning/no-data panels, and
  non-color encodings for clinically meaningful categories.
