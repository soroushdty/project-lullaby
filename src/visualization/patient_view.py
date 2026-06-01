from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

from src.visualization import schema_registry as registry
from src.visualization.design import DEFAULT_STYLE, add_dashboard_title, configure_style, render_warning_panel, save_figure, style_card


@dataclass(frozen=True)
class TimelineRenderResult:
    artifact_id: str
    path: Path
    title: str
    warnings: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)


def render_patient_timeline(
    *,
    participants: pd.DataFrame,
    daily_vitals: pd.DataFrame,
    alerts: pd.DataFrame,
    staff_contacts: pd.DataFrame,
    clinical_outcomes: pd.DataFrame,
    environment: pd.DataFrame,
    selected: Any,
    data_source: str,
    out_dir: Path,
    overlay_environment: bool = False,
    week_start: int | None = None,
    week_end: int | None = None,
) -> TimelineRenderResult:
    configure_style()
    participant_id = selected.participant_id
    daily = _with_study_day(daily_vitals)
    participant_daily = _participant_rows(daily, participant_id, "vital.participant_id", "daily_vitals")
    fig = plt.figure(figsize=(16, 9), constrained_layout=False)
    add_dashboard_title(
        fig,
        "Single-Participant Clinical Timeline",
        f"Source: {data_source} | participant: {participant_id} | shared study-day axis | no imputation",
    )
    gs = fig.add_gridspec(5, 4, left=0.04, right=0.98, top=0.88, bottom=0.07, wspace=0.34, hspace=0.58)
    warnings: list[str] = []
    summary_fields, summary_warnings = _summary_fields(participants, participant_id)
    warnings.extend(summary_warnings)
    _summary_card(fig.add_subplot(gs[0, 0]), participant_id, summary_fields)
    track_counts = {
        "vital_tracks": 0,
        "alert_markers": 0,
        "contact_markers": 0,
        "outcome_markers": 0,
    }
    vital_gap_days: dict[str, list[int]] = {}
    axes = [
        fig.add_subplot(gs[0, 1:4]),
        fig.add_subplot(gs[1, :2]),
        fig.add_subplot(gs[1, 2:4]),
        fig.add_subplot(gs[2, :2]),
        fig.add_subplot(gs[2, 2:4]),
    ]
    vital_groups = [
        ["vital.systolic_bp", "vital.diastolic_bp"],
        ["vital.heart_rate", "vital.respiratory_rate"],
        ["vital.skin_temperature_c"],
        ["vital.weight_kg", "vital.body_water_pct"],
        ["vital.sleep_hours", "vital.steps"],
    ]
    for ax, roles in zip(axes, vital_groups, strict=False):
        plotted, gaps = _plot_vital_group(ax, participant_daily, participant_id, roles)
        track_counts["vital_tracks"] += plotted
        vital_gap_days.update(gaps)
    if overlay_environment:
        _overlay_environment(axes[0], environment, daily, participant_daily)
    reference_start = _timeline_start(participant_daily)
    alert_events = _event_days(alerts, participant_id, "alert.participant_id", "alert.date", reference_start=reference_start)
    contact_events = _event_days(staff_contacts, participant_id, "contact.participant_id", "contact.date", reference_start=reference_start)
    outcome_events = _event_days(clinical_outcomes, participant_id, "outcome.participant_id", "outcome.cv_event_date", reference_start=reference_start)
    track_counts["alert_markers"] = len(alert_events)
    track_counts["contact_markers"] = len(contact_events)
    track_counts["outcome_markers"] = len(outcome_events)
    _events_panel(fig.add_subplot(gs[3, :]), alert_events, contact_events, outcome_events)
    _wear_missingness_panel(fig.add_subplot(gs[4, :]), participant_daily)
    metadata = {
        "selected_participant": selected.to_metadata(),
        "summary_fields": summary_fields,
        "track_counts": track_counts,
        "has_missingness_wear_track": True,
        "vital_gap_days": vital_gap_days,
        "imputation_performed": False,
        "week_filter": {"week_start": week_start, "week_end": week_end},
    }
    path = out_dir / "07_patient_timeline.png"
    save_figure(fig, path)
    plt.close(fig)
    return TimelineRenderResult(
        "eda_longitudinal_07_patient_timeline",
        path,
        "Single-Participant Clinical Timeline",
        warnings,
        metadata,
    )


