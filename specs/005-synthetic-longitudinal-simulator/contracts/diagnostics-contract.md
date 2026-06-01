---
id: CONTRACT-005-DIAGNOSTICS
title: Synthetic Simulator Diagnostics Contract
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-005, PLAN-005]
implements: [P2, P5, P7, P8]
supersedes: null
superseded_by: null
related: [SPEC-001, SPEC-004, SPEC-006, SPEC-008]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Contract: Synthetic Simulator Diagnostics

## Summary File

`simulation_summary.json`

## Top-Level Shape

```json
{
  "status": "pass",
  "ready_for_downstream": true,
  "seed": 20260601,
  "n_participants": 200,
  "study_days": 84,
  "output_dir": "data/synthetic/longitudinal",
  "schema_validation_status": "pass",
  "target_checks": [],
  "warnings": [],
  "errors": [],
  "synthetic_data": true,
  "generated_at_utc": "ISO-8601 timestamp"
}
```

## Diagnostic Check Shape

```json
{
  "name": "event_rate.cv_event",
  "required": true,
  "target": 0.075,
  "observed": 0.08,
  "tolerance": 0.03,
  "denominator": 200,
  "status": "pass",
  "details": {}
}
```

## Required Checks

- Event rates for cardiovascular events, heat illness, emergency department visits, and
  hospitalization.
- Archetype proportions.
- Aggregate wear-hours decline over study time.
- Aggregate scale-adherence decline over study time.
- Positive seven-day pre-event body-water trend for true or emerging CV cases with enough data.
- Heat-strain day body-water decrease with HR/temp increase more often than not.
- Non-random missingness by archetype, heat exposure, adherence, and worsening state.
- Overlap cases remain imperfectly separable by body-water direction.
- Schema validation status.

## Readiness Rules

- Any failed required check sets `status="fail"` and `ready_for_downstream=false`.
- Warnings may set `status="warn"` only when all required checks pass.
- Failed runs must keep artifacts inspectable.
- Each check records denominator and coverage so missingness cannot hide weak evidence.

## Tolerances

- Default N=200 event rates: absolute tolerance 0.03.
- Default N=200 archetype proportions: absolute tolerance 0.05.
- Larger cohorts use tighter tolerance documented in the generated summary.
