---
id: SPEC-003
title: Streaming Ingestion
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-001, SPEC-002]
implements: [P4, P5]
supersedes: null
superseded_by: null
related: [SPEC-001, SPEC-002]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Feature Specification: Streaming Ingestion

**Feature Branch**: `003-streaming-ingestion`

**Created**: 2026-06-01

**Status**: Draft

**Input**: User description: "SPEC-003 · Streaming Ingestion — real-time (sync) ingestion with 1-minute base granularity, landing in the same canonical schema so batch and stream are indistinguishable downstream. Simulated real-time stream adapter (reference implementation) that replays the synthetic cohort at configurable cadence; duplicate / out-of-order / late records deduped and ordered by timestamp; clock skew tolerated within a declared window; backpressure / partial-record handling fails loud, never corrupts the store. Acceptance: streamed replay produces a canonical store equivalent to the batch load of the same data; ordering and dedup verified in CI."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Stream Replay: Canonical Equivalence (Priority: P1)

A data engineer starts the stream adapter pointing at the bundled synthetic cohort. The adapter replays the data at a configurable cadence (default: 1-minute windows). After all windows are consumed and accumulated, the resulting canonical store is row-for-row equivalent to a batch load of the same source data.

**Why this priority**: This is the core correctness invariant — "batch and stream indistinguishable downstream" is the foundational promise of the streaming layer. Without it, no downstream component can trust the stream.

**Independent Test**: Run the stream adapter in accelerated mode against the bundled synthetic cohort; accumulate all emitted windows; assert the accumulated frames equal the batch-loaded frames. No external services required.

**Acceptance Scenarios**:
1. **Given** the bundled synthetic cohort, **when** the stream adapter runs at 100× accelerated cadence and all windows are consumed, **then** the accumulated canonical store is row-for-row equal to the batch-loaded canonical store for all five tables.
2. **Given** a single-table synthetic source, **when** the stream adapter runs and the consumer pulls all windows, **then** the accumulated table passes `LullabySchema` validation with exit code 0.
3. **Given** a source with all records in a single minute-window, **when** the stream adapter runs, **then** exactly one window is emitted containing all records.

---

### User Story 2 — Deduplication and Ordering (Priority: P2)

A data engineer feeds the stream adapter a source containing duplicate records (same primary key) and out-of-order records (earlier event timestamps arriving after later ones). The adapter deduplicates by primary key and sorts by canonical timestamp within each window before emitting.

**Why this priority**: Dedup and ordering are the correctness guarantees that make the accumulated canonical store equivalent to the batch load. Without them, the P1 invariant cannot hold.

**Independent Test**: Inject a synthetic stream with known duplicates and inversions; assert the emitted window contains exactly the expected deduplicated, timestamp-ordered rows.

**Acceptance Scenarios**:
1. **Given** a window containing two records with the same primary key and different field values, **when** the adapter emits the window, **then** exactly one record is present (last-write-wins, matching SPEC-002 dedup semantics).
2. **Given** a window containing records with event timestamps in reverse order, **when** the adapter emits the window, **then** the emitted DataFrame is sorted ascending by the canonical timestamp column.
3. **Given** a stream with duplicates across two consecutive windows (same primary key in both), **when** both windows are accumulated, **then** the accumulated store contains exactly one row for that primary key.

---

### User Story 3 — Late-Arrival Tolerance (Priority: P2)

A data coordinator's device has clock drift. Records are emitted with event timestamps up to a declared tolerance (default: 5 minutes) behind the current stream clock. The adapter accepts and integrates these late records into their target time window. Records arriving beyond the tolerance are excluded and logged.

**Why this priority**: Clock skew is a physical reality in a monitoring scenario. Silent exclusion of late data would corrupt the canonical store without warning; rejection with a log surfaces the issue while keeping the store clean.

**Independent Test**: Inject records timestamped at varying offsets from the current stream clock; verify accepted records appear in the correct window and rejected records are logged and excluded.

