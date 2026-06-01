---
id: CONTRACT-007-CLI
title: Core Descriptive EDA CLI Contract
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-007, SPEC-004, SPEC-006]
implements: [P3, P5, P7]
supersedes: null
superseded_by: null
related: [CONTRACT-004-VALIDATION-COMMAND]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Contract: Core Descriptive EDA CLI

## Command

```bash
python -m src.visualization.generate_eda --data-dir data/raw --out-dir outputs/figures/eda --panels core
```

## Arguments

| Argument | Required | Default | Contract |
|----------|----------|---------|----------|
| `--data-dir` | No | `data/raw` | Directory containing accepted canonical source filenames. If `data/raw` is absent but `data/` exists, the default run may resolve to `data/`. |
| `--out-dir` | No | `outputs/figures/eda` | Directory where panel PNG artifacts are written. |
| `--panels` | No | `core` | Only `core` is supported for SPEC-007. |
| `--manifest` | No | `outputs/figures/manifest.json` | Manifest updated for repo-relative generated artifacts. |

## Success Behavior

- Exit code is `0`.
- Standard output includes `Generated 4 EDA core dashboard artifacts`.
- Four PNG files are written under `--out-dir`.
- Repo-relative outputs are registered in the manifest.
- Optional missingness and unavailable sections are warnings, not command failures.

## Failure Behavior

- Exit code is non-zero for missing required input tables, missing required semantic roles, or
  invalid required boolean-like tokens.
- Error text identifies the entity, source path, and role where possible.
- The command fails before writing affected PNG artifacts or manifest entries.
- Optional roles do not fail the command unless they are promoted to required by the requested
  panel contract.

## Synthetic Run

```bash
python -m src.visualization.generate_eda \
  --data-dir data/synthetic/longitudinal \
  --out-dir outputs/figures/eda_synthetic \
  --panels core
```

The synthetic run follows the same panel, validation, and manifest rules as the default run.
