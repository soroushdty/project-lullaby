from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd


class SchemaValidationError(Exception):
    def __init__(
        self,
        message: str,
        *,
        entity: str = "",
        role_id: str = "",
        source_filename: str = "",
        candidates: list[str] | None = None,
        remediation: str = "",
    ) -> None:
        self.entity = entity
        self.role_id = role_id
        self.source_filename = source_filename
        self.candidates = candidates or []
        self.remediation = remediation
        super().__init__(message)


@dataclass(frozen=True)
class SemanticRole:
    role_id: str
    entity: str
    required: bool
    value_type: str
    label: str
    unit: str | None = None
    accepted_columns: tuple[str, ...] = ()
    hard_range: tuple[float | None, float | None] | None = None
    capture_worthy_range: tuple[float | None, float | None] | None = None
    categories: tuple[str, ...] = ()
    priority_column: str | None = None


@dataclass(frozen=True)
class EntitySpec:
    name: str
    status: str
    source_filenames: tuple[str, ...]
    primary_key_roles: tuple[str, ...]
    participant_role: str | None
    datetime_roles: tuple[str, ...]
    required_roles: tuple[str, ...]
    optional_roles: tuple[str, ...]
    display_labels: dict[str, str] = field(default_factory=dict)
    units: dict[str, str] = field(default_factory=dict)
    default_aggregation: str = "none"
    missingness_policy: str = "explicit"


@dataclass(frozen=True)
class RoleResolution:
    role_id: str
    entity: str
    column: str | None
    match_type: str
    candidates: tuple[str, ...]
    required: bool
    warning: str | None = None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.match_type in {"exact", "alias"}


@dataclass
class RegistryValidationResult:
    status: str
    entity: str
    resolved_roles: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    extra_columns: list[str] = field(default_factory=list)
    resolutions: list[RoleResolution] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "entity": self.entity,
            "resolved_roles": self.resolved_roles,
            "warnings": self.warnings,
            "errors": self.errors,
            "extra_columns": self.extra_columns,
            "resolutions": [r.__dict__ for r in self.resolutions],
        }


PHYSIOLOGIC_BOUNDS: dict[str, dict[str, tuple[float | None, float | None]]] = {
    "vital.systolic_bp": {
        "hard": (50, 260),
        "capture": (90, 180),
    },
    "vital.diastolic_bp": {
        "hard": (30, 160),
        "capture": (50, 120),
    },
    "vital.heart_rate": {
        "hard": (25, 240),
        "capture": (50, 140),
    },
    "vital.respiratory_rate": {
        "hard": (5, 60),
        "capture": (10, 30),
    },
    "vital.skin_temperature_c": {
        "hard": (25, 45),
        "capture": (34, 39),
    },
    "vital.ambient_temperature_c": {
        "hard": (-20, 60),
        "capture": (0, 40),
    },
    "vital.heat_index_c": {
        "hard": (0, 70),
        "capture": (None, 35),
    },
    "vital.sensor_wear_hours": {
        "hard": (0, 24),
        "capture": (8, None),
    },
}


def _role(
    role_id: str,
    entity: str,
    required: bool,
    value_type: str,
    label: str,
    aliases: tuple[str, ...],
    unit: str | None = None,
    categories: tuple[str, ...] = (),
) -> SemanticRole:
    bounds = PHYSIOLOGIC_BOUNDS.get(role_id, {})
    return SemanticRole(
        role_id=role_id,
        entity=entity,
        required=required,
        value_type=value_type,
        label=label,
        unit=unit,
        accepted_columns=aliases,
        hard_range=bounds.get("hard"),
        capture_worthy_range=bounds.get("capture"),
        categories=categories,
    )


