---
id: CONTRACT-004A-REGISTRY
title: Visualization Schema Registry Contract
status: draft
version: 0.1.0
created: 2026-06-01
updated: 2026-06-01
author: Soroush Dianaty
depends_on: [SPEC-004A, PLAN-004A]
implements: [P3, P5]
supersedes: null
superseded_by: null
related: [SPEC-001]
---

<!-- Conforms to Project Lullaby Constitution v1.0.0 -->

# Contract: Visualization Schema Registry

## Module

`src.visualization.schema_registry`

## Required Public Functions

```python
def get_entity(name: str) -> EntitySpec: ...

def load_entity(data_dir: Path, entity: str) -> pd.DataFrame: ...

def resolve_column(
    df: pd.DataFrame,
    semantic_role: str,
    *,
    entity: str | None = None,
) -> RoleResolution: ...

def require_roles(
    df: pd.DataFrame,
    roles: list[str],
    *,
    entity: str | None = None,
) -> ValidationResult: ...

def available_roles(
    df: pd.DataFrame,
    roles: list[str],
    *,
    entity: str | None = None,
) -> dict[str, str]: ...
```

## Entity Loading

- Default validation uses `data/`.
- Each current entity declares ordered accepted filenames.
- Repository-root filenames are preferred where present:
  - `lullaby_participants.csv`
  - `lullaby_daily_vitals.csv`
  - `lullaby_alerts.csv`
  - `lullaby_staff_contacts.csv`
  - `lullaby_clinical_outcomes.csv`
- Canonical synthetic filenames such as `participants.csv` remain valid when callers pass
  `--data-dir data/synthetic`.
- Missing files for current required entities are validation errors.
- Missing files for future optional entities are structured warnings.

## Role Resolution

- Resolution is deterministic.
- Exact semantic column names are checked before aliases.
- Alias lists are checked in declared order.
- Unknown extra columns remain available in the source DataFrame and are reported as context.
- Required missing roles become errors.
- Optional missing roles become warnings.
- Ambiguous matches become errors unless an explicit priority winner is declared in the
  entity spec.

## Minimum Current Roles

The registry must cover these current role families:

```text
participant.id
participant.age
participant.enrollment_date
participant.delivery_date
participant.observation_start_date
participant.pih_severity
participant.gestational_diabetes
participant.has_ac
participant.health_literacy
participant.social_support
participant.depression
participant.anxiety

vital.participant_id
vital.date
vital.study_day
vital.week
vital.systolic_bp
vital.diastolic_bp
vital.heart_rate
vital.respiratory_rate
vital.skin_temperature_c
vital.ambient_temperature_c
vital.heat_index_c
vital.sensor_wear_hours

alert.id
alert.participant_id
alert.date
alert.hour
alert.level
alert.trigger_reasons
alert.classification
alert.called_nurse

contact.participant_id
contact.date
contact.type
contact.week
contact.completed
contact.reason

outcome.participant_id
outcome.cv_event
outcome.cv_event_type
outcome.cv_event_date
outcome.ed_visit
outcome.hospitalized
outcome.heat_illness
```

## Acceptance Tests

- Required roles resolve for all supported root `data/lullaby_*.csv` tables.
- Required roles resolve for canonical synthetic fixtures where equivalent roles exist.
- Missing optional roles return warnings, not exceptions.
- Ambiguous aliases produce deterministic error details.
- Extra columns are reported and preserved.
