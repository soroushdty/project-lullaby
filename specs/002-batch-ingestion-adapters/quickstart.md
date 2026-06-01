---
id:            PLAN-002-QUICKSTART
title:         Quickstart - Batch Ingestion Adapters
status:        draft
version:       0.1.0
created:       2026-06-01
updated:       2026-06-01
author:        Soroush Dianaty
depends_on:    [SPEC-002, SPEC-001]
implements:    [P2, P4, P5]
supersedes:    null
superseded_by: null
related:       [PLAN-002]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Quickstart

## 1. Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pandas openpyxl boto3 azure-storage-blob google-cloud-storage \
            sqlalchemy pymysql requests tenacity pydantic \
            pytest pytest-httpserver
```

## 2. Run Tier 1 tests (no cloud accounts, no Docker)

```bash
pytest tests/unit tests/contract tests/integration/test_adapters_local.py -q
```

Expected: all tests pass, exit 0.

## 3. Run Tier 2 tests (cloud emulators via Docker Compose)

```bash
docker compose up -d --wait
pytest tests/integration/test_adapters_emulated.py -q
docker compose down
```

Expected: MinIO, Azurite, and fake-gcs-server serve the synthetic cohort; all adapters return valid frames.

## 4. Run Tier 3 tests (REDCap recorded fixtures)

```bash
pytest tests/integration/test_adapters_fixtures.py -q
```

Expected: REDCap adapter parses all fixture files; frames pass validation.

## 5. Use an adapter directly

```python
from src.ingestion.adapters.file_adapter import FileAdapter, FileAdapterConfig

config = FileAdapterConfig(path="data/synthetic/participants.csv")
frames = FileAdapter().load(config)
# frames["participants"] is a canonical pd.DataFrame
```

## 6. Add a new adapter

1. Create `src/ingestion/adapters/my_adapter.py`
2. Define `MyAdapterConfig(AdapterConfig)` with Pydantic v2 fields; use `SecretStr` for credentials
3. Define `class MyAdapter(BatchAdapter[MyAdapterConfig])` and implement `load(config)`
4. Log INFO at start/end and ERROR on exceptions (NFR-004)
5. Raise typed `BatchAdapterError` subclasses — never return partial output
6. Add tests to the appropriate tier in `tests/integration/`

## Authoring checklist for implementation PRs

- Include `SPEC-002` in PR title or body
- Add exactly one `CHANGELOG.md` entry (in the final completing PR if multi-PR)
- Run all three test tiers locally before pushing
- Confirm no secrets appear in test output (`pytest -s` + grep for known token values)
