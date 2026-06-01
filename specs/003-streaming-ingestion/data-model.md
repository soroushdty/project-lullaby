---
id:            DATA-MODEL-003
title:         Streaming Ingestion Data Model
status:        draft
version:       0.1.0
created:       2026-06-01
updated:       2026-06-01
author:        Soroush Dianaty
depends_on:    [SPEC-003, PLAN-003, RESEARCH-003]
related:       [SPEC-002, DATA-MODEL-002]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Data Model: Streaming Ingestion (SPEC-003)

---

## Entities

### StreamAdapterConfig

Extends `AdapterConfig` (SPEC-002, `src/ingestion/adapters/base.py`).

| Field | Type | Default | Constraint | Description |
|-------|------|---------|------------|-------------|
| `cadence_s` | `int` | `60` | `≥ 1` | Window duration in seconds |
| `skew_tolerance_s` | `int` | `300` | `≥ 0` | Max late-arrival tolerance in seconds |
| `speed_factor` | `float` | `1.0` | `> 0` | Virtual clock multiplier (informational; no sleep calls made) |
| `backpressure_timeout_s` | `float` | `30.0` | `> 0` | Max elapsed time between yield and consumer calling next() before `StreamAdapterError` |

Inherited from `AdapterConfig`: `max_attempts`, `rate_limit_default_wait_s`.

---

### StreamAdapter

Public generator class. Lives in `src/ingestion/stream/adapter.py`.

| Attribute | Type | Description |
|-----------|------|-------------|
| `late_arrival_count` | `int` | Incremented once per excluded late-arrival record; resets to 0 on construction |

**Constructor parameters**:
- `batch_adapter: BatchAdapter[C]` — any SPEC-002 adapter that loads the source
- `source_config: C` — config passed to `batch_adapter.load()` at iteration start
- `schema: LullabySchema` — provides `table_contract(table)` for PK and timestamp column
- `config: StreamAdapterConfig` — cadence, tolerance, speed factor, backpressure timeout

**Generator protocol**: `StreamAdapter.__iter__` yields `(window_start: datetime, frames: dict[str, pd.DataFrame])` tuples in ascending `window_start` order.

**State transitions**:
```
IDLE → iterating (first next() call) → RUNNING (per-window loop) → EXHAUSTED (StopIteration)
                                                                  ↘ ERROR (StreamAdapterError)
```

---

### StreamWindow (internal)

Not a public class. Represents the in-progress assembly of one cadence interval during
`__iter__`. Logically contains:
- `window_start: datetime`
- per-table DataFrames after dedup, sort, and skew filtering

---

### StreamAccumulator

Public helper class. Lives in `src/ingestion/stream/accumulator.py`.

**Method**: `accumulate(adapter: StreamAdapter) -> dict[str, pd.DataFrame]`

Exhausts the generator. For each table, concatenates all window DataFrames, applies
last-write-wins dedup by primary key, sorts by timestamp column when present (otherwise
by primary key), resets index.

```
accumulated[table] = (
    pd.concat([window_frames[table] for (_, window_frames) in all_windows
               if table in window_frames], ignore_index=True)
      .drop_duplicates(subset=primary_key, keep='last')
      .sort_values(timestamp_column if timestamp_column else primary_key)
      .reset_index(drop=True)
)
```

Returns empty DataFrames (matching schema columns) for tables with no records across all
windows.

---

### StreamAdapterError

Inherits `BatchAdapterError` (`src/ingestion/adapters/base.py`). Lives in
`src/ingestion/stream/errors.py`.

Triggering conditions (see `stream-error-taxonomy.md` for full taxonomy):

| Condition | Raised when |
|-----------|-------------|
| Null timestamp | A record's timestamp column is null or unparseable |
| Schema-invalid record | Any record in the current window fails `LullabySchema` validation |
| Backpressure timeout | Consumer holds a yielded window longer than `backpressure_timeout_s` |
| Non-empty pending buffer at end-of-stream | Source exhausted with undeliverable future-timestamp records |

---

### LateArrivalWarning (log event, not a class)

Emitted via `logging.warning(...)` with structured fields. Not raised as an exception.

| Field | Description |
|-------|-------------|
| `adapter` | Adapter class name |
| `record_ts` | Event timestamp of the excluded record |
| `skew_s` | Number of seconds the record arrived late beyond the current window |

Detected in CI via `adapter.late_arrival_count` counter.

---

## Relationships

```
BatchAdapter[C] ←── wraps ──── StreamAdapter
                                    │
                     uses ──────────┤
                                    │
LullabySchema ◄──────────────────── │ (reads table_contract per table)
                                    │
                    yields ─────────┴──→ (window_start, dict[str, pd.DataFrame])
                                                          │
                                           consumed by ──→ StreamAccumulator
                                                          │
                                           produces ─────→ dict[str, pd.DataFrame]
                                                           (canonical store, batch-equivalent)
```

---

## Validation Rules

- `cadence_s ≥ 1` — enforced by pydantic `Field(ge=1)`
- `skew_tolerance_s ≥ 0` — zero means no late records are tolerated
- `speed_factor > 0` — pydantic `Field(gt=0)`
- `backpressure_timeout_s > 0` — pydantic `Field(gt=0)`
- Null or unparseable timestamp values in tables with `timestamp_column != ""` → `StreamAdapterError` (not `LateArrivalWarning`)
- Schema-invalid records in a window → `StreamAdapterError` before any frames are yielded
