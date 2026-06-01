---
id:            SCHEMA-001-DATA-DICT
title:         Lullaby Schema Data Dictionary
status:        draft
version:       1.0.0
created:       2026-06-01
updated:       2026-06-01
author:        Soroush Dianaty
implements:    [FR-005]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Lullaby Schema Data Dictionary

Authoritative column-level reference for all canonical Lullaby tables.
All timestamps are stored in UTC. Ingestion rejects records with missing or ambiguous timezone metadata.

---

## participants

| Column | Type | Nullable | Unit | Description |
|--------|------|----------|------|-------------|
| `participant_id` | str | No | — | Unique cohort identifier (e.g. `LUL-2000`) |
| `enrollment_ts` | datetime[UTC] | No | — | UTC timestamp of study enrollment |
| `site_code` | str | No | — | Clinical site identifier (e.g. `PHX-SOUTH`) |
| `demographics` | str | Yes | — | Optional JSON string with demographic metadata |

**Primary key**: `participant_id`

---

## daily_vitals

| Column | Type | Nullable | Unit | Description |
|--------|------|----------|------|-------------|
| `participant_id` | str | No | — | Links to `participants.participant_id` |
| `event_ts` | datetime[UTC] | No | — | UTC timestamp of the measurement window |
| `cadence` | str | No | — | Measurement cadence label (e.g. `daily`) |
| `heart_rate` | float | Yes | bpm | Mean heart rate over the measurement window |
| `systolic_bp` | float | Yes | mmHg | Mean systolic blood pressure |
| `diastolic_bp` | float | Yes | mmHg | Mean diastolic blood pressure |
| `temperature_c` | float | Yes | °C | Mean skin temperature |

**Primary key**: `(participant_id, event_ts)`

**Missingness policy**: Nullable vitals preserve informative missingness. Missing values are flagged, not imputed.

---

## alerts

| Column | Type | Nullable | Unit | Description |
|--------|------|----------|------|-------------|
| `alert_id` | str | No | — | Unique alert identifier (e.g. `A-0001`) |
| `participant_id` | str | No | — | Links to `participants.participant_id` |
| `event_ts` | datetime[UTC] | No | — | UTC timestamp when the alert was generated |
| `alert_level` | str | No | — | Severity: `yellow`, `red`, or `composite-red` |
| `source` | str | No | — | Triggering sensor or system (e.g. `bp_sensor`) |

**Primary key**: `alert_id`

**Constraint**: `alert_level` must be one of `{yellow, red, composite-red}`.

---

## clinical_outcomes

| Column | Type | Nullable | Unit | Description |
|--------|------|----------|------|-------------|
| `outcome_id` | str | No | — | Unique outcome record identifier (e.g. `OC-0001`) |
| `participant_id` | str | No | — | Links to `participants.participant_id` |
| `event_ts` | datetime[UTC] | No | — | UTC timestamp of the outcome event |
| `outcome_type` | str | No | — | Classification label (e.g. `hypertensive_crisis`, `ed_visit`, `no_event`) |
| `is_primary_cv_event` | bool | No | — | Whether this is a primary cardiovascular event |

**Primary key**: `outcome_id`

---

## staff_contacts

| Column | Type | Nullable | Unit | Description |
|--------|------|----------|------|-------------|
| `staff_id` | str | No | — | Unique staff identifier (e.g. `STAFF-01`) |
| `role` | str | No | — | Clinical role (e.g. `nurse`, `physician`) |
| `contact_method` | str | No | — | Preferred contact method (e.g. `phone`, `secure_message`) |
| `availability_window` | str | Yes | — | Availability schedule string (e.g. `Mon-Fri 08:00-17:00 MST`) |

**Primary key**: `staff_id`

---

## Relationships

```
participants.participant_id
    ← daily_vitals.participant_id
    ← alerts.participant_id
    ← clinical_outcomes.participant_id
```

`staff_contacts` is a standalone reference table.
