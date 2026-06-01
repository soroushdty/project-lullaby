from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from matplotlib import dates as mdates
from matplotlib import pyplot as plt

from src.visualization import schema_registry as registry
from src.visualization.design import DEFAULT_STYLE, add_dashboard_title, configure_style, render_warning_panel, save_figure, style_card
from src.visualization.eda_relationships import (
    RELATIONSHIP_ARTIFACT_IDS,
    RELATIONSHIP_PANEL_FILENAMES,
    RelationshipEDATables,
    RelationshipPanelResult,
    _boolean_series,
    _role_column,
    _role_label,
    _subtitle,
    _wrap,
)


def render_heat_environment(tables: RelationshipEDATables, out_dir: Path) -> RelationshipPanelResult:
    configure_style()
    fig = plt.figure(figsize=(16, 9), constrained_layout=False)
    add_dashboard_title(
        fig,
        "Heat Exposure and Environmental Context",
        f"{_subtitle(tables, [tables.environment, tables.daily_vitals])} | environment data are never fabricated in EDA",
    )
    gs = fig.add_gridspec(3, 4, left=0.04, right=0.98, top=0.88, bottom=0.07, wspace=0.35, hspace=0.55)
    warnings: list[str] = []
    metadata: dict[str, Any] = {
        "environment_available": not tables.environment.empty,
        "high_heat_definition": "unavailable",
        "environment_missingness": {},
        "vital_response_rows": [],
        "environment_data_fabricated": False,
    }

    if tables.environment.empty:
        ax = fig.add_subplot(gs[:, :])
        render_warning_panel(
            ax,
            "Environment Data Unavailable",
            "Panel 11 requires an environment table from SPEC-005 synthetic generation or a real environment source. The EDA step does not fabricate ambient temperature, heat index, or heat-wave periods.",
        )
        warnings.append("environment table unavailable; rendered explicit unavailable panel")
        path = out_dir / RELATIONSHIP_PANEL_FILENAMES["heat_environment"]
        save_figure(fig, path)
        plt.close(fig)
        return RelationshipPanelResult(
            RELATIONSHIP_ARTIFACT_IDS["heat_environment"],
            path,
            "Heat Exposure and Environmental Context",
            warnings,
            metadata,
        )

    env_frame, env_warnings = prepare_environment_frame(tables.environment)
    warnings.extend(env_warnings)
    if env_frame.empty:
        ax = fig.add_subplot(gs[:, :])
        render_warning_panel(
            ax,
            "Environment Data Unavailable",
            "The environment table exists, but date/study-day, ambient temperature, or heat-index roles could not be resolved with observed values.",
        )
        warnings.append("environment table present but required observed environment roles unavailable")
        path = out_dir / RELATIONSHIP_PANEL_FILENAMES["heat_environment"]
        save_figure(fig, path)
        plt.close(fig)
        return RelationshipPanelResult(
            RELATIONSHIP_ARTIFACT_IDS["heat_environment"],
            path,
            "Heat Exposure and Environmental Context",
            warnings,
            metadata,
        )

    high_heat, high_heat_definition, high_heat_warnings = classify_high_heat(tables.environment, env_frame)
    env_frame = env_frame.assign(high_heat=high_heat)
    warnings.extend(high_heat_warnings)
    metadata["high_heat_definition"] = high_heat_definition
    metadata["environment_missingness"] = environment_missingness_summary(env_frame)

    _environment_timeseries_panel(fig.add_subplot(gs[0:2, 0:2]), env_frame)
    response_rows, response_warnings = _vital_response_rows(tables, env_frame)
    warnings.extend(response_warnings)
    metadata["vital_response_rows"] = response_rows
    _vital_response_panel(fig.add_subplot(gs[0:2, 2:4]), response_rows)
    _environment_missingness_panel(fig.add_subplot(gs[2, 0:2]), env_frame, metadata["environment_missingness"])
    _heat_definition_panel(fig.add_subplot(gs[2, 2:4]), env_frame, high_heat_definition, response_warnings)

    path = out_dir / RELATIONSHIP_PANEL_FILENAMES["heat_environment"]
    save_figure(fig, path)
    plt.close(fig)
    return RelationshipPanelResult(
        RELATIONSHIP_ARTIFACT_IDS["heat_environment"],
        path,
        "Heat Exposure and Environmental Context",
        warnings,
        metadata,
    )


