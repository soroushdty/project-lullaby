---
id:            PLAN-012
title:         Analytic Dashboard for Model Outputs — Implementation Plan
status:        draft
version:       0.1.0
created:       2026-06-01
updated:       2026-06-01
author:        Soroush Dianaty
depends_on:    [SPEC-012]
implements:    [P7, P8, P9, P10]
supersedes:    null
superseded_by: null
related:       [SPEC-004, SPEC-007, SPEC-010, SPEC-011]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Implementation Plan: Analytic Dashboard for Model Outputs

**Branch**: `012-analytic-model-dashboard` | **Date**: 2026-06-01 | **Spec**: `/specs/012-analytic-model-dashboard/spec.md`

**Input**: Feature specification from `/specs/012-analytic-model-dashboard/spec.md`

**Note**: This plan was produced by the `/speckit.plan` workflow after `/speckit.clarify` resolved the five key ambiguities captured in the spec's Clarifications section.

## Summary

Implement a static analytic reporting layer over the SPEC-011 model bake-off. The feature adds two new Python modules (`analytic_dashboard.py`, `model_cards.py`) under the existing `src/visualization/` package, a `config/costs.yaml` file, and three test files. A single CLI command reads completed SPEC-011 artifact files from a configurable model directory, renders 11 static panel PNGs to `outputs/figures/analytic/`, generates a TRIPOD-AI model card, and registers every artifact in the shared `outputs/figures/manifest.json` under `"type": "analytic"`. No model is retrained or re-scored during rendering.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: matplotlib ≥ 3.8 (panels), pandas ≥ 3.0 (artifact CSVs), PyYAML ≥ 6.0 (cost config), scikit-learn ≥ 1.5 (calibration diagnostics if needed). All already declared in `pyproject.toml`; no new dependencies required.

**Storage**: Repository files only — reads `outputs/modeling/` SPEC-011 CSVs and `config/costs.yaml`; writes PNGs and markdown to `outputs/figures/analytic/`; updates `outputs/figures/manifest.json`.

**Testing**: pytest ≥ 9.0 (`pyproject.toml` dev dependency).

**Target Platform**: Linux/macOS development; GitHub Actions CI.

**Project Type**: CLI reporting tool (static visualization layer).

**Performance Goals**: All 11 panels + model card complete in < 5 minutes on a single developer machine with SPEC-011 synthetic fixture data.

**Constraints**: No network calls; no model training or scoring; deterministic rendering (fixed matplotlib backend, fixed random seeds for any stochastic elements); unavailable panels for missing optional inputs; CLI exits 0 even when optional panels cannot render.

**Scale/Scope**: Single-repository static reporting; ~200 synthetic participants; ~8 400 participant-days; 11 PNG artifacts + 1 markdown artifact per run.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- P7 Honest Evaluation: PASS. Panel 1 ranks by AUPRC; accuracy and AUROC are not headline metrics; CI bounds required; Panel 4 reads all cost assumptions from config (no cherry-picked finance values).
- P8 Clinical Fidelity & Participant Safety: PASS. All outputs framed as signal characterization or synthetic-data characterization; no validated-clinical-performance claims anywhere in spec or plan.
- P9 Privacy & Synthetic-Data Transparency: PASS. Synthetic-data caveat required in model card; no PHI enters the repo.
- P10 Equity-Centered & Accessible Design: PASS. Subgroup fairness panel (Panel 9) required with denominators and sparse-data warnings; TRIPOD-AI model card requires subgroup assessment section.
- Provenance / Traceability: PASS. All artifacts carry `"type": "analytic"` in manifest; model card references exact config and output paths.

## Project Structure

### Documentation (this feature)

```text
specs/012-analytic-model-dashboard/
├── plan.md          ← this file
├── research.md      ← Phase 0 output
├── data-model.md    ← Phase 1 output
├── quickstart.md    ← Phase 1 output
└── contracts/
    ├── analytic-dashboard-cli.md
    └── manifest-entry-analytic.md
```

### Source Code (repository root)

```text
src/visualization/
├── analytic_dashboard.py   ← new: 11-panel renderer + CLI entry point
├── model_cards.py          ← new: TRIPOD-AI model card generator
├── design.py               ← existing: shared style helpers (reuse)
├── artifacts.py            ← existing: manifest read/write helpers (reuse)
└── schema_registry.py      ← existing: semantic labels / units (reuse)

config/
└── costs.yaml              ← new: cost assumptions for Panel 4

tests/
├── test_analytic_dashboard_outputs.py   ← new
├── test_cost_config_used.py             ← new
└── test_model_card_generation.py        ← new
```

**Structure Decision**: Add two new modules directly under the existing `src/visualization/` package. Reuse `design.py` for figure style, `artifacts.py` for manifest I/O, and `schema_registry.py` for axis label lookup — exactly the same pattern used by `eda_core.py`, `eda_longitudinal.py`, and `eda_archetypes.py`. No new packages or sub-packages are introduced.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| None | N/A | N/A |

## Post-Design Constitution Check

- P7: PASS. CLI design enforces read-only artifact mode; leaderboard contract (contracts/analytic-dashboard-cli.md) locks metric ordering at AUPRC primary.
- P8: PASS. Synthetic-data framing requirement flows into model card contract; unavailable-panel fallback prevents silent metric fabrication.
- P9: PASS. No PHI path; cost config is purely operational, not participant-level.
- P10: PASS. Subgroup panel contract specifies denominator requirement and sparse-data warning gate.
- Provenance/Traceability: PASS. Manifest entry contract specifies `"type"` field; model card contract specifies exact-path references.
