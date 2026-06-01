---
id:            PLAN-001-QUICKSTART
title:         Quickstart - Canonical Schema & Validation
status:        draft
version:       0.1.0
created:       2026-06-01
updated:       2026-06-01
author:        Soroush Dianaty
depends_on:    [SPEC-001]
implements:    [P2, P3, P5]
supersedes:    null
superseded_by: null
related:       [PLAN-001]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Quickstart

## 1. Environment (Python)
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install pandas pandera pydantic-settings PyYAML pytest
```

## 2. Run canonical ingestion + validation (bundled synthetic data)
```bash
python -m src.cli.validate_schema --schema lullaby --input data/synthetic
```

Expected result:
- exit code 0
- all five canonical tables validated
- validation report emitted to `artifacts/validation-report.json`

## 3. Run with alternate schema object
```bash
python -m src.cli.validate_schema --schema custom.module:CustomSchema --input data/synthetic
```

Expected result:
- Conforming custom schema: validation passes.
- Non-conforming custom schema/data: validation fails with table/column/constraint details.

## 4. Run tests
```bash
pytest -q
```

## 5. CI contract
Create a workflow job named `validate-schema` that executes the same CLI command against
bundled synthetic data and fails the build on validation errors.