ROLES: dict[str, SemanticRole] = {
    "participant.id": _role("participant.id", "participants", True, "string", "Participant ID", ("participant_id", "record_id")),
    "participant.age": _role("participant.age", "participants", False, "number", "Age", ("age",)),
    "participant.enrollment_date": _role("participant.enrollment_date", "participants", False, "date", "Enrollment Date", ("enrollment_date", "enrollment_ts")),
    "participant.delivery_date": _role("participant.delivery_date", "participants", False, "date", "Delivery Date", ("delivery_date",)),
    "participant.observation_start_date": _role("participant.observation_start_date", "participants", False, "date", "Observation Start", ("observation_start_date",)),
    "participant.pih_severity": _role("participant.pih_severity", "participants", False, "category", "PIH Severity", ("pih_severity",)),
    "participant.gestational_diabetes": _role("participant.gestational_diabetes", "participants", False, "boolean", "Gestational Diabetes", ("gestational_diabetes",)),
    "participant.has_ac": _role("participant.has_ac", "participants", False, "boolean", "Has Air Conditioning", ("has_ac",)),
    "participant.health_literacy": _role("participant.health_literacy", "participants", False, "number", "Health Literacy", ("bhls_health_literacy",)),
    "participant.social_support": _role("participant.social_support", "participants", False, "number", "Social Support", ("mspss_social_support",)),
    "participant.depression": _role("participant.depression", "participants", False, "number", "Depression Score", ("epds_depression",)),
    "participant.anxiety": _role("participant.anxiety", "participants", False, "number", "Anxiety Score", ("pass_anxiety",)),
    "vital.participant_id": _role("vital.participant_id", "daily_vitals", True, "string", "Participant ID", ("participant_id",)),
    "vital.date": _role("vital.date", "daily_vitals", True, "date", "Measurement Date", ("date", "event_ts")),
    "vital.study_day": _role("vital.study_day", "daily_vitals", False, "number", "Study Day", ("study_day",)),
    "vital.week": _role("vital.week", "daily_vitals", False, "number", "Week", ("week",)),
    "vital.systolic_bp": _role("vital.systolic_bp", "daily_vitals", True, "number", "Systolic BP", ("sbp_mean", "systolic_bp"), "mmHg"),
    "vital.diastolic_bp": _role("vital.diastolic_bp", "daily_vitals", False, "number", "Diastolic BP", ("dbp_mean", "diastolic_bp"), "mmHg"),
    "vital.heart_rate": _role("vital.heart_rate", "daily_vitals", False, "number", "Heart Rate", ("hr_mean", "heart_rate"), "bpm"),
    "vital.respiratory_rate": _role("vital.respiratory_rate", "daily_vitals", False, "number", "Respiratory Rate", ("rr_mean",), "breaths/min"),
    "vital.skin_temperature_c": _role("vital.skin_temperature_c", "daily_vitals", False, "number", "Skin Temperature", ("skin_temp_mean_c", "temperature_c"), "C"),
    "vital.ambient_temperature_c": _role("vital.ambient_temperature_c", "daily_vitals", False, "number", "Ambient Temperature", ("ambient_temp_c",), "C"),
    "vital.heat_index_c": _role("vital.heat_index_c", "daily_vitals", False, "number", "Heat Index", ("heat_index_c",), "C"),
    "vital.sensor_wear_hours": _role("vital.sensor_wear_hours", "daily_vitals", False, "number", "Sensor Wear", ("sensor_wear_hours",), "hours"),
    "alert.id": _role("alert.id", "alerts", True, "string", "Alert ID", ("alert_id",)),
    "alert.participant_id": _role("alert.participant_id", "alerts", True, "string", "Participant ID", ("participant_id",)),
    "alert.date": _role("alert.date", "alerts", False, "date", "Alert Date", ("date", "event_ts")),
    "alert.hour": _role("alert.hour", "alerts", False, "number", "Alert Hour", ("alert_hour",)),
    "alert.level": _role("alert.level", "alerts", True, "category", "Alert Level", ("alert_level",), categories=("yellow", "red", "composite-red")),
    "alert.trigger_reasons": _role("alert.trigger_reasons", "alerts", False, "string", "Trigger Reasons", ("trigger_reasons", "source")),
    "alert.classification": _role("alert.classification", "alerts", False, "category", "Classification", ("classification",)),
    "alert.called_nurse": _role("alert.called_nurse", "alerts", False, "boolean", "Called Nurse", ("called_nurse",)),
    "contact.participant_id": _role("contact.participant_id", "staff_contacts", False, "string", "Participant ID", ("participant_id",)),
    "contact.date": _role("contact.date", "staff_contacts", False, "date", "Contact Date", ("contact_date",)),
    "contact.type": _role("contact.type", "staff_contacts", True, "category", "Contact Type", ("contact_type", "role")),
    "contact.week": _role("contact.week", "staff_contacts", False, "number", "Contact Week", ("contact_week",)),
    "contact.completed": _role("contact.completed", "staff_contacts", False, "boolean", "Contact Completed", ("participant_reached", "contact_method")),
    "contact.reason": _role("contact.reason", "staff_contacts", False, "string", "Contact Reason", ("reason", "availability_window")),
    "outcome.participant_id": _role("outcome.participant_id", "clinical_outcomes", True, "string", "Participant ID", ("participant_id",)),
    "outcome.cv_event": _role("outcome.cv_event", "clinical_outcomes", True, "boolean", "CV Event", ("cv_event", "outcome_type")),
    "outcome.cv_event_type": _role("outcome.cv_event_type", "clinical_outcomes", False, "category", "CV Event Type", ("cv_event_type", "outcome_type")),
    "outcome.cv_event_date": _role("outcome.cv_event_date", "clinical_outcomes", False, "date", "CV Event Date", ("cv_event_date", "event_ts")),
    "outcome.ed_visit": _role("outcome.ed_visit", "clinical_outcomes", False, "boolean", "ED Visit", ("ed_visit",)),
    "outcome.hospitalized": _role("outcome.hospitalized", "clinical_outcomes", False, "boolean", "Hospitalized", ("hospitalized",)),
    "outcome.heat_illness": _role("outcome.heat_illness", "clinical_outcomes", False, "number", "Heat Illness Episodes", ("heat_illness_episodes",)),
}