**Acceptance Scenarios**:
1. **Given** a record whose event timestamp is 3 minutes behind the current stream clock and a 5-minute tolerance, **when** the adapter processes the record, **then** the record is accepted into its correct target window.
2. **Given** a record whose event timestamp is 7 minutes behind the current stream clock and a 5-minute tolerance, **when** the adapter processes the record, **then** the record is excluded from all windows and a `LateArrivalWarning` is logged with the record's timestamp and the skew amount.
3. **Given** a record with a future timestamp (clock skew forward), **when** the adapter processes the record, **then** the record is held until its target window opens — it is never dropped silently.

---

### User Story 4 — Backpressure and Partial-Record Failure (Priority: P3)

The downstream consumer is slower than the producer, or a record in the current window is malformed or schema-invalid. The adapter blocks on backpressure without dropping records. On a partial or corrupt window it raises immediately, emits nothing for that window, and leaves the canonical store uncorrupted.

**Why this priority**: P5 (Resilience) — silent data loss or corrupt partial writes are more dangerous than a loud failure. This story protects the integrity of every window.

**Independent Test**: Inject a window containing one valid and one schema-invalid record; assert `StreamAdapterError` is raised, no partial output is returned, and the store remains in its pre-window state.

**Acceptance Scenarios**:
1. **Given** a window with a schema-invalid record (missing required column), **when** the adapter processes the window, **then** `StreamAdapterError` is raised before any rows are written, and no partial frames are returned.
2. **Given** a consumer that pauses mid-stream, **when** the producer reaches its buffer limit, **then** the producer blocks (does not drop or skip records) until the consumer resumes.
3. **Given** a window where backpressure causes a timeout beyond a configurable maximum wait, **when** the timeout elapses, **then** `StreamAdapterError` is raised with the reason; the window is abandoned and the store is unchanged.

---

### User Story 5 — CI Equivalence Verification (Priority: P1)

A CI job runs the stream adapter over the bundled synthetic cohort in accelerated mode and compares the accumulated canonical store to the batch load of the same data. The job fails if the stores differ or if the stream emits any `LateArrivalWarning` for the synthetic cohort (which has well-formed timestamps).

**Why this priority**: The CI job is the automated proof of the core invariant. Without it, the P1 correctness guarantee degrades to "works on my machine."

**Independent Test**: Run as a standalone pytest job; no external services, no Docker. Completes in under 2 minutes.

**Acceptance Scenarios**:
1. **Given** the bundled synthetic cohort, **when** the CI equivalence job runs, **then** all five accumulated canonical tables are row-for-row equal to the batch-loaded tables and the job exits 0.
2. **Given** a deliberate mutation to one record in the stream source, **when** the CI equivalence job runs, **then** the job detects the discrepancy and exits non-zero with a diagnostic identifying the differing table and row count.
3. **Given** any `LateArrivalWarning` emitted during the synthetic cohort replay, **when** the CI job runs, **then** the job fails — because the synthetic cohort has well-formed timestamps and late arrivals indicate a bug.

---

### Edge Cases