def _summary_fields(participants: pd.DataFrame, participant_id: str) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    participant_col = _role_column(participants, "participant.id", entity="participants") or "participant_id"
    row = participants[participants[participant_col].astype(str) == str(participant_id)].head(1)
    if row.empty:
        return {}, [f"participant summary unavailable for {participant_id}"]
    record = row.iloc[0]
    fields = {
        "pih_severity": _first_value(record, "pih_severity"),
        "ac_access": _first_value(record, "has_ac"),
        "insurance": _first_value(record, "insurance", "payer"),
        "parity": _first_value(record, "para", "parity"),
        "health_literacy": _first_value(record, "bhls_health_literacy", "health_literacy"),
        "social_support": _first_value(record, "mspss_social_support", "social_support"),
        "depression": _first_value(record, "epds_depression", "depression"),
        "anxiety": _first_value(record, "pass_anxiety", "anxiety"),
    }
    for key, value in fields.items():
        if value == "Unavailable":
            warnings.append(f"summary field unavailable: {key}")
    return fields, warnings


def _summary_card(ax, participant_id: str, fields: dict[str, Any]) -> None:
    style_card(ax, "Participant Summary")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.text(0.05, 0.88, participant_id, transform=ax.transAxes, fontsize=14, fontweight="bold")
    y = 0.72
    for key, value in fields.items():
        ax.text(0.05, y, f"{key.replace('_', ' ').title()}: {value}", transform=ax.transAxes, fontsize=8.5)
        y -= 0.10


def _plot_vital_group(ax, daily: pd.DataFrame, participant_id: str, roles: list[str]) -> tuple[int, dict[str, list[int]]]:
    style_card(ax, " / ".join(registry.get_role(role).label for role in roles))
    gaps: dict[str, list[int]] = {}
    plotted = 0
    for idx, role_id in enumerate(roles):
        series = _selected_vital_series(daily, participant_id, role_id)
        if series.empty:
            continue
        role = registry.get_role(role_id)
        color = DEFAULT_STYLE.palette[idx % len(DEFAULT_STYLE.palette)]
        ax.plot(series["study_day"], series["value"], marker="o", linewidth=1.5, label=role.label, color=color)
        _reference_band(ax, role)
        gap_days = series.loc[series["value"].isna(), "study_day"].astype(int).tolist()
        if gap_days:
            gaps[role_id] = gap_days
        _label_capture_extreme(ax, series, role)
        plotted += 1
    ax.set_xlabel("Study day")
    ax.legend(loc="upper right", fontsize=7)
    return plotted, gaps


def _reference_band(ax, role: registry.SemanticRole) -> None:
    if role.capture_worthy_range is None:
        return
    low, high = role.capture_worthy_range
    if low is not None and high is not None:
        ax.axhspan(low, high, color=DEFAULT_STYLE.palette[2], alpha=0.08)


def _label_capture_extreme(ax, series: pd.DataFrame, role: registry.SemanticRole) -> None:
    if role.capture_worthy_range is None or series["value"].dropna().empty:
        return
    low, high = role.capture_worthy_range
    observed = series.dropna(subset=["value"])
    mask = pd.Series(False, index=observed.index)
    if low is not None:
        mask |= observed["value"] < low
    if high is not None:
        mask |= observed["value"] > high
    if not mask.any():
        return
    row = observed.loc[mask].iloc[0]
    ax.text(row["study_day"], row["value"], f"capture-worthy {row['value']:.1f}", fontsize=7, color=DEFAULT_STYLE.capture_worthy_color)


