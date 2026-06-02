---
id:            TASKS-012
title:         Analytic Dashboard for Model Outputs — Task List
status:        draft
version:       0.1.0
created:       2026-06-01
updated:       2026-06-01
author:        Soroush Dianaty
depends_on:    [PLAN-012, SPEC-012]
implements:    [P7, P8, P9, P10]
supersedes:    null
superseded_by: null
related:       [SPEC-011, SPEC-007, SPEC-004]
description:   "Dependency-ordered task list for implementing the SPEC-012 analytic dashboard"
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Tasks: Analytic Dashboard for Model Outputs

**Input**: Design documents from `/specs/012-analytic-model-dashboard/`

**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. Tests are included because FR-004–006 explicitly require three test files.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to

---

## Phase 1: Setup

**Purpose**: Create all new files with correct module stubs so imports work before implementation begins.

- [ ] T001 Create `src/visualization/analytic_dashboard.py` with module docstring, `matplotlib.use("Agg")`, and placeholder stubs for `render_panel_1` through `render_panel_11` and CLI `main()`
- [ ] T002 [P] Create `src/visualization/model_cards.py` with module docstring and placeholder stub for `generate_tripod_ai_card()`
- [ ] T003 [P] Create `config/costs.yaml` with the default values specified in the SPEC-012 Cost Configuration Contract
- [ ] T004 [P] Create `tests/test_analytic_dashboard_outputs.py` with empty test module
- [ ] T005 [P] Create `tests/test_cost_config_used.py` with empty test module
- [ ] T006 [P] Create `tests/test_model_card_generation.py` with empty test module

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared helpers that every panel function depends on. Must be complete before any user story panel is implemented.

**⚠️ CRITICAL**: No panel implementation should begin until this phase is complete.

- [ ] T007 Implement `render_unavailable_panel(title, message, out_path, width=1920, height=1080)` → saves a labeled PNG with the unavailable message and returns `(width, height)` in `src/visualization/analytic_dashboard.py`
- [ ] T008 [P] Implement `register_analytic_artifact(path, panel, available, warning, manifest_path)` in `src/visualization/analytic_dashboard.py` — calls `artifacts.register_artifact()` from `src/visualization/artifacts.py` with `artifact_type="analytic"` and the `panel`, `available`, `warning` fields from `contracts/manifest-entry-analytic.md`
- [ ] T009 [P] Implement `detect_synthetic_run(model_dir)` → bool in `src/visualization/analytic_dashboard.py` — reads `{model_dir}/bakeoff_summary.json`; returns `True` if `data_source == "synthetic"` or if `model_dir` path contains the substring `synthetic`
- [ ] T010 Implement CLI `main()` in `src/visualization/analytic_dashboard.py` with `argparse` arguments `--model-dir`, `--data-dir`, `--out-dir`, `--cost-config`; calls `render_panel_1` through `render_panel_11` and `generate_tripod_ai_card` in a loop; catches per-panel exceptions and writes unavailable panels; always exits 0 unless a required arg is missing

**Checkpoint**: Shared helpers exist, CLI wiring compiles, and `python -m src.visualization.analytic_dashboard --help` succeeds.

---

## Phase 3: User Story 1 — Full Analytic Report (Priority: P1) 🎯 MVP

**Goal**: Running the CLI on SPEC-011 fixture outputs writes all 11 PNGs and the model card (available or unavailable), registers them all in `manifest.json`, and the run is deterministic.

**Independent Test**: `pytest tests/test_analytic_dashboard_outputs.py::test_full_run_creates_all_artifacts tests/test_analytic_dashboard_outputs.py::test_run_is_deterministic`