ENTITIES: dict[str, EntitySpec] = {
    "participants": EntitySpec(
        name="participants",
        status="current",
        source_filenames=("lullaby_participants.csv", "participants.csv"),
        primary_key_roles=("participant.id",),
        participant_role=None,
        datetime_roles=("participant.enrollment_date", "participant.delivery_date", "participant.observation_start_date"),
        required_roles=("participant.id",),
        optional_roles=tuple(r for r in ROLES if r.startswith("participant.") and r != "participant.id"),
        default_aggregation="one_row_per_participant",
    ),
    "daily_vitals": EntitySpec(
        name="daily_vitals",
        status="current",
        source_filenames=("lullaby_daily_vitals.csv", "daily_vitals.csv"),
        primary_key_roles=("vital.participant_id", "vital.date"),
        participant_role="vital.participant_id",
        datetime_roles=("vital.date",),
        required_roles=("vital.participant_id", "vital.date", "vital.systolic_bp"),
        optional_roles=tuple(r for r in ROLES if r.startswith("vital.") and r not in {"vital.participant_id", "vital.date", "vital.systolic_bp"}),
        default_aggregation="participant_day",
    ),
    "alerts": EntitySpec(
        name="alerts",
        status="current",
        source_filenames=("lullaby_alerts.csv", "alerts.csv"),
        primary_key_roles=("alert.id",),
        participant_role="alert.participant_id",
        datetime_roles=("alert.date",),
        required_roles=("alert.id", "alert.participant_id", "alert.level"),
        optional_roles=tuple(r for r in ROLES if r.startswith("alert.") and r not in {"alert.id", "alert.participant_id", "alert.level"}),
        default_aggregation="participant_day",
    ),
    "staff_contacts": EntitySpec(
        name="staff_contacts",
        status="current",
        source_filenames=("lullaby_staff_contacts.csv", "staff_contacts.csv"),
        primary_key_roles=("contact.participant_id", "contact.date", "contact.type"),
        participant_role="contact.participant_id",
        datetime_roles=("contact.date",),
        required_roles=("contact.type",),
        optional_roles=tuple(r for r in ROLES if r.startswith("contact.") and r != "contact.type"),
        default_aggregation="participant_week",
    ),
    "clinical_outcomes": EntitySpec(
        name="clinical_outcomes",
        status="current",
        source_filenames=("lullaby_clinical_outcomes.csv", "clinical_outcomes.csv"),
        primary_key_roles=("outcome.participant_id",),
        participant_role="outcome.participant_id",
        datetime_roles=("outcome.cv_event_date",),
        required_roles=("outcome.participant_id", "outcome.cv_event"),
        optional_roles=tuple(r for r in ROLES if r.startswith("outcome.") and r not in {"outcome.participant_id", "outcome.cv_event"}),
        default_aggregation="participant",
    ),
    "environment": EntitySpec("environment", "future_optional", (), (), None, (), (), ()),
    "recruitment": EntitySpec("recruitment", "future_optional", (), (), None, (), (), ()),
    "model_predictions": EntitySpec("model_predictions", "future_optional", (), (), None, (), (), ()),
    "model_metrics": EntitySpec("model_metrics", "future_optional", (), (), None, (), (), ()),
}


