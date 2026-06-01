---
id:            CONTRACT-003-INTERFACE
title:         StreamAdapter & StreamAccumulator Interface Contract
status:        draft
version:       0.1.0
created:       2026-06-01
updated:       2026-06-01
author:        Soroush Dianaty
depends_on:    [SPEC-003, PLAN-003]
related:       [CONTRACT-002-INTERFACE]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Contract: StreamAdapter & StreamAccumulator Interface

---

## StreamAdapter

**Module**: `src.ingestion.stream.adapter`

### Constructor

```python
StreamAdapter(
    batch_adapter: BatchAdapter[C],
    source_config: C,
    schema: LullabySchema,
    config: StreamAdapterConfig = StreamAdapterConfig(),
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `batch_adapter` | `BatchAdapter[C]` | Any SPEC-002 adapter; `load(source_config)` is called once at the start of iteration |
| `source_config` | `C` | Config forwarded to `batch_adapter.load()` |
| `schema` | `LullabySchema` | Provides `table_contract(table)` for primary key and timestamp column names |
| `config` | `StreamAdapterConfig` | Cadence, skew tolerance, speed factor, backpressure timeout |

### Generator Protocol

```python
for window_start, frames in adapter:
    # window_start: datetime — start of this cadence window (UTC)
    # frames: dict[str, pd.DataFrame] — canonical frames for this window
    ...
```

- Yields windows in ascending `window_start` order.
- An empty cadence interval yields an empty `dict[str, pd.DataFrame]`. Non-empty windows
  contain one key per canonical table; tables with no rows in that interval yield an empty
  `pd.DataFrame` with correct schema columns.
- Tables whose schema contract has `timestamp_column == ""` are static reference tables:
  deduplicated by primary key, emitted once in the first stream window, and not repeated in
  later windows.
- All frames within a window are deduplicated by primary key (last-write-wins). Timestamped
  tables are sorted ascending by timestamp column before yielding; static reference tables
  are sorted deterministically by primary key.
- Raises `StreamAdapterError` on: null/unparseable timestamp, schema-invalid record,
  backpressure timeout, or non-empty pending buffer at end-of-stream.

### Public Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `late_arrival_count` | `int` | Cumulative count of excluded late-arrival records since construction |

### Guarantees

1. A `StreamAdapterError` is always raised before any partial frames escape the generator.
2. Re-iterating the same `StreamAdapter` instance from a fresh construction (same source
   + config) produces the same sequence of windows (deterministic replay — FR-012).
3. `late_arrival_count` is never decremented.
4. No `time.sleep()` calls are made during iteration.

---

## StreamAccumulator

**Module**: `src.ingestion.stream.accumulator`

### Method

```python
StreamAccumulator.accumulate(
    adapter: StreamAdapter,
    schema: LullabySchema,
) -> dict[str, pd.DataFrame]
```

Exhausts the `adapter` generator and merges all emitted windows into a single canonical
store.

**Merge semantics**:
- For each table: `pd.concat` all per-window DataFrames → `drop_duplicates(subset=pk, keep='last')` → sort by timestamp column when present, otherwise by primary key → `reset_index(drop=True)`.
- Tables present in `schema` but absent from all windows → empty `pd.DataFrame` with the
  correct columns.
- The returned store is row-for-row equivalent to a batch load of the same source data when
  the source has no late arrivals or out-of-order records (SC-001 invariant).

**Raises**: propagates any `StreamAdapterError` raised by the adapter during iteration.

---

## Usage Example (CI Equivalence Job)

```python
batch_adapter = FileAdapter()
source_config = FileAdapterConfig(path="data/synthetic_cohort/")
schema = LullabySchema()

stream_adapter = StreamAdapter(
    batch_adapter=batch_adapter,
    source_config=source_config,
    schema=schema,
    config=StreamAdapterConfig(cadence_s=60, speed_factor=100.0),
)

accumulated = StreamAccumulator.accumulate(stream_adapter, schema)

assert stream_adapter.late_arrival_count == 0

batch_frames = batch_adapter.load(source_config)
for table in schema.table_names():
    pd.testing.assert_frame_equal(
        accumulated[table].reset_index(drop=True),
        batch_frames[table].reset_index(drop=True),
        check_like=True,
    )
```
