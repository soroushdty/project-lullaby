from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json

import numpy as np
import pandas as pd
import yaml

from src.simulation.config import SimulationConfig
from src.simulation.environment import generate_environment
from src.simulation.missingness import (
    OBSERVED_VALUE_COLUMNS,
    adherence_values,
    dropout_day,
    row_missing_probability,
)
from src.simulation.physiology import bounded_uniform, cv_ramp_multiplier, heat_skin_spike_c


@dataclass
class SimulationTables:
    participants: pd.DataFrame
    daily_vitals: pd.DataFrame
    alerts: pd.DataFrame
    staff_contacts: pd.DataFrame
    clinical_outcomes: pd.DataFrame
    environment: pd.DataFrame
    recruitment: pd.DataFrame

    def as_dict(self) -> dict[str, pd.DataFrame]:
        return {
            "participants": self.participants,
            "daily_vitals": self.daily_vitals,
            "alerts": self.alerts,
            "staff_contacts": self.staff_contacts,
            "clinical_outcomes": self.clinical_outcomes,
            "environment": self.environment,
            "recruitment": self.recruitment,
        }


PARTICIPANT_COLUMNS = [
    "participant_id",
    "site_code",
    "enrollment_date",
    "delivery_date",
    "observation_start_date",
    "archetype",
    "baseline_cv_risk",
    "pih_severity",
    "has_ac",
    "gestational_diabetes",
    "health_literacy",
    "social_support",
    "depression",
    "anxiety",
    "synthetic_data",
]

DAILY_COLUMNS = [
    "participant_id",
    "date",
    "study_day",
    "week",
    "archetype",
    "latent_cv_risk",
    "latent_heat_exposure",
    "latent_adherence_probability",
    "latent_missingness_probability",
    "dropout_active",
    "cv_event_window",
    "heat_strain_day",
    "overlap_day",
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
    "scale_used",
    "ambient_temp_c",
    "heat_index_c",
    "heat_wave",
    "heat_exposure_level",
    "missingness_reasons",
    "synthetic_data",
]

ALERT_COLUMNS = [
    "alert_id",
    "participant_id",
    "date",
    "alert_hour",
    "alert_level",
    "trigger_reasons",
    "classification",
    "called_nurse",
    "survey_completed",
    "synthetic_data",
]

CONTACT_COLUMNS = [
    "contact_id",
    "participant_id",
    "contact_date",
    "contact_type",
    "contact_week",
    "completed",
    "reason",
    "related_alert_id",
    "synthetic_data",
]

OUTCOME_COLUMNS = [
    "participant_id",
    "cv_event",
    "cv_event_type",
    "cv_event_date",
    "heat_illness",
    "heat_illness_date",
    "ed_visit",
    "hospitalized",
    "synthetic_data",
]

RECRUITMENT_COLUMNS = [
    "participant_id",
    "recruitment_date",
    "recruitment_source",
    "eligible",
    "enrolled",
    "decline_reason",
    "synthetic_data",
]


def generate_cohort_tables(config: SimulationConfig) -> SimulationTables:
    environment = generate_environment(config)
    participants = _generate_participants(config)
    event_plan = _assign_events(config, participants, environment)
    recruitment = _generate_recruitment(config, participants)
    daily_vitals = _generate_daily_vitals(config, participants, environment, event_plan)
    alerts, contacts = _derive_alerts_and_contacts(config, daily_vitals)
    outcomes = _derive_outcomes(participants, event_plan)
    return SimulationTables(
        participants=participants[PARTICIPANT_COLUMNS],
        daily_vitals=daily_vitals[DAILY_COLUMNS],
        alerts=alerts[ALERT_COLUMNS],
        staff_contacts=contacts[CONTACT_COLUMNS],
        clinical_outcomes=outcomes[OUTCOME_COLUMNS],
        environment=environment,
        recruitment=recruitment[RECRUITMENT_COLUMNS],
    )


