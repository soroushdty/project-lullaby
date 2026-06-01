---
id:            PLAN-001-DATA-MODEL
title:         Data Model - Canonical Schema & Validation
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

# Data Model

## SchemaContract (abstract)
Fields:
- `name: str`
- `version: str`
- `tables: dict[str, TableContract]`
- `cadence_field: str` (default: `cadence`)

Required behavior:
- MUST expose table contracts for all canonical tables.
- MUST expose dataframe validation schemas for each table.
- MUST expose data dictionary mapping for each table/column.

## TableContract
Fields:
- `table_name: str`
- `required_columns: list[str]`
- `optional_columns: list[str]`
- `primary_key: list[str]`
- `timestamp_column: str`
- `constraints: list[str]`

Validation rules:
- Required columns must exist.
- Timestamp column must parse and be timezone-consistent.
- Missing required values are errors unless explicitly marked nullable.

## Canonical Entities

### Participant
Core fields:
- `participant_id` (string, required, unique)
- `enrollment_ts` (datetime, required)
- `site_code` (string, required)
- `demographics` (object/json, optional)

### DailyVital
Core fields:
- `participant_id` (string, required)
- `event_ts` (datetime, required)
- `cadence` (string, required)
- `heart_rate`, `systolic_bp`, `diastolic_bp`, `temperature_c` (numeric, nullable)

Validation:
- `event_ts` required; cadence required.
- Clinically implausible values are flagged as validation errors, not dropped silently.

### Alert
Core fields:
- `alert_id` (string, required, unique)
- `participant_id` (string, required)
- `event_ts` (datetime, required)
- `alert_level` (enum: yellow|red|composite-red)
- `source` (string, required)

### ClinicalOutcome
Core fields:
- `outcome_id` (string, required, unique)
- `participant_id` (string, required)
- `event_ts` (datetime, required)
- `outcome_type` (string, required)
- `is_primary_cv_event` (bool, required)

### StaffContact
Core fields:
- `staff_id` (string, required)
- `role` (string, required)
- `contact_method` (string, required)
- `availability_window` (string, optional)

## Relationships
- `participant_id` links `Participant` to `DailyVital`, `Alert`, and `ClinicalOutcome`.
- `Alert` may reference `StaffContact` workflow metadata in downstream modules.

## State Transitions

### Ingestion State
1. `raw_loaded`
2. `normalized_to_canonical_columns`
3. `schema_validated` or `schema_rejected`
4. `accepted_for_downstream` (only from `schema_validated`)

Transition rules:
- `raw_loaded -> normalized_to_canonical_columns` requires table mapping resolution.
- `normalized_to_canonical_columns -> schema_validated` requires all table contracts pass.
- Any violation leads to `schema_rejected` with actionable errors.
