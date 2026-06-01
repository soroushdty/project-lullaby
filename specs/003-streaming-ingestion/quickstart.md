---
id:            QUICKSTART-003
title:         Streaming Ingestion Quickstart
status:        draft
version:       0.1.0
created:       2026-06-01
updated:       2026-06-01
author:        Soroush Dianaty
depends_on:    [SPEC-003, PLAN-003]
related:       [QUICKSTART-002]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Quickstart: Streaming Ingestion (SPEC-003)

---

## Prerequisites

- Python 3.11
- SPEC-001 (`LullabySchema`) and SPEC-002 (`BatchAdapter`, `FileAdapter`) implemented
- Bundled synthetic cohort available at `data/synthetic_cohort/`

No new dependencies required beyond those installed for SPEC-002.

---

## 1 — Stream the Synthetic Cohort (Accelerated Mode)

```python
from src.ingestion.adapters.file_adapter import FileAdapter, FileAdapterConfig
from src.ingestion.stream.adapter import StreamAdapter, StreamAdapterConfig
from src.ingestion.stream.accumulator import StreamAccumulator
from src.schemas.lullaby import LullabySchema

schema = LullabySchema()
batch_adapter = FileAdapter()
source_config = FileAdapterConfig(path="data/synthetic_cohort/")

stream_adapter = StreamAdapter(
    batch_adapter=batch_adapter,
    source_config=source_config,
    schema=schema,
    config=StreamAdapterConfig(cadence_s=60, speed_factor=100.0),
)

for window_start, frames in stream_adapter:
    print(f"Window {window_start}: {', '.join(f'{t}={len(df)}' for t, df in frames.items())}")

print(f"Late arrivals: {stream_adapter.late_arrival_count}")
```

---

## 2 — Accumulate All Windows into a Canonical Store

```python
stream_adapter = StreamAdapter(
    batch_adapter=FileAdapter(),
    source_config=FileAdapterConfig(path="data/synthetic_cohort/"),
    schema=schema,
    config=StreamAdapterConfig(speed_factor=100.0),
)

accumulated = StreamAccumulator.accumulate(stream_adapter, schema)

for table_name, df in accumulated.items():
    print(f"{table_name}: {len(df)} rows")
```

---

## 3 — CI Equivalence Check

```python
# Run in pytest (tests/integration/test_stream_equivalence.py)
batch_frames = FileAdapter().load(FileAdapterConfig(path="data/synthetic_cohort/"))

stream_adapter = StreamAdapter(
    batch_adapter=FileAdapter(),
    source_config=FileAdapterConfig(path="data/synthetic_cohort/"),
    schema=schema,
    config=StreamAdapterConfig(speed_factor=100.0),
)
accumulated = StreamAccumulator.accumulate(stream_adapter, schema)

assert stream_adapter.late_arrival_count == 0

for table in schema.table_names():
    pd.testing.assert_frame_equal(
        accumulated[table].sort_values(schema.table_contract(table).primary_key)
                          .reset_index(drop=True),
        batch_frames[table].sort_values(schema.table_contract(table).primary_key)
                           .reset_index(drop=True),
        check_like=True,
    )
```

---

## 4 — Running the Tests

```bash
# All streaming tests (tier 1 — no Docker required)
pytest tests/unit/test_stream_adapter_unit.py \
       tests/contract/test_stream_adapter_contract.py \
       tests/integration/test_stream_equivalence.py -v

# Full CI workflow
pytest tests/ -v --tb=short
```

---

## Failure Modes

| Symptom | Likely cause |
|---------|--------------|
| `StreamAdapterError: Null timestamp` | Source data has `NaT` in a timestamp column |
| `StreamAdapterError: Backpressure timeout` | Consumer is slow; increase `backpressure_timeout_s` or speed up processing |
| `StreamAdapterError: pending buffer` | Source contains records timestamped beyond the last window; check source data quality |
| `adapter.late_arrival_count > 0` on synthetic cohort | Bug in timestamp parsing or skew tolerance misconfigured |
