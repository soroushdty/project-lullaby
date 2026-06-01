---
id: CONTRACT-005-OUTPUT
title: Synthetic Simulator Output Package Contract
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-005, PLAN-005]
implements: [P2, P3, P5, P8, P9]
supersedes: null
superseded_by: null
related: [SPEC-001, SPEC-004]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Contract: Synthetic Simulator Output Package

## Default Directory

`data/synthetic/longitudinal/`

## Required Files

```text
participants.csv
daily_vitals.csv
alerts.csv
staff_contacts.csv
clinical_outcomes.csv
environment.csv
recruitment.csv
simulation_config_used.yaml
simulation_summary.json
```

## Table Grain

| File | Grain | Required Identity |
|------|-------|-------------------|
| `participants.csv` | one row per participant | `participant_id` |
| `daily_vitals.csv` | one row per participant-day for full study window | `participant_id`, `date` |
| `alerts.csv` | one row per generated alert | `alert_id` |
| `staff_contacts.csv` | one row per generated contact attempt | `contact_id` |
| `clinical_outcomes.csv` | one row per participant | `participant_id` |
| `environment.csv` | one row per calendar date/study day | `date`, `study_day` |
| `recruitment.csv` | one row per participant recruitment record | `participant_id` |

## Required Export Rules

- CSV column order is deterministic.
- Rows are sorted by table identity.
- Missing values remain empty CSV cells.
- Temperature and heat-index columns use Celsius.
- Each CSV contains a `synthetic_data` indicator where schema allows extra columns.
- `daily_vitals.csv` row count equals `n_participants * study_days`.
- Generated tables validate through the SPEC-004 schema registry before readiness is true.

## Required Schema Registry Extensions

- `environment` becomes a generated current entity for this output package.
- `recruitment` becomes a generated current entity for this output package.
- `daily_vitals` aliases include body water, weight, sleep, steps, active minutes, wear hours,
  scale adherence, ambient temperature, and heat index.

## Acceptance Tests

- All required files exist after a default run.
- Required identities are unique where specified.
- `daily_vitals.csv` contains 16,800 rows for the default 200 x 84 configuration.
- No generated table presents synthetic records as real participant data.
