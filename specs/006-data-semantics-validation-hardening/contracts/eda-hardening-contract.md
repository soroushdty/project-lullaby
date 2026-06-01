---
id: CONTRACT-006-EDA
title: EDA Hardening Contract
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-006, SPEC-004A, SPEC-005]
implements: [P3, P5, P7, P10]
supersedes: null
superseded_by: null
related: [SPEC-004A, SPEC-005]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Contract: EDA Hardening

## Required Input Preflight

For each requested dashboard panel, required entities and roles must be validated before writing
or registering requested artifacts. Invalid required inputs fail the command and must not produce
new requested PNGs or manifest entries.

## Optional Input Behavior

Optional entities and roles may render unavailable or warning panels. Warnings must be propagated
to the artifact manifest when the artifact is registered.

## Outcome Prevalence

Outcome prevalence counts must expose:

- positive count
- negative count
- missing/unknown count
- denominator
- percent based on the documented denominator

Missing/unknown outcomes are never counted as negatives.

## Risk Indicators

Comorbidity and risk indicator displays must expose yes, no, and missing/unknown counts.
Missing values are never counted as "No".

## Alert Funnel

Survey, call, and contact states must include an explicit missing/unknown category.
Completed-call counts must use explicit completed states and must not treat every non-null
`nurse_outcome` as completed.

## Category Completeness

Clinically meaningful category charts must display every category when readable. If direct labels
would be unreadable, the artifact must preserve every omitted or grouped category and count in a
visible overflow table or artifact metadata.
