---
id: QUICKSTART-006
title: Data Semantics and Validation Hardening Quickstart
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

# Quickstart: Data Semantics and Validation Hardening

## 1. Install Local Dependencies

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
```

## 2. Run Focused Hardening Tests

```bash
.venv/bin/pytest \
  tests/unit/test_boolean_semantics.py \
  tests/unit/test_stream_adapter_unit.py \
  tests/unit/test_simulation_targets.py \
  tests/test_eda_missingness_policy.py \
  tests/test_eda_core_outputs.py \
  tests/unit/test_artifact_manifest.py
```

Expected result: all focused tests pass, including CSV/string boolean cases, missing outcome
counts, required-input failures before artifact writes, optional-role warnings, and manifest
registration for repo-relative alternate outputs.

## 3. Regenerate Dashboard Acceptance Artifacts

```bash
.venv/bin/python -m src.visualization.generate_eda \
  --data-dir data/raw \
  --out-dir outputs/figures/eda \
  --panels core
```

Expected artifacts:

```text
outputs/figures/eda/01_cohort_overview.png
outputs/figures/eda/02_outcome_prevalence.png
outputs/figures/eda/03_distribution_outliers.png
outputs/figures/eda/04_alert_engagement_funnel.png
outputs/figures/manifest.json
```

## 4. Optional Synthetic Dashboard Run

```bash
.venv/bin/python -m src.visualization.generate_eda \
  --data-dir data/synthetic/longitudinal \
  --out-dir outputs/figures/eda_synthetic \
  --panels core
```

Expected result: repo-relative synthetic dashboard artifacts are registered in the default
manifest. If an output directory outside the repository is selected, the command warns that
outside-repo artifacts are not registered.

## 5. Run Full Validation Suite

```bash
.venv/bin/pytest
```

Expected result: the full local test suite passes without network access. Tests that require
socket fixtures may need the same local permissions already used by the existing suite.
