---
id:            PLAN-002-CONTRACT-001
title:         BatchAdapter Interface Contract
status:        draft
version:       0.1.0
created:       2026-06-01
updated:       2026-06-01
author:        Soroush Dianaty
depends_on:    [SPEC-002]
implements:    [P4, P5]
supersedes:    null
superseded_by: null
related:       [PLAN-002]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# BatchAdapter Interface Contract

## ABC definition

```python
from abc import ABC, abstractmethod
from typing import Generic, TypeVar
import pandas as pd

C = TypeVar("C", bound="AdapterConfig")

class BatchAdapter(ABC, Generic[C]):
    @abstractmethod
    def load(self, config: C) -> dict[str, pd.DataFrame]:
        """
        Load source data and return canonical frames keyed by table name.
        Raises a BatchAdapterError subclass on any failure.
        Never returns partial output — either all tables succeed or an exception is raised.
        """
        ...
```

## Output contract

- Return type: `dict[str, pd.DataFrame]`
- Keys: canonical table names from `LullabySchema` — `participants`, `daily_vitals`, `alerts`, `clinical_outcomes`, `staff_contacts` (or a subset; never additional keys)
- Each DataFrame: columns and dtypes MUST match `LullabySchema` for the named table
- Dedup: primary keys read from `LullabySchema.primary_keys(table_name)` at runtime; `drop_duplicates(subset=keys, keep="last")` applied before return
- Validation: all frames pass through `ValidationEngine(schema).validate(frames)` before return

## Invariants

- Partial loads are forbidden: if any table fails, the adapter raises and returns nothing
- No inter-adapter imports: each adapter module is standalone
- No secrets in logs or exception messages (`pydantic.SecretStr` on all credential fields)
- `load()` is idempotent: same config + same source → same output, no side effects

## Stub contract

Stub adapters (`DropboxAdapter`, `OneDriveAdapter`, `GenericFallbackAdapter`) MUST:
- Inherit from `BatchAdapter[XConfig]`
- Raise `NotImplementedError("Not implemented: <AdapterName>. See contracts/ for interface.")` in `load()`
- Have a fully typed config class
- Be importable without error

## Logging contract (NFR-004)

Every concrete adapter MUST emit:
- `INFO`: `"adapter=<name> starting load"` before the first I/O call
- `INFO`: `"adapter=<name> loaded <N> tables, row_counts=<{table: N, ...}>"` on success
- `ERROR`: `"adapter=<name> raised <ExceptionType>: <sanitized_message>"` on any exception

Sanitized message MUST NOT contain: tokens, passwords, connection strings, or file paths embedding credentials.
