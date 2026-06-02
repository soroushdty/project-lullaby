from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype, is_numeric_dtype, is_object_dtype, is_string_dtype


class ModelingDataError(ValueError):
    """Raised when modeling inputs cannot be made into a supervised dataset."""


@dataclass
class ModelingDataBundle:
    data_dir: Path
    resolved_data_dir: Path
    participants: pd.DataFrame
    daily_vitals: pd.DataFrame
    clinical_outcomes: pd.DataFrame
    alerts: pd.DataFrame | None = None
    environment: pd.DataFrame | None = None
    load_warnings: list[str] = field(default_factory=list)
    synthetic_detected: bool = False


@dataclass
class ModelingDataset:
    participant_ids: list[str]
    observation_ids: list[str]
    y: np.ndarray
    event_dates: pd.Series
    features: pd.DataFrame
    feature_columns: list[str]
    metadata: dict[str, Any]
    source_bundle: ModelingDataBundle


_TABLE_CANDIDATES = {
    "participants": ["participants.csv", "lullaby_participants.csv"],
    "daily_vitals": ["daily_vitals.csv", "lullaby_daily_vitals.csv"],
    "clinical_outcomes": ["clinical_outcomes.csv", "lullaby_clinical_outcomes.csv"],
    "alerts": ["alerts.csv", "lullaby_alerts.csv"],
    "environment": ["environment.csv", "lullaby_environment.csv"],
}

_ALIASES = {
    "participant_id": ["participant_id", "participant.id", "id"],
    "cv_event": ["cv_event", "outcome.cv_event", "is_primary_cv_event"],
    "cv_event_date": ["cv_event_date", "outcome.cv_event_date", "event_ts", "date"],
    "date": ["date", "event_ts"],
    "study_day": ["study_day"],
    "systolic_bp": ["systolic_bp", "sbp_mean", "vital.systolic_bp"],
    "diastolic_bp": ["diastolic_bp", "dbp_mean", "vital.diastolic_bp"],
    "heart_rate": ["heart_rate", "hr_mean", "vital.heart_rate"],
    "respiratory_rate": ["respiratory_rate", "rr_mean", "vital.respiratory_rate"],
    "skin_temperature_c": ["skin_temperature_c", "skin_temp_mean_c", "temperature_c"],
    "weight_kg": ["weight_kg"],
    "body_water_pct": ["body_water_pct"],
    "sleep_hours": ["sleep_hours"],
    "steps": ["steps"],
    "active_minutes": ["active_minutes"],
    "sensor_wear_hours": ["sensor_wear_hours"],
    "scale_used": ["scale_used"],
    "ambient_temp_c": ["ambient_temp_c"],
    "heat_index_c": ["heat_index_c"],
    "alert_level": ["alert_level"],
    "called_nurse": ["called_nurse"],
}

_VITAL_FEATURES = [
    "systolic_bp",
    "diastolic_bp",
    "heart_rate",
    "respiratory_rate",
    "skin_temperature_c",
    "weight_kg",
    "body_water_pct",
    "sleep_hours",
    "steps",
    "active_minutes",
    "sensor_wear_hours",
]

_PARTICIPANT_FEATURE_CANDIDATES = [
    "age",
    "gravida",
    "para",
    "prior_csection",
    "prior_pih",
    "prior_gdm",
    "ga_delivery_weeks",
    "on_antihypertensives",
    "gestational_diabetes",
    "pre_pregnancy_bmi",
    "prior_cv_history",
    "fhx_hypertension",
    "fhx_preeclampsia",
    "fhx_stroke",
    "fhx_early_cv_disease",
    "has_ac",
    "household_size",
    "bhls_health_literacy",
    "mspss_social_support",
    "epds_depression",
    "pass_anxiety",
    "baseline_cv_risk",
    "health_literacy",
    "social_support",
    "depression",
    "anxiety",
]


def resolve_data_dir(data_dir: str | Path) -> tuple[Path, list[str]]:
    path = Path(data_dir)
    warnings: list[str] = []
    if path.exists():
        return path, warnings
    if path.as_posix().rstrip("/") == "data/raw" and Path("data").exists():
        warnings.append("data/raw not found; resolved default raw-data path to bundled data/")
        return Path("data"), warnings
    raise ModelingDataError(f"Data directory does not exist: {path}")


