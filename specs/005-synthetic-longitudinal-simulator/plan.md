---
id: PLAN-005
title: Synthetic Longitudinal Physiologic Data Simulator Implementation Plan
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-005, SPEC-001, SPEC-004A]
implements: [P1, P2, P3, P5, P7, P8, P9]
supersedes: null
superseded_by: null
related: [SPEC-004A, SPEC-004B, SPEC-006, SPEC-007]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Implementation Plan: Synthetic Longitudinal Physiologic Data Simulator

**Branch**: `005-synthetic-longitudinal-simulator` | **Date**: 2026-06-01 | **Spec**: `specs/005-synthetic-longitudinal-simulator/spec.md`

**Input**: Feature specification from `specs/005-synthetic-longitudinal-simulator/spec.md`

## Summary

Implement a canonical, seeded longitudinal synthetic cohort simulator that produces a full
participant-day grid and related cohort tables under `data/synthetic/longitudinal/`. The
implementation adds a `src/simulation/` package, default YAML configuration, and a clone-to-run
generation script while extending SPEC-004A's schema registry so all generated tables validate
before downstream dashboards or model workflows consume them. Generation preserves missingness
as evidence, encodes cardiovascular, heat-strain, and overlap physiology, and writes a structured
summary that gates readiness on schema validation and target diagnostics.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**:
- Existing: pandas, PyYAML, pytest, pandera, pydantic, matplotlib
- Add: numpy as an explicit dependency for deterministic vectorized random generation
- No notebook, network service, database, web runtime, or external data dependency required

**Storage**:
- YAML input config at `config/simulation.yaml`
- CSV/YAML/JSON output package under `data/synthetic/longitudinal/` by default
- Temporary test output directories through pytest fixtures

**Testing**: pytest unit and integration-style tests focused on reproducibility, target
diagnostics, schema validation, CLI behavior, and preservation of missing values

**Target Platform**: Linux/macOS developer environments and GitHub Actions CI; offline-only
runtime

**Project Type**: Python library + CLI/script generator inside the existing single-package repo

**Performance Goals**:
- Default 200 participant x 84 day run completes in under 30 seconds locally
- Larger 10,000 participant x 84 day run completes in under 2 minutes on CI-class hardware
- Focused simulation tests complete in under 2 minutes from the repository root

**Constraints**:
- Same seed and effective configuration produce byte-identical CSV content except explicitly
  allowed run metadata in JSON/YAML summary files
- `daily_vitals.csv` uses a full participant-day grid: participant count multiplied by study days
- Temperature and heat-index exports are Celsius, even when scenario defaults are specified in F
- Missing values remain missing in raw exports; no sentinel replacement and no imputation
- Schema validation and required target diagnostics are readiness gates
- Failed validation or failed target diagnostics leave artifacts inspectable, mark the summary
  failed/not ready, and report command failure
- Alert thresholds and clinical outcome definitions are safety-critical configuration
- Synthetic data must be clearly labeled as synthetic and contain no real PHI

**Scale/Scope**:
- Default cohort: 200 participants, 84 study days, five archetypes
- Default daily vitals rows: 16,800
- Required output artifacts: 7 CSV tables plus effective config YAML and summary JSON
- Implementation scope: simulator, config, export, schema-registry extension, CLI/script, tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **P1 Specification-Driven Development**: PASS. Plan derives from SPEC-005 and the
  2026-06-01 clarification record.
- **P2 Reproducibility by Default**: PASS. The design uses fixed seeds, effective config capture,
  deterministic export ordering, and clone-to-run commands.
- **P3 Schema-Driven Extensibility**: PASS. Generated columns validate through SPEC-004A's
  schema registry, which is extended for environment and recruitment.
- **P5 Resilience / Graceful Degradation**: PASS. Missingness is preserved, validation fails
  loud, and failed runs remain inspectable without being marked ready.
- **P7 Honest Evaluation**: PASS. Summary diagnostics expose target, observed value, tolerance,
  denominator, and pass/fail status.
- **P8 Clinical Fidelity & Participant Safety**: PASS. Alert thresholds and outcome definitions
  are configuration-driven and treated as safety-critical.
- **P9 Privacy & Synthetic-Data Transparency**: PASS. Outputs are synthetic-only and include
  explicit synthetic provenance in config and summary.
- **Provenance / Traceability**: PASS. Planning artifacts carry frontmatter and link to SPEC-005,
  SPEC-001, and SPEC-004A.

## Project Structure

### Documentation (this feature)

```text
specs/005-synthetic-longitudinal-simulator/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- config-contract.md
|   |-- diagnostics-contract.md
|   |-- generator-cli-contract.md
|   `-- output-package-contract.md
`-- tasks.md             # Phase 2 output (/speckit.tasks - NOT created here)
```

### Source Code (repository root)

```text
config/
|-- meows_thresholds.synthetic.yaml
|-- simulation.yaml
`-- visualization.yaml

scripts/
`-- generate_synthetic.py

src/
|-- simulation/
|   |-- __init__.py
|   |-- cohort.py
|   |-- config.py
|   |-- environment.py
|   |-- export.py
|   |-- missingness.py
|   `-- physiology.py
`-- visualization/
    |-- schema_registry.py    # Extend entity/role registry for generated tables
    `-- validation.py         # Reuse for generation readiness checks

tests/
|-- integration/
|   `-- test_simulation_cli.py
`-- unit/
    |-- test_simulation_config.py
    |-- test_simulation_reproducibility.py
    |-- test_simulation_schema_validation.py
    `-- test_simulation_targets.py
```

**Structure Decision**: Single Python project. Add a cohesive `src/simulation/` package for
configuration, cohort assignment, environment generation, physiology, missingness, and export.
Keep CLI entry through a small `scripts/generate_synthetic.py` wrapper to match the SPEC-005
clone-to-run command, while public generation functions remain importable from `src.simulation`.
Reuse SPEC-004A visualization validation instead of adding a parallel schema gate.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Post-Design Constitution Check

- **P1**: PASS. Research, data model, contracts, and quickstart map to SPEC-005 requirements and
  clarifications.
- **P2**: PASS. Quickstart regenerates the cohort from local config, seed, and deterministic
  export ordering.
- **P3**: PASS. Output table contracts align with and extend the visualization schema registry.
- **P5**: PASS. Failure contracts leave artifacts inspectable while marking runs failed/not ready.
- **P7**: PASS. Diagnostics contract records target checks with denominators and tolerances.
- **P8**: PASS. Alert and outcome logic stays under explicit config and contracts.
- **P9**: PASS. Data model and output package identify synthetic provenance and avoid PHI.