- [ ] T011 [US1] Write `test_full_run_creates_all_artifacts` in `tests/test_analytic_dashboard_outputs.py` — runs CLI on SPEC-011 synthetic fixture directory; asserts all 11 PNG paths and `model_card_tripod_ai.md` exist under `out_dir`; asserts each PNG entry in manifest has `"type": "analytic"`
- [ ] T012 [P] [US1] Write `test_run_is_deterministic` in `tests/test_analytic_dashboard_outputs.py` — runs CLI twice with identical inputs; asserts byte-identical PNGs for all available panels
- [ ] T013 [P] [US1] Write `test_missing_optional_input_renders_unavailable` in `tests/test_analytic_dashboard_outputs.py` — removes one optional SPEC-011 file from fixture directory; asserts the affected panel PNG exists with `available == false` in manifest and remaining panels are unaffected
- [ ] T014 [P] [US1] Implement `render_panel_10(model_dir, out_dir, manifest_path)` in `src/visualization/analytic_dashboard.py` — probes for `{model_dir}/learning_curve.csv`; if present renders performance-vs-training-N for each model_id; if absent calls `render_unavailable_panel` with message explaining the optional SPEC-011 output
- [ ] T015 [US1] Implement `generate_tripod_ai_card(model_dir, data_dir, cost_config_path, out_path)` stub dispatch in `src/visualization/model_cards.py` that writes a skeleton model card with all 14 required TRIPOD-AI section headings from SPEC-012 FR-046 (full content implemented in Phase 12)

**Checkpoint**: CLI runs end-to-end without crash; all 12 artifact files are written (11 PNGs + model card); manifest has 12 analytic entries.

---

## Phase 4: User Story 2 — Model Leaderboard (Priority: P1)

**Goal**: Panel 1 renders with AUPRC as the primary sort key and headline column; AUROC and accuracy are not headline metrics; CI bounds are shown.

**Independent Test**: `pytest tests/test_analytic_dashboard_outputs.py::test_panel_1_auprc_is_primary tests/test_analytic_dashboard_outputs.py::test_panel_1_auroc_not_headline`

- [ ] T016 [US2] Implement `render_panel_1(model_dir, out_dir, manifest_path)` in `src/visualization/analytic_dashboard.py` — reads `{model_dir}/metrics_summary.csv`; filters `primary_metric == True` rows for headline columns (AUPRC, recall_at_precision, brier); sorts models descending by AUPRC mean; renders a horizontal bar or table figure with CI bounds; uses `schema_registry.label()` for axis labels; calls `register_analytic_artifact`
- [ ] T017 [P] [US2] Write `test_panel_1_auprc_is_primary` in `tests/test_analytic_dashboard_outputs.py` — provides fixture `metrics_summary.csv` with AUPRC, AUROC, brier rows; calls `render_panel_1`; asserts PNG exists and is ≥ 1600×900px; asserts `primary_metric` flag is respected (no AUROC row in headline position in manifest metadata)
- [ ] T018 [P] [US2] Write `test_panel_1_auroc_not_headline` in `tests/test_analytic_dashboard_outputs.py` — asserts that when `primary_metric == False` for AUROC rows, those rows do not appear as headline columns in the rendered figure metadata

**Checkpoint**: Panel 1 renders correctly with a fixture `metrics_summary.csv`; tests pass.

---

## Phase 5: User Story 3 — Calibration and Decision Curve (Priority: P1)

**Goal**: Panel 2 renders calibration belt when bins are sufficient (≥ 3 non-empty bins, each with ≥ 10 samples), and renders a sparse-data warning panel otherwise.

**Independent Test**: `pytest tests/test_analytic_dashboard_outputs.py::test_panel_2_sparse_warning`

- [ ] T019 [US3] Implement `render_panel_2(model_dir, out_dir, manifest_path)` in `src/visualization/analytic_dashboard.py` — reads `{model_dir}/calibration_table.csv` and `{model_dir}/decision_curve.csv`; applies sparsity gate (< 3 non-empty bins OR any non-empty bin with < 10 samples → `render_unavailable_panel` with sparse-data message); otherwise renders calibration plot + Brier score + decision curve with treat-all and treat-none baselines; calls `register_analytic_artifact`
- [ ] T020 [P] [US3] Write `test_panel_2_sparse_warning` in `tests/test_analytic_dashboard_outputs.py` — provides fixture `calibration_table.csv` with 2 non-empty bins; calls `render_panel_2`; asserts PNG is the sparse-data warning panel and manifest entry has `available == false`
- [ ] T021 [P] [US3] Write `test_panel_2_renders_belt_when_sufficient` in `tests/test_analytic_dashboard_outputs.py` — provides fixture with 3 non-empty bins each having ≥ 10 samples; asserts `available == true` in manifest and PNG is ≥ 1600×900px

