---
id: QUICKSTART-010
title: Relationships, Heat Exposure, Archetypes, and Recruitment Dashboards Quickstart
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-010, SPEC-001, SPEC-004, SPEC-007, SPEC-009]
implements: [P3, P5, P7, P10]
supersedes: null
superseded_by: null
related: [SPEC-004, SPEC-005, SPEC-006, SPEC-007, SPEC-009]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Quickstart: Relationships, Heat Exposure, Archetypes, and Recruitment Dashboards

## 1. Install Local Dependencies

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
```

## 2. Generate Default SPEC-010 EDA Dashboards

```bash
.venv/bin/python -m src.visualization.generate_eda \
  --data-dir data/raw \
  --out-dir outputs/figures/eda \
  --panels relationships
```

Expected result:

```text
Generated 4 EDA relationships dashboard artifacts
outputs/figures/eda/10_relationships.png
outputs/figures/eda/11_heat_environment.png
outputs/figures/eda/12_archetype_explorer.png
outputs/figures/eda/13_recruitment_timeline.png
```

The command also updates `outputs/figures/manifest.json` for repo-relative outputs. If the raw
data path has no standalone `environment.csv`, Panel 11 renders an explicit unavailable panel
and records a manifest warning.

## 3. Generate With Synthetic Environment And Recruitment Data

```bash
.venv/bin/python -m src.visualization.generate_eda \
  --data-dir data/synthetic/longitudinal \
  --out-dir outputs/figures/eda_synthetic \
  --panels relationships
```

Expected result: all four SPEC-010 artifacts render with environment, recruitment, and explicit
archetype context where the synthetic tables provide it.

## 4. Generate All EDA Panels

```bash
.venv/bin/python -m src.visualization.generate_eda \
  --data-dir data/raw \
  --out-dir outputs/figures/eda \
  --panels all
```

Expected result: panels 1 through 13 are generated through the existing core, longitudinal,
and relationships panel sets.

## 5. Verify Required Artifacts

```bash
.venv/bin/pytest tests/test_eda_relationships_outputs.py
```

Expected result: focused SPEC-010 EDA tests pass, including artifact creation, image size,
manifest entries, observed-pair metadata, environment-unavailable behavior, explicit versus
provisional archetype behavior, and recruitment timeline fallbacks.

## 6. Required Failure Smoke Test

```bash
tmpdir="$(mktemp -d)"
.venv/bin/python -m src.visualization.generate_eda \
  --data-dir "$tmpdir" \
  --out-dir outputs/figures/eda \
  --panels relationships
```

Expected result: the command exits non-zero with an actionable required-input validation
message and does not write affected PNG artifacts or manifest entries.

## 7. Existing EDA Regression Check

```bash
.venv/bin/pytest tests/test_eda_core_outputs.py tests/test_eda_longitudinal_outputs.py
```

Expected result: existing core and longitudinal EDA tests continue to pass after the CLI adds
`relationships` and `all`.

## 8. Full Local Validation

```bash
.venv/bin/pytest
```

Expected result: the full test suite passes without network access. Any socket-bound tests use
the same local permissions already required by the existing suite.
