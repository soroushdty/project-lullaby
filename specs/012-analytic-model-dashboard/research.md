---
id:            RESEARCH-012
title:         Analytic Dashboard for Model Outputs — Phase 0 Research
status:        complete
version:       0.1.0
created:       2026-06-01
updated:       2026-06-01
author:        Soroush Dianaty
related:       [PLAN-012, SPEC-012]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Research: Analytic Dashboard for Model Outputs

## 1. Existing Visualization Infrastructure

**Decision**: Reuse `src/visualization/design.py`, `artifacts.py`, and `schema_registry.py` without modification.

**Rationale**: Every EDA module (`eda_core.py`, `eda_longitudinal.py`, `eda_archetypes.py`, `eda_environment.py`, `eda_relationships.py`) already calls `design.apply_lullaby_style()` for figure aesthetics, `artifacts.register_artifact()` for manifest writes, and `schema_registry.label()` for axis labeling. SPEC-012 will follow the same call pattern, ensuring visual and manifest consistency with zero duplication.

**Alternatives considered**: Creating a separate `analytic/` sub-package. Rejected because the existing flat module layout is sufficient for the feature size and adding a sub-package would add import-path complexity without benefit.

---

## 2. Manifest Strategy

**Decision**: Shared `outputs/figures/manifest.json` with `"type": "analytic"` on every SPEC-012 entry. EDA entries use `"type": "eda"`. Resolved in `/speckit.clarify` Q1.

**Rationale**: `artifacts.py` already handles manifest read/write. A single registry enables downstream SPEC-008-style pipeline QA to audit all artifact types in one file. The `"type"` field distinguishes EDA from analytic without requiring a second manifest discovery mechanism.

**Alternatives considered**: Separate `outputs/figures/analytic/manifest.json`. Rejected because it would require pipeline QA tools to discover and merge multiple manifests. Aggregating manifest (`outputs/artifact_manifest.json`) deferred to SPEC-008.

---

## 3. Panel Rendering Pattern

**Decision**: Each panel is implemented as a standalone function `render_panel_N(model_dir, data_dir, out_dir, cost_config)` in `analytic_dashboard.py`. The CLI iterates panels, catches per-panel exceptions, and writes an unavailable PNG when a panel fails due to a missing optional input. Panel 4 writes an unavailable PNG (not an exception) when `costs.yaml` is absent; CLI exits 0.

**Rationale**: The per-panel function pattern matches how EDA modules handle missing optional roles (e.g., `eda_environment.py` renders an explicit unavailable panel for absent `environment` table). The SPEC-012 clarifications (Q4) confirmed Panel 4 failure must be isolated — same isolation applies to all optional-input panels by the same principle.

**Alternatives considered**: One monolithic render function with conditionals. Rejected because it makes unavailable-panel paths harder to test in isolation and conflicts with the acceptance-scenario structure which tests each panel's available vs. unavailable path independently.

---

## 4. Calibration Sparsity Threshold

**Decision**: Warn (render sparse-data warning panel) when `< 3` non-empty calibration bins exist **OR** any non-empty bin has `< 10` samples. Resolved in `/speckit.clarify` Q2.

**Rationale**: Three bins is the minimum needed for a visually meaningful calibration belt shape. Ten samples per bin is the minimum for stable fraction estimates (mirrors Hosmer–Lemeshow 10-group practice). The threshold is deterministic and directly testable: a fixture with 2 bins or a bin of 9 triggers the warning; 3 bins of 10 each renders the belt.

**Implementation note**: Bin detection reads `calibration_table.csv` columns `bin_lower`, `bin_upper`, `n_observations`, `observed_fraction`, `mean_predicted`. If columns are absent, the panel renders unavailable (missing-input state, not sparse-data state).

---

## 5. Lead-Time Event Threshold

**Decision**: Aggregate (median + IQR band) when `≥ 5` confirmed events exist; individual trajectories + sparse-data warning when `< 5`. Resolved in `/speckit.clarify` Q3.

**Rationale**: Five is the minimum for a non-degenerate median and for bootstrap or IQR uncertainty to be meaningful. Below five, showing individual trajectories preserves honesty (P7) while still surfacing available signal. The threshold is an integer comparison against the count of unique `event_participant_id` values with `days_before_event` rows in `predictions_oof.csv` (or a derived lead-time file).

---

## 6. Learning-Curve File Path

**Decision**: Panel 10 probes for `{model_dir}/learning_curve.csv`. Absent → explicit unavailable panel. Resolved in `/speckit.clarify` Q5.

**Rationale**: Flat naming alongside `metrics_summary.csv`, `predictions_oof.csv`, etc. is consistent with SPEC-011 output conventions. Panel 10's unavailable message will state: "learning_curve.csv is an optional SPEC-011 output; re-run the bake-off with learning-curve generation enabled to populate this panel."

**Expected columns** (if file exists): `model_id`, `training_n`, `n_events`, `auprc_mean`, `auprc_ci_lower`, `auprc_ci_upper`, `recall_at_precision_mean`, `recall_at_precision_ci_lower`, `recall_at_precision_ci_upper`.

---

## 7. TRIPOD-AI Model Card Generation

**Decision**: Implement in `src/visualization/model_cards.py` as `generate_tripod_ai_card(model_dir, data_dir, cost_config_path, out_path)`. The function reads `bakeoff_summary.json` for run metadata, `bakeoff_config_used.yaml` for exact config paths, and the SPEC-011 CSVs for metric summaries. It renders a Markdown file.

**Rationale**: Separating card generation into its own module (`model_cards.py`) mirrors the EDA pattern of one module per visualization concern and enables independent unit testing of card content without rendering panels.

**Synthetic-data caveat trigger**: If `bakeoff_summary.json` contains `"data_source": "synthetic"` or the `--model-dir` path contains `synthetic`, the card includes the mandatory synthetic-data caveat section.

---

## 8. Cost Config Loading

**Decision**: Load `config/costs.yaml` with `PyYAML` at Panel 4 render time. If absent, write an unavailable PNG and register it with `"warning": "costs.yaml not found"` in the manifest. No hardcoded fallback values anywhere.

**Rationale**: PyYAML is already a declared dependency. Loading at render time (not at CLI startup) ensures that a missing config file only fails Panel 4, not the whole run (Q4 clarification). The `config/costs.yaml` default values from the spec's Configuration Contract section are the canonical source; the file ships with the repo so the absent case is a user misconfiguration, not a normal runtime path.

---

## 9. matplotlib Backend

**Decision**: Use `matplotlib.use("Agg")` (non-interactive backend) at module import time in `analytic_dashboard.py`.

**Rationale**: Agg is headless and deterministic across platforms. All EDA modules already use it. Consistent with P2 (Reproducibility by Default).

---

## 10. No New Dependencies

**Decision**: All SPEC-012 functionality is achievable with already-declared dependencies. No additions to `pyproject.toml`.

**Rationale**: `matplotlib`, `pandas`, `PyYAML`, `scikit-learn` cover panels, data loading, cost config, and any calibration math. Adding optional SHAP or other explanation libraries is explicitly out of scope — Panel 5 labels the method actually available and renders unavailable if no explanation file exists.
