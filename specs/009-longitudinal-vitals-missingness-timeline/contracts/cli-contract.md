---
id: CONTRACT-009-CLI
title: Longitudinal EDA CLI Contract
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-009, SPEC-004, SPEC-007]
implements: [P3, P5, P7]
supersedes: null
superseded_by: null
related: [CONTRACT-007-CLI]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Contract: Longitudinal EDA CLI

## Command

```bash
python -m src.visualization.generate_eda --data-dir data/raw --out-dir outputs/figures/eda --panels longitudinal
```

## Arguments

| Argument | Required | Default | Contract |
|----------|----------|---------|----------|
| `--data-dir` | No | `data/raw` | Directory containing accepted canonical source filenames. If `data/raw` is absent but `data/` exists, the default run may resolve to `data/`. |
| `--out-dir` | No | `outputs/figures/eda` | Directory where panel PNG artifacts are written. |
| `--panels` | No | `core` | Must accept `core` and `longitudinal`; SPEC-009 acceptance uses `longitudinal`. |
| `--manifest` | No | `outputs/figures/manifest.json` | Manifest updated for repo-relative generated artifacts. |
| `--participant-id` | No | automatic selection | Participant id used for participant-focused Panel 5 and Panel 7 rendering. |
| `--week-start` | No | full observed range | Inclusive 1-based starting study week. Study days 1-7 are week 1. |
| `--week-end` | No | full observed range | Inclusive 1-based ending study week. Must be greater than or equal to `--week-start` when both are supplied. |
| `--overlay-environment` | No | `false` | Accepts `true` or `false`; when true, overlays environment only if optional environment data and roles are available. |

## Success Behavior

- Exit code is `0`.
- Standard output includes `Generated 5 EDA longitudinal dashboard artifacts`.
- Five PNG files are written under `--out-dir`.
- Repo-relative outputs are registered in the manifest.
- Optional missingness, unavailable environment data, unavailable participant context, and
  unavailable diagnostic stratifiers are warnings, not command failures.
- If no participant id is supplied, automatic participant selection is deterministic and is
  recorded in manifest metadata.

## Failure Behavior

- Exit code is non-zero for missing required input tables, missing required semantic roles,
  invalid `--overlay-environment` values, invalid week ranges, invalid required boolean-like
  tokens, or unknown supplied participant ids.
- Error text identifies the entity, source path, role, argument, or participant id where
  possible.
- The command fails before writing affected PNG artifacts or manifest entries.
- Optional roles do not fail the command unless they are required by the requested panel
  contract.

## Participant-Specific Run

```bash
python -m src.visualization.generate_eda \
  --data-dir data/raw \
  --out-dir outputs/figures/eda \
  --panels longitudinal \
  --participant-id PARTICIPANT_ID \
  --overlay-environment true
```

Panel 5 and Panel 7 use `PARTICIPANT_ID`. Other longitudinal panels continue to compute
cohort-level summaries unless the implementation explicitly annotates the selected
participant as context.
