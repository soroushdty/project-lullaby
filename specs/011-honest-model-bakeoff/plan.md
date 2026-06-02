---
id: PLAN-011
title: Honest Model Bake-off Under Severe Class Imbalance Implementation Plan
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-011, SPEC-001, SPEC-004, SPEC-005]
implements: [P7, P8]
supersedes: null
superseded_by: null
related: [SPEC-004, SPEC-005, SPEC-006, SPEC-007, SPEC-009, SPEC-010]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Implementation Plan: Honest Model Bake-off Under Severe Class Imbalance

**Branch**: `011-honest-model-bakeoff` | **Date**: 2026-06-01 | **Spec**: `specs/011-honest-model-bakeoff/spec.md`

**Input**: Feature specification from `specs/011-honest-model-bakeoff/spec.md`

## Summary

Implement a reproducible participant-level modeling bake-off that compares a MEOWS-style
logistic baseline, classic machine-learning models, and an MLP under participant-grouped
cross-validation. The technical approach is to add a new `src/modeling/` package and
`scripts/run_model_bakeoff.py`, resolve canonical and synthetic longitudinal CSVs through a
small dataset adapter, build fold-local sklearn pipelines, compute imbalance-aware metrics
and calibration summaries, and write auditable CSV/JSON/YAML artifacts under the requested
output directory.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**:
- Existing runtime: numpy, pandas, PyYAML, pydantic, pandera
- New runtime dependency: scikit-learn for logistic regression, random forest, gradient
  boosting, MLP, metrics, preprocessing, and grouped/stratified CV primitives
- Existing test tooling: pytest
- No imbalanced-learn dependency planned for the default implementation; `resampling: none`
  is the default and non-default resampling remains a fold-local extension point

**Storage**:
- Local CSV inputs under caller-provided `--data-dir`
- Default config at `config/modeling.yaml`
- Modeling outputs under caller-provided `--out-dir`, defaulting to `outputs/modeling`
- No database, external service, network call, or server state

**Testing**:
- Focused pytest files required by SPEC-011:
  `tests/test_grouped_cv_no_leakage.py`,
  `tests/test_resampling_inside_fold.py`,
  `tests/test_bakeoff_outputs.py`,
  `tests/test_model_metrics_ci.py`
- Existing schema, simulation, and visualization tests should remain unaffected

**Target Platform**: Local Linux/macOS developer environments and GitHub Actions CI; offline
batch CLI execution only

**Project Type**: Single Python package with deterministic batch CLI and file-based artifacts

**Performance Goals**:
- Focused SPEC-011 tests complete in under 3 minutes from the repository root
- Synthetic longitudinal bake-off completes in under 10 minutes on a normal developer machine
  with the default 200-participant bundled synthetic cohort
- Default run remains deterministic by seed across fold assignment, model initialization,
  threshold selection, bootstrap resampling, and row ordering

**Constraints**:
- Participant-level rows are the default modeling unit; `observation_id` defaults to
  participant id
- Target is `outcome.cv_event`
- Event participants use only observations strictly before
  `cv_event_date - leakage_guard_days_before_event`; non-event participants use the full
  observed window
- No participant may appear in both train and validation in any fold or repeat
- Preprocessing, imputation, scaling, optional resampling, feature selection, model fitting,
  and threshold tuning are fold-local
- Resampling must never happen before the split
- Raw EDA dataframes are never mutated by modeling imputation or preprocessing
- Primary headline metrics are AUPRC, recall at fixed precision, and Brier score
- AUROC is secondary when present; accuracy is never a headline metric
- Calibration and operating-point notes must record unavailable or degenerate cases rather
  than fabricating values
- Synthetic runs are framed as exploratory signal characterization, not validated clinical
  performance
- No real PHI path, credential, external ingestion, or clinical deployment behavior is added

**Scale/Scope**:
- Default synthetic longitudinal cohort: hundreds of participants and roughly one
  participant-level modeling row per participant
- Default CV: 5 folds x 10 repeats x four enabled models
- Required modules: eight files under `src/modeling/`, one config file, one script, and four
  focused test files
- Required outputs: nine non-optional CSV/JSON/YAML artifacts plus optional explanation
  artifacts when supported

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **P1 Specification-Driven Development**: PASS. This plan maps directly to SPEC-011 and its
  2026-06-01 clarification record.
- **P2 Reproducibility by Default**: PASS. The CLI, config, seed, CV repeats, model random
  states, threshold selection, and bootstrap CI method are deterministic.
