from __future__ import annotations

import pandas as pd
import pandera.pandas as pa

from src.schemas.base import SchemaContract, SchemaTableMissingError, TableContract

CANONICAL_TABLES = [
    "participants",
    "daily_vitals",
    "alerts",
    "clinical_outcomes",
    "staff_contacts",
]

# Accept any UTC-aware datetime regardless of nanosecond vs microsecond resolution.
# The ingestion pipeline enforces UTC at load time; Pandera's job is to confirm the
# column is timezone-aware and reject naive timestamps (FR-011).
_UTC_CHECK = pa.Check(
    lambda s: hasattr(s, "dt") and s.dt.tz is not None,
    error="timestamp column must be timezone-aware (UTC required)",
)

_CONTRACTS: dict[str, TableContract] = {
    "participants": TableContract(
        table_name="participants",
        required_columns=["participant_id", "enrollment_ts", "site_code"],
        optional_columns=["demographics"],
        primary_key=["participant_id"],
        timestamp_column="enrollment_ts",
        constraints=["participant_id is unique"],
        column_aliases={"enrollment_date": "enrollment_ts"},
    ),
    "daily_vitals": TableContract(
        table_name="daily_vitals",
        required_columns=["participant_id", "event_ts", "cadence"],
        optional_columns=["heart_rate", "systolic_bp", "diastolic_bp", "temperature_c"],
        primary_key=["participant_id", "event_ts"],
        timestamp_column="event_ts",
        column_aliases={
            "date": "event_ts",
            "study_day": "cadence",  # Mapping study_day to cadence as a placeholder if needed
            "sbp_mean": "systolic_bp",
            "dbp_mean": "diastolic_bp",
            "hr_mean": "heart_rate",
            "rr_mean": "respiratory_rate",
            "skin_temp_mean_c": "temperature_c",
        },
    ),
    "alerts": TableContract(
        table_name="alerts",
        required_columns=["alert_id", "participant_id", "event_ts", "alert_level", "source"],
        optional_columns=[],
        primary_key=["alert_id"],
        timestamp_column="event_ts",
        constraints=["alert_level in {yellow, red, composite-red}", "alert_id is unique"],
    ),
    "clinical_outcomes": TableContract(
        table_name="clinical_outcomes",
        required_columns=["outcome_id", "participant_id", "event_ts", "outcome_type", "is_primary_cv_event"],
        optional_columns=[],
        primary_key=["outcome_id"],
        timestamp_column="event_ts",
        constraints=["outcome_id is unique"],
    ),
    "staff_contacts": TableContract(
        table_name="staff_contacts",
        required_columns=["staff_id", "role", "contact_method"],
        optional_columns=["availability_window"],
        primary_key=["staff_id"],
        timestamp_column="",
    ),
}

def _utc_col(nullable: bool = False) -> pa.Column:
    return pa.Column(checks=_UTC_CHECK, nullable=nullable)


_PANDERA_SCHEMAS: dict[str, pa.DataFrameSchema] = {
    "participants": pa.DataFrameSchema(
        {
            "participant_id": pa.Column(str, unique=True),
            "enrollment_ts": _utc_col(),
            "site_code": pa.Column(str),
            "demographics": pa.Column(object, nullable=True, required=False, coerce=True),
        }
    ),
    "daily_vitals": pa.DataFrameSchema(
        {
            "participant_id": pa.Column(str),
            "event_ts": _utc_col(),
            "cadence": pa.Column(str),
            "heart_rate": pa.Column(float, nullable=True, required=False, coerce=True),
            "systolic_bp": pa.Column(float, nullable=True, required=False, coerce=True),
            "diastolic_bp": pa.Column(float, nullable=True, required=False, coerce=True),
            "temperature_c": pa.Column(float, nullable=True, required=False, coerce=True),
        }
    ),
    "alerts": pa.DataFrameSchema(
        {
            "alert_id": pa.Column(str, unique=True),
            "participant_id": pa.Column(str),
            "event_ts": _utc_col(),
            "alert_level": pa.Column(
                str,
                pa.Check.isin(["yellow", "red", "composite-red"]),
            ),
            "source": pa.Column(str),
        }
    ),
    "clinical_outcomes": pa.DataFrameSchema(
        {
            "outcome_id": pa.Column(str, unique=True),
            "participant_id": pa.Column(str),
            "event_ts": _utc_col(),
            "outcome_type": pa.Column(str),
            "is_primary_cv_event": pa.Column(bool),
        }
    ),
    "staff_contacts": pa.DataFrameSchema(
        {
            "staff_id": pa.Column(str),
            "role": pa.Column(str),
            "contact_method": pa.Column(str),
            "availability_window": pa.Column(str, nullable=True, required=False),
        }
    ),
}

