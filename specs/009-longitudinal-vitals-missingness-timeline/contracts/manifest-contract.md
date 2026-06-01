---
id: CONTRACT-009-MANIFEST
title: Longitudinal EDA Manifest Contract
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-009, SPEC-004, SPEC-007]
implements: [P2, P3, P5, P7]
supersedes: null
superseded_by: null
related: [CONTRACT-007-MANIFEST]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Contract: Longitudinal EDA Manifest Entries

## Manifest Path

`outputs/figures/manifest.json`

## Required Entry Fields

Each longitudinal EDA dashboard entry must include:

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
  - `eda_longitudinal_05_vital_trajectories`
  - `eda_longitudinal_06_missingness_adherence`
  - `eda_longitudinal_07_patient_timeline`
  - `eda_longitudinal_08_data_quality_scorecard`
  - `eda_longitudinal_09_missingness_mechanism`
- `path` is repository-relative and points to the written PNG file.
- `spec` is `SPEC-009` for artifacts generated for this feature.
- `inputs` names the canonical entities used by the panel.
- `required_roles` lists the roles that must resolve before the artifact may be written.
- `optional_roles_used` lists enrichment roles used when available.
- `warnings` preserves optional missingness, unavailable sections, missing score components,
  downsampling, environment overlay unavailability, and diagnostic caveats.
- `metadata` preserves selected participant context, week filters, environment overlay state,
  data-quality formula metadata, display downsampling details, observed denominators, and
  exploratory mechanism labels that cannot fit visibly in the static panel.
- `deterministic` is `true`.

## Registration Rules

- Default repo-relative outputs are registered or upserted in the manifest.
- Alternate repo-relative outputs may be registered with non-conflicting artifact ids.
- Outside-repo outputs are not registered in the default manifest and must warn.
- A required-input failure writes no affected manifest entry.
- Automatically selected participant ids and selection score components must be stored in
  manifest metadata for Panel 5 and Panel 7.
- Adjusted quality score formulas must be stored in manifest metadata for Panel 8 whenever any
  component weight is redistributed.
