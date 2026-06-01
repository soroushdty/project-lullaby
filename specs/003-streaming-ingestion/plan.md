---
id:            PLAN-003
title:         Streaming Ingestion Implementation Plan
status:        draft
version:       0.1.0
created:       2026-06-01
updated:       2026-06-01
author:        Soroush Dianaty
depends_on:    [SPEC-003, SPEC-002, SPEC-001]
implements:    [P4, P5]
supersedes:    null
superseded_by: null
related:       [SPEC-003, SPEC-002, SPEC-001, PLAN-002]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Implementation Plan: Streaming Ingestion

**Branch**: `003-streaming-ingestion` | **Date**: 2026-06-01 | **Spec**: `specs/003-streaming-ingestion/spec.md`

**Input**: Feature specification from `specs/003-streaming-ingestion/spec.md`

## Summary

Implement a `StreamAdapter` generator class and companion `StreamAccumulator` helper under
`src/ingestion/stream/`. `StreamAdapter` wraps any existing `BatchAdapter` source, partitions
timestamped records into cadence-bounded windows using an event-timestamp-driven virtual
clock (no `time.sleep()` calls), emits no-timestamp static reference tables once, applies
per-window dedup and deterministic ordering, and exposes a synchronous Python generator
interface (`__iter__`) yielding `(window_start, dict[str, pd.DataFrame])` tuples.
`StreamAccumulator` consumes the generator and merges all windows into a final canonical
store with cross-window last-write-wins dedup. A CI equivalence job
asserts that the accumulated stream output is row-for-row equal to the batch load of the same
synthetic cohort and that `adapter.late_arrival_count == 0`.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**:
- `pandas` — DataFrame output contract (already in use)
- `pydantic` v2 — `StreamAdapterConfig` (extends `AdapterConfig` from SPEC-002)
- `pytest` — unit, contract, and integration tests

No new dependencies required. Streaming is implemented as an in-process simulation;
no message-queue, async, or concurrency libraries are needed.

**Storage**: In-memory DataFrames only; no persistence written by the adapter

**Testing**: pytest; all streaming tests are tier 1 (local, no external services, no Docker)

**Target Platform**: Linux/macOS + GitHub Actions

**Performance Goals**: CI equivalence job completes in <2 min against the bundled synthetic
cohort (SC-006); trivially satisfied because the virtual clock is event-driven with no
sleeping

**Constraints**:
- No `time.sleep()` calls in `StreamAdapter` (FR-011)
- No external services, Docker, or live data in any streaming test (NFR-003)
- `StreamAdapterError` must be raised before any partial output is returned (FR-008)
- `late_arrival_count` resets to 0 on adapter construction (not per-window)

**Scale/Scope**: 1 adapter class, 1 accumulator class, 3 contract files, 3 test modules;
five canonical tables; single-maintainer repo

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **P4 Source-Agnostic Ingestion**: PASS. `StreamAdapter` wraps the same `BatchAdapter`
  source interface as SPEC-002; downstream receives `dict[str, pd.DataFrame]` indistinguishable
  from batch output.
- **P5 Resilience / Graceful Degradation**: PASS. `StreamAdapterError` raised on
  corrupt/partial windows, null timestamps, backpressure timeout, and non-empty pending buffer
  at end-of-stream; no partial frames ever returned.
- **P1 Specification-Driven Development**: PASS. Every design decision maps to a SPEC-003
  FR/NFR or clarification bullet (Session 2026-06-01).
- **P3 Schema-Driven Extensibility**: PASS. Primary keys and timestamp columns read from
  `LullabySchema.table_contract` at runtime; no canonical names hardcoded.
- **Provenance / Traceability**: PASS. All artifacts carry YAML frontmatter with
  `depends_on: [SPEC-003, SPEC-002, SPEC-001]`.

## Project Structure

### Documentation (this feature)

```text
specs/003-streaming-ingestion/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── stream-adapter-interface.md
│   ├── stream-config-schema.md
│   └── stream-error-taxonomy.md
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code (repository root)

```text
src/
└── ingestion/
    └── stream/
        ├── __init__.py          # Public exports: StreamAdapter, StreamAdapterConfig,
        │                        #   StreamAccumulator, StreamAdapterError
        ├── adapter.py           # StreamAdapter generator class
        ├── accumulator.py       # StreamAccumulator helper
        └── errors.py            # StreamAdapterError (inherits BatchAdapterError)

tests/
├── unit/
│   └── test_stream_adapter_unit.py      # Per-scenario unit tests (mocked source)
├── contract/
│   └── test_stream_adapter_contract.py  # Generator protocol, error fields, config defaults
└── integration/
    └── test_stream_equivalence.py       # CI equivalence job (FR-013)

.github/workflows/
└── test-stream.yml              # Tier-1 CI: unit + contract + equivalence (no Docker)
```

**Structure Decision**: New `src/ingestion/stream/` subpackage, parallel to
`src/ingestion/adapters/`. Keeps batch and stream concerns cleanly separated.
`StreamAdapterError` inherits `BatchAdapterError` from `src/ingestion/adapters/base.py`
— the only cross-subpackage dependency.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None      | N/A        | N/A                                 |

## Post-Design Constitution Check

- **P4**: PASS. Generator interface makes stream output interchangeable with batch output at the
  `dict[str, pd.DataFrame]` boundary.
- **P5**: PASS. Backpressure timeout via monotonic-clock elapsed check after `yield`; null-ts
  and schema-invalid records raise before any frames escape.
- **P3**: PASS. `LullabySchema.table_contract(table).primary_key` and `.timestamp_column`
  drive all dedup and windowing logic.
- **P1**: PASS. Every class, field, and error condition maps to a SPEC-003 FR or clarification.
