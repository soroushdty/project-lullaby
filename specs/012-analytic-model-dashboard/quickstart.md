---
id:            QUICKSTART-012
title:         Analytic Dashboard for Model Outputs — Quickstart
status:        complete
version:       0.1.0
created:       2026-06-01
author:        Soroush Dianaty
related:       [PLAN-012, SPEC-012]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Quickstart: Analytic Dashboard for Model Outputs

## Prerequisites

1. SPEC-011 bake-off has been run and `outputs/modeling/` (or `outputs/modeling_synthetic/`) contains the required artifact CSVs.
2. Python 3.11+ environment with project dependencies installed:
   ```bash
   pip install -e .
   ```
3. `config/costs.yaml` exists (shipped with the repo).

## Run on synthetic bake-off output

```bash
python -m src.visualization.analytic_dashboard \
  --model-dir outputs/modeling_synthetic \
  --data-dir data/synthetic/longitudinal \
  --out-dir outputs/figures/analytic \
  --cost-config config/costs.yaml
```

Expected output under `outputs/figures/analytic/`:
```
01_model_leaderboard.png
02_calibration_decision_curve.png
03_threshold_explorer.png
04_alarm_cost.png
05_explainability.png
06_cv_vs_heat_discrimination.png
07_lead_time_analysis.png
08_grouped_cv_variance.png
09_subgroup_fairness_audit.png
10_label_efficiency_learning_curve.png   ← unavailable if learning_curve.csv absent
11_novelty_anomaly_view.png
model_card_tripod_ai.md
```

Artifacts registered in `outputs/figures/manifest.json` under `"type": "analytic"`.

## Run on raw bake-off output

```bash
python -m src.visualization.analytic_dashboard \
  --model-dir outputs/modeling \
  --data-dir data/raw \
  --out-dir outputs/figures/analytic \
  --cost-config config/costs.yaml
```

## Run tests

```bash
PYTHONPATH=. pytest tests/test_analytic_dashboard_outputs.py \
                   tests/test_cost_config_used.py \
                   tests/test_model_card_generation.py
```

## Update cost assumptions

Edit `config/costs.yaml` only. No plotting code changes required. Re-run the dashboard CLI to regenerate Panel 4 with updated assumptions.

## Check a specific panel

Each panel function is independently callable from Python:

```python
from src.visualization.analytic_dashboard import render_panel_1
render_panel_1(
    model_dir="outputs/modeling_synthetic",
    out_dir="outputs/figures/analytic",
    manifest_path="outputs/figures/manifest.json",
)
```

## Manifest inspection

```python
import json
manifest = json.loads(open("outputs/figures/manifest.json").read())
analytic = [e for e in manifest["artifacts"] if e["type"] == "analytic"]
unavailable = [e for e in analytic if not e["available"]]
print(f"{len(analytic)} analytic artifacts, {len(unavailable)} unavailable")
for e in unavailable:
    print(f"  {e['path']}: {e['warning']}")
```