def get_entity(name: str) -> EntitySpec:
    try:
        return ENTITIES[name]
    except KeyError as exc:
        raise SchemaValidationError(
            f"Unknown visualization entity: {name}",
            entity=name,
            remediation="Use one of the registered entity names.",
        ) from exc


def get_role(role_id: str) -> SemanticRole:
    try:
        return ROLES[role_id]
    except KeyError as exc:
        raise SchemaValidationError(
            f"Unknown semantic role: {role_id}",
            role_id=role_id,
            remediation="Use a role declared in the visualization schema registry.",
        ) from exc


def load_entity(data_dir: Path, entity: str) -> pd.DataFrame:
    spec = get_entity(entity)
    for filename in spec.source_filenames:
        path = data_dir / filename
        if path.exists():
            return pd.read_csv(path)
    if spec.status == "future_optional":
        return pd.DataFrame()
    raise SchemaValidationError(
        f"Missing source file for entity '{entity}' in {data_dir}",
        entity=entity,
        candidates=list(spec.source_filenames),
        remediation="Pass --data-dir with a directory containing one accepted source filename.",
    )


def resolve_column(
    df: pd.DataFrame,
    semantic_role: str,
    *,
    entity: str | None = None,
) -> RoleResolution:
    role = get_role(semantic_role)
    if entity and role.entity != entity:
        return RoleResolution(
            role_id=semantic_role,
            entity=entity,
            column=None,
            match_type="missing",
            candidates=(),
            required=role.required,
            warning=f"Role {semantic_role} belongs to {role.entity}, not {entity}",
        )

    columns = set(df.columns)
    if semantic_role in columns:
        return RoleResolution(semantic_role, role.entity, semantic_role, "exact", (semantic_role,), role.required)

    candidates = tuple(col for col in role.accepted_columns if col in columns)
    if not candidates:
        message = f"Missing {'required' if role.required else 'optional'} role {semantic_role}"
        return RoleResolution(
            semantic_role,
            role.entity,
            None,
            "missing",
            (),
            role.required,
            error=message if role.required else None,
            warning=message if not role.required else None,
        )
    if len(candidates) > 1 and role.priority_column not in candidates:
        message = f"Ambiguous columns for role {semantic_role}: {', '.join(candidates)}"
        return RoleResolution(
            semantic_role,
            role.entity,
            None,
            "ambiguous",
            candidates,
            role.required,
            error=message,
        )
    selected = role.priority_column if role.priority_column in candidates else candidates[0]
    return RoleResolution(semantic_role, role.entity, selected, "alias", candidates, role.required)


def require_roles(
    df: pd.DataFrame,
    roles: list[str],
    *,
    entity: str | None = None,
) -> RegistryValidationResult:
    inferred_entity = entity or (get_role(roles[0]).entity if roles else "")
    result = RegistryValidationResult(status="pass", entity=inferred_entity)
    all_known_columns = _accepted_columns_for_entity(inferred_entity)
    for role_id in roles:
        resolution = resolve_column(df, role_id, entity=entity)
        result.resolutions.append(resolution)
        if resolution.ok and resolution.column:
            result.resolved_roles[role_id] = resolution.column
        if resolution.warning:
            result.warnings.append(resolution.warning)
        if resolution.error:
            result.errors.append(resolution.error)
    result.extra_columns = sorted(col for col in df.columns if col not in all_known_columns)
    result.status = "fail" if result.errors else "warn" if result.warnings else "pass"
    return result


def available_roles(
    df: pd.DataFrame,
    roles: list[str],
    *,
    entity: str | None = None,
) -> dict[str, str]:
    available: dict[str, str] = {}
    for role_id in roles:
        resolution = resolve_column(df, role_id, entity=entity)
        if resolution.ok and resolution.column:
            available[role_id] = resolution.column
    return available


def current_entities() -> list[EntitySpec]:
    return [spec for spec in ENTITIES.values() if spec.status == "current"]


def future_optional_entities() -> list[EntitySpec]:
    return [spec for spec in ENTITIES.values() if spec.status == "future_optional"]


def _accepted_columns_for_entity(entity: str) -> set[str]:
    accepted = {role_id for role_id, role in ROLES.items() if role.entity == entity}
    for role in ROLES.values():
        if role.entity == entity:
            accepted.update(role.accepted_columns)
    return accepted
