---
id: QUICKSTART-007
title: Core Descriptive EDA Dashboards Quickstart
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

# Quickstart: Core Descriptive EDA Dashboards

## 1. Install Local Dependencies

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
```

## 2. Generate Default Core EDA Dashboards

```bash
.venv/bin/python -m src.visualization.generate_eda \
  --data-dir data/raw \
  --out-dir outputs/figures/eda \
  --panels core
```

Expected result:

```text
Generated 4 EDA core dashboard artifacts
outputs/figures/eda/01_cohort_overview.png
outputs/figures/eda/02_outcome_prevalence.png
outputs/figures/eda/03_distribution_outliers.png
outputs/figures/eda/04_alert_engagement_funnel.png
```

The command also updates `outputs/figures/manifest.json` for repo-relative outputs.

## 3. Verify Required Artifacts

```bash
.venv/bin/pytest tests/test_eda_core_outputs.py tests/test_eda_missingness_policy.py
```

Expected result: focused EDA tests pass, including image size checks, manifest entries,
required-input failures, missing optional-role warnings, rare-outcome counts, schema-driven
capture-worthy labeling, and engagement funnel missingness behavior.

## 4. Optional Synthetic Longitudinal Run

```bash
.venv/bin/python -m src.visualization.generate_eda \
  --data-dir data/synthetic/longitudinal \
  --out-dir outputs/figures/eda_synthetic \
  --panels core
```

Expected result: the same four core dashboard filenames are written under the synthetic output
directory. If the output directory is repo-relative, entries are registered in the default
manifest with artifact ids that avoid colliding with the default EDA outputs.

## 5. Required Failure Smoke Test

```bash
tmpdir="$(mktemp -d)"
.venv/bin/python -m src.visualization.generate_eda \
  --data-dir "$tmpdir" \
  --out-dir outputs/figures/eda \
  --panels core
```

Expected result: the command exits non-zero with an actionable required-input validation
message and does not write affected PNG artifacts or manifest entries.

## 6. Full Local Validation

```bash
.venv/bin/pytest
```

Expected result: the full test suite passes without network access. Any socket-bound tests use
the same local permissions already required by the existing suite.
