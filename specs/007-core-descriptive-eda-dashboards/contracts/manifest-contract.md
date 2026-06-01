---
id: CONTRACT-007-MANIFEST
title: Core Descriptive EDA Manifest Contract
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-007, SPEC-004, SPEC-006]
implements: [P2, P3, P5, P7]
supersedes: null
superseded_by: null
related: [CONTRACT-004-MANIFEST]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Contract: Core Descriptive EDA Manifest Entries

## Manifest Path

`outputs/figures/manifest.json`

## Required Entry Fields

Each core EDA dashboard entry must include:

- `artifact_id`
- `path`
- `title`
- `spec`
- `inputs`
- `required_roles`
- `optional_roles_used`
- `warnings`
- `metadata`
- `created_at_utc`
- `deterministic`

## Field Rules

- `artifact_id` is stable for default outputs:
  - `eda_core_01_cohort_overview`
  - `eda_core_02_outcome_prevalence`
  - `eda_core_03_distribution_outliers`
  - `eda_core_04_alert_engagement_funnel`
- `path` is repository-relative and points to the written PNG file.
- `spec` is `SPEC-007` for artifacts generated for this feature.
- `inputs` names the canonical entities used by the panel.
- `required_roles` lists the roles that must resolve before the artifact may be written.
- `optional_roles_used` lists enrichment roles used when available.
- `warnings` preserves optional missingness, invalid optional tokens treated as missing, and
  unavailable sections.
- `metadata` preserves any category overflow or completeness evidence that cannot fit visibly
  in the static panel.
- `deterministic` is `true`.

## Registration Rules

- Default repo-relative outputs are registered or upserted in the manifest.
- Alternate repo-relative outputs may be registered with non-conflicting artifact ids.
- Outside-repo outputs are not registered in the default manifest and must warn.
- A required-input failure writes no affected manifest entry.