def _generate_participants(config: SimulationConfig) -> pd.DataFrame:
    rng = config.rng_for("participants")
    counts = _counts_from_weights(
        [item.normalized_weight for item in config.archetypes],
        config.n_participants,
    )
    archetypes: list[str] = []
    for item, count in zip(config.archetypes, counts):
        archetypes.extend([item.name] * count)
    rng.shuffle(archetypes)
    start = pd.Timestamp(config.summer_heat.start_date)
    rows: list[dict[str, Any]] = []
    for index, archetype in enumerate(archetypes, start=1):
        delivery_offset = int(rng.integers(1, 8))
        enrollment_offset = int(rng.integers(4, 18))
        profile = _profile_for_archetype(archetype, rng)
        rows.append(
            {
                "participant_id": f"P{index:04d}",
                "site_code": "PHX" if index % 3 else "MESA",
                "enrollment_date": (start - pd.Timedelta(days=enrollment_offset)).date().isoformat(),
                "delivery_date": (start - pd.Timedelta(days=delivery_offset)).date().isoformat(),
                "observation_start_date": start.date().isoformat(),
                "archetype": archetype,
                "synthetic_data": True,
                **profile,
            }
        )
    return pd.DataFrame(rows).sort_values("participant_id").reset_index(drop=True)


def _profile_for_archetype(archetype: str, rng: np.random.Generator) -> dict[str, Any]:
    baseline = {
        "diligent_monitor": 0.25,
        "overwhelmed_mom": 0.45,
        "heat_stressed": 0.40,
        "true_emergency": 0.85,
        "silent_decliner": 0.72,
    }.get(archetype, 0.4)
    return {
        "baseline_cv_risk": round(float(np.clip(rng.normal(baseline, 0.08), 0.05, 0.98)), 3),
        "pih_severity": "severe" if archetype in {"true_emergency", "silent_decliner"} else "mild",
        "has_ac": bool(archetype not in {"heat_stressed"} and rng.random() > 0.12),
        "gestational_diabetes": bool(rng.random() < (0.24 if archetype in {"true_emergency", "silent_decliner"} else 0.12)),
        "health_literacy": round(float(np.clip(rng.normal(3.7 if archetype == "diligent_monitor" else 2.8, 0.5), 1, 5)), 2),
        "social_support": round(float(np.clip(rng.normal(4.0 if archetype == "diligent_monitor" else 3.0, 0.6), 1, 5)), 2),
        "depression": round(float(np.clip(rng.normal(6 if archetype == "diligent_monitor" else 11, 3), 0, 30)), 1),
        "anxiety": round(float(np.clip(rng.normal(8 if archetype == "diligent_monitor" else 14, 4), 0, 30)), 1),
    }


