---
id:            PLAN-003-TASKS
title:         Tasks - Streaming Ingestion
status:        draft
version:       0.1.0
created:       2026-06-01
updated:       2026-06-01
author:        Soroush Dianaty
depends_on:    [SPEC-003, PLAN-003, SPEC-002, SPEC-001]
implements:    [P4, P5]
supersedes:    null
superseded_by: null
related:       [DATA-MODEL-003, RESEARCH-003, CONTRACT-003-INTERFACE, CONTRACT-003-CONFIG, CONTRACT-003-ERRORS]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Tasks: Streaming Ingestion (SPEC-003)

**Input**: Design documents from `specs/003-streaming-ingestion/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Note**: Test tasks are included because SPEC-003 explicitly requires CI equivalence, ordering, deduplication, late-arrival, and loud-failure verification.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (independent files, no incomplete dependencies)
- **[Story]**: User story this task belongs to (US1-US5)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the stream package, test modules, and CI shell expected by the plan.

- [x] T001 Create stream package skeleton in `src/ingestion/stream/__init__.py`, `src/ingestion/stream/adapter.py`, `src/ingestion/stream/accumulator.py`, and `src/ingestion/stream/errors.py`
- [x] T002 [P] Create streaming test module skeletons in `tests/unit/test_stream_adapter_unit.py`, `tests/contract/test_stream_adapter_contract.py`, and `tests/integration/test_stream_equivalence.py`
- [x] T003 [P] Create tier-1 streaming CI workflow skeleton in `.github/workflows/test-stream.yml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared config, exception, timestamp, schema-validation, and fixture helpers used by every story.

**CRITICAL**: No user story work should begin until this phase is complete.

- [x] T004 Define `StreamAdapterError` inheriting `BatchAdapterError` in `src/ingestion/stream/errors.py`
- [x] T005 Define `StreamAdapterConfig` extending `AdapterConfig` with `cadence_s`, `skew_tolerance_s`, `speed_factor`, and `backpressure_timeout_s` constraints in `src/ingestion/stream/adapter.py`
- [x] T006 Implement internal timestamp parsing and epoch-floor window helper functions in `src/ingestion/stream/adapter.py`
- [x] T007 Implement internal schema validation wrapper that converts validation failures to `StreamAdapterError` before emission in `src/ingestion/stream/adapter.py`
- [x] T008 [P] Add reusable in-memory batch adapter and minimal timestamped schema fixtures in `tests/unit/test_stream_adapter_unit.py`
- [x] T009 [P] Write contract tests for `StreamAdapterConfig` defaults, pydantic constraints, JSON round-trip, and `StreamAdapterError` inheritance in `tests/contract/test_stream_adapter_contract.py`

**Checkpoint**: Foundation ready. Stream stories can be implemented and tested independently.

---

## Phase 3: User Story 1 - Stream Replay: Canonical Equivalence (Priority: P1) MVP

**Goal**: Replay bundled synthetic data as cadence-bounded windows and accumulate it into a canonical store equivalent to batch output.

**Independent Test**: `pytest tests/integration/test_stream_equivalence.py -k synthetic_equivalence -v` passes with all five canonical tables row-for-row equal.

### Tests for User Story 1

- [x] T010 [US1] Write contract test for `StreamAdapter.__iter__` yielding `(window_start, frames)` tuples in ascending order in `tests/contract/test_stream_adapter_contract.py`
- [x] T011 [US1] Write contract tests for single-minute source emission, empty interval `{}` emission, non-empty window schema keys, and no-timestamp static table emission in `tests/contract/test_stream_adapter_contract.py`
- [x] T012 [P] [US1] Write integration test for accelerated synthetic replay accumulated equivalence against `FileAdapter` batch load in `tests/integration/test_stream_equivalence.py`
- [x] T013 [P] [US1] Write unit tests for deterministic replay and `speed_factor` not changing window starts, frames, or emitted timestamps in `tests/unit/test_stream_adapter_unit.py`

### Implementation for User Story 1