def _events_panel(ax, alert_days: list[int], contact_days: list[int], outcome_days: list[int]) -> None:
    style_card(ax, "Alerts, Contacts, and Outcomes")
    ax.set_ylim(-0.5, 2.5)
    ax.set_yticks([0, 1, 2], ["Alerts", "Contacts", "Outcomes"])
    for day in alert_days:
        ax.scatter(day, 0, marker="^", color=DEFAULT_STYLE.warning_color, s=70)
        ax.text(day, 0.12, "alert", fontsize=7, ha="center")
    for day in contact_days:
        ax.scatter(day, 1, marker="s", color=DEFAULT_STYLE.palette[0], s=55)
        ax.text(day, 1.12, "contact", fontsize=7, ha="center")
    for day in outcome_days:
        ax.scatter(day, 2, marker="*", color=DEFAULT_STYLE.capture_worthy_color, s=95)
        ax.text(day, 2.12, "outcome", fontsize=7, ha="center")
    ax.set_xlabel("Study day")
    ax.text(0.02, 0.04, "Event markers use required participant id and event-date roles.", transform=ax.transAxes, fontsize=8, color=DEFAULT_STYLE.muted_text_color)


def _wear_missingness_panel(ax, daily: pd.DataFrame) -> None:
    style_card(ax, "Missingness / Wear Track")
    if daily.empty:
        ax.text(0.04, 0.70, "No daily records for selected participant.", transform=ax.transAxes, color=DEFAULT_STYLE.warning_color)
        return
    vital_cols = [col for col in (_role_column(daily, role, entity="daily_vitals") for role in _vital_roles()) if col]
    wear_col = _role_column(daily, "vital.sensor_wear_hours", entity="daily_vitals")
    days = sorted(daily["__study_day"].dropna().astype(int).unique())
    min_day, max_day = min(days), max(days)
    full = pd.DataFrame({"study_day": range(min_day, max_day + 1)})
    availability = daily.groupby("__study_day")[vital_cols].apply(lambda frame: frame.notna().any(axis=1).any()).reindex(full["study_day"]).fillna(False)
    ax.bar(full["study_day"], availability.astype(int), color=[DEFAULT_STYLE.palette[0] if value else "#ffffff" for value in availability], edgecolor=DEFAULT_STYLE.grid_color, label="Any vital present")
    if wear_col:
        wear = daily.groupby("__study_day")[wear_col].mean().reindex(full["study_day"])
        ax2 = ax.twinx()
        ax2.plot(full["study_day"], wear, color=DEFAULT_STYLE.warning_color, linewidth=1.5, label="Wear hours")
        ax2.set_ylabel("Wear hours")
    ax.set_ylim(0, 1.15)
    ax.set_yticks([0, 1], ["Missing", "Present"])
    ax.set_xlabel("Study day")


def _overlay_environment(ax, environment: pd.DataFrame, daily: pd.DataFrame, participant_daily: pd.DataFrame) -> None:
    overlay = pd.DataFrame()
    if not environment.empty:
        day = _environment_study_day(environment)
        column = "heat_index_c" if "heat_index_c" in environment else "ambient_temp_c" if "ambient_temp_c" in environment else None
        if column:
            overlay = pd.DataFrame({"study_day": day, "value": pd.to_numeric(environment[column], errors="coerce")}).dropna()
    if overlay.empty:
        column = "heat_index_c" if "heat_index_c" in daily else "ambient_temp_c" if "ambient_temp_c" in daily else None
        if column:
            overlay = daily.groupby("__study_day")[column].mean().reset_index().rename(columns={"__study_day": "study_day", column: "value"})
    if overlay.empty:
        ax.text(0.02, 0.08, "Environment overlay unavailable", transform=ax.transAxes, fontsize=7, color=DEFAULT_STYLE.warning_color)
        return
    env_ax = ax.twinx()
    env_ax.plot(overlay["study_day"], overlay["value"], color=DEFAULT_STYLE.warning_color, linestyle="--", alpha=0.45)
    env_ax.set_ylabel("Heat/ambient C", fontsize=7)
    env_ax.tick_params(axis="y", labelsize=7)


