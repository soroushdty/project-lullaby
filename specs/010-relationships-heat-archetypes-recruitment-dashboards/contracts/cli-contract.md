---
id: CONTRACT-010-CLI
title: Relationships EDA CLI Contract
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-010, SPEC-004, SPEC-007, SPEC-009]
implements: [P3, P5, P7]
supersedes: null
superseded_by: null
related: [CONTRACT-007-CLI, CONTRACT-009-CLI]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Contract: Relationships EDA CLI

## SPEC-010 Command

```bash
python -m src.visualization.generate_eda --data-dir data/raw --out-dir outputs/figures/eda --panels relationships
```

## All-Panels Command

```bash
python -m src.visualization.generate_eda --data-dir data/raw --out-dir outputs/figures/eda --panels all
```

## Arguments

| Argument | Required | Default | Contract |
|----------|----------|---------|----------|
| `--data-dir` | No | `data/raw` | Directory containing accepted canonical source filenames. If `data/raw` is absent but `data/` exists, the default run may resolve to `data/`. |
| `--out-dir` | No | `outputs/figures/eda` | Directory where panel PNG artifacts are written. |
| `--panels` | No | `core` | Must accept `core`, `longitudinal`, `relationships`, and `all`; SPEC-010 acceptance uses `relationships` and smoke-checks `all`. |
| `--manifest` | No | `outputs/figures/manifest.json` | Manifest updated for repo-relative generated artifacts. |
| `--participant-id` | No | Existing longitudinal default | Used only by longitudinal panels when `--panels longitudinal` or `--panels all`. |
| `--week-start` | No | Existing longitudinal default | Used only by longitudinal panels when `--panels longitudinal` or `--panels all`. |
| `--week-end` | No | Existing longitudinal default | Used only by longitudinal panels when `--panels longitudinal` or `--panels all`. |
| `--overlay-environment` | No | `false` | Used only by longitudinal panels when `--panels longitudinal` or `--panels all`. |

## Success Behavior

- Exit code is `0`.
- `--panels relationships` standard output includes `Generated 4 EDA relationships dashboard artifacts`.
- `--panels relationships` writes four PNG files under `--out-dir`.
- `--panels all` writes all available EDA panel artifacts 1 through 13 through the existing
  panel-set generators.
- Repo-relative outputs are registered in the manifest.
- Optional missing environment, recruitment, alerts, clinical outcomes, or archetype labels
  produce warnings or unavailable panels, not command failures.

## Failure Behavior

- Exit code is non-zero for missing required input tables, missing required semantic roles,
  invalid required boolean-like tokens, or inherited longitudinal argument errors during
  `--panels all`.
- Error text identifies the entity, source path, role, argument, or participant id where
  possible.
- The command fails before writing requested PNG artifacts or manifest entries.
- Optional roles do not fail the command unless they are required by the requested panel
  contract.
