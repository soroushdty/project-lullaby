---
id:            RESEARCH-003
title:         Streaming Ingestion Research
status:        complete
version:       0.1.0
created:       2026-06-01
updated:       2026-06-01
author:        Soroush Dianaty
depends_on:    [SPEC-003, PLAN-003]
related:       [SPEC-002, PLAN-002]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Research: Streaming Ingestion (SPEC-003)

All NEEDS CLARIFICATION items were resolved during `/speckit.clarify` (Session 2026-06-01).
This document records the design decisions, rationale, and algorithms that inform Phase 1.

---

## Decision 1 — Python Generator as the Consumption Interface

**Decision**: `StreamAdapter` implements `__iter__` / `yield`; consumers iterate with
`for window_start, frames in adapter`.

**Rationale**: A synchronous generator is the simplest correct design for an in-process
reference simulation. Backpressure is inherent — the generator suspends at each `yield` and
resumes only when the consumer calls `next()`. No threading, asyncio, or queue infrastructure
is needed. The `Iterator` protocol integrates directly with `for` loops and `list()` coercion.

**Alternatives considered**:
- Async generator (`async for`) — adds `asyncio` complexity with no benefit for a synchronous
  reference implementation.
- Explicit pull (`next_window()` method) — equivalent expressiveness but non-standard;
  breaks interoperability with Python iteration utilities.
- Callback push (`run(on_window: Callable)`) — inverts control in a way that complicates
  test assertions and backpressure detection.

---

## Decision 2 — StreamAccumulator as a Provided Helper

**Decision**: A `StreamAccumulator` class is provided; its `accumulate(adapter)` method
exhausts the generator and merges all windows into a final `dict[str, pd.DataFrame]` using
cross-window last-write-wins dedup by primary key.

**Rationale**: The CI equivalence job (FR-013) and any caller needing the full canonical store
would otherwise re-implement the same `pd.concat` + `drop_duplicates(keep='last')` logic.
Providing it as a library class ensures consistent dedup semantics and a single assertion point
(`adapter.late_arrival_count == 0`).

**Merge algorithm**:
```
accumulated[table] = (
    pd.concat([window[table] for window in all_windows if table in window])
    .drop_duplicates(subset=primary_key, keep='last')
    .sort_values(timestamp_column if timestamp_column else primary_key)
    .reset_index(drop=True)
)
```

**Alternatives considered**:
- Method on `StreamAdapter` (`adapter.accumulate()`) — conflates the generator source with
  the consumer; breaks separation of concerns.
- Caller responsibility — forces every caller to re-implement merge semantics correctly.

---

## Decision 3 — Event-Timestamp-Driven Virtual Clock (No Sleeping)

**Decision**: Window boundaries are computed from event timestamps in the data. No
`time.sleep()` calls are made. The `speed_factor` config field is stored and exposed but
does not affect execution timing.

**Windowing algorithm**:
1. Load all source data via `batch_adapter.load(source_config)`.
2. For each table with a timestamp column, parse the timestamp column
   (`LullabySchema.table_contract(t).timestamp_column`).
3. For each timestamped record in each table, compute its window assignment:
   `window_start = epoch_floor(event_ts, cadence_s)` where
   `epoch_floor(ts, c) = datetime.fromtimestamp(floor(ts.timestamp() / c) * c, tz=ts.tzinfo)`.
4. Collect all unique `window_start` values across timestamped tables; sort ascending →
   `window_timeline`.
5. Treat tables with `timestamp_column == ""` as static reference tables: deduplicate by
   primary key and emit once in the first stream window.
6. Iterate `window_timeline`, yielding one window per step.

**Rationale**: For a reference simulation, wall-clock speed is irrelevant — correctness and
determinism matter. Removing `time.sleep()` eliminates flakiness, makes tests instantaneous,
and trivially satisfies SC-006 (<2 min).

**Alternatives considered**:
- Sleep-based pacing (`sleep(cadence_s / speed_factor)`) — introduces real latency, flakiness,
  and test slowness with no correctness benefit for a simulation.
- Hybrid (sleep at 1×, no sleep at ≥10×) — unnecessary complexity; the spec explicitly states
  "no time.sleep() calls" after clarification.

---

## Decision 4 — Backpressure Timeout via Monotonic-Clock Elapsed Check

**Decision**: After each `yield`, the adapter records the wall-clock time before suspension
and checks elapsed time upon resumption. If `time.monotonic()` delta > `backpressure_timeout_s`,
raise `StreamAdapterError`.

