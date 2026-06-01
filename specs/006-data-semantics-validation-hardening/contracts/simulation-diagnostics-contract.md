---
id: CONTRACT-006-DIAGNOSTICS
title: Simulation Diagnostics Hardening Contract
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-006, SPEC-005]
implements: [P5, P7, P9]
supersedes: null
superseded_by: null
related: [SPEC-005]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Contract: Simulation Diagnostics Hardening

## Purpose

Ensure simulator diagnostics produce the same counts and rates for equivalent native-boolean,
CSV-loaded, and object/string boolean inputs.

## Required Diagnostic Consumers

The shared boolean semantics parser must be used for:

- cardiovascular event rate
- heat illness rate
- emergency department visit rate
- hospitalization rate
- scale adherence decline
- cardiovascular event window checks
- heat strain day checks
- missingness by worsening physiologic state

## Missing Values

Missing values must remain missing for diagnostic denominators that explicitly disclose coverage.
Diagnostics may exclude missing values from a rate only when the denominator is reported.

## Invalid Tokens

Invalid tokens in required diagnostic fields fail readiness diagnostics with a clear error.
Optional diagnostic fields may warn and treat invalid tokens as `Missing/Unknown`.

## Tests

Focused tests must compare native-boolean and CSV/string-boolean inputs and assert equivalent
diagnostic results.
