---
id: CONTRACT-011-CLI
title: Modeling Bake-off CLI Contract
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-011]
implements: [P7, P8]
supersedes: null
superseded_by: null
related: []
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Contract: Modeling Bake-off CLI

## Required Commands

```bash
python scripts/run_model_bakeoff.py --config config/modeling.yaml --data-dir data/raw --out-dir outputs/modeling --seed 20260601
```

```bash
python scripts/run_model_bakeoff.py --config config/modeling.yaml --data-dir data/synthetic/longitudinal --out-dir outputs/modeling_synthetic --seed 20260601
```

## Arguments

| Argument | Required | Default | Contract |
|----------|----------|---------|----------|
| `--config` | Yes | None | YAML configuration file. Default acceptance path uses `config/modeling.yaml`. |
| `--data-dir` | Yes | None | Directory containing canonical or accepted synthetic CSV tables. |
| `--out-dir` | Yes | None | Directory where bake-off artifacts are written. Created if absent. |
| `--seed` | No | Config seed | Overrides or confirms the run seed used for CV, models, threshold tuning, and bootstrap. |

## Success Behavior

- Exit code is `0`.
- Standard output includes the output directory and number of trained model candidates.
- Required non-optional artifacts are written under `--out-dir`.
- `bakeoff_config_used.yaml` contains the effective config after CLI seed override.
- `bakeoff_summary.json` records seed, data directory, output directory, participant/event
  counts, enabled models, limitations, warnings, and artifact paths.
- Synthetic inputs are labeled as synthetic signal characterization in summary limitations.

## Failure Behavior

- Exit code is non-zero for missing required config, invalid YAML, missing required input
  tables, missing required semantic roles, one-class targets, invalid CV settings, unsupported
  model configuration, or inability to write requested outputs.
- Error text identifies the failing config key, input role, table path, model id, or output
  path where possible.
- The command fails before model training when required dataset validation fails.
- The command does not use outer validation labels for threshold selection under any failure
  or fallback path.
