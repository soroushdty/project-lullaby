---
id: QUICKSTART-009
title: Longitudinal Vitals, Missingness, Signal Quality, and Patient Timeline Quickstart
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-009, SPEC-001, SPEC-004, SPEC-007]
implements: [P3, P5, P7, P10]
supersedes: null
superseded_by: null
related: [SPEC-004, SPEC-005, SPEC-006, SPEC-007]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Quickstart: Longitudinal Vitals, Missingness, Signal Quality, and Patient Timeline

## 1. Install Local Dependencies

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
```

## 2. Generate Default Longitudinal EDA Dashboards

```bash
.venv/bin/python -m src.visualization.generate_eda \
  --data-dir data/raw \
  --out-dir outputs/figures/eda \
  --panels longitudinal
```

Expected result:

```text
Generated 5 EDA longitudinal dashboard artifacts
outputs/figures/eda/05_vital_trajectories.png
outputs/figures/eda/06_missingness_adherence.png
outputs/figures/eda/07_patient_timeline.png
outputs/figures/eda/08_data_quality_scorecard.png
outputs/figures/eda/09_missingness_mechanism.png
```

The command also updates `outputs/figures/manifest.json` for repo-relative outputs. If no
participant id is supplied, the manifest records the automatically selected participant and
score components.

## 3. Generate A Participant-Specific Timeline With Environment Overlay

```bash
.venv/bin/python -m src.visualization.generate_eda \
  --data-dir data/raw \
  --out-dir outputs/figures/eda \
  --panels longitudinal \
  --participant-id PARTICIPANT_ID \
  --overlay-environment true
```

Expected result: the same five longitudinal artifact filenames are written, with Panel 5 and
Panel 7 using the supplied participant id and rendering heat index or ambient temperature
overlays when environment data are available.

## 4. Generate A Week-Filtered Longitudinal View

```bash
.venv/bin/python -m src.visualization.generate_eda \
  --data-dir data/raw \
  --out-dir outputs/figures/eda \
  --panels longitudinal \
  --week-start 1 \
  --week-end 6
```

Expected result: longitudinal panels render the inclusive study-week range. Study days 1-7 are
week 1; omitted week filters render the full observed range.

## 5. Verify Required Artifacts

```bash
.venv/bin/pytest tests/test_eda_longitudinal_outputs.py tests/test_patient_timeline.py
```

Expected result: focused longitudinal EDA tests pass, including artifact creation, image size,
manifest entries, visible gaps, no imputation, deterministic participant selection,
quality-score formula metadata, participant timeline tracks, and exploratory diagnostic labels.

## 6. Required Failure Smoke Test

```bash
tmpdir="$(mktemp -d)"
.venv/bin/python -m src.visualization.generate_eda \
  --data-dir "$tmpdir" \
  --out-dir outputs/figures/eda \
  --panels longitudinal
```

Expected result: the command exits non-zero with an actionable required-input validation
message and does not write affected PNG artifacts or manifest entries.

## 7. Invalid Participant Smoke Test

```bash
.venv/bin/python -m src.visualization.generate_eda \
  --data-dir data/raw \
  --out-dir outputs/figures/eda \
  --panels longitudinal \
  --participant-id NOT_A_PARTICIPANT
```

Expected result: the command exits non-zero before writing participant-specific artifacts.

## 8. Full Local Validation

```bash
.venv/bin/pytest
```

Expected result: the full test suite passes without network access. Any socket-bound tests use
the same local permissions already required by the existing suite.

## 9. Implementation Evidence

Recorded on 2026-06-01:

- Default longitudinal generation passed in 0:03.35 and wrote all five PNG artifacts under `outputs/figures/eda/`.
- Participant overlay generation passed in 0:03.37 with `--participant-id LUL-2179 --overlay-environment true`.
- Inclusive week-filter generation passed in 0:03.32 with `--week-start 1 --week-end 6`.
- Focused acceptance tests passed: `12 passed, 2 warnings in 10.29s`.
- Full validation passed with local socket permission for adapter fixtures: `230 passed, 4 skipped, 9 warnings in 79.21s`.
- A sandboxed full-suite run without local socket permission reached `218 passed, 4 skipped` and errored only in HTTP-adapter fixtures with `PermissionError: [Errno 1] Operation not permitted`.