def _assign_events(
    config: SimulationConfig,
    participants: pd.DataFrame,
    environment: pd.DataFrame,
) -> dict[str, dict[str, Any]]:
    rng = config.rng_for("events")
    ids = participants["participant_id"].tolist()
    plan = {
        participant_id: {
            "cv_event": False,
            "cv_event_type": "",
            "cv_event_day": None,
            "heat_illness": False,
            "heat_illness_day": None,
            "ed_visit": False,
            "hospitalized": False,
        }
        for participant_id in ids
    }
    by_archetype = {
        name: participants.loc[participants["archetype"] == name, "participant_id"].tolist()
        for name in participants["archetype"].unique()
    }
    cv_ids = _choose_priority_ids(
        rng,
        _target_count(config.event_rate.cv_event, config.n_participants),
        [by_archetype.get("true_emergency", []), by_archetype.get("silent_decliner", []), ids],
    )
    heat_priority = by_archetype.get("heat_stressed", []) + cv_ids[: max(1, min(5, len(cv_ids)))]
    heat_ids = _choose_priority_ids(
        rng,
        _target_count(config.event_rate.heat_illness, config.n_participants),
        [heat_priority, by_archetype.get("overwhelmed_mom", []), ids],
    )
    ed_ids = _choose_priority_ids(
        rng,
        _target_count(config.event_rate.ed_visit, config.n_participants),
        [cv_ids + heat_ids, ids],
    )
    hospital_ids = _choose_priority_ids(
        rng,
        _target_count(config.event_rate.hospitalization, config.n_participants),
        [cv_ids, ed_ids, ids],
    )
    hot_days = environment.loc[environment["heat_exposure_level"].isin(["high", "extreme"]), "study_day"].astype(int).tolist()
    if not hot_days:
        hot_days = list(range(max(2, config.study_days // 3), config.study_days + 1))
    for index, participant_id in enumerate(cv_ids):
        day = int(rng.integers(max(14, config.study_days // 4), max(15, config.study_days - 3)))
        plan[participant_id].update(
            {
                "cv_event": True,
                "cv_event_type": "primary_cv_composite",
                "cv_event_day": day,
            }
        )
    for participant_id in heat_ids:
        if plan[participant_id]["cv_event"] and plan[participant_id]["cv_event_day"] is not None:
            day = max(1, int(plan[participant_id]["cv_event_day"]) - 2)
        else:
            day = int(rng.choice(hot_days))
        plan[participant_id].update({"heat_illness": True, "heat_illness_day": day})
    for participant_id in ed_ids:
        plan[participant_id]["ed_visit"] = True
    for participant_id in hospital_ids:
        plan[participant_id]["hospitalized"] = True
    return plan


def _generate_recruitment(config: SimulationConfig, participants: pd.DataFrame) -> pd.DataFrame:
    rng = config.rng_for("recruitment")
    sources = np.array(["clinic_referral", "community_partner", "postpartum_unit"])
    rows = []
    for _, participant in participants.iterrows():
        recruitment_date = (
            pd.Timestamp(participant["enrollment_date"]) - pd.Timedelta(days=int(rng.integers(1, 8)))
        ).date().isoformat()
        rows.append(
            {
                "participant_id": participant["participant_id"],
                "recruitment_date": recruitment_date,
                "recruitment_source": str(rng.choice(sources)),
                "eligible": True,
                "enrolled": True,
                "decline_reason": "",
                "synthetic_data": True,
            }
        )
    return pd.DataFrame(rows)


def _generate_daily_vitals(
    config: SimulationConfig,
    participants: pd.DataFrame,
    environment: pd.DataFrame,
    event_plan: dict[str, dict[str, Any]],
) -> pd.DataFrame:
    rng = config.rng_for("daily_vitals")
    missing_rng = config.rng_for("missingness")
    dropout_count = _target_count(config.missingness.participant_dropout_rate, config.n_participants)
    dropout_ids = set(_choose_priority_ids(missing_rng, dropout_count, [
        participants.loc[participants["archetype"].isin(["silent_decliner", "overwhelmed_mom"]), "participant_id"].tolist(),
        participants["participant_id"].tolist(),
    ]))
    dropout_days = {
        participant_id: dropout_day(config, idx, participant_id in dropout_ids, missing_rng)
        for idx, participant_id in enumerate(participants["participant_id"], start=1)
    }
    cv_slopes = {
        row.participant_id: (
            bounded_uniform(rng, config.physiology.cv_bp_slope_per_day),
            bounded_uniform(rng, config.physiology.cv_hr_slope_per_day),
            bounded_uniform(rng, config.physiology.cv_body_water_slope_per_day),
        )
        for row in participants.itertuples(index=False)
    }
    rows: list[dict[str, Any]] = []
    for participant in participants.itertuples(index=False):
        plan = event_plan[participant.participant_id]
        for env in environment.itertuples(index=False):
            week = int((int(env.study_day) - 1) // 7 + 1)
            row = _base_daily_row(config, participant, env, week, rng)
            row.update(_event_state(config, participant.participant_id, int(env.study_day), plan, cv_slopes, rng))
            row = _apply_missingness(
                config,
                row,
                participant.archetype,
                dropout_days[participant.participant_id],
                week,
                missing_rng,
            )
            rows.append(row)
    return pd.DataFrame(rows).sort_values(["participant_id", "study_day"]).reset_index(drop=True)


def _base_daily_row(
    config: SimulationConfig,
    participant: Any,
    env: Any,
    week: int,
    rng: np.random.Generator,
) -> dict[str, Any]:
    risk = float(participant.baseline_cv_risk)
    archetype = str(participant.archetype)
    heat_latent = {"low": 0.1, "moderate": 0.35, "high": 0.7, "extreme": 0.9}.get(env.heat_exposure_level, 0.2)
    wear, scale_used = adherence_values(config, archetype, week, rng)
    return {
        "participant_id": participant.participant_id,
        "date": env.date,
        "study_day": int(env.study_day),
        "week": week,
        "archetype": archetype,
        "latent_cv_risk": round(risk, 3),
        "latent_heat_exposure": round(heat_latent, 3),
        "latent_adherence_probability": round(wear / 24.0, 3),
        "latent_missingness_probability": 0.0,
        "dropout_active": False,
        "cv_event_window": False,
        "heat_strain_day": False,
        "overlap_day": False,
        "systolic_bp": round(float(rng.normal(116 + risk * 18, 5)), 1),
        "diastolic_bp": round(float(rng.normal(74 + risk * 10, 4)), 1),
        "heart_rate": round(float(rng.normal(76 + risk * 8 + heat_latent * 4, 5)), 1),
        "respiratory_rate": round(float(rng.normal(16 + heat_latent, 1.4)), 1),
        "skin_temperature_c": round(float(rng.normal(36.55 + heat_latent * 0.25, 0.18)), 2),
        "weight_kg": round(float(rng.normal(78 - risk * 2, 6)), 2),
        "body_water_pct": round(float(rng.normal(49.5 + risk * 1.5, 1.4)), 2),
        "sleep_hours": round(float(np.clip(rng.normal(6.7 - risk * 0.8, 1.0), 2.5, 10.5)), 2),
        "steps": int(np.clip(rng.normal(5200 - risk * 1500 - heat_latent * 900, 900), 300, 12000)),
        "active_minutes": int(np.clip(rng.normal(42 - risk * 12 - heat_latent * 9, 10), 0, 160)),
        "sensor_wear_hours": round(wear, 2),
        "scale_used": scale_used,
        "ambient_temp_c": env.ambient_temp_c,
        "heat_index_c": env.heat_index_c,
        "heat_wave": bool(env.heat_wave),
        "heat_exposure_level": env.heat_exposure_level,
        "missingness_reasons": "",
        "synthetic_data": True,
    }


def _event_state(
    config: SimulationConfig,
    participant_id: str,
    study_day: int,
    plan: dict[str, Any],
    cv_slopes: dict[str, tuple[float, float, float]],
    rng: np.random.Generator,
) -> dict[str, Any]:
    updates: dict[str, Any] = {}
    cv_multiplier = cv_ramp_multiplier(study_day, plan.get("cv_event_day"))
    heat_day = plan.get("heat_illness_day")
    heat_multiplier = 1.0 if heat_day is not None and study_day == int(heat_day) else 0.0
    if cv_multiplier > 0:
        bp_slope, hr_slope, water_slope = cv_slopes[participant_id]
        updates.update(
            {
                "cv_event_window": True,
                "systolic_bp_delta": bp_slope * cv_multiplier,
                "diastolic_bp_delta": bp_slope * cv_multiplier * 0.55,
                "heart_rate_delta": hr_slope * cv_multiplier,
                "body_water_delta": (water_slope + 0.35) * cv_multiplier,
            }
        )
    if heat_multiplier > 0 and config.summer_heat.enabled:
        updates.update(
            {
                "heat_strain_day": True,
                "heart_rate_delta": updates.get("heart_rate_delta", 0.0)
                + bounded_uniform(rng, config.physiology.heat_hr_spike) * heat_multiplier,
                "skin_temperature_delta": heat_skin_spike_c(config.physiology.heat_skin_temp_spike_f, rng),
                "body_water_delta": updates.get("body_water_delta", 0.0)
                - (bounded_uniform(rng, config.physiology.heat_body_water_drop) + 2.0),
            }
        )
    return updates


def _apply_missingness(
    config: SimulationConfig,
    row: dict[str, Any],
    archetype: str,
    participant_dropout_day: int | None,
    week: int,
    rng: np.random.Generator,
) -> dict[str, Any]:
    for delta_name, target in (
        ("systolic_bp_delta", "systolic_bp"),
        ("diastolic_bp_delta", "diastolic_bp"),
        ("heart_rate_delta", "heart_rate"),
        ("skin_temperature_delta", "skin_temperature_c"),
        ("body_water_delta", "body_water_pct"),
    ):
        if delta_name in row:
            row[target] = round(float(row[target] + row.pop(delta_name)), 2)
    row["overlap_day"] = bool(row["cv_event_window"] and row["heat_strain_day"])
    probability = row_missing_probability(
        config,
        archetype,
        heat_exposure_level=str(row["heat_exposure_level"]),
        cv_event_window=bool(row["cv_event_window"]),
        heat_strain_day=bool(row["heat_strain_day"]),
        week=week,
    )
    row["latent_missingness_probability"] = round(probability, 3)
    reasons: list[str] = []
    if participant_dropout_day is not None and int(row["study_day"]) >= participant_dropout_day:
        row["dropout_active"] = True
        reasons.append("dropout")
        for column in (*OBSERVED_VALUE_COLUMNS, "sensor_wear_hours", "scale_used"):
            row[column] = None
        row["missingness_reasons"] = ";".join(reasons)
        return row
    if str(row["heat_exposure_level"]) in {"high", "extreme"}:
        reasons.append("heat_context")
    if archetype in {"overwhelmed_mom", "silent_decliner"}:
        reasons.append("archetype_burden")
    clustered = bool(rng.random() < config.missingness.clustered_gap_probability * probability)
    for column in OBSERVED_VALUE_COLUMNS:
        protected_signal = (
            bool(row["cv_event_window"]) and column in {"systolic_bp", "heart_rate", "body_water_pct"}
        ) or (bool(row["heat_strain_day"]) and column in {"heart_rate", "skin_temperature_c", "body_water_pct"})
        column_probability = probability * (1.7 if clustered else 1.0)
        if not protected_signal and rng.random() < column_probability:
            row[column] = None
            reasons.append("clustered_gap" if clustered else "mcar_mar_mnar_proxy")
    if row["scale_used"] is False:
        row["weight_kg"] = None
    row["missingness_reasons"] = ";".join(dict.fromkeys(reasons))
    return row


def _derive_alerts_and_contacts(
    config: SimulationConfig,
    daily_vitals: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    thresholds = _load_thresholds(config.alerts.meows_thresholds_path)
    alert_rng = config.rng_for("alerts")
    alerts: list[dict[str, Any]] = []
    contacts: list[dict[str, Any]] = []
    alert_index = 1
    contact_index = 1
    candidate_rows = daily_vitals.loc[
        daily_vitals["cv_event_window"].fillna(False)
        | daily_vitals["heat_strain_day"].fillna(False)
        | (pd.to_numeric(daily_vitals["systolic_bp"], errors="coerce") >= thresholds["yellow"]["systolic_bp_min"])
    ]
    for row in candidate_rows.itertuples(index=False):
        level, classification, reasons = _classify_alert(row, thresholds)
        if not reasons:
            continue
        alert_id = f"A{alert_index:05d}"
        called = bool(alert_rng.random() < config.alerts.call_completion_probability)
        surveyed = bool(alert_rng.random() < config.alerts.survey_completion_probability)
        alerts.append(
            {
                "alert_id": alert_id,
                "participant_id": row.participant_id,
                "date": row.date,
                "alert_hour": int(alert_rng.integers(8, 21)),
                "alert_level": level,
                "trigger_reasons": ";".join(reasons),
                "classification": classification,
                "called_nurse": called,
                "survey_completed": surveyed,
                "synthetic_data": True,
            }
        )
        for contact_type, completed, reason in (
            ("survey", surveyed, "alert_survey"),
            ("nurse_call", called, "alert_follow_up"),
        ):
            contacts.append(
                {
                    "contact_id": f"C{contact_index:05d}",
                    "participant_id": row.participant_id,
                    "contact_date": row.date,
                    "contact_type": contact_type,
                    "contact_week": int(row.week),
                    "completed": completed,
                    "reason": reason,
                    "related_alert_id": alert_id,
                    "synthetic_data": True,
                }
            )
            contact_index += 1
        alert_index += 1
    return pd.DataFrame(alerts, columns=ALERT_COLUMNS), pd.DataFrame(contacts, columns=CONTACT_COLUMNS)


def _classify_alert(row: Any, thresholds: dict[str, Any]) -> tuple[str, str, list[str]]:
    reasons: list[str] = []
    cv_red = _ge(row.systolic_bp, thresholds["red"]["systolic_bp_min"]) or _ge(row.diastolic_bp, thresholds["red"]["diastolic_bp_min"])
    cv_yellow = _ge(row.systolic_bp, thresholds["yellow"]["systolic_bp_min"]) or _ge(row.diastolic_bp, thresholds["yellow"]["diastolic_bp_min"])
    heat_signal = (
        bool(row.heat_strain_day)
        or (
            _ge(row.heart_rate, thresholds["heat"]["heart_rate_min"])
            and _ge(row.skin_temperature_c, thresholds["heat"]["skin_temperature_c_min"])
            and _ge(row.heat_index_c, thresholds["heat"]["heat_index_c_min"])
        )
    )
    composite = (
        _ge(row.systolic_bp, thresholds["composite"]["systolic_bp_min"])
        and _ge(row.heart_rate, thresholds["composite"]["heart_rate_min"])
        and _ge(row.heat_index_c, thresholds["composite"]["heat_index_c_min"])
    )
    if cv_red:
        reasons.append("red_bp")
    elif cv_yellow or bool(row.cv_event_window):
        reasons.append("yellow_bp_or_cv_window")
    if heat_signal:
        reasons.append("heat_strain")
    if composite or (bool(row.cv_event_window) and heat_signal):
        return "composite-red", "overlap", reasons + ["composite"]
    if cv_red:
        return "red", "cv_like", reasons
    if heat_signal:
        return "yellow", "heat_like", reasons
    if cv_yellow or bool(row.cv_event_window):
        return "yellow", "cv_like", reasons
    return "yellow", "other", reasons


def _derive_outcomes(
    participants: pd.DataFrame,
    event_plan: dict[str, dict[str, Any]],
) -> pd.DataFrame:
    rows = []
    start_dates = participants.set_index("participant_id")["observation_start_date"].to_dict()
    for participant_id in participants["participant_id"]:
        plan = event_plan[participant_id]
        start = pd.Timestamp(start_dates[participant_id])
        cv_date = _event_date(start, plan.get("cv_event_day"))
        heat_date = _event_date(start, plan.get("heat_illness_day"))
        rows.append(
            {
                "participant_id": participant_id,
                "cv_event": bool(plan["cv_event"]),
                "cv_event_type": plan["cv_event_type"],
                "cv_event_date": cv_date,
                "heat_illness": bool(plan["heat_illness"]),
                "heat_illness_date": heat_date,
                "ed_visit": bool(plan["ed_visit"]),
                "hospitalized": bool(plan["hospitalized"]),
                "synthetic_data": True,
            }
        )
    return pd.DataFrame(rows)


def _event_date(start: pd.Timestamp, study_day: int | None) -> str:
    if study_day is None:
        return ""
    return (start + pd.Timedelta(days=int(study_day) - 1)).date().isoformat()


def _load_thresholds(path: str | Path) -> dict[str, Any]:
    threshold_path = Path(path)
    if not threshold_path.exists():
        raise FileNotFoundError(f"MEOWS threshold config not found: {threshold_path}")
    data = yaml.safe_load(threshold_path.read_text()) or {}
    required = {"yellow", "red", "heat", "composite"}
    missing = required.difference(data)
    if missing:
        raise ValueError(f"MEOWS threshold config missing sections: {', '.join(sorted(missing))}")
    return data


def _target_count(rate: float, n: int) -> int:
    return int(round(float(rate) * n))


def _counts_from_weights(weights: list[float], total: int) -> list[int]:
    raw = np.array(weights, dtype=float) * total
    counts = np.floor(raw).astype(int)
    remainder = total - int(counts.sum())
    if remainder:
        order = np.argsort(-(raw - counts))
        for index in order[:remainder]:
            counts[index] += 1
    return [int(value) for value in counts]


def _choose_priority_ids(
    rng: np.random.Generator,
    count: int,
    priority_groups: list[list[str]],
) -> list[str]:
    chosen: list[str] = []
    seen: set[str] = set()
    for group in priority_groups:
        available = [item for item in group if item not in seen]
        rng.shuffle(available)
        for item in available:
            if len(chosen) >= count:
                return chosen
            chosen.append(item)
            seen.add(item)
    return chosen


def _ge(value: Any, threshold: float) -> bool:
    if value is None or pd.isna(value):
        return False
    return float(value) >= float(threshold)


def tables_to_jsonable_summary(tables: SimulationTables) -> dict[str, Any]:
    return {name: {"rows": len(df), "columns": list(df.columns)} for name, df in tables.as_dict().items()}


def dump_tables_debug(tables: SimulationTables, path: Path) -> None:
    path.write_text(json.dumps(tables_to_jsonable_summary(tables), indent=2, sort_keys=True) + "\n")