**Implementation pattern**:
```python
t_yield = time.monotonic()
yield window_start, frames
elapsed = time.monotonic() - t_yield
if elapsed > self._config.backpressure_timeout_s:
    raise StreamAdapterError(
        f"Backpressure timeout: consumer held window for {elapsed:.1f}s "
        f"(limit={self._config.backpressure_timeout_s}s)"
    )
```

**Rationale**: In a synchronous generator, `yield` suspends the producer until `next()` is
called by the consumer. The elapsed time between suspension and resumption exactly equals
the consumer's hold time. No threading or `signal.alarm` required — the check is free.

**Alternatives considered**:
- Thread-based watchdog — heavyweight, introduces concurrency hazards.
- No timeout — violates FR-009 (configurable maximum backpressure wait).

---

## Decision 5 — End-of-Stream Pending Buffer Error

**Decision**: If the source is exhausted while the pending buffer (future-timestamp records)
is non-empty, raise `StreamAdapterError` with count and timestamp range of undeliverable
records.

**Rationale**: Silent discard violates P5. Flushing into a synthetic overflow window would
break the canonical-equivalence invariant (SC-001). A loud error surfaces the problem without
corrupting the store. The synthetic cohort has well-formed timestamps, so this path only fires
on genuinely pathological input.

---

## Decision 6 — LateArrivalWarning via `logging.warning()` + `late_arrival_count` Counter

**Decision**: Each excluded late record calls `logging.warning(...)` (structured fields:
adapter name, record timestamp, skew amount) and increments `adapter.late_arrival_count`.
CI asserts `adapter.late_arrival_count == 0` after synthetic cohort replay.

**Rationale**: Python `logging` integrates with pytest `caplog` for test inspection without
custom infrastructure. The counter provides a direct numeric assertion without log-string
parsing. Together they satisfy both FR-006 (must be logged) and FR-013 (CI must detect).

---

## Algorithm: Core `StreamAdapter.__iter__` Pseudocode

```
function __iter__():
    source_frames ← batch_adapter.load(source_config)

    for each table in source_frames:
        ts_col ← schema.table_contract(table).timestamp_column
        if ts_col == "":
            continue
        if any null in source_frames[table][ts_col]:
            raise StreamAdapterError("Null timestamp in table {table}")

    window_timeline ← sorted(unique(epoch_floor(ts, cadence_s)
                              for table in source_frames
                              for ts_col in [schema.table_contract(table).timestamp_column]
                              if ts_col != ""
                              for ts in source_frames[table][ts_col]))

    pending_buffer ← {}   # window_start → {table → [rows]}

    for window_start in window_timeline:
        window_frames ← {}

        for table in source_frames:
            ts_col ← schema.table_contract(table).timestamp_column
            pk     ← schema.table_contract(table).primary_key
            df     ← source_frames[table]

            if ts_col == "":
                in_window ← df if window_start == window_timeline[0] else empty DataFrame
                if pk:
                    in_window ← in_window.drop_duplicates(subset=pk, keep='last').sort_values(pk)
                window_frames[table] ← in_window.reset_index(drop=True)
                continue

            # Partition records for this window
            assigned_window ← epoch_floor(df[ts_col], cadence_s)
            in_window ← df[assigned_window == window_start]

            # Late arrivals (already past their window + tolerance)
            cutoff ← window_start - timedelta(seconds=skew_tolerance_s)
            late_mask ← assigned_window < cutoff
            for row in df[late_mask]:
                log LateArrivalWarning; late_arrival_count += 1

            # Future records: assigned to a window beyond current
            future_mask ← assigned_window > window_start
            add df[future_mask] to pending_buffer[future_window_start][table]

            # Release pending records for this window
            in_window ← concat(in_window, pending_buffer.pop(window_start, {}).get(table, []))

            # Dedup + sort
            if pk:
                in_window ← in_window.drop_duplicates(subset=pk, keep='last')
            in_window ← in_window.sort_values(ts_col).reset_index(drop=True)

            window_frames[table] ← in_window

        # Validate window before emission
        validate_schema(window_frames, schema)   # raises StreamAdapterError on failure

        # Backpressure check
        t_yield ← monotonic()
        yield (window_start, window_frames)
        if monotonic() - t_yield > backpressure_timeout_s:
            raise StreamAdapterError("Backpressure timeout")

    # End-of-stream pending buffer check
    if pending_buffer is non-empty:
        raise StreamAdapterError(f"{count} undeliverable records in pending buffer; "
                                 f"ts range=[{min_ts}, {max_ts}]")
```
