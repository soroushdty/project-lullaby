---
id:            CONTRACT-003-CONFIG
title:         StreamAdapterConfig Schema
status:        draft
version:       0.1.0
created:       2026-06-01
updated:       2026-06-01
author:        Soroush Dianaty
depends_on:    [SPEC-003, PLAN-003]
related:       [CONTRACT-002-CONFIG]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Contract: StreamAdapterConfig Schema

**Module**: `src.ingestion.stream.adapter`

`StreamAdapterConfig` extends `AdapterConfig` (SPEC-002). Validated by pydantic v2.

---

## Fields

| Field | Type | Default | Pydantic constraint | Description |
|-------|------|---------|---------------------|-------------|
| `cadence_s` | `int` | `60` | `ge=1` | Window size in seconds. Each yielded window covers `[window_start, window_start + cadence_s)`. |
| `skew_tolerance_s` | `int` | `300` | `ge=0` | Late-arrival tolerance. Records with `event_ts < window_start - skew_tolerance_s` are excluded and logged. `0` means zero tolerance. |
| `speed_factor` | `float` | `1.0` | `gt=0` | Virtual clock multiplier. Stored and exposed; does not trigger any sleep calls. Typical values: `1.0`, `10.0`, `100.0`. |
| `backpressure_timeout_s` | `float` | `30.0` | `gt=0` | Maximum elapsed seconds between a window being yielded and the consumer calling `next()`. Exceeded → `StreamAdapterError`. |

Inherited from `AdapterConfig`:
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_attempts` | `int` | `3` | Retry attempts for the underlying `BatchAdapter.load()` call |
| `rate_limit_default_wait_s` | `int` | `60` | Default wait when `Retry-After` header is absent |

---

## Serialization

`StreamAdapterConfig` is a pydantic `BaseModel`. JSON round-trip is lossless.

```python
config = StreamAdapterConfig(cadence_s=60, speed_factor=100.0)
assert config.model_dump() == {
    "cadence_s": 60,
    "skew_tolerance_s": 300,
    "speed_factor": 100.0,
    "backpressure_timeout_s": 30.0,
    "max_attempts": 3,
    "rate_limit_default_wait_s": 60,
}
```