**Checkpoint**: Panel 2 correctly switches between belt and sparse-data warning based on the calibration data fixture.

---

## Phase 6: User Story 4 — Threshold Explorer (Priority: P1)

**Goal**: Panel 3 renders the full operating-point grid with the three default highlight points marked when available.

**Independent Test**: `pytest tests/test_analytic_dashboard_outputs.py::test_panel_3_highlights_default_points`

- [ ] T022 [US4] Implement `render_panel_3(model_dir, out_dir, manifest_path)` in `src/visualization/analytic_dashboard.py` — reads `{model_dir}/operating_points.csv`; renders threshold-vs-metric grid showing precision, recall, FPR, alert burden, NNA; identifies and marks up to 3 default points (highest recall at precision ≥ 0.80; lowest alert burden at recall ≥ 0.80; model default threshold); calls `register_analytic_artifact`
- [ ] T023 [P] [US4] Write `test_panel_3_highlights_default_points` in `tests/test_analytic_dashboard_outputs.py` — provides fixture `operating_points.csv` with known default-point candidates; calls `render_panel_3`; asserts PNG ≥ 1600×900px and manifest entry is available

**Checkpoint**: Panel 3 renders without crash; default points are selected per spec rules.

---

## Phase 7: User Story 5 — Alarm Cost Analysis (Priority: P1)

**Goal**: Panel 4 reads all cost assumptions from `config/costs.yaml`; when the file is absent, Panel 4 renders an unavailable panel and the CLI exits 0.

**Independent Test**: `pytest tests/test_cost_config_used.py`

- [ ] T024 [US5] Implement `render_panel_4(model_dir, out_dir, cost_config_path, manifest_path)` in `src/visualization/analytic_dashboard.py` — if `cost_config_path` is absent or unreadable, calls `render_unavailable_panel` naming the missing file and returns; otherwise reads `costs.yaml` with PyYAML; renders FPR → false-alerts → call-volume → cost chain; shows sensitivity bands for each list in `sensitivity:` section; labels participant-days and cost-per-call from config; calls `register_analytic_artifact`
- [ ] T025 [P] [US5] Write `test_panel_4_reads_costs_from_yaml` in `tests/test_cost_config_used.py` — provides fixture `costs.yaml` with known values; monkeypatches any internal cost reads; calls `render_panel_4`; asserts PNG is available and no hardcoded values appear
- [ ] T026 [P] [US5] Write `test_panel_4_unavailable_if_costs_absent` in `tests/test_cost_config_used.py` — calls `render_panel_4` with a nonexistent `cost_config_path`; asserts returned manifest entry has `available == false` and the warning string names the missing file

**Checkpoint**: Panel 4 never uses hardcoded finance values; tests pass with and without `costs.yaml`.

---

## Phase 8: User Story 6 — Explainability (Priority: P2)

**Goal**: Panel 5 shows global importance and local explanations when the files exist; renders an unavailable panel without fabricating values when they don't.

**Independent Test**: Run CLI with and without explanation fixture files; assert Panel 5 PNG exists in both cases.

- [ ] T027 [US6] Implement `render_panel_5(model_dir, out_dir, manifest_path)` in `src/visualization/analytic_dashboard.py` — probes for `{model_dir}/feature_importance.csv` and `{model_dir}/local_explanations.csv`; if both absent calls `render_unavailable_panel`; otherwise renders available data with `method` column from the CSV as the labeled explanation method; never fabricates SHAP or other values; calls `register_analytic_artifact`