_DATA_DICTIONARIES: dict[str, dict[str, dict]] = {
    "participants": {
        "participant_id": {"type": "str", "nullable": False, "description": "Unique cohort identifier"},
        "enrollment_ts": {"type": "datetime[UTC]", "nullable": False, "description": "UTC enrollment timestamp"},
        "site_code": {"type": "str", "nullable": False, "description": "Clinical site identifier"},
        "demographics": {"type": "str", "nullable": True, "description": "Optional demographic metadata (JSON string)"},
    },
    "daily_vitals": {
        "participant_id": {"type": "str", "nullable": False, "description": "Participant identifier"},
        "event_ts": {"type": "datetime[UTC]", "nullable": False, "description": "UTC timestamp of the measurement"},
        "cadence": {"type": "str", "nullable": False, "description": "Measurement cadence label (e.g. daily)"},
        "heart_rate": {"type": "float", "nullable": True, "unit": "bpm", "description": "Mean heart rate"},
        "systolic_bp": {"type": "float", "nullable": True, "unit": "mmHg", "description": "Mean systolic blood pressure"},
        "diastolic_bp": {"type": "float", "nullable": True, "unit": "mmHg", "description": "Mean diastolic blood pressure"},
        "temperature_c": {"type": "float", "nullable": True, "unit": "°C", "description": "Mean skin temperature"},
    },
    "alerts": {
        "alert_id": {"type": "str", "nullable": False, "description": "Unique alert identifier"},
        "participant_id": {"type": "str", "nullable": False, "description": "Participant identifier"},
        "event_ts": {"type": "datetime[UTC]", "nullable": False, "description": "UTC alert timestamp"},
        "alert_level": {"type": "str", "nullable": False, "enum": ["yellow", "red", "composite-red"], "description": "Severity level"},
        "source": {"type": "str", "nullable": False, "description": "Triggering sensor or system"},
    },
    "clinical_outcomes": {
        "outcome_id": {"type": "str", "nullable": False, "description": "Unique outcome record identifier"},
        "participant_id": {"type": "str", "nullable": False, "description": "Participant identifier"},
        "event_ts": {"type": "datetime[UTC]", "nullable": False, "description": "UTC outcome timestamp"},
        "outcome_type": {"type": "str", "nullable": False, "description": "Outcome classification label"},
        "is_primary_cv_event": {"type": "bool", "nullable": False, "description": "Whether this is a primary cardiovascular event"},
    },
    "staff_contacts": {
        "staff_id": {"type": "str", "nullable": False, "description": "Unique staff identifier"},
        "role": {"type": "str", "nullable": False, "description": "Clinical role (e.g. nurse, physician)"},
        "contact_method": {"type": "str", "nullable": False, "description": "Preferred contact method"},
        "availability_window": {"type": "str", "nullable": True, "description": "Availability schedule string"},
    },
}


class LullabySchema(SchemaContract):
    @property
    def name(self) -> str:
        return "lullaby"

    @property
    def version(self) -> str:
        return "1.0.0"

    def table_names(self) -> list[str]:
        return list(CANONICAL_TABLES)

    def table_contract(self, table_name: str) -> TableContract:
        if table_name not in CANONICAL_TABLES:
            raise SchemaTableMissingError(table_name)
        return _CONTRACTS[table_name]

    def pandera_schema(self, table_name: str) -> pa.DataFrameSchema:
        if table_name not in CANONICAL_TABLES:
            raise SchemaTableMissingError(table_name)
        return _PANDERA_SCHEMAS[table_name]

    def data_dictionary(self, table_name: str) -> dict[str, dict]:
        if table_name not in CANONICAL_TABLES:
            raise SchemaTableMissingError(table_name)
        return _DATA_DICTIONARIES[table_name]

    def table_aliases(self) -> dict[str, str]:
        return {f"lullaby_{name}": name for name in CANONICAL_TABLES}
