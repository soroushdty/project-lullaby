---
id: QUICKSTART-011
title: Honest Model Bake-off Under Severe Class Imbalance Quickstart
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

# Quickstart: Honest Model Bake-off Under Severe Class Imbalance

## 1. Install Local Dependencies

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
```

SPEC-011 implementation adds scikit-learn to project dependencies. After implementation,
the install command above should provide the modeling estimators and metrics used by the
bake-off.

## 2. Run The Synthetic Bake-off

```bash
.venv/bin/python scripts/run_model_bakeoff.py \
  --config config/modeling.yaml \
  --data-dir data/synthetic/longitudinal \
  --out-dir outputs/modeling_synthetic \
  --seed 20260601
```

Expected result:

```text
Wrote modeling bake-off artifacts to outputs/modeling_synthetic
Trained 4 model candidates
```

Observed implementation validation on 2026-06-01 with seed `20260601` completed in
`0:03.67` and wrote the artifact set below.

The run writes the required non-optional artifacts:

```text
outputs/modeling_synthetic/predictions_oof.csv
outputs/modeling_synthetic/predictions_by_fold.csv
outputs/modeling_synthetic/metrics_by_fold.csv
outputs/modeling_synthetic/metrics_summary.csv
outputs/modeling_synthetic/operating_points.csv
outputs/modeling_synthetic/calibration_table.csv
outputs/modeling_synthetic/decision_curve.csv
outputs/modeling_synthetic/bakeoff_config_used.yaml
outputs/modeling_synthetic/bakeoff_summary.json
```

Optional artifacts are written only when supported:

```text
outputs/modeling_synthetic/feature_importance.csv
outputs/modeling_synthetic/local_explanations.csv
```

## 3. Run The Default Raw-Data Command

```bash
.venv/bin/python scripts/run_model_bakeoff.py \
  --config config/modeling.yaml \
  --data-dir data/raw \
  --out-dir outputs/modeling \
  --seed 20260601
```

Expected result: if `data/raw` contains conforming canonical tables, the command writes the
same artifact set under `outputs/modeling`. If required roles are missing, the command exits
non-zero with an actionable validation error before training.

## 4. Inspect Headline Metrics

```bash
.venv/bin/python -c "import csv; rows=list(csv.DictReader(open('outputs/modeling_synthetic/metrics_summary.csv'))); print([r for r in rows if r['primary_metric'].lower() == 'true'][:6])"
```

Expected result: primary rows include AUPRC, recall at fixed precision, and Brier score for
each trained model. AUROC may appear only as a secondary metric. Accuracy is not a headline
metric.

## 5. Inspect Synthetic-Data Framing

```bash
.venv/bin/python -c "import json; print(json.load(open('outputs/modeling_synthetic/bakeoff_summary.json'))['limitations'])"
```

Expected result: limitations state that synthetic runs are exploratory signal
characterization and are not validated clinical performance.

## 6. Verify Focused Tests

```bash
.venv/bin/pytest \
  tests/test_grouped_cv_no_leakage.py \
  tests/test_resampling_inside_fold.py \
  tests/test_bakeoff_outputs.py \
  tests/test_model_metrics_ci.py
```

Expected result: all focused SPEC-011 tests pass.

Observed implementation validation on 2026-06-01: `18 passed in 14.57s`,
elapsed `0:15.60`.

## 7. Required Leakage Smoke Test

```bash
.venv/bin/pytest tests/test_grouped_cv_no_leakage.py
```

Expected result: every repeat/fold split has disjoint train and validation participant ids.

## 8. Existing Regression Validation

```bash
.venv/bin/pytest \
  tests/unit/test_lullaby_schema.py \
  tests/test_eda_core_outputs.py \
  tests/test_eda_longitudinal_outputs.py \
  tests/test_eda_relationships_outputs.py
```

Observed implementation validation on 2026-06-01: `35 passed, 20 warnings in
29.31s`. Warnings were limited to existing pandera/date-parse warnings and
outside-repo manifest registration warnings from EDA tests.

## 9. Full Local Validation

```bash
.venv/bin/pytest
```

Expected result: the full test suite passes without network access. Existing EDA, schema,
simulation, and ingestion tests remain compatible with the new modeling package.

Observed implementation validation on 2026-06-01 with local socket permissions for
adapter tests: `253 passed, 4 skipped, 23 warnings in 94.75s`.
