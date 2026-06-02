---
id:            CONTRACT-012-CLI
title:         Analytic Dashboard CLI Contract
status:        complete
version:       0.1.0
created:       2026-06-01
author:        Soroush Dianaty
related:       [PLAN-012, SPEC-012]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Contract: Analytic Dashboard CLI

## Invocation

```bash
python -m src.visualization.analytic_dashboard \
  --model-dir outputs/modeling \
  --data-dir data/raw \
  --out-dir outputs/figures/analytic \
  --cost-config config/costs.yaml
```

```bash
# Synthetic run
python -m src.visualization.analytic_dashboard \
  --model-dir outputs/modeling_synthetic \
  --data-dir data/synthetic/longitudinal \
  --out-dir outputs/figures/analytic \
  --cost-config config/costs.yaml
```

## Arguments

| Argument | Required | Default | Notes |
|----------|----------|---------|-------|
| `--model-dir` | Yes | — | Directory containing SPEC-011 output CSVs |
| `--data-dir` | Yes | — | Directory containing source data tables for Panels 6–9, 11 |
| `--out-dir` | Yes | — | Output directory for PNGs and model card |
| `--cost-config` | Yes | — | Path to `costs.yaml`; Panel 4 renders unavailable if absent |

## Exit behavior

| Condition | Exit code |
|-----------|-----------|
| All panels rendered (available or unavailable) | 0 |
| Missing `--model-dir` or `--out-dir` (required arg) | non-zero |
| Missing `--cost-config` | 0 (Panel 4 → unavailable panel) |
| Unexpected exception in one panel | 0 (panel → unavailable; exception logged) |
| Unexpected exception before any panel renders | non-zero |

## Invariants

- The CLI MUST NOT train or score any model.
- Every panel function MUST be called; no panel is silently skipped.
- Every panel result (available or unavailable) MUST be registered in `outputs/figures/manifest.json`.
- Manifest entries for SPEC-012 artifacts MUST carry `"type": "analytic"`.
- AUPRC MUST be the sort key for Panel 1; `primary_metric == True` rows from `metrics_summary.csv` determine headline columns.
- Panel 4 MUST NOT read any finance value that is not present in `--cost-config`.
- When `bakeoff_summary.json` contains `"data_source": "synthetic"` or `--model-dir` path contains the substring `synthetic`, every panel title and the model card MUST include the synthetic-data framing note.
