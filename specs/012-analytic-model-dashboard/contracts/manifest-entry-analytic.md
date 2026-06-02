---
id:            CONTRACT-012-MANIFEST
title:         Analytic Manifest Entry Contract
status:        complete
version:       0.1.0
created:       2026-06-01
author:        Soroush Dianaty
related:       [PLAN-012, SPEC-012, SPEC-007]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Contract: Analytic Manifest Entry

## Shared manifest file

`outputs/figures/manifest.json` — the same file written by SPEC-007 (EDA panels). EDA entries carry `"type": "eda"`; analytic entries carry `"type": "analytic"`. The `artifacts.register_artifact()` helper in `src/visualization/artifacts.py` handles reads and writes; SPEC-012 calls it with `artifact_type="analytic"`.

## Required fields (every analytic entry)

| Field | Type | Constraint |
|-------|------|-----------|
| `path` | str | repo-relative path; must start with `outputs/` |
| `type` | str | always `"analytic"` |
| `panel` | int \| null | 1–11 for PNGs; null for model card |
| `width_px` | int \| null | required for PNGs; null for markdown |
| `height_px` | int \| null | required for PNGs; null for markdown |
| `available` | bool | `true` if rendered; `false` if unavailable panel |
| `warning` | str \| null | human-readable explanation when `available == false` or partial issue |

## Minimum size gate

A SPEC-012 PNG entry with `available == true` MUST have `width_px >= 1600` and `height_px >= 900`. Any entry below this threshold MUST have `available == false` and a `warning` explaining the render failure.

## Invariants

- No SPEC-012 artifact path may point outside `outputs/`.
- Every panel function that runs (including unavailable fallback renders) MUST write an entry.
- `warning` must be a non-empty string when `available == false`; null is not permitted in that state.
- Existing EDA entries in the manifest MUST NOT be modified or removed by the SPEC-012 run.
