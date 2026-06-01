---
id: CONTRACT-005-CLI
title: Synthetic Simulator CLI Contract
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-005, PLAN-005]
implements: [P2, P5, P8, P9]
supersedes: null
superseded_by: null
related: [SPEC-001, SPEC-004A]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Contract: Synthetic Simulator CLI

## Command

```bash
python scripts/generate_synthetic.py \
  --config config/simulation.yaml \
  --out-dir data/synthetic/longitudinal \
  --seed 20260601
```

## Arguments

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--config` | No | `config/simulation.yaml` | YAML simulation configuration |
| `--out-dir` | No | `data/synthetic/longitudinal` | Output package directory |
| `--seed` | No | value from config | Root seed override |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Generation, schema validation, and required diagnostics passed |
| 1 | Artifacts were exported but schema validation or required diagnostics failed |
| 2 | Usage error, unreadable config, invalid config, or output path error |

## Required Behavior

- Print a concise human-readable summary with output path, seed, readiness status, warnings, and
  failures.
- Write all required output artifacts even when schema or target diagnostics fail after generation.
- On failure, mark `simulation_summary.json` with `status="fail"` and
  `ready_for_downstream=false`.
- Preserve missing values in raw CSV outputs.
- Never fetch external data or call network services.
- Default output path is repository-relative unless a caller explicitly supplies another local
  path.

## Acceptance Tests

- Same config and seed produce byte-identical CSV files across two runs.
- Invalid config returns exit code 2 and writes no ready summary.
- Schema validation failure returns exit code 1 and leaves artifacts inspectable.
- Required target diagnostic failure returns exit code 1 and leaves artifacts inspectable.