- [x] T014 [US1] Implement `StreamAdapter` constructor and `batch_adapter.load(source_config)` startup path in `src/ingestion/stream/adapter.py`
- [x] T015 [US1] Implement event-timestamp-driven virtual clock timeline with no `time.sleep()` calls in `src/ingestion/stream/adapter.py`
- [x] T016 [US1] Implement per-window frame assembly for timestamped tables and no-timestamp static tables, including empty DataFrames with schema columns for non-empty windows in `src/ingestion/stream/adapter.py`
- [x] T017 [US1] Implement empty interval `{}` emission across cadence gaps between first and last event windows in `src/ingestion/stream/adapter.py`
- [x] T018 [P] [US1] Implement `StreamAccumulator.accumulate(adapter, schema)` concatenation and schema-table completion in `src/ingestion/stream/accumulator.py`
- [x] T019 [US1] Export `StreamAdapter`, `StreamAdapterConfig`, `StreamAccumulator`, and `StreamAdapterError` in `src/ingestion/stream/__init__.py`

**Checkpoint**: US1 passes independently and proves the batch/stream canonical boundary.

---

## Phase 4: User Story 5 - CI Equivalence Verification (Priority: P1)

**Goal**: Add a no-Docker CI proof that streaming synthetic replay equals batch load and has zero late arrivals.

**Independent Test**: `pytest tests/integration/test_stream_equivalence.py -v` exits 0 locally in under 2 minutes.

### Tests for User Story 5

- [x] T020 [US5] Add integration assertion that synthetic replay leaves `stream_adapter.late_arrival_count == 0` in `tests/integration/test_stream_equivalence.py`
- [x] T021 [US5] Add integration assertion that synthetic replay emits no late-arrival warning logs in `tests/integration/test_stream_equivalence.py`
- [x] T022 [US5] Add deliberate mutation test that reports the differing table and row-count diagnostic on stream/batch mismatch in `tests/integration/test_stream_equivalence.py`

### Implementation for User Story 5

- [x] T023 [P] [US5] Configure `.github/workflows/test-stream.yml` to run `tests/unit/test_stream_adapter_unit.py`, `tests/contract/test_stream_adapter_contract.py`, and `tests/integration/test_stream_equivalence.py` with a CI timeout that enforces SC-006
- [x] T024 [US5] Add CI-friendly equality helper for sorted canonical DataFrame comparisons in `tests/integration/test_stream_equivalence.py`

**Checkpoint**: US5 can fail CI on stream/batch drift or unexpected late arrivals.

---

## Phase 5: User Story 2 - Deduplication and Ordering (Priority: P2)

**Goal**: Deduplicate by schema-defined primary keys and sort records by each table's canonical timestamp within emitted windows and accumulated stores.

**Independent Test**: `pytest tests/unit/test_stream_adapter_unit.py -k "dedup or ordering" -v` passes with duplicates and inversions injected.

### Tests for User Story 2

- [x] T025 [US2] Write unit test for per-window duplicate primary key last-write-wins behavior in `tests/unit/test_stream_adapter_unit.py`
- [x] T026 [US2] Write unit test for ascending timestamp order within emitted timestamped-table windows and primary-key ordering for static no-timestamp tables in `tests/unit/test_stream_adapter_unit.py`
- [x] T027 [US2] Write unit test for cross-window duplicate primary key collapse in `StreamAccumulator` in `tests/unit/test_stream_adapter_unit.py`

### Implementation for User Story 2

- [x] T028 [US2] Implement schema-driven per-window `drop_duplicates(..., keep="last")` by table primary key in `src/ingestion/stream/adapter.py`
- [x] T029 [US2] Implement schema-driven per-window timestamp sorting with reset index in `src/ingestion/stream/adapter.py`
- [x] T030 [P] [US2] Implement schema-driven cross-window last-write-wins deduplication and timestamp sorting in `src/ingestion/stream/accumulator.py`

**Checkpoint**: US2 passes independently with duplicates and out-of-order records.

---

## Phase 6: User Story 3 - Late-Arrival Tolerance (Priority: P2)

