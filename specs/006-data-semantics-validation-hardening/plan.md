---
id: PLAN-006
title: Data Semantics and Validation Hardening Implementation Plan
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-006, SPEC-001, SPEC-003, SPEC-004A, SPEC-005]
implements: [P3, P5, P7, P10]
supersedes: null
superseded_by: null
related: [SPEC-003, SPEC-004A, SPEC-005]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Implementation Plan: Data Semantics and Validation Hardening

**Branch**: `006-core-descriptive-eda-dashboards` | **Date**: 2026-06-01 | **Spec**: `specs/006-data-semantics-validation-hardening/spec.md`

**Input**: Feature specification from `specs/006-data-semantics-validation-hardening/spec.md`

## Summary

Implement a cross-cutting hardening pass that makes Project Lullaby's boolean semantics,
missingness policy, required-input validation, artifact registration, simulator diagnostics,
and category completeness behavior explicit and testable. The technical approach is to add a
small shared semantic parsing layer, route ingestion/simulation/EDA boolean logic through it,
fail before artifact writes when required dashboard inputs are invalid, preserve missing and
invalid optional states as warnings, register all repo-relative artifacts in the default
manifest, and refresh affected tracked dashboard artifacts after semantic fixes.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**:
- Existing: pandas, numpy, matplotlib, PyYAML, pandera, pydantic, pytest
- No new runtime dependency planned
- No network service, notebook flow, database, or external data dependency required

**Storage**:
- Local CSV input tables under `data/` and `data/synthetic/longitudinal/`
- Static PNG dashboard outputs under `outputs/figures/**`
- Default artifact manifest at `outputs/figures/manifest.json`
- Focused pytest fixtures using temporary directories

**Testing**: pytest unit, contract, and integration-style tests for semantic parsing, stream
pending selection, simulator diagnostics, EDA missingness/required-input behavior, manifest
registration, and regenerated artifact acceptance evidence

**Target Platform**: Local Linux/macOS development environments and GitHub Actions CI; offline
runtime only

**Project Type**: Single Python package with CLI entry points and static artifact generation

**Performance Goals**:
- Shared boolean parser handles typical dashboard/simulator tables with vectorized pandas
  operations and negligible overhead relative to plotting
- Focused SPEC-006 tests complete in under 2 minutes from the repository root
- Existing full test suite remains practical for CI and local validation

**Constraints**:
- Missingness is evidence and must not be silently converted to negative/false
- Invalid boolean-like tokens fail required roles but warn and render as `Missing/Unknown` for
  optional roles
- Required dashboard input failures stop before writing or registering requested artifacts
- Optional dashboard inputs continue through labeled unavailable/warning panels
- Manifest entries must use repo-relative paths; outside-repo outputs warn and remain
  unregistered
- Category overflow must preserve every clinically meaningful category and count
- Dashboard semantics changes require regenerated tracked artifacts and manifest updates
- No real PHI enters the repo; bundled and generated data remain synthetic-only

**Scale/Scope**:
- Cross-cutting changes across ingestion stream replay, simulator diagnostics, visualization
  EDA core, artifact manifest validation, and focused tests
- Existing four dashboard PNGs and default manifest are acceptance artifacts when affected
- No new dashboard panels, no predictive modeling, and no imputation behavior

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **P1 Specification-Driven Development**: PASS. Plan derives from SPEC-006 and the
  2026-06-01 clarification record.
- **P2 Reproducibility by Default**: PASS. Hardening preserves clone-to-run commands and
  requires regenerated tracked artifacts when semantics change.
- **P3 Schema-Driven Extensibility**: PASS. Required/optional role behavior remains driven by
  schema contracts and shared semantic parsing, not one-off column truthiness.
- **P5 Resilience / Graceful Degradation**: PASS. Required failures fail loud before artifact
  writes; optional invalids degrade with structured warnings and visible missing/unknown state.
- **P7 Honest Evaluation**: PASS. Outcome prevalence, class imbalance, and simulator
  diagnostics stop treating missing/string false values as negative or true by accident.
- **P8 Clinical Fidelity & Participant Safety**: PASS. Alert and contact states use explicit
  completion mappings instead of treating any non-null nurse outcome as completed.
- **P9 Privacy & Synthetic-Data Transparency**: PASS. Work uses local synthetic/bundled data
  and introduces no real PHI path.
- **P10 Equity-Centered & Accessible Design**: PASS. Category completeness preserves rare and
  equity-relevant categories while keeping figures readable.
- **Provenance / Traceability**: PASS. Planning artifacts carry frontmatter and link to the
  originating spec and dependency specs.

## Project Structure

### Documentation (this feature)

```text
specs/006-data-semantics-validation-hardening/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- domain-boolean-semantics-contract.md
|   |-- eda-hardening-contract.md
|   |-- manifest-registration-contract.md
|   `-- simulation-diagnostics-contract.md
`-- tasks.md             # Phase 2 output (/speckit.tasks - NOT created here)
```

### Source Code (repository root)

```text
src/
|-- validation/
|   |-- engine.py
|   |-- pandera_models.py
|   `-- semantics.py             # New shared domain boolean/missingness parsing
|-- ingestion/
|   `-- stream/
|       `-- adapter.py           # Use shared parser for _stream_pending
|-- simulation/
|   `-- export.py                # Use shared parser for diagnostics
`-- visualization/
    |-- artifacts.py             # Repo-relative manifest registration behavior
    |-- eda_core.py              # Missingness, required input, category, funnel fixes
    `-- generate_eda.py          # CLI error/warning propagation as needed

tests/
|-- contract/
|   |-- test_artifact_manifest_contract.py
|   `-- test_stream_adapter_contract.py
|-- integration/
|   |-- test_simulation_cli.py
|   `-- test_visualization_foundation_cli.py
|-- unit/
|   |-- test_boolean_semantics.py
|   |-- test_artifact_manifest.py
|   |-- test_simulation_targets.py
|   |-- test_stream_adapter_unit.py
|   `-- test_visualization_validation.py
|-- test_eda_core_outputs.py
`-- test_eda_missingness_policy.py
```

**Structure Decision**: Use the existing single Python package. Add one shared
`src/validation/semantics.py` helper for domain boolean parsing and missing/invalid state
classification, then update ingestion, simulation diagnostics, and visualization callers to
reuse it. Keep dashboard generation in `src/visualization/eda_core.py` and artifact manifest
logic in `src/visualization/artifacts.py`; expand existing tests rather than creating a new
parallel validation stack.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Post-Design Constitution Check

- **P1**: PASS. Research, data model, contracts, and quickstart map directly to SPEC-006
  requirements and clarifications.
- **P2**: PASS. Quickstart includes deterministic local test and regeneration commands.
- **P3**: PASS. Boolean semantics and required/optional roles are centralized and reusable.
- **P5**: PASS. Failure and degradation behavior is explicit in contracts.
- **P7**: PASS. Diagnostics and EDA prevalence counts expose denominators and missingness.
- **P8**: PASS. Completion states are explicit and do not infer clinical follow-up success.
- **P9**: PASS. No real-data pathway is introduced.
- **P10**: PASS. Rare and equity-relevant categories stay auditable even when overflow is used.