- A cadence interval containing zero timestamped records and no static-table emission MUST be emitted as an empty `dict[str, pd.DataFrame]` — not skipped — so consumers can detect gaps.
- A schema table with `timestamp_column == ""` MUST be treated as static reference data: deduplicated by primary key, emitted once in the first stream window, included in the accumulated canonical store, and not repeated in later windows.
- A record whose event timestamp column is null or unparseable MUST raise `StreamAdapterError` for that window — it cannot be silently assigned to any window.
- The synthetic cohort timestamps may not span multiple natural 1-minute windows; the adapter MUST support a virtual-clock mode (accelerated replay) driven purely by event timestamps — window boundaries advance with the data, not wall-clock time, and no `time.sleep()` calls are made.
- Stream replay from the same source twice MUST produce the same sequence of windows (deterministic).
- If the source is exhausted while the pending buffer (future-timestamp records) is non-empty, `StreamAdapterError` MUST be raised with the count of undeliverable records and their timestamp range — silent discard is not permitted.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a `StreamAdapter` reference implementation that consumes the same source types as `BatchAdapter` (SPEC-002) and emits canonical `dict[str, pd.DataFrame]` windows on a configurable cadence (default: 60-second windows). `StreamAdapter` MUST implement `__iter__`, yielding `(window_start: datetime, frames: dict[str, pd.DataFrame])` tuples; consumers iterate with a standard `for` loop.
- **FR-002**: The `StreamAdapter` MUST produce output conforming to the same `LullabySchema` canonical contract as batch adapters — downstream pipeline receives no indication of whether data arrived via batch or stream.
- **FR-003**: Each emitted window MUST be deduplicated by schema-defined primary keys (read from `LullabySchema.table_contract` at runtime, matching SPEC-002 dedup semantics; last-write-wins).
- **FR-004**: Records within each window MUST be sorted ascending by the table's canonical timestamp column before emission. Tables without a timestamp column MUST be sorted deterministically by primary key.
- **FR-005**: The `StreamAdapter` MUST accept a configurable clock-skew tolerance (default: 300 seconds); records whose event timestamp falls within the tolerance behind the current stream clock MUST be accepted into their correct target window.
- **FR-006**: Records whose event timestamp falls beyond the declared skew tolerance MUST be excluded from all windows; a `LateArrivalWarning` MUST be emitted via `logging.warning(...)` per excluded record (adapter name, record timestamp, skew amount) and the adapter's `late_arrival_count` counter MUST be incremented. This is non-fatal.
- **FR-007**: Records with a future event timestamp MUST be held in a pending buffer until their target window opens — they MUST NOT be dropped or assigned to an incorrect window. If the source is exhausted while the pending buffer is non-empty (records whose target window never opened), `StreamAdapterError` MUST be raised with the count of undeliverable records and their timestamp range.
- **FR-008**: A window containing any malformed, schema-invalid, or null-timestamp record MUST cause `StreamAdapterError` to be raised before any frames are returned; the canonical store MUST remain uncorrupted.
- **FR-009**: When the consumer is slower than the producer (backpressure), the producer MUST block until the consumer resumes; it MUST NOT drop records or buffer without bound. A configurable maximum backpressure wait (default: 30 seconds) triggers `StreamAdapterError` on timeout.
- **FR-010**: An empty window (no records in the interval and no static-table emission) MUST be emitted as an empty `dict[str, pd.DataFrame]` — not silently skipped. Non-empty windows MUST include one key per schema table; tables with no rows in that interval are represented as empty DataFrames with schema columns.
- **FR-011**: The `StreamAdapter` MUST support a configurable speed factor (default: 1×; also: 10×, 100×) for replay configuration compatibility. Window boundaries are computed from event timestamp ranges and `cadence_s`, not wall-clock time or `speed_factor`. No `time.sleep()` calls are made. Event timestamps in emitted frames are never altered.
- **FR-012**: Re-running the `StreamAdapter` with the same source and config MUST produce the same sequence of windows (deterministic replay).
- **FR-013**: A CI equivalence job MUST run the `StreamAdapter` over the bundled synthetic cohort, use `StreamAccumulator` to merge all windows into a final canonical store, and assert that the result equals the batch load of the same data. The job MUST assert `adapter.late_arrival_count == 0` after replay — any non-zero value fails the job.

### Non-Functional Requirements

- **NFR-001**: The streaming canonical output is semantically identical to batch output — downstream validation, dedup, and schema checks are unchanged.
- **NFR-002**: No secrets appear in logs or exception messages.
- **NFR-003**: The `StreamAdapter` and its CI job are independently testable without external services, Docker, or live data sources.

### Key Entities