**Goal**: Accept records within skew tolerance, reject beyond-tolerance late records with warnings, and hold future records until their target window opens.

**Independent Test**: `pytest tests/unit/test_stream_adapter_unit.py -k "late or future or pending" -v` passes.

### Tests for User Story 3

- [x] T031 [US3] Write unit test for within-tolerance late record acceptance into the correct target window in `tests/unit/test_stream_adapter_unit.py`
- [x] T032 [US3] Write unit test for beyond-tolerance exclusion, `logging.warning(...)`, and `late_arrival_count` increment in `tests/unit/test_stream_adapter_unit.py`
- [x] T033 [US3] Write unit test for future timestamp buffering until the target window opens in `tests/unit/test_stream_adapter_unit.py`
- [x] T034 [US3] Write unit test for non-empty pending buffer end-of-stream `StreamAdapterError` with count and timestamp range in `tests/unit/test_stream_adapter_unit.py`

### Implementation for User Story 3

- [x] T035 [US3] Implement skew-tolerance comparison and beyond-tolerance late-arrival exclusion in `src/ingestion/stream/adapter.py`
- [x] T036 [US3] Implement structured late-arrival warning logging and cumulative `late_arrival_count` in `src/ingestion/stream/adapter.py`
- [x] T037 [US3] Implement future timestamp pending buffer release by target window in `src/ingestion/stream/adapter.py`
- [x] T038 [US3] Implement end-of-stream pending buffer error with undeliverable record count and timestamp range in `src/ingestion/stream/adapter.py`

**Checkpoint**: US3 passes independently and late/future timestamp behavior is explicit.

---

## Phase 7: User Story 4 - Backpressure and Partial-Record Failure (Priority: P3)

**Goal**: Block naturally on synchronous generator backpressure, time out slow consumers, and fail before corrupt or partial windows escape.

**Independent Test**: `pytest tests/unit/test_stream_adapter_unit.py -k "backpressure or partial or timestamp" -v` passes.

### Tests for User Story 4

- [x] T039 [US4] Write unit test for null timestamp raising `StreamAdapterError` before any window yield in `tests/unit/test_stream_adapter_unit.py`
- [x] T040 [US4] Write unit test for unparseable timestamp raising `StreamAdapterError` before any window yield in `tests/unit/test_stream_adapter_unit.py`
- [x] T041 [US4] Write unit test for schema-invalid window raising `StreamAdapterError` with no partial output in `tests/unit/test_stream_adapter_unit.py`
- [x] T042 [US4] Write unit tests using monkeypatched `time.monotonic()` for below-timeout consumer continuation with no dropped records and above-timeout backpressure failure after a yielded window in `tests/unit/test_stream_adapter_unit.py`

### Implementation for User Story 4

- [x] T043 [US4] Implement null and unparseable timestamp detection before window assembly in `src/ingestion/stream/adapter.py`
- [x] T044 [US4] Implement all-or-nothing window validation before yielding frames in `src/ingestion/stream/adapter.py`
- [x] T045 [US4] Implement generator backpressure elapsed-time check after `yield` using `time.monotonic()` in `src/ingestion/stream/adapter.py`
- [x] T046 [P] [US4] Ensure stream errors never include secrets or raw credential values in `src/ingestion/stream/errors.py`

**Checkpoint**: US4 passes independently and corrupt input cannot mutate the accumulated store silently.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, release traceability, and full validation.

- [x] T047 [P] Reconcile quickstart imports and commands with the implemented API in `specs/003-streaming-ingestion/quickstart.md`
- [x] T048 [P] Add SPEC-003 changelog entry with `Date`, `Spec`, `Summary`, `Rationale`, `Impact`, and `Targets` in `CHANGELOG.md`
- [x] T049 Run focused streaming test suite for `tests/unit/test_stream_adapter_unit.py`, `tests/contract/test_stream_adapter_contract.py`, and `tests/integration/test_stream_equivalence.py`, confirming the equivalence job completes under 2 minutes
- [x] T050 Run full regression suite for `tests/` and confirm SPEC-001/SPEC-002 behavior still passes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies; start immediately.
- **Phase 2 (Foundational)**: Depends on Phase 1; blocks every user story.
- **Phase 3 (US1)**: Depends on Phase 2; provides the MVP stream/accumulator path.
- **Phase 4 (US5)**: Depends on US1; proves the MVP in CI.
- **Phase 5 (US2)**: Depends on Phase 2; can run after or alongside US1 once base iteration exists.
- **Phase 6 (US3)**: Depends on Phase 2 and the US1 window loop.
- **Phase 7 (US4)**: Depends on Phase 2 and the US1 window loop.
- **Phase 8 (Polish)**: Depends on all desired user stories being complete.

