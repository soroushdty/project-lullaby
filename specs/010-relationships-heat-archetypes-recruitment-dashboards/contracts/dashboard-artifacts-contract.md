---
id: CONTRACT-010-ARTIFACTS
title: Relationships, Heat, Archetype, and Recruitment Artifact Contract
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-010, SPEC-004, SPEC-007, SPEC-009]
implements: [P5, P7, P10]
supersedes: null
superseded_by: null
related: [CONTRACT-007-DASHBOARDS, CONTRACT-009-ARTIFACTS]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Contract: SPEC-010 Dashboard Artifacts

## Common Artifact Requirements

Every SPEC-010 dashboard artifact must:

- Be a PNG file.
- Be at least 1600 x 900 pixels.
- Include a title and source/date-range subtitle.
- Include labels and schema units where units are available.
- Include direct count, denominator, source, or warning annotations where feasible.
- Preserve missing values in denominators, unavailable panels, and annotations.
- Avoid prediction, model scores, causal attribution, and imputation.
- Record relevant optional-data warnings in the manifest.

## Required Artifacts

| Panel | Filename | Required inputs |
|-------|----------|-----------------|
| Relationships | `10_relationships.png` | `daily_vitals`, `vital.participant_id`, `vital.date`, `vital.systolic_bp` |
| Heat environment | `11_heat_environment.png` | `environment` for available-data rendering; otherwise explicit unavailable panel |
| Archetype explorer | `12_archetype_explorer.png` | `participants`, `participant.id`, `daily_vitals`, `vital.participant_id`, `vital.date` |
| Recruitment timeline | `13_recruitment_timeline.png` | `participants`, `participant.id`; parseable dates for available-data rendering |

## Panel 10: Relationships

- Shows a descriptive correlation heatmap among numeric vital variables.
- Uses observed pairs only and annotates pairwise N.
- Shows body-water direction versus BP, HR, and skin temperature.
- Shows heat-index versus HR and skin temperature when environment heat index or a Panel
  10-only daily-vitals heat-index proxy is available.
- Labels daily-vitals heat index as a proxy when used.
- Highlights the descriptive CV-vs-heat discriminator:
  - Body water rising plus BP/HR rising suggests a CV-risk-like trajectory.
  - Body water falling plus HR/skin temperature rising suggests a heat-strain-like trajectory.
- Labels correlations and discriminator counts as descriptive and non-causal.

## Panel 11: Heat Environment

- Uses only a real `environment` table for environment trends and missing environment coverage.
- Renders an explicit unavailable panel when the environment table is absent.
- Shows ambient temperature and heat index over calendar date or study day when available.
- Shades or annotates high-heat periods using the clarified high-heat fallback order.
- Overlays or stratifies by participant AC access when available.
- Summarizes observed HR and skin-temperature responses during high-heat versus non-high-heat
  days when daily vitals can be aligned to environment rows.
- Shows missing environment rows, date gaps, or missing environment field counts.
- Does not fabricate environment data from daily-vitals columns.

## Panel 12: Archetype Explorer

- Includes the five required archetype segments: diligent monitor, overwhelmed mom,
  heat-stressed, true emergency, and silent decliner.
- Uses explicit archetype labels when available.
- Normalizes known aliases to the five canonical segment names.
- Preserves unknown explicit labels as additional rows and metadata.
- Assigns provisional descriptive labels when explicit labels are absent.
- Marks provisional labels visibly and in metadata.
- Resolves provisional rule conflicts to exactly one label using priority order: true
  emergency, heat-stressed, silent decliner, overwhelmed mom, diligent monitor.
- Summarizes N, adherence, missingness, alert burden, event prevalence, AC access, and PIH
  severity for each segment.
- Computes alert burden from optional alert rows when available and marks it unavailable when
  alerts are absent.

## Panel 13: Recruitment Timeline

- Shows enrollment or recruitment dates over calendar time when parseable dates exist.
- Shows observation windows from observation fields or daily-vitals date bounds.
- Marks delivery dates when available.
- Shows participant count enrolled over time.
- Shows cohort observation density over calendar time.
- Overlays high-heat periods when environment data are available.
- Uses recruitment dates when a recruitment table exists.
- Infers timeline dates from participant enrollment, observation, and daily-vitals dates when
  recruitment data are absent.
- Renders an unavailable panel and manifest warning when no parseable date source exists.
- May downsample displayed participant rows deterministically while retaining full-cohort
  metrics.

## Manifest Entry Requirements

Each SPEC-010 dashboard entry must include:

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

Stable default artifact ids:

- `eda_relationships_10_relationships`
- `eda_relationships_11_heat_environment`
- `eda_relationships_12_archetype_explorer`
- `eda_relationships_13_recruitment_timeline`

Field rules:

- `spec` is `SPEC-010`.
- `path` is repository-relative and points to the written PNG file.
- `warnings` preserves unavailable environment, provisional labels, alert burden
  unavailability, recruitment inference, date unavailability, and downsampling.
- `metadata` preserves observed-pair denominators, heat source, high-heat definition,
  environment availability, label source, provisional rule summary, recruitment source, and
  calendar-awareness state.
- `deterministic` is `true`.
