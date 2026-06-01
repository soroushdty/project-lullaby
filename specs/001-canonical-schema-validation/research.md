---
id:            PLAN-001-RESEARCH
title:         Research Notes - Canonical Schema & Validation
status:        draft
version:       0.1.0
created:       2026-06-01
updated:       2026-06-01
author:        Soroush Dianaty
depends_on:    [SPEC-001]
implements:    [P3, P5]
supersedes:    null
superseded_by: null
related:       [PLAN-001]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Research: Canonical Schema & Validation

## Decision: Use Python ABC for canonical schema contract
Rationale: Native abstract base classes provide an explicit, enforceable contract for
required table definitions and schema metadata while staying lightweight for users writing
custom schema subclasses.
Alternatives considered: `typing.Protocol` only (too permissive at runtime); concrete base
class with no abstract methods (insufficient guarantees).

## Decision: Use Pandera as primary validation engine
Rationale: Pandera integrates directly with pandas workflows, produces granular constraint
errors, and supports dataframe-level and column-level checks that align with ingestion
boundary validation.
Alternatives considered: Great Expectations only (strong for data docs, but heavier for
runtime in-process enforcement); custom validators (high maintenance and lower clarity).

## Decision: Treat cadence as explicit data column/metadata
Rationale: Carrying cadence in data enables moving from daily to higher-frequency streams
without branching code paths, consistent with the time-series-first principle.
Alternatives considered: hardcoded cadence constants in code (not extensible);
per-adapter logic flags (drifts behavior across sources).

## Decision: Enforce no-imputation rule at ingestion boundary
Rationale: Preserving informative missingness protects downstream clinical interpretation
and follows resilience guidance to fail loud rather than mutate input silently.
Alternatives considered: auto-fill defaults during ingestion (masks data quality issues);
late imputation in ingestion adapters (inconsistent outcomes).

## Decision: CI gate for bundled data validation
Rationale: A dedicated `validate-schema` workflow guarantees reproducibility and blocks
schema regressions before merge.
Alternatives considered: local-only validation (not enforceable); periodic validation job
without PR blocking (slow feedback).
