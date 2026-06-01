---
id: QS-005
title: Synthetic Longitudinal Physiologic Data Simulator Quickstart
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-005, PLAN-005]
implements: [P2, P3, P5, P7, P8, P9]
supersedes: null
superseded_by: null
related: [SPEC-001, SPEC-004, SPEC-006, SPEC-007, SPEC-008]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Quickstart: Synthetic Longitudinal Physiologic Data Simulator

## Prerequisites

From the repository root, install the project and development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Implementation of SPEC-005 adds numpy as an explicit project dependency.

## Generate the Default Longitudinal Cohort

```bash
python scripts/generate_synthetic.py \
  --config config/simulation.yaml \
  --out-dir data/synthetic/longitudinal \
  --seed 20260601
```

Expected behavior:

- Writes all required output files under `data/synthetic/longitudinal/`
- Uses 200 participants and 84 study days by default
- Writes `daily_vitals.csv` with 16,800 participant-day rows
- Preserves missing values as empty cells
- Exports temperature and heat-index columns in Celsius
- Writes `simulation_config_used.yaml`
- Writes `simulation_summary.json`
- Returns exit code 0 only when schema validation and required target diagnostics pass

## Validate Generated Tables

```bash
python -m src.cli.validate_visualization_foundation \
  --data-dir data/synthetic/longitudinal
```

Expected behavior:

- Uses the SPEC-004 schema registry
- Reports no required-role failures
- Preserves missingness and extra columns
- Writes `artifacts/validation-report.json`

## Verify Reproducibility

```bash
python scripts/generate_synthetic.py \
  --config config/simulation.yaml \
  --out-dir /tmp/lullaby-sim-a \
  --seed 20260601

python scripts/generate_synthetic.py \
  --config config/simulation.yaml \
  --out-dir /tmp/lullaby-sim-b \
  --seed 20260601
```

CSV contents in the two output directories should match byte-for-byte. Allowed timestamp
metadata appears only in summary/config artifacts and is excluded from CSV content checks.

## Run Focused Simulation Tests

```bash
pytest \
  tests/unit/test_simulation_config.py \
  tests/unit/test_simulation_reproducibility.py \
  tests/unit/test_simulation_targets.py \
  tests/unit/test_simulation_schema_validation.py \
  tests/integration/test_simulation_cli.py
```

## Inspect Diagnostics

```bash
python -m json.tool data/synthetic/longitudinal/simulation_summary.json
```

The summary must include target, observed value, tolerance, denominator, status, warnings, and
errors for every required readiness check.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Exit code 1 with artifacts present | Schema or required diagnostic failed | Inspect `simulation_summary.json` |
| Temperature range violations | Fahrenheit values were exported instead of Celsius | Convert exports to Celsius before writing CSV |
| Daily row count mismatch | Full participant-day grid was not preserved | Rebuild `daily_vitals.csv` from participant x study-day grid |
| Reproducibility test fails | Non-deterministic IDs, row ordering, or RNG stream use | Sort exports and use component-owned RNG streams |
| Missingness diagnostics fail | Missingness collapsed into random gaps only | Recheck archetype, heat, adherence, and worsening-state masks |