def _find_table(data_dir: Path, table: str, *, required: bool) -> Path | None:
    for filename in _TABLE_CANDIDATES[table]:
        candidate = data_dir / filename
        if candidate.exists():
            return candidate
    if required:
        names = ", ".join(_TABLE_CANDIDATES[table])
        raise ModelingDataError(f"Missing required {table} table; expected one of: {names}")
    return None


def _read_csv(path: Path | None) -> pd.DataFrame | None:
    if path is None:
        return None
    return pd.read_csv(path)


def _col(df: pd.DataFrame | None, role: str, *, required: bool = False) -> str | None:
    if df is None:
        if required:
            raise ModelingDataError(f"Missing table for required role {role}")
        return None
    for name in _ALIASES.get(role, [role]):
        if name in df.columns:
            return name
    if required:
        raise ModelingDataError(f"Missing required role {role}; accepted aliases: {_ALIASES.get(role, [role])}")
    return None


def _as_bool(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series.fillna(False)
    normalized = series.astype(str).str.strip().str.lower()
    truthy = {"1", "true", "yes", "y", "t"}
    falsy = {"0", "false", "no", "n", "f", "", "nan", "none"}
    unknown = sorted(set(normalized.dropna()) - truthy - falsy)
    if unknown:
        # Numeric strings such as "1.0" are common after CSV coercion.
        converted = pd.to_numeric(normalized, errors="coerce")
        if converted.notna().any():
            return converted.fillna(0).astype(float) > 0
        raise ModelingDataError(f"Cannot parse binary target values: {unknown[:5]}")
    return normalized.isin(truthy)


def _to_numeric_frame(df: pd.DataFrame, prefix: str) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    for col in df.columns:
        values = df[col]
        if is_object_dtype(values) or is_string_dtype(values):
            numeric = pd.to_numeric(values, errors="coerce")
            if numeric.notna().any():
                out[f"{prefix}{col}"] = numeric
            elif values.notna().any() and values.nunique(dropna=True) <= 12:
                dummies = pd.get_dummies(values.fillna("missing").astype(str), prefix=f"{prefix}{col}", dtype=float)
                out = pd.concat([out, dummies], axis=1)
        elif is_numeric_dtype(values) or is_bool_dtype(values):
            out[f"{prefix}{col}"] = pd.to_numeric(values, errors="coerce")
    return out


def load_modeling_tables(data_dir: str | Path) -> ModelingDataBundle:
    requested = Path(data_dir)
    resolved, warnings = resolve_data_dir(requested)
    participants = _read_csv(_find_table(resolved, "participants", required=True))
    daily_vitals = _read_csv(_find_table(resolved, "daily_vitals", required=True))
    clinical_outcomes = _read_csv(_find_table(resolved, "clinical_outcomes", required=True))
    alerts = _read_csv(_find_table(resolved, "alerts", required=False))
    environment = _read_csv(_find_table(resolved, "environment", required=False))
    assert participants is not None
    assert daily_vitals is not None
    assert clinical_outcomes is not None
    synthetic_detected = "synthetic" in resolved.as_posix().lower()
    for frame in [participants, daily_vitals, clinical_outcomes, alerts, environment]:
        if frame is not None and "synthetic_data" in frame.columns:
            synthetic_detected = synthetic_detected or bool(_as_bool(frame["synthetic_data"]).any())
    return ModelingDataBundle(
        data_dir=requested,
        resolved_data_dir=resolved,
        participants=participants.copy(deep=True),
        daily_vitals=daily_vitals.copy(deep=True),
        clinical_outcomes=clinical_outcomes.copy(deep=True),
        alerts=None if alerts is None else alerts.copy(deep=True),
        environment=None if environment is None else environment.copy(deep=True),
        load_warnings=warnings,
        synthetic_detected=synthetic_detected,
    )


def _participant_features(participants: pd.DataFrame, participant_id_col: str, include: bool) -> pd.DataFrame:
    indexed = participants.set_index(participant_id_col, drop=False)
    if not include:
        return pd.DataFrame(index=indexed.index)
    cols = [c for c in _PARTICIPANT_FEATURE_CANDIDATES if c in indexed.columns]
    also_categorical = [c for c in ["race_ethnicity", "insurance", "pih_severity", "site_code", "archetype"] if c in indexed.columns]
    return _to_numeric_frame(indexed[cols + also_categorical], "demo_")


def _eligible_rows(
    frame: pd.DataFrame,
    participant_id_col: str,
    date_col: str | None,
    pid: str,
    event_date: pd.Timestamp | pd.NaT,
    guard_days: int,
) -> pd.DataFrame:
    rows = frame[frame[participant_id_col].astype(str) == str(pid)].copy()
    if date_col is None or rows.empty:
        return rows
    rows["__model_date"] = pd.to_datetime(rows[date_col], errors="coerce")
    if pd.notna(event_date):
        cutoff = event_date - pd.Timedelta(days=int(guard_days))
        rows = rows[rows["__model_date"] < cutoff]
    return rows


def _summarize_numeric(rows: pd.DataFrame, role_names: list[str], prefix: str) -> dict[str, float]:
    summary: dict[str, float] = {}
    for role in role_names:
        col = _col(rows, role) if not rows.empty else None
        if col is None:
            continue
        values = pd.to_numeric(rows[col], errors="coerce")
        summary[f"{prefix}{role}_mean"] = float(values.mean()) if values.notna().any() else np.nan
        summary[f"{prefix}{role}_min"] = float(values.min()) if values.notna().any() else np.nan
        summary[f"{prefix}{role}_max"] = float(values.max()) if values.notna().any() else np.nan
        summary[f"{prefix}{role}_last"] = float(values.dropna().iloc[-1]) if values.notna().any() else np.nan
        summary[f"{prefix}{role}_observed_days"] = float(values.notna().sum())
    return summary


def _daily_summary(bundle: ModelingDataBundle, participant_ids: list[str], event_dates: pd.Series, guard_days: int, include: bool) -> pd.DataFrame:
    daily = bundle.daily_vitals
    pid_col = _col(daily, "participant_id", required=True)
    date_col = _col(daily, "date")
    rows = []
    for pid in participant_ids:
        eligible = _eligible_rows(daily, pid_col, date_col, pid, event_dates.get(pid, pd.NaT), guard_days)
        summary = {"participant_id": pid, "feature_window_observed_rows": float(len(eligible))}
        if include:
            summary.update(_summarize_numeric(eligible, _VITAL_FEATURES, "vital_"))
            scale_col = _col(eligible, "scale_used") if not eligible.empty else None
            if scale_col:
                summary["vital_scale_adherence"] = float(_as_bool(eligible[scale_col]).mean())
        rows.append(summary)
    return pd.DataFrame(rows).set_index("participant_id")


def _alert_summary(bundle: ModelingDataBundle, participant_ids: list[str], event_dates: pd.Series, guard_days: int, include: bool) -> pd.DataFrame:
    if bundle.alerts is None or not include:
        return pd.DataFrame(index=participant_ids)
    alerts = bundle.alerts
    pid_col = _col(alerts, "participant_id", required=True)
    date_col = _col(alerts, "date")
    level_col = _col(alerts, "alert_level")
    called_col = _col(alerts, "called_nurse")
    rows = []
    for pid in participant_ids:
        eligible = _eligible_rows(alerts, pid_col, date_col, pid, event_dates.get(pid, pd.NaT), guard_days)
        summary = {"participant_id": pid, "alert_count": float(len(eligible))}
        if level_col and not eligible.empty:
            levels = eligible[level_col].astype(str).str.lower()
            summary["alert_yellow_count"] = float((levels == "yellow").sum())
            summary["alert_red_count"] = float(levels.isin(["red", "composite-red"]).sum())
        if called_col and not eligible.empty:
            summary["alert_called_nurse_count"] = float(_as_bool(eligible[called_col]).sum())
        rows.append(summary)
    return pd.DataFrame(rows).set_index("participant_id")


def _environment_summary(bundle: ModelingDataBundle, participant_ids: list[str], event_dates: pd.Series, guard_days: int, include: bool) -> pd.DataFrame:
    if not include:
        return pd.DataFrame(index=participant_ids)
    # Prefer participant-specific daily-vitals heat context; use environment only for cohort-level
    # date context when daily heat columns are unavailable.
    daily = bundle.daily_vitals
    heat_roles = [role for role in ["ambient_temp_c", "heat_index_c"] if _col(daily, role) is not None]
    if not heat_roles:
        return pd.DataFrame(index=participant_ids)
    pid_col = _col(daily, "participant_id", required=True)
    date_col = _col(daily, "date")
    rows = []
    for pid in participant_ids:
        eligible = _eligible_rows(daily, pid_col, date_col, pid, event_dates.get(pid, pd.NaT), guard_days)
        summary = {"participant_id": pid}
        summary.update(_summarize_numeric(eligible, heat_roles, "env_"))
        rows.append(summary)
    return pd.DataFrame(rows).set_index("participant_id")


def build_modeling_dataset(data_dir: str | Path, config: dict[str, Any]) -> ModelingDataset:
    bundle = load_modeling_tables(data_dir)
    participants = bundle.participants
    outcomes = bundle.clinical_outcomes
    participant_col = _col(participants, "participant_id", required=True)
    outcome_pid_col = _col(outcomes, "participant_id", required=True)
    target_col = _col(outcomes, "cv_event", required=True)
    event_date_col = _col(outcomes, "cv_event_date")

    participants = participants.copy()
    participants[participant_col] = participants[participant_col].astype(str)
    participant_ids = participants[participant_col].tolist()

    outcome_indexed = outcomes.copy()
    outcome_indexed[outcome_pid_col] = outcome_indexed[outcome_pid_col].astype(str)
    outcome_indexed = outcome_indexed.drop_duplicates(outcome_pid_col).set_index(outcome_pid_col)
    y_series = _as_bool(outcome_indexed.reindex(participant_ids)[target_col]).fillna(False)
    y = y_series.astype(int).to_numpy()
    if len(np.unique(y)) < 2:
        raise ModelingDataError("Target outcome.cv_event must contain at least two classes")

    if event_date_col:
        event_dates = pd.to_datetime(outcome_indexed.reindex(participant_ids)[event_date_col], errors="coerce")
    else:
        event_dates = pd.Series(pd.NaT, index=participant_ids, dtype="datetime64[ns]")
    event_dates.index = participant_ids

    features_config = config.get("features", {})
    guard_days = int(features_config.get("leakage_guard_days_before_event", 0) or 0)
    participant_frame = _participant_features(
        participants,
        participant_col,
        bool(features_config.get("include_demographics", True)),
    )
    daily_frame = _daily_summary(
        bundle,
        participant_ids,
        event_dates,
        guard_days,
        bool(features_config.get("include_daily_vitals_summary", True)),
    )
    alert_frame = _alert_summary(
        bundle,
        participant_ids,
        event_dates,
        guard_days,
        bool(features_config.get("include_alert_history", True)),
    )
    env_frame = _environment_summary(
        bundle,
        participant_ids,
        event_dates,
        guard_days,
        bool(features_config.get("include_environment", True)),
    )

    features = pd.concat(
        [
            participant_frame.reindex(participant_ids),
            daily_frame.reindex(participant_ids),
            alert_frame.reindex(participant_ids),
            env_frame.reindex(participant_ids),
        ],
        axis=1,
    )
    features = features.loc[:, ~features.columns.duplicated()]
    features = features.replace([np.inf, -np.inf], np.nan)
    if features.empty:
        raise ModelingDataError("No modeling features could be constructed from enabled feature groups")

    no_pre_event = []
    for pid, target in zip(participant_ids, y):
        no_pre_event.append(bool(target == 1 and daily_frame.loc[pid, "feature_window_observed_rows"] == 0))

    metadata = {
        "n_participants": len(participant_ids),
        "n_events": int(y.sum()),
        "synthetic_detected": bundle.synthetic_detected,
        "load_warnings": bundle.load_warnings,
        "feature_groups": {
            "demographics": bool(features_config.get("include_demographics", True)),
            "daily_vitals_summary": bool(features_config.get("include_daily_vitals_summary", True)),
            "alert_history": bool(features_config.get("include_alert_history", True)) and bundle.alerts is not None,
            "environment": bool(features_config.get("include_environment", True)),
        },
        "leakage_guard_days_before_event": guard_days,
        "no_pre_event_observations": dict(zip(participant_ids, no_pre_event)),
    }
    return ModelingDataset(
        participant_ids=participant_ids,
        observation_ids=participant_ids.copy(),
        y=y.astype(int),
        event_dates=event_dates,
        features=features.astype(float),
        feature_columns=list(features.columns),
        metadata=metadata,
        source_bundle=bundle,
    )