- **StreamAdapter**: A Python generator (`__iter__` / `yield`) that produces an ordered sequence of `(window_start, dict[str, pd.DataFrame])` tuples at a fixed cadence. Consumers iterate with `for window_start, frames in adapter`. Wraps any compatible source.
- **StreamAdapterConfig**: Cadence, skew tolerance, speed factor, backpressure timeout — all configurable with defaults.
- **StreamWindow**: A time-bounded slice of incoming records for one cadence interval; includes dedup, ordering, and skew-filtering before emission.
- **LateArrivalWarning**: A non-fatal event emitted via `logging.warning(...)` recording an excluded record's timestamp, skew amount, and adapter name. The adapter exposes `late_arrival_count: int` (incremented per exclusion) for programmatic assertion in CI.
- **StreamAdapterError**: Raised on partial/corrupt window, null timestamps, or backpressure timeout. Inherits from `BatchAdapterError` (SPEC-002).
- **StreamAccumulator**: A provided helper class that consumes a `StreamAdapter` generator, merges all emitted windows into a final `dict[str, pd.DataFrame]`, and applies cross-window deduplication (last-write-wins by primary key). Used by the CI equivalence job and any caller that needs the fully-accumulated canonical store.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The accumulated canonical store from a full synthetic-cohort stream replay is row-for-row equal to the batch load of the same data for all five canonical tables — verified by the CI equivalence job.
- **SC-002**: A stream containing N duplicate records for the same primary key produces exactly 1 row for that key in the accumulated canonical store.
- **SC-003**: Out-of-order records within the skew tolerance window appear in their correct target window — verified by injecting records with known timestamp offsets.
- **SC-004**: Records arriving beyond the skew tolerance are excluded without corrupting the canonical store; each exclusion produces exactly one `LateArrivalWarning` log entry.
- **SC-005**: A window containing one schema-invalid record raises `StreamAdapterError` and returns no frames — verified by test.
- **SC-006**: The CI equivalence job completes in under 2 minutes against the bundled synthetic cohort.

---

## Assumptions

- "Batch and stream indistinguishable downstream" means the final accumulated canonical store (after all windows have been consumed and merged) equals the batch-loaded store — not that individual windows equal individual batches.
- The `StreamAdapter` is a reference/simulation implementation (in-process replay); it does not integrate with Kafka, Spark, or any external streaming platform.
- Clock skew tolerance applies to event timestamps carried in the data, not to wall-clock ingestion time.
- The synthetic cohort's timestamped canonical tables (`participants`, `daily_vitals`, `alerts`, `clinical_outcomes`) have timestamps spanning at least one 1-minute window in virtual-clock accelerated mode; `staff_contacts` is static reference data with no timestamp column.
- The `StreamAdapter` wraps the same source interface as `BatchAdapter` (SPEC-002) — it does not define new source connectors.
- Primary keys and timestamp columns are read from `LullabySchema.table_contract` at runtime, never hardcoded, consistent with P3 (Schema-Driven Extensibility).

---

## Clarifications

### Session 2026-06-01

- Q: What is the Python interface for consuming StreamAdapter windows — generator, explicit pull, callback, or async? → A: Python generator (`__iter__` / `yield`); consumers iterate with `for window_start, frames in adapter`.
- Q: Who accumulates emitted windows into the final canonical store — a provided helper, a method on the adapter, or the caller? → A: `StreamAccumulator` provided helper class; consumes the generator and merges all windows with cross-window last-write-wins dedup.
- Q: What happens at end-of-stream if the future-timestamp pending buffer is non-empty? → A: Raise `StreamAdapterError` with the count of undeliverable records and their timestamp range.
- Q: How does CI detect and assert on `LateArrivalWarning` events? → A: `logging.warning(...)` per exclusion + `adapter.late_arrival_count` counter; CI asserts `adapter.late_arrival_count == 0`.
- Q: Does the speed factor use wall-clock sleeping or event-timestamp-driven virtual clock? → A: Event-timestamp-driven virtual clock; window boundaries derived from data timestamps, no `time.sleep()` calls.