- **P3 Schema-Driven Extensibility**: PASS. The dataset adapter resolves canonical roles and
  accepted synthetic aliases without hardcoding one future institution's schema.
- **P5 Resilience / Graceful Degradation**: PASS. Required roles fail before training;
  optional features and non-estimable metrics are recorded as unavailable with notes.
- **P7 Honest Evaluation**: PASS. Primary metrics are rare-event appropriate, CIs are
  reported, AUROC is secondary, accuracy is not headline, and limitations are written beside
  outputs.
- **P8 Clinical Fidelity & Participant Safety**: PASS. The primary CV-event target and
  MEOWS-style baseline are treated as safety-critical study-design logic; threshold behavior
  is explicit and auditable.
- **P9 Privacy & Synthetic-Data Transparency**: PASS. The plan uses local bundled/synthetic
  data and adds no PHI ingestion or storage path.
- **P10 Equity-Centered & Accessible Design**: PASS. The output language avoids clinical
  overclaiming and includes alert-burden operating points relevant to participant and staff
  load.
- **Provenance / Traceability**: PASS. Planning artifacts carry frontmatter and link to
  SPEC-011 plus dependency specs.

## Project Structure

### Documentation (this feature)

```text
specs/011-honest-model-bakeoff/
|-- spec.md
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- bakeoff-cli-contract.md
|   |-- modeling-artifacts-contract.md
|   `-- cv-metrics-contract.md
`-- tasks.md             # Phase 2 output (/speckit.tasks - NOT created here)
```

### Source Code (repository root)

```text
config/
`-- modeling.yaml

scripts/
`-- run_model_bakeoff.py

src/
|-- modeling/
|   |-- __init__.py
|   |-- datasets.py          # Load CSVs, resolve roles/aliases, build participant rows
|   |-- splits.py            # Repeated grouped stratified CV and leakage checks
|   |-- models.py            # sklearn estimators and fold-local pipelines
|   |-- metrics.py           # AUPRC, recall@precision, AUROC secondary, CIs, ops metrics
|   |-- calibration.py       # Brier, calibration slope/intercept, ECE
|   |-- bakeoff.py           # Orchestration, artifact writing, summary notes
|   `-- explainability.py    # Feature importance and local explanation availability
|-- schemas/
|   `-- lullaby.py           # Existing canonical schema contract
|-- validation/
|   `-- semantics.py         # Existing boolean/value parsing helpers where useful
`-- visualization/
    `-- ...                  # Existing EDA modules remain unchanged unless helpers reused

tests/
|-- test_grouped_cv_no_leakage.py
|-- test_resampling_inside_fold.py
|-- test_bakeoff_outputs.py
|-- test_model_metrics_ci.py
|-- unit/
|-- integration/
`-- contract/

outputs/
`-- modeling/
    |-- predictions_oof.csv
    |-- predictions_by_fold.csv
    |-- metrics_by_fold.csv
    |-- metrics_summary.csv
    |-- operating_points.csv
    |-- calibration_table.csv
    |-- decision_curve.csv
    |-- feature_importance.csv       # if available
    |-- local_explanations.csv       # if available
    |-- bakeoff_config_used.yaml
    `-- bakeoff_summary.json
```

**Structure Decision**: Use the existing single Python package. Add a dedicated
`src/modeling/` package because the behavior is distinct from visualization and simulation,
while keeping all inputs/outputs local and config-driven.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Post-Design Constitution Check

- **P1**: PASS. Research, data model, contracts, and quickstart trace to SPEC-011
  requirements and clarifications.
- **P2**: PASS. Quickstart commands use fixed seeds and local outputs; artifact contracts
  specify deterministic row ordering and saved config.
- **P3**: PASS. Data model keeps role/alias resolution explicit and does not bind the
  pipeline to one institution-specific column naming scheme.
- **P5**: PASS. Contracts require pre-train validation for required roles and note-based
  degradation for optional outputs and non-estimable metrics.
- **P7**: PASS. CV, metric, threshold, CI, and calibration contracts enforce honest
  imbalance-aware evaluation.
- **P8**: PASS. The baseline and target definitions remain tied to documented clinical-study
  logic; no adaptive clinical deployment behavior is introduced.
- **P9**: PASS. Outputs avoid PHI and mark synthetic runs as signal characterization.
- **P10**: PASS. Operating-point outputs make alert burden and staff-call estimates explicit.
