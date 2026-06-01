---
id: CONTRACT-006-BOOLEAN
title: Domain Boolean Semantics Contract
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-006, SPEC-001, SPEC-003, SPEC-004A, SPEC-005]
implements: [P3, P5, P7]
supersedes: null
superseded_by: null
related: [SPEC-003, SPEC-004A, SPEC-005]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Contract: Domain Boolean Semantics

## Purpose

Define one shared interpretation for boolean-like domain fields across ingestion, simulator
diagnostics, EDA, and tests.

## Accepted Values

True tokens:

```text
True, 1, 1.0, "true", "t", "yes", "y"
```

False tokens:

```text
False, 0, 0.0, "false", "f", "no", "n"
```

Missing/unknown tokens:

```text
null, NaN, "", "missing", "unknown", "not_available", "na", "n/a"
```

All string tokens are trimmed and matched case-insensitively.

## Required Role Behavior

Invalid tokens in required roles are validation errors. The error must include:

- role or field name
- source column when available
- invalid token representation
- row reference when available

## Optional Role Behavior

Invalid tokens in optional roles are structured warnings. Downstream dashboards and diagnostics
must represent those cells as `Missing/Unknown`.

## Prohibited Behavior

Domain boolean-like fields must not be parsed with generic `.astype(bool)` truthiness when values
may originate from CSV, object-typed columns, or external source adapters.

## Required Consumers

- `src/ingestion/stream/adapter.py` for `_stream_pending`
- `src/simulation/export.py` diagnostics
- `src/visualization/eda_core.py` outcome prevalence, risk indicators, and engagement funnel
- Tests that assert boolean-derived rates or counts