def _selected_vital_series(daily: pd.DataFrame, participant_id: str, role_id: str) -> pd.DataFrame:
    column = _role_column(daily, role_id, entity="daily_vitals")
    participant_col = _role_column(daily, "vital.participant_id", entity="daily_vitals") or "participant_id"
    if daily.empty or column is None or participant_col not in daily:
        return pd.DataFrame()
    participant = daily[daily[participant_col].astype(str) == str(participant_id)]
    if participant.empty:
        return pd.DataFrame()
    min_day = int(participant["__study_day"].min())
    max_day = int(participant["__study_day"].max())
    values = participant.groupby("__study_day")[column].mean()
    full = pd.Series(index=range(min_day, max_day + 1), dtype=float)
    full.loc[values.index.astype(int)] = values.values
    return pd.DataFrame({"study_day": list(full.index), "value": full.values})


def _event_days(
    frame: pd.DataFrame,
    participant_id: str,
    participant_role: str,
    date_role: str,
    *,
    reference_start: pd.Timestamp | None,
) -> list[int]:
    participant_col = _role_column(frame, participant_role, entity=registry.get_role(participant_role).entity)
    date_col = _role_column(frame, date_role, entity=registry.get_role(date_role).entity)
    if frame.empty or participant_col is None or date_col is None or reference_start is None:
        return []
    subset = frame[frame[participant_col].astype(str) == str(participant_id)]
    dates = pd.to_datetime(subset[date_col], errors="coerce").dropna()
    if dates.empty:
        return []
    aligned_days = ((dates - reference_start).dt.days + 1).astype(int)
    return sorted(aligned_days[aligned_days > 0].tolist())


def _timeline_start(participant_daily: pd.DataFrame) -> pd.Timestamp | None:
    if participant_daily.empty or "date" not in participant_daily:
        return None
    dates = pd.to_datetime(participant_daily["date"], errors="coerce").dropna()
    if dates.empty:
        return None
    return dates.min()


def _participant_rows(frame: pd.DataFrame, participant_id: str, role_id: str, entity: str) -> pd.DataFrame:
    column = _role_column(frame, role_id, entity=entity)
    if column is None:
        return pd.DataFrame()
    return frame[frame[column].astype(str) == str(participant_id)].copy()


def _with_study_day(daily: pd.DataFrame) -> pd.DataFrame:
    if daily.empty:
        return daily.copy()
    result = daily.copy()
    if "__study_day" in result:
        return result
    if "study_day" in result:
        result["__study_day"] = pd.to_numeric(result["study_day"], errors="coerce").astype("Int64")
        return result
    dates = pd.to_datetime(result["date"], errors="coerce")
    participant_col = _role_column(result, "vital.participant_id", entity="daily_vitals") or "participant_id"
    starts = dates.groupby(result[participant_col].astype(str)).transform("min")
    result["__study_day"] = (dates - starts).dt.days.add(1).astype("Int64")
    return result


def _environment_study_day(env: pd.DataFrame) -> pd.Series:
    if "study_day" in env:
        return pd.to_numeric(env["study_day"], errors="coerce").astype("Int64")
    dates = pd.to_datetime(env["date"], errors="coerce")
    return (dates - dates.min()).dt.days.add(1).astype("Int64")


def _role_column(df: pd.DataFrame, role_id: str, *, entity: str) -> str | None:
    if df.empty:
        return None
    resolution = registry.resolve_column(df, role_id, entity=entity)
    return resolution.column if resolution.ok else None


def _first_value(record: pd.Series, *columns: str) -> Any:
    for column in columns:
        if column not in record:
            continue
        value = record[column]
        if pd.isna(value):
            continue
        return value
    return "Unavailable"


def _vital_roles() -> list[str]:
    return [
        "vital.systolic_bp",
        "vital.diastolic_bp",
        "vital.heart_rate",
        "vital.respiratory_rate",
        "vital.skin_temperature_c",
        "vital.weight_kg",
        "vital.body_water_pct",
        "vital.sleep_hours",
        "vital.steps",
    ]


__all__ = ["TimelineRenderResult", "render_patient_timeline"]
