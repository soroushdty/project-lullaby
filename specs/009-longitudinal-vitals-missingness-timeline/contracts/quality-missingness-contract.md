---
id: CONTRACT-009-QUALITY-MISSINGNESS
title: Longitudinal Missingness, Quality Score, and Mechanism Contract
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-009, SPEC-004, SPEC-006, SPEC-007]
implements: [P3, P5, P7, P8, P10]
supersedes: null
superseded_by: null
related: [CONTRACT-007-MISSINGNESS, CONTRACT-006-BOOLEAN, CONTRACT-004-REGISTRY]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Contract: Longitudinal Missingness, Quality Score, and Mechanism Diagnostics

## Missingness

- Missing values are counted and displayed where relevant.
- Missing values are not imputed.
- Missing days remain on the study-day axis so gaps are visible.
- Missing optional roles render unavailable or warning sections.
- Missing required tables or roles fail before affected artifact writes.
- Missing and present states must be distinguishable without relying on color alone.

## Study-Day And Week Axis

- `vital.study_day` is used when present.
- When `vital.study_day` is absent, study day may be derived from `vital.date` and participant
  observation start or the earliest observed participant date.
- `--week-start` and `--week-end` are inclusive 1-based study-week filters.
- Study days 1-7 are week 1, 8-14 are week 2, and so on.
- Invalid week ranges fail before affected artifacts are written.

## Automatic Participant Selection

- Selection score equals `observed_vital_days + distinct_alert_days + distinct_outcome_events`.
- Ties are broken by observed vital variable count and then lexicographic participant id.
- Selection must not use clinical risk severity or outcome class as a risk rank.
- Manifest metadata records the selected participant id, selection mode, score components, and
  tie-breaker evidence.

## Data-Quality Score

When all components are available:

```text
quality_score = 0.40 * wear_completeness + 0.25 * scale_adherence + 0.20 * vital_completeness + 0.15 * contact_traceability
```

Component rules:

- Components are normalized to 0-1 participant-level scores.
- `wear_completeness` uses observed or valid wear hours against the expected participant-day
  denominator when `vital.sensor_wear_hours` is available.
- `scale_adherence` uses explicit scale-use observations against the expected participant-day
  denominator when `vital.scale_used` is available.
- `vital_completeness` uses observed vital measurements across expected vital roles and study
  days.
- `contact_traceability` uses available staff contact participant/date/completion evidence
  against expected contact opportunities when available.
- A component with no valid denominator is unavailable rather than zero.
- Unavailable component weights are redistributed proportionally across available components.
- The adjusted formula and warning are stored in manifest metadata.

## Gap Clustering

- Gap clusters are derived only from observed timestamps, study days, hours, or suitable
  documented proxies.
- Overnight, feeding/morning, hot afternoon, and late-study decline clusters are shown only
  when the data support them.
- Unsupported clusters render unavailable labels and manifest warnings rather than guessed
  categories.

## Recent Abnormal Vitals

- Recent abnormal vital context uses observed values only.
- Capture-worthy and impossible thresholds come from schema registry ranges when available.
- Missing values are not filled to infer abnormality.
- If no threshold or range exists for a vital role, that role is omitted from abnormal-vital
  diagnostics and recorded as unavailable when relevant.

## Mechanism Diagnostics

- MCAR/MAR/MNAR language is exploratory only.
- Panel 9 must label results as exploratory signals consistent with mechanism hypotheses, not
  proof.
- Stratifiers such as archetype, AC access, insurance, PIH severity, and health literacy are
  used only when present.
- Heat exposure diagnostics are shown only when optional environment data are available.
- No imputation, model training, or causal claim is allowed in the mechanism panel.