### User Story Dependencies

| Story | Priority | Depends On | Can Parallelize With |
|---|---:|---|---|
| US1 - Stream Replay | P1 | Phase 2 | None for MVP |
| US5 - CI Equivalence | P1 | US1 | US2/US3/US4 tests after MVP path exists |
| US2 - Dedup and Ordering | P2 | Phase 2, US1 window loop | US3 and US4 |
| US3 - Late Arrival | P2 | Phase 2, US1 window loop | US2 and US4 |
| US4 - Backpressure and Partial Failure | P3 | Phase 2, US1 window loop | US2 and US3 |

### Within Each User Story

- Write story tests first and confirm they fail.
- Implement the narrowest code needed for that story.
- Run the story's independent test command.
- Move to the next story only after the checkpoint passes.

---

## Parallel Execution Examples

### Phase 1

```bash
Task T002: Create tests/unit/test_stream_adapter_unit.py, tests/contract/test_stream_adapter_contract.py, tests/integration/test_stream_equivalence.py
Task T003: Create .github/workflows/test-stream.yml
```

### Phase 2

```bash
Task T004: StreamAdapterError in src/ingestion/stream/errors.py
Task T008: Unit fixtures in tests/unit/test_stream_adapter_unit.py
Task T009: Contract tests in tests/contract/test_stream_adapter_contract.py
```

### User Story 1

```bash
Task T012: Synthetic equivalence test in tests/integration/test_stream_equivalence.py
Task T013: Deterministic replay test in tests/unit/test_stream_adapter_unit.py
Task T018: StreamAccumulator implementation in src/ingestion/stream/accumulator.py
```

### User Story 2

```bash
Task T028: Per-window dedup in src/ingestion/stream/adapter.py
Task T030: Cross-window accumulator dedup in src/ingestion/stream/accumulator.py
```

### Final Polish

```bash
Task T047: Quickstart reconciliation in specs/003-streaming-ingestion/quickstart.md
Task T048: Changelog entry in CHANGELOG.md
```

---

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 (US1) only.
3. Validate with `pytest tests/integration/test_stream_equivalence.py -k synthetic_equivalence -v`.
4. Stop and review the canonical equivalence result before broadening behavior.

### Incremental Delivery

1. US1: stream replay and accumulation equivalence.
2. US5: CI proof for the synthetic cohort.
3. US2: deduplication and ordering edge cases.
4. US3: late and future timestamp behavior.
5. US4: backpressure and all-or-nothing failure paths.
6. Phase 8: quickstart, changelog, and regression verification.

### Validation Commands

```bash
pytest tests/unit/test_stream_adapter_unit.py -v
pytest tests/contract/test_stream_adapter_contract.py -v
pytest tests/integration/test_stream_equivalence.py -v
pytest tests/ -v --tb=short
```

---

## Notes

- `[P]` tasks touch independent files and have no incomplete task dependencies.
- Stream output must use `schema.table_contract(table).primary_key` and `.timestamp_column`; never hardcode canonical table-specific behavior.
- `speed_factor` is stored and validated but must not cause sleeping.
- `staff_contacts` has no timestamp column in the current schema; implementation must handle no-timestamp tables deterministically rather than inventing timestamps.
- A window with no records is emitted as an empty `dict[str, pd.DataFrame]` only when no canonical table has records for that interval; otherwise each schema table key maps to a DataFrame, possibly empty.