def prepare_environment_frame(environment: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    warnings: list[str] = []
    if environment.empty:
        return pd.DataFrame(), ["environment table unavailable"]
    date_col = _role_column(environment, "environment.date", entity="environment")
    day_col = _role_column(environment, "environment.study_day", entity="environment")
    ambient_col = _role_column(environment, "environment.ambient_temp_c", entity="environment")
    heat_col = _role_column(environment, "environment.heat_index_c", entity="environment")
    if ambient_col is None:
        warnings.append("environment ambient temperature unavailable")
    if heat_col is None:
        warnings.append("environment heat index unavailable")
    if date_col is None and day_col is None:
        warnings.append("environment calendar date and study day unavailable")
        return pd.DataFrame(), warnings
    if ambient_col is None and heat_col is None:
        return pd.DataFrame(), warnings

    result = pd.DataFrame(index=environment.index)
    if date_col:
        result["date"] = pd.to_datetime(environment[date_col], errors="coerce").dt.normalize()
    else:
        result["date"] = pd.NaT
    if day_col:
        result["study_day"] = pd.to_numeric(environment[day_col], errors="coerce")
    elif result["date"].notna().any():
        result["study_day"] = (result["date"] - result["date"].min()).dt.days.add(1)
    else:
        result["study_day"] = np.nan
    result["ambient_temp_c"] = pd.to_numeric(environment[ambient_col], errors="coerce") if ambient_col else np.nan
    result["heat_index_c"] = pd.to_numeric(environment[heat_col], errors="coerce") if heat_col else np.nan
    result["axis"] = result["date"] if result["date"].notna().any() else result["study_day"]
    result["axis_kind"] = "date" if result["date"].notna().any() else "study_day"
    result = result.sort_values(["date", "study_day"], na_position="last").reset_index(drop=True)
    observed = result[["ambient_temp_c", "heat_index_c"]].notna().any(axis=1)
    return result.loc[observed].copy(), warnings


def classify_high_heat(environment: pd.DataFrame, env_frame: pd.DataFrame) -> tuple[pd.Series, str, list[str]]:
    warnings: list[str] = []
    heat_wave_col = _role_column(environment, "environment.heat_wave", entity="environment")
    if heat_wave_col:
        heat_wave, heat_warnings = _boolean_series(environment, "environment.heat_wave", required=False)
        warnings.extend(heat_warnings)
        aligned = heat_wave.reindex(environment.index).fillna(False).astype(bool)
        high_heat = aligned.loc[env_frame.index] if set(env_frame.index).issubset(set(aligned.index)) else aligned.reset_index(drop=True).reindex(env_frame.index, fill_value=False)
        if high_heat.any():
            return high_heat.reset_index(drop=True), "environment.heat_wave true", warnings

    exposure_col = _role_column(environment, "environment.heat_exposure_level", entity="environment")
    if exposure_col:
        exposure = environment[exposure_col].astype(str).str.strip().str.lower().replace({"nan": ""})
        high_heat = exposure.isin({"high", "extreme", "heat_wave", "heat wave"})
        high_heat = high_heat.reset_index(drop=True).reindex(env_frame.index, fill_value=False)
        if high_heat.any():
            return high_heat.reset_index(drop=True), "environment.heat_exposure_level in high/extreme", warnings

    observed_heat = pd.to_numeric(env_frame["heat_index_c"], errors="coerce").dropna()
    if observed_heat.empty:
        warnings.append("high heat classification unavailable: heat index missing")
        return pd.Series(False, index=env_frame.index), "unavailable", warnings
    threshold = float(observed_heat.quantile(0.75))
    return env_frame["heat_index_c"].ge(threshold).fillna(False), f"observed heat_index_c >= 75th percentile ({threshold:.1f} C)", warnings


def environment_missingness_summary(env_frame: pd.DataFrame) -> dict[str, Any]:
    if env_frame.empty:
        return {"rows": 0}
    summary: dict[str, Any] = {
        "rows": int(len(env_frame)),
        "ambient_temp_missing_rows": int(env_frame["ambient_temp_c"].isna().sum()),
        "heat_index_missing_rows": int(env_frame["heat_index_c"].isna().sum()),
        "high_heat_days": int(env_frame["high_heat"].sum()) if "high_heat" in env_frame else 0,
    }
    if env_frame["date"].notna().any():
        dates = env_frame["date"].dropna()
        full_dates = pd.date_range(dates.min(), dates.max(), freq="D")
        observed_dates = set(dates.dt.normalize())
        summary["calendar_missing_days"] = int(sum(date not in observed_dates for date in full_dates))
        summary["calendar_start"] = dates.min().date().isoformat()
        summary["calendar_end"] = dates.max().date().isoformat()
    else:
        days = pd.to_numeric(env_frame["study_day"], errors="coerce").dropna().astype(int)
        full_days = set(range(int(days.min()), int(days.max()) + 1)) if not days.empty else set()
        summary["study_day_missing_days"] = int(len(full_days - set(days)))
    return summary


def add_heat_shading(ax, env_frame: pd.DataFrame) -> None:
    if env_frame.empty or "high_heat" not in env_frame:
        return
    high = env_frame[env_frame["high_heat"].eq(True)]
    if high.empty:
        return
    is_date = bool(env_frame["date"].notna().any())
    for _, row in high.iterrows():
        if is_date and pd.notna(row["date"]):
            start = row["date"] - pd.Timedelta(hours=12)
            end = row["date"] + pd.Timedelta(hours=12)
            ax.axvspan(start, end, color=DEFAULT_STYLE.warning_color, alpha=0.08, linewidth=0)
        elif pd.notna(row["study_day"]):
            day = float(row["study_day"])
            ax.axvspan(day - 0.5, day + 0.5, color=DEFAULT_STYLE.warning_color, alpha=0.08, linewidth=0)


def _environment_timeseries_panel(ax, env_frame: pd.DataFrame) -> None:
    style_card(ax, "Ambient Temperature and Heat Index")
    x = env_frame["date"] if env_frame["date"].notna().any() else env_frame["study_day"]
    add_heat_shading(ax, env_frame)
    ax.plot(x, env_frame["ambient_temp_c"], marker="o", linewidth=1.6, label=_role_label("environment.ambient_temp_c"), color=DEFAULT_STYLE.palette[0])
    ax.plot(x, env_frame["heat_index_c"], marker="^", linewidth=1.6, label=_role_label("environment.heat_index_c"), color=DEFAULT_STYLE.warning_color)
    ax.set_ylabel("C")
    ax.set_xlabel("Calendar date" if env_frame["date"].notna().any() else "Study day")
    if env_frame["date"].notna().any():
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    ax.legend(loc="upper left", fontsize=8)
    high_count = int(env_frame["high_heat"].sum()) if "high_heat" in env_frame else 0
    ax.text(0.02, 0.05, f"Shaded days: high heat / heat wave ({high_count:,} days)", transform=ax.transAxes, fontsize=8, color=DEFAULT_STYLE.muted_text_color)


def _vital_response_rows(tables: RelationshipEDATables, env_frame: pd.DataFrame) -> tuple[list[dict[str, Any]], list[str]]:
    daily = tables.daily_vitals.copy()
    if daily.empty:
        return [], ["vital response unavailable: daily_vitals empty"]
    joined = _join_daily_to_environment(daily, env_frame)
    if joined.empty or "high_heat" not in joined:
        return [], ["vital response unavailable: environment could not be aligned to daily_vitals"]

    participant_col = _role_column(joined, "vital.participant_id", entity="daily_vitals") or "participant_id"
    ac_state = _participant_ac_state(tables.participants)
    if ac_state:
        joined["ac_access"] = joined[participant_col].astype(str).map(ac_state).fillna("AC missing")
    else:
        joined["ac_access"] = "All participants"
    rows: list[dict[str, Any]] = []
    for role_id in ("vital.heart_rate", "vital.skin_temperature_c"):
        column = _role_column(joined, role_id, entity="daily_vitals")
        if column is None:
            continue
        role = registry.get_role(role_id)
        local = joined.assign(__value=pd.to_numeric(joined[column], errors="coerce")).dropna(subset=["__value", "high_heat"])
        for (high_heat, ac_access), group in local.groupby(["high_heat", "ac_access"], dropna=False):
            rows.append(
                {
                    "measure": role.label,
                    "unit": role.unit or "",
                    "heat_group": "High heat" if bool(high_heat) else "Non-high heat",
                    "ac_access": str(ac_access),
                    "mean": float(group["__value"].mean()),
                    "n": int(group["__value"].notna().sum()),
                }
            )
    warnings: list[str] = []
    if not rows:
        warnings.append("vital response unavailable: HR and skin temperature roles missing")
    if not ac_state:
        warnings.append("AC access unavailable; vital response summarized without AC stratification")
    return rows, warnings


def _join_daily_to_environment(daily: pd.DataFrame, env_frame: pd.DataFrame) -> pd.DataFrame:
    daily = daily.copy()
    date_col = _role_column(daily, "vital.date", entity="daily_vitals")
    day_col = _role_column(daily, "vital.study_day", entity="daily_vitals")
    env_cols = ["date", "study_day", "high_heat", "ambient_temp_c", "heat_index_c"]
    if date_col and env_frame["date"].notna().any():
        daily["__date"] = pd.to_datetime(daily[date_col], errors="coerce").dt.normalize()
        env = env_frame[env_cols].dropna(subset=["date"]).rename(columns={"date": "__date"})
        return daily.merge(env.drop(columns=["study_day"]), on="__date", how="left")
    if day_col:
        daily["__study_day_key"] = pd.to_numeric(daily[day_col], errors="coerce")
    elif "__study_day" in daily:
        daily["__study_day_key"] = pd.to_numeric(daily["__study_day"], errors="coerce")
    else:
        return pd.DataFrame()
    env = env_frame[env_cols].dropna(subset=["study_day"]).rename(columns={"study_day": "__study_day_key"})
    return daily.merge(env.drop(columns=["date"]), on="__study_day_key", how="left")


def _participant_ac_state(participants: pd.DataFrame) -> dict[str, str]:
    participant_col = _role_column(participants, "participant.id", entity="participants")
    ac_col = _role_column(participants, "participant.has_ac", entity="participants")
    if participants.empty or participant_col is None or ac_col is None:
        return {}
    parsed, _warnings = _boolean_series(participants, "participant.has_ac", required=False)
    labels = pd.Series("AC missing", index=participants.index, dtype=object)
    labels.loc[parsed.eq(True)] = "AC yes"
    labels.loc[parsed.eq(False)] = "AC no"
    return dict(zip(participants[participant_col].astype(str), labels, strict=False))


def _vital_response_panel(ax, rows: list[dict[str, Any]]) -> None:
    style_card(ax, "Vital Response During High vs Non-High Heat")
    if not rows:
        ax.text(0.04, 0.72, "No aligned HR or skin-temperature observations available.", transform=ax.transAxes, fontsize=10, color=DEFAULT_STYLE.warning_color)
        return
    rows = rows[:10]
    labels = [_wrap(f"{row['measure']} | {row['heat_group']} | {row['ac_access']}", 34) for row in rows]
    values = [row["mean"] for row in rows]
    colors = [DEFAULT_STYLE.warning_color if row["heat_group"] == "High heat" else DEFAULT_STYLE.palette[0] for row in rows]
    bars = ax.barh(range(len(rows)), values, color=colors, alpha=0.82)
    ax.set_yticks(range(len(rows)), labels, fontsize=7)
    ax.invert_yaxis()
    ax.set_xlabel("Mean observed value")
    ax.set_xlim(0, max(max(values) * 1.18, 1.0))
    for bar, row in zip(bars, rows, strict=False):
        ax.text(bar.get_width(), bar.get_y() + bar.get_height() / 2, f" {row['mean']:.1f} {row['unit']} (N={row['n']})", va="center", fontsize=7)


def _environment_missingness_panel(ax, env_frame: pd.DataFrame, summary: dict[str, Any]) -> None:
    style_card(ax, "Missing Environment Data")
    ax.set_xticks([])
    ax.set_yticks([])
    lines = [
        f"Environment rows: {summary.get('rows', 0):,}",
        f"Ambient temp missing rows: {summary.get('ambient_temp_missing_rows', 0):,}",
        f"Heat index missing rows: {summary.get('heat_index_missing_rows', 0):,}",
    ]
    if "calendar_missing_days" in summary:
        lines.append(f"Missing calendar days in range: {summary['calendar_missing_days']:,}")
        lines.append(f"Calendar range: {summary.get('calendar_start')} to {summary.get('calendar_end')}")
    if "study_day_missing_days" in summary:
        lines.append(f"Missing study days in range: {summary['study_day_missing_days']:,}")
    ax.text(0.04, 0.82, "\n".join(lines), transform=ax.transAxes, ha="left", va="top", fontsize=10)
    ax.text(0.04, 0.12, "Missing environment rows are shown explicitly and are not filled in by this EDA step.", transform=ax.transAxes, fontsize=8, color=DEFAULT_STYLE.muted_text_color, wrap=True)


def _heat_definition_panel(ax, env_frame: pd.DataFrame, high_heat_definition: str, response_warnings: list[str]) -> None:
    style_card(ax, "High-Heat Stratification")
    ax.set_xticks([])
    ax.set_yticks([])
    high_days = int(env_frame["high_heat"].sum()) if "high_heat" in env_frame else 0
    total_days = int(len(env_frame))
    text = [
        f"Definition: {high_heat_definition}",
        f"High-heat days: {high_days:,}/{total_days:,}",
        "Vital summaries use observed daily_vitals joined to observed environment rows.",
    ]
    if response_warnings:
        text.append("Warnings: " + "; ".join(response_warnings[:3]))
    ax.text(0.04, 0.82, "\n".join(text), transform=ax.transAxes, ha="left", va="top", fontsize=10, wrap=True)


__all__ = [
    "add_heat_shading",
    "classify_high_heat",
    "environment_missingness_summary",
    "prepare_environment_frame",
    "render_heat_environment",
]
