---
id:            CONTRACT-003-ERRORS
title:         Stream Adapter Error Taxonomy
status:        draft
version:       0.1.0
created:       2026-06-01
updated:       2026-06-01
author:        Soroush Dianaty
depends_on:    [SPEC-003, PLAN-003]
related:       [CONTRACT-002-ERRORS]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Contract: Stream Adapter Error Taxonomy

---

## Exception Hierarchy

```
BatchAdapterError (SPEC-002, src/ingestion/adapters/base.py)
└── StreamAdapterError (src/ingestion/stream/errors.py)
```

`StreamAdapterError` is the single raised exception type for all streaming failure modes.
The error message carries a `reason` field distinguishing the triggering condition.

---

## Triggering Conditions

| Condition | FR | When raised | Invariant preserved |
|-----------|-----|-------------|---------------------|
| **Null / unparseable timestamp** | FR-008 | A record's timestamp column is `NaT`, `None`, or cannot be parsed | No frames yielded for that window; canonical store unchanged |
| **Schema-invalid record** | FR-008 | A record in the current window fails `LullabySchema` validation (missing required column, type mismatch) | No frames yielded for that window; canonical store unchanged |
| **Backpressure timeout** | FR-009 | Consumer holds a yielded window longer than `backpressure_timeout_s` seconds (measured by `time.monotonic()` delta after `yield`) | The timed-out window was already yielded; adapter stops iteration |
| **Non-empty pending buffer at end-of-stream** | FR-007 | Source exhausted while future-timestamp records remain in the pending buffer | No frames yielded for undeliverable records; canonical store unchanged |

---

## Non-Fatal Events

| Event | Mechanism | FR |
|-------|-----------|----|
| **LateArrivalWarning** | `logging.warning(...)` + `adapter.late_arrival_count += 1` | FR-006 |

Late arrival is **not** raised as an exception. The excluded record is dropped, the warning
is logged with structured fields (`adapter`, `record_ts`, `skew_s`), and iteration continues.

---

## Error Message Format

```
StreamAdapterError: <reason>
```

Where `<reason>` is one of:

- `"Null timestamp in table '{table}': {count} record(s) with NaT timestamp_column='{col}'"` 
- `"Schema-invalid record in table '{table}': {validation_detail}"`
- `"Backpressure timeout: consumer held window {window_start} for {elapsed:.1f}s (limit={timeout}s)"`
- `"Stream exhausted with {count} undeliverable future-timestamp record(s) in pending buffer; ts range=[{min_ts}, {max_ts}]"`

---

## Detecting Errors in Tests

```python
import pytest
from src.ingestion.stream.errors import StreamAdapterError

with pytest.raises(StreamAdapterError, match="Null timestamp"):
    list(adapter)  # exhaust generator to trigger the error
```