**Checkpoint**: Panel 5 renders available state with explanation fixture and unavailable state without.

---

## Phase 9: User Story 7 — CV-vs-Heat Discrimination (Priority: P2)

**Goal**: Panel 6 shows risk score stratified by body-water direction, BP, HR, and skin-temp trajectory dimensions; renders unavailable when trajectory columns are absent.

**Independent Test**: Run CLI with fixture `predictions_oof.csv` including trajectory columns; assert Panel 6 is available; run without trajectory columns; assert Panel 6 is unavailable.

- [ ] T028 [US7] Implement `render_panel_6(model_dir, data_dir, out_dir, manifest_path)` in `src/visualization/analytic_dashboard.py` — reads `{model_dir}/predictions_oof.csv`; checks for `body_water_direction`, `bp_trend`, `hr_trend`, `skin_temp_trend` columns; if absent calls `render_unavailable_panel`; otherwise renders risk-score distributions per trajectory direction; marks confirmed CV and heat outcomes where `y_true == 1` and event type is available; calls `register_analytic_artifact`

**Checkpoint**: Panel 6 renders correctly with and without trajectory columns in fixture data.

---

## Phase 10: User Story 8 — Lead-Time Analysis (Priority: P2)

**Goal**: Panel 7 shows aggregate (median + IQR band) when ≥ 5 confirmed events exist; individual trajectories + sparse-data warning when < 5; unavailable when no events at all.

**Independent Test**: Run with fixture having 6 events (aggregate path) and 3 events (individual path); assert each renders the correct variant.

- [ ] T029 [US8] Implement `render_panel_7(model_dir, data_dir, out_dir, manifest_path)` in `src/visualization/analytic_dashboard.py` — reads `{model_dir}/predictions_oof.csv` for rows with `days_before_event` column; counts unique event participants (rows where `y_true == 1` and `days_before_event` is non-null); if 0: `render_unavailable_panel`; if 1–4: renders individual trajectories with a visible sparse-data warning annotation and `available == true` in manifest; if ≥ 5: renders median trajectory + IQR band; adds a non-event comparison baseline as a horizontal dashed band (median ± IQR of `y_score` for rows where `y_true == 0`) for visual reference; calls `register_analytic_artifact`

**Checkpoint**: Panel 7 branch logic matches the ≥ 5 / < 5 / 0 event thresholds from SPEC-012 clarification Q3.

---

## Phase 11: User Story 9 — Grouped CV Fold Structure (Priority: P2)

**Goal**: Panel 8 shows fold assignment, per-fold class counts, per-fold metric variance, and a visible no-leakage annotation.

**Independent Test**: Run CLI with `predictions_by_fold.csv` and `metrics_by_fold.csv` fixtures; assert Panel 8 PNG is available and ≥ 1600×900px.

- [ ] T030 [US9] Implement `render_panel_8(model_dir, out_dir, manifest_path)` in `src/visualization/analytic_dashboard.py` — reads `{model_dir}/predictions_by_fold.csv` and `{model_dir}/metrics_by_fold.csv`; if fold/repeat columns absent: `render_unavailable_panel`; otherwise renders fold assignment grid, per-fold positive/negative counts, AUPRC and recall-at-precision variance across folds; adds a text annotation "No participant leakage: each participant appears in training or validation only, never both" on the figure; calls `register_analytic_artifact`

**Checkpoint**: Panel 8 always includes the no-leakage annotation text regardless of fold count.

---

## Phase 12: User Story 10 — Subgroup Fairness Audit + Model Card (Priority: P2)

**Goal**: Panel 9 shows subgroup metrics with denominators and sparse warnings; model card is fully populated with all 14 TRIPOD-AI sections.

**Independent Test**: `pytest tests/test_analytic_dashboard_outputs.py::test_panel_9_shows_denominators tests/test_model_card_generation.py`

