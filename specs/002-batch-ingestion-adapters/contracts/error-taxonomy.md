---
id:            PLAN-002-CONTRACT-003
title:         Error Taxonomy Contract
status:        draft
version:       0.1.0
created:       2026-06-01
updated:       2026-06-01
author:        Soroush Dianaty
depends_on:    [SPEC-002]
implements:    [P5]
supersedes:    null
superseded_by: null
related:       [PLAN-002]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Error Taxonomy Contract

All exceptions inherit from `BatchAdapterError(RuntimeError)` defined in `src/ingestion/adapters/base.py`.

## Exception hierarchy

```
BatchAdapterError(RuntimeError)
├── SchemaMismatchError      — source does not conform to canonical schema
├── ConnectorError           — network/cloud/DB failure after retry exhaustion
├── AuthConfigError          — missing or invalid credentials
├── UnsupportedFormatError   — file type or MIME type not in supported set
├── EncodingError            — file cannot be decoded with declared encoding
└── UnitAmbiguityError       — unit-sensitive column has no declared/detectable unit
```

## Exception field contracts

```python
class SchemaMismatchError(BatchAdapterError):
    table: str
    missing_columns: list[str]
    found_columns: list[str]

class ConnectorError(BatchAdapterError):
    adapter: str           # class name of the failing adapter
    cause: Exception       # original exception
    attempts: int          # number of attempts made

class AuthConfigError(BatchAdapterError):
    adapter: str
    credential_env_var: str   # e.g. "REDCAP_TOKEN"

class UnsupportedFormatError(BatchAdapterError):
    adapter: str
    detected_type: str     # e.g. ".json", "application/xml"

class EncodingError(BatchAdapterError):
    adapter: str
    path: str              # sanitized — no credential components
    detected_encoding: str | None

class UnitAmbiguityError(BatchAdapterError):
    column: str
    sample_value: str      # first non-null value as string, for diagnostics
```

## Invariants

- Exceptions MUST be raised before any partial output is returned
- `cause` in `ConnectorError` MUST be the original exception (not a string); callers can chain with `raise ConnectorError(...) from original`
- `credential_env_var` in `AuthConfigError` contains the env var NAME, not its value
- `path` in `EncodingError` is the repository-relative path with no embedded secrets
- All exception `__str__` representations MUST be free of secret values