- [ ] T031 [US10] Implement `render_panel_9(model_dir, data_dir, out_dir, manifest_path)` in `src/visualization/analytic_dashboard.py` — checks for `race_ethnicity`, `insurance`, `ac_access`, `health_literacy` in `{model_dir}/predictions_oof.csv` or joined source data; if all absent: `render_unavailable_panel`; otherwise renders AUPRC or recall-at-precision per subgroup with N and positive-event count; suppresses metric and shows sparse-subgroup warning when `n_in_subgroup < 10`; shows metric with overinterpretation caution annotation when `n_events_in_subgroup < 3`; calls `register_analytic_artifact`
- [ ] T032 [P] [US10] Write `test_panel_9_shows_denominators` in `tests/test_analytic_dashboard_outputs.py` — provides fixture with known subgroup columns; calls `render_panel_9`; asserts PNG ≥ 1600×900px and available
- [ ] T033 [US10] Complete `generate_tripod_ai_card()` implementation in `src/visualization/model_cards.py` — reads `bakeoff_summary.json` for metadata, `bakeoff_config_used.yaml` for exact paths, `metrics_summary.csv` for model comparison; writes all 14 required TRIPOD-AI sections (FR-046); includes synthetic-data caveat when `detect_synthetic_run()` returns True; references exact config and output paths
- [ ] T034 [P] Write `test_model_card_has_required_sections` in `tests/test_model_card_generation.py` — calls `generate_tripod_ai_card()` with fixture artifacts; reads output `.md`; asserts all 14 required section headings are present
- [ ] T035 [P] Write `test_model_card_synthetic_caveat` in `tests/test_model_card_generation.py` — calls with a `bakeoff_summary.json` fixture containing `"data_source": "synthetic"`; asserts the output contains the synthetic-data caveat section

**Checkpoint**: Panel 9 and model card tests pass; card contains all 14 sections and the caveat section appears for synthetic runs.

---

## Phase 13: User Story 11 — Novelty and Anomaly View (Priority: P3)

**Goal**: Panel 11 surfaces capture-worthy extremes linked to participant and study-day context; labels anomalies as capture-worthy, not errors.

**Independent Test**: Run CLI with and without novelty score fixture; assert Panel 11 is available in the first case, unavailable in the second.

- [ ] T036 [US11] Implement `render_panel_11(model_dir, data_dir, out_dir, manifest_path)` in `src/visualization/analytic_dashboard.py` — probes for `{model_dir}/novelty_scores.csv`; if absent: `render_unavailable_panel` stating the file is an optional SPEC-011 output; if present: renders a scatter of `novelty_score` by `participant_id` and `study_day`, labels high-score points as "capture-worthy" (not "error" or "outlier"), links each point to participant and study-day context; calls `register_analytic_artifact`

**Checkpoint**: Panel 11 uses "capture-worthy" language consistently; unavailable panel is rendered cleanly.

---

## Phase 14: Polish and Cross-Cutting Concerns

**Purpose**: Size gate verification, manifest integrity, and final test suite run.

- [ ] T037 Verify all available panel PNGs are ≥ 1600×900px — add an assertion in `tests/test_analytic_dashboard_outputs.py::test_full_run_creates_all_artifacts` that reads each PNG's dimensions via PIL or struct and asserts width ≥ 1600, height ≥ 900
- [ ] T038 [P] Verify no SPEC-012 run modifies or removes existing EDA manifest entries — add assertion in `test_full_run_creates_all_artifacts` that EDA entries present before the run are still present and unchanged after
- [ ] T039 [P] Run full SPEC-012 test suite and confirm all pass: `PYTHONPATH=. pytest tests/test_analytic_dashboard_outputs.py tests/test_cost_config_used.py tests/test_model_card_generation.py`
- [ ] T040 [P] Run full quickstart scenario from `specs/012-analytic-model-dashboard/quickstart.md` on synthetic fixture data; confirm all 12 artifact files are written and the manifest has 12 analytic entries

---

## Dependencies and Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — all 6 tasks in parallel.
- **Foundational (Phase 2)**: Depends on Phase 1 completion. T007 blocks all panel implementations.
- **User Story Phases (3–13)**: All depend on Phase 2 completion. P1 stories (Phases 3–7) should be completed before P2 stories (Phases 8–12) to keep the MVP shippable incrementally.
- **Polish (Phase 14)**: Depends on all desired user story phases being complete.

### User Story Dependencies

| Story | Phase | Priority | Can start after |
|-------|-------|----------|----------------|
| US1 Full Run | 3 | P1 🎯 | Phase 2 |
| US2 Leaderboard | 4 | P1 | Phase 2 |
| US3 Calibration | 5 | P1 | Phase 2 |
| US4 Threshold | 6 | P1 | Phase 2 |
| US5 Alarm Cost | 7 | P1 | Phase 2 |
| US6 Explainability | 8 | P2 | Phase 2 |
| US7 CV-vs-Heat | 9 | P2 | Phase 2 |
| US8 Lead-Time | 10 | P2 | Phase 2 |
| US9 Grouped CV | 11 | P2 | Phase 2 |
| US10 Subgroup + Card | 12 | P2 | Phase 2 |
| US11 Novelty | 13 | P3 | Phase 2 |

Panel render functions are independent of each other — Phases 4–13 can be worked in parallel by different implementers after Phase 2 completes.

### Within Each Phase

- Test tasks [P] can be written concurrently with or before the implementation task they cover.
- The panel function must be importable before its test can be run — stubs from Phase 1 satisfy this.

---

## Parallel Example: Phase 2 (Foundational)

```bash
# T008 and T009 can run in parallel (different helper functions, same file — coordinate):
Task T008: "Implement register_analytic_artifact() in analytic_dashboard.py"
Task T009: "Implement detect_synthetic_run() in analytic_dashboard.py"
# T007 should be done first (render_unavailable_panel is called by all panels)
# T010 should be done last (CLI main() calls all helpers)
```

## Parallel Example: P1 Panel Phases (4–7)

```bash
# After Phase 3 is complete, all four P1 panel implementations can run in parallel:
Task T016: "render_panel_1() in analytic_dashboard.py"
Task T019: "render_panel_2() in analytic_dashboard.py"
Task T022: "render_panel_3() in analytic_dashboard.py"
Task T024: "render_panel_4() in analytic_dashboard.py"
```

---

## Implementation Strategy

### MVP (Phases 1–7 only)

1. Complete Phase 1 (Setup) — all tasks parallelizable.
2. Complete Phase 2 (Foundational) — T007 first, then T008+T009 in parallel, then T010.
3. Complete Phase 3 (US1 Full Run) — CLI wiring and end-to-end smoke test.
4. Complete Phases 4–7 (Panels 1–4, all P1 stories).
5. **STOP and validate**: Run `pytest tests/test_analytic_dashboard_outputs.py tests/test_cost_config_used.py`; confirm SC-001 through SC-009.

### Incremental Delivery

- MVP (above) → delivers all P1 panel PNGs, AUPRC-primary leaderboard, calibration, threshold, alarm-cost.
- Add Phases 8–12 → delivers P2 panels + fully populated model card.
- Add Phase 13 → delivers novelty view.
- Add Phase 14 → delivers polish, size gate verification, manifest integrity check.

---

## Notes

- `[P]` tasks operate on different functions/sections within the same file — coordinate merges to avoid conflicts on `analytic_dashboard.py`.
- Each panel function is independently callable (see quickstart.md) — implement and test each in isolation before wiring into the CLI loop.
- `render_unavailable_panel()` is the single fallback for all missing-input, sparse-data, and error states — implement it robustly in Phase 2 before touching any panel.
- The `"type": "analytic"` manifest field (from clarification Q1) must be present in every `register_analytic_artifact()` call — the contract test in T038 will catch any missing entries.
- Do not add any new entries to `pyproject.toml` — all required libraries are already declared.
