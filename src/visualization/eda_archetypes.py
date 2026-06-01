from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from matplotlib import dates as mdates
from matplotlib import pyplot as plt

from src.validation.semantics import DomainBooleanParsePolicy, parse_domain_boolean_series
from src.visualization import schema_registry as registry
from src.visualization.design import DEFAULT_STYLE, add_dashboard_title, configure_style, render_warning_panel, save_figure, style_card
from src.visualization.eda_environment import add_heat_shading, classify_high_heat, prepare_environment_frame
from src.visualization.eda_relationships import (
    RELATIONSHIP_ARTIFACT_IDS,
    RELATIONSHIP_PANEL_FILENAMES,
    RelationshipEDATables,
    RelationshipPanelResult,
    _boolean_series,
    _daily_with_heat_index,
    _outcome_positive_by_participant,
    _role_column,
    _subtitle,
    _vital_roles,
    _wrap,
)


ARCHETYPE_ORDER = [
    "diligent monitor",
    "overwhelmed mom",
    "heat-stressed",
    "true emergency",
    "silent decliner",
]
ARCHETYPE_ALIASES = {
    "diligent_monitor": "diligent monitor",
    "diligent monitor": "diligent monitor",
    "overwhelmed_mom": "overwhelmed mom",
    "overwhelmed mom": "overwhelmed mom",
    "heat_stressed": "heat-stressed",
    "heat stressed": "heat-stressed",
    "heat-stressed": "heat-stressed",
    "heat_strain": "heat-stressed",
    "heat strain": "heat-stressed",
    "true_emergency": "true emergency",
    "true emergency": "true emergency",
    "silent_decliner": "silent decliner",
    "silent decliner": "silent decliner",
}
PROVISIONAL_RULE_SUMMARY = [
    "true emergency: observed event flag or severe BP range",
    "heat-stressed: repeated high heat with elevated HR or skin temperature",
    "silent decliner: low adherence or high late missingness",
    "overwhelmed mom: high missingness or psychosocial burden proxies",
    "diligent monitor: high adherence, low missingness, and low alert burden",
]


def render_archetype_explorer(tables: RelationshipEDATables, out_dir: Path) -> RelationshipPanelResult:
    configure_style()
    fig = plt.figure(figsize=(16, 9), constrained_layout=False)
    add_dashboard_title(
        fig,
        "Participant-Archetype Explorer",
        f"{_subtitle(tables, [tables.participants, tables.daily_vitals, tables.clinical_outcomes])} | descriptive segments, not ground truth unless explicitly labeled",
    )
    gs = fig.add_gridspec(3, 4, left=0.04, right=0.98, top=0.88, bottom=0.07, wspace=0.35, hspace=0.55)
    segment_frame, metadata, warnings = prepare_archetype_segments(tables)

    _archetype_summary_table(fig.add_subplot(gs[:, 0:2]), segment_frame, metadata)
    _archetype_count_panel(fig.add_subplot(gs[0, 2:4]), segment_frame)
    _adherence_missingness_panel(fig.add_subplot(gs[1, 2]), segment_frame)
    _alert_event_panel(fig.add_subplot(gs[1, 3]), segment_frame)
    _context_panel(fig.add_subplot(gs[2, 2:4]), segment_frame, metadata)

    path = out_dir / RELATIONSHIP_PANEL_FILENAMES["archetype_explorer"]
    save_figure(fig, path)
    plt.close(fig)
    return RelationshipPanelResult(
        RELATIONSHIP_ARTIFACT_IDS["archetype_explorer"],
        path,
        "Participant-Archetype Explorer",
        warnings,
        metadata,
    )


def prepare_archetype_segments(tables: RelationshipEDATables) -> tuple[pd.DataFrame, dict[str, Any], list[str]]:
    metrics, metric_warnings = _participant_metrics(tables)
    explicit_labels, label_source = _explicit_archetype_labels(tables)
    warnings = list(metric_warnings)
    if explicit_labels:
        metrics["archetype"] = metrics["participant_id"].map(explicit_labels).fillna("unlabeled explicit")
        label_mode = "explicit"
        rule_summary: list[str] = []
    else:
        metrics["archetype"] = metrics.apply(_assign_provisional_archetype, axis=1)
        label_mode = "provisional"
        label_source = "transparent rules from participants and daily_vitals"
        rule_summary = PROVISIONAL_RULE_SUMMARY
        warnings.append("archetype labels unavailable; assigned provisional descriptive segments")

    summaries = _segment_summary(metrics)
    metadata = {
        "label_source": label_mode,
        "label_source_detail": label_source,
        "provisional": label_mode == "provisional",
        "rule_summary": rule_summary,
        "segments": summaries.to_dict("records"),
        "alert_burden_source": "alerts table" if not tables.alerts.empty else "unavailable",
    }
    return summaries, metadata, warnings


def render_recruitment_timeline(tables: RelationshipEDATables, out_dir: Path) -> RelationshipPanelResult:
    configure_style()
    fig = plt.figure(figsize=(16, 9), constrained_layout=False)
    add_dashboard_title(
        fig,
        "Enrollment and Recruitment Timeline",
        f"{_subtitle(tables, [tables.participants, tables.recruitment, tables.daily_vitals, tables.environment])} | calendar-aware where dates are available",
    )
    gs = fig.add_gridspec(3, 4, left=0.04, right=0.98, top=0.88, bottom=0.07, wspace=0.34, hspace=0.55)
    timeline, metadata, warnings = prepare_recruitment_timeline(tables)
    if timeline.empty:
        ax = fig.add_subplot(gs[:, :])
        render_warning_panel(
            ax,
            "Recruitment Timeline Unavailable",
            "Enrollment, recruitment, observation, delivery, and daily-vitals dates are missing or unparseable, so a calendar-aware recruitment timeline cannot be rendered.",
        )
        warnings.append("recruitment timeline unavailable: no parseable calendar dates")
        path = out_dir / RELATIONSHIP_PANEL_FILENAMES["recruitment_timeline"]
        save_figure(fig, path)
        plt.close(fig)
        return RelationshipPanelResult(
            RELATIONSHIP_ARTIFACT_IDS["recruitment_timeline"],
            path,
            "Enrollment and Recruitment Timeline",
            warnings,
            metadata,
        )

    env_frame = _timeline_environment_frame(tables)
    _participant_window_panel(fig.add_subplot(gs[0:2, 0:3]), timeline, env_frame, warnings, metadata)
    _timeline_source_panel(fig.add_subplot(gs[0:2, 3]), metadata, warnings)
    _cumulative_enrollment_panel(fig.add_subplot(gs[2, 0:2]), timeline, env_frame)
    _observation_density_panel(fig.add_subplot(gs[2, 2:4]), tables, timeline, env_frame, metadata)

    path = out_dir / RELATIONSHIP_PANEL_FILENAMES["recruitment_timeline"]
    save_figure(fig, path)
    plt.close(fig)
    return RelationshipPanelResult(
        RELATIONSHIP_ARTIFACT_IDS["recruitment_timeline"],
        path,
        "Enrollment and Recruitment Timeline",
        warnings,
        metadata,
    )


def prepare_recruitment_timeline(tables: RelationshipEDATables) -> tuple[pd.DataFrame, dict[str, Any], list[str]]:
    participants = tables.participants.copy()
    participant_col = _role_column(participants, "participant.id", entity="participants")
    if participants.empty or participant_col is None:
        return pd.DataFrame(), {"recruitment_source": "unavailable"}, ["participants unavailable for recruitment timeline"]
    participants["participant_id"] = participants[participant_col].astype(str)
    enrollment = _participant_date(participants, "participant.enrollment_date")
    delivery = _participant_date(participants, "participant.delivery_date")
    observation_start = _participant_date(participants, "participant.observation_start_date")

    recruitment_dates = _recruitment_dates(tables.recruitment)
    if not recruitment_dates.empty:
        participants["recruitment_date"] = participants["participant_id"].map(recruitment_dates)
    else:
        participants["recruitment_date"] = pd.NaT

    daily_min, daily_max = _daily_date_bounds(tables.daily_vitals)
    participants["daily_start_date"] = participants["participant_id"].map(daily_min)
    participants["daily_end_date"] = participants["participant_id"].map(daily_max)
    participants["enrollment_date"] = enrollment
    participants["delivery_date"] = delivery
    participants["observation_start"] = observation_start.combine_first(participants["daily_start_date"])
    participants["observation_end"] = participants["daily_end_date"].combine_first(delivery)
    participants["timeline_enrollment"] = enrollment.combine_first(participants["recruitment_date"]).combine_first(participants["observation_start"])
    date_cols = ["timeline_enrollment", "recruitment_date", "delivery_date", "observation_start", "observation_end", "daily_start_date", "daily_end_date"]
    if not participants[date_cols].notna().any().any():
        return pd.DataFrame(), {"recruitment_source": "unavailable", "calendar_aware": False}, []

    source = "recruitment table" if not recruitment_dates.empty else "inferred from participant enrollment/observation/daily dates"
    warnings: list[str] = []
    if recruitment_dates.empty:
        warnings.append("recruitment table unavailable; inferred recruitment timeline from participant and observation dates")
    missing_enrollment = int(participants["timeline_enrollment"].isna().sum())
    if missing_enrollment:
        warnings.append(f"timeline enrollment date unavailable for {missing_enrollment} participants")

    timeline = participants[
        [
            "participant_id",
            "timeline_enrollment",
            "recruitment_date",
            "delivery_date",
            "observation_start",
            "observation_end",
            "daily_start_date",
            "daily_end_date",
        ]
    ].copy()
    timeline = timeline.sort_values(["timeline_enrollment", "observation_start", "participant_id"], na_position="last").reset_index(drop=True)
    metadata = {
        "recruitment_source": source,
        "calendar_aware": True,
        "participants": int(len(timeline)),
        "participants_missing_timeline_enrollment": missing_enrollment,
        "observation_density_source": "daily_vitals dates" if daily_min else "participant observation windows",
    }
    return timeline, metadata, warnings


def _participant_metrics(tables: RelationshipEDATables) -> tuple[pd.DataFrame, list[str]]:
    participants = tables.participants.copy()
    participant_col = _role_column(participants, "participant.id", entity="participants")
    if participant_col:
        ids = participants[participant_col].dropna().astype(str).unique().tolist()
    else:
        daily_pid = _role_column(tables.daily_vitals, "vital.participant_id", entity="daily_vitals")
        ids = tables.daily_vitals[daily_pid].dropna().astype(str).unique().tolist() if daily_pid else []
    metrics = pd.DataFrame({"participant_id": sorted(ids)})
    warnings: list[str] = []
    daily = tables.daily_vitals.copy()
    daily_pid = _role_column(daily, "vital.participant_id", entity="daily_vitals") or "participant_id"
    vital_cols = [col for col in (_role_column(daily, role, entity="daily_vitals") for role in _vital_roles()) if col]
    if not daily.empty and daily_pid in daily and vital_cols:
        any_vital = daily[vital_cols].notna().any(axis=1)
        expected = _expected_days(daily, daily_pid)
        observed_days = daily.loc[any_vital].groupby(daily.loc[any_vital, daily_pid].astype(str))["__study_day"].nunique()
        missingness = daily.groupby(daily[daily_pid].astype(str))[vital_cols].apply(lambda frame: float(frame.isna().sum().sum()) / max(frame.size, 1))
        metrics["adherence"] = metrics["participant_id"].map({pid: observed_days.get(pid, 0) / max(days, 1) for pid, days in expected.items()}).fillna(0.0)
        metrics["missingness"] = metrics["participant_id"].map(missingness).fillna(1.0)
        metrics["late_missingness"] = metrics["participant_id"].map(_late_missingness(daily, daily_pid, vital_cols)).fillna(0.0)
        for role_id, output in [("vital.systolic_bp", "max_sbp"), ("vital.diastolic_bp", "max_dbp"), ("vital.heart_rate", "mean_hr"), ("vital.skin_temperature_c", "mean_skin_temp")]:
            column = _role_column(daily, role_id, entity="daily_vitals")
            if column:
                values = pd.to_numeric(daily[column], errors="coerce")
                grouped = values.groupby(daily[daily_pid].astype(str))
                metrics[output] = metrics["participant_id"].map(grouped.max() if output.startswith("max") else grouped.mean())
            else:
                metrics[output] = np.nan
    else:
        warnings.append("participant vital adherence/missingness unavailable")
        metrics["adherence"] = 0.0
        metrics["missingness"] = 1.0
        metrics["late_missingness"] = 0.0
        metrics["max_sbp"] = np.nan
        metrics["max_dbp"] = np.nan
        metrics["mean_hr"] = np.nan
        metrics["mean_skin_temp"] = np.nan

    metrics["high_heat_days"] = metrics["participant_id"].map(_participant_high_heat_days(tables)).fillna(0).astype(int)
    alert_counts = _alert_counts(tables)
    metrics["alert_burden"] = metrics["participant_id"].map(alert_counts)
    event_map, event_warnings = _outcome_positive_by_participant(tables.clinical_outcomes)
    warnings.extend(event_warnings if tables.clinical_outcomes.empty else [])
    metrics["event_positive"] = metrics["participant_id"].map(event_map).fillna(False).astype(bool)
    context = _participant_context(participants)
    metrics = metrics.merge(context, on="participant_id", how="left")
    return metrics, warnings


def _explicit_archetype_labels(tables: RelationshipEDATables) -> tuple[dict[str, str], str]:
    participants = tables.participants
    participant_col = _role_column(participants, "participant.id", entity="participants")
    archetype_col = _role_column(participants, "participant.archetype", entity="participants")
    if participant_col and archetype_col:
        labels = {
            str(pid): _normalize_archetype_label(value)
            for pid, value in zip(participants[participant_col], participants[archetype_col], strict=False)
            if not pd.isna(value)
        }
        if labels:
            return labels, f"explicit labels from participants.{archetype_col}"
    daily = tables.daily_vitals
    daily_pid = _role_column(daily, "vital.participant_id", entity="daily_vitals")
    daily_archetype = "archetype" if "archetype" in daily.columns else None
    if daily_pid and daily_archetype:
        labels = daily.dropna(subset=[daily_archetype]).groupby(daily[daily_pid].astype(str))[daily_archetype].agg(lambda values: values.mode().iloc[0] if not values.mode().empty else values.iloc[0])
        if not labels.empty:
            return {str(pid): _normalize_archetype_label(value) for pid, value in labels.items()}, f"explicit labels from daily_vitals.{daily_archetype}"
    return {}, "no explicit archetype labels found"


def _normalize_archetype_label(value: Any) -> str:
    text = str(value).strip().lower().replace("-", " ").replace("_", " ")
    alias_key = text.replace(" ", "_")
    return ARCHETYPE_ALIASES.get(alias_key, ARCHETYPE_ALIASES.get(text, text or "unlabeled explicit"))


def _assign_provisional_archetype(row: pd.Series) -> str:
    if bool(row.get("event_positive", False)) or _ge(row.get("max_sbp"), 160) or _ge(row.get("max_dbp"), 110):
        return "true emergency"
    if _ge(row.get("high_heat_days"), 2) and (_ge(row.get("mean_hr"), 95) or _ge(row.get("mean_skin_temp"), 37.0)):
        return "heat-stressed"
    if _lt(row.get("adherence"), 0.50) or _ge(row.get("late_missingness"), 0.60):
        return "silent decliner"
    if (
        _ge(row.get("missingness"), 0.35)
        or _ge(row.get("depression"), 10)
        or _ge(row.get("anxiety"), 18)
        or _lt(row.get("health_literacy"), 3)
        or _lt(row.get("social_support"), 3)
    ):
        return "overwhelmed mom"
    if _ge(row.get("adherence"), 0.80) and _lt(row.get("missingness"), 0.25) and (pd.isna(row.get("alert_burden")) or _lt(row.get("alert_burden"), 2)):
        return "diligent monitor"
    return "overwhelmed mom"


def _segment_summary(metrics: pd.DataFrame) -> pd.DataFrame:
    labels = ARCHETYPE_ORDER + sorted(label for label in metrics["archetype"].dropna().unique() if label not in ARCHETYPE_ORDER)
    rows: list[dict[str, Any]] = []
    for label in labels:
        group = metrics[metrics["archetype"] == label]
        n = int(len(group))
        alert_burden = float(group["alert_burden"].mean()) if n and group["alert_burden"].notna().any() else np.nan
        rows.append(
            {
                "archetype": label,
                "n": n,
                "adherence": float(group["adherence"].mean()) if n else np.nan,
                "missingness": float(group["missingness"].mean()) if n else np.nan,
                "alert_burden": alert_burden,
                "event_prevalence": float(group["event_positive"].mean()) if n else np.nan,
                "ac_access": float(group["has_ac"].eq(True).mean()) if n and "has_ac" in group else np.nan,
                "pih_severity": _top_category(group["pih_severity"]) if n and "pih_severity" in group else "unavailable",
            }
        )
    return pd.DataFrame(rows)


def _archetype_summary_table(ax, summary: pd.DataFrame, metadata: dict[str, Any]) -> None:
    style_card(ax, "Segment Summary")
    ax.set_xticks([])
    ax.set_yticks([])
    headers = ["Segment", "N", "Adherence", "Missing", "Alerts", "Events", "AC", "PIH"]
    rows = []
    for _, row in summary.iterrows():
        rows.append(
            [
                row["archetype"],
                f"{int(row['n'])}",
                _pct(row["adherence"]),
                _pct(row["missingness"]),
                "unavail" if pd.isna(row["alert_burden"]) else f"{row['alert_burden']:.1f}",
                _pct(row["event_prevalence"]),
                _pct(row["ac_access"]),
                _wrap(row["pih_severity"], 14),
            ]
        )
    table = ax.table(
        cellText=rows,
        colLabels=headers,
        loc="center",
        cellLoc="left",
        colLoc="left",
        colWidths=[0.22, 0.06, 0.12, 0.12, 0.10, 0.10, 0.10, 0.18],
        bbox=[0.0, 0.11, 1.0, 0.78],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(7.5)
    for (row_idx, _col_idx), cell in table.get_celld().items():
        cell.set_edgecolor(DEFAULT_STYLE.grid_color)
        if row_idx == 0:
            cell.set_text_props(fontweight="bold")
    source = "Explicit labels" if metadata["label_source"] == "explicit" else "Provisional descriptive rules"
    ax.text(0.02, 0.94, f"{source}: {metadata['label_source_detail']}", transform=ax.transAxes, fontsize=8.5, color=DEFAULT_STYLE.muted_text_color, wrap=True)
    ax.text(0.02, 0.03, "Provisional segments are review aids, not ground truth or model targets.", transform=ax.transAxes, fontsize=8, color=DEFAULT_STYLE.warning_color if metadata["provisional"] else DEFAULT_STYLE.muted_text_color)


def _archetype_count_panel(ax, summary: pd.DataFrame) -> None:
    style_card(ax, "Participants by Segment")
    display = summary.sort_values("n", ascending=True)
    bars = ax.barh(range(len(display)), display["n"], color=DEFAULT_STYLE.palette[: len(display)])
    ax.set_yticks(range(len(display)), [_wrap(label, 24) for label in display["archetype"]], fontsize=8)
    ax.set_xlabel("Participants")
    ax.set_xlim(0, max(float(display["n"].max()) * 1.25, 1.0))
    for bar, value in zip(bars, display["n"], strict=False):
        ax.text(bar.get_width(), bar.get_y() + bar.get_height() / 2, f" {int(value):,}", va="center", fontsize=8)


def _adherence_missingness_panel(ax, summary: pd.DataFrame) -> None:
    style_card(ax, "Adherence vs Missingness")
    labels = [_wrap(label, 12) for label in summary["archetype"]]
    x = np.arange(len(summary))
    ax.bar(x - 0.18, summary["adherence"].fillna(0), width=0.36, color=DEFAULT_STYLE.palette[0], label="Adherence")
    ax.bar(x + 0.18, summary["missingness"].fillna(0), width=0.36, color=DEFAULT_STYLE.warning_color, label="Missing")
    ax.set_ylim(0, 1)
    ax.set_xticks(x, labels, rotation=35, ha="right", fontsize=7)
    ax.set_ylabel("Share")
    ax.legend(loc="upper right", fontsize=7)


def _alert_event_panel(ax, summary: pd.DataFrame) -> None:
    style_card(ax, "Alert Burden and Events")
    labels = [_wrap(label, 12) for label in summary["archetype"]]
    x = np.arange(len(summary))
    alerts = summary["alert_burden"].fillna(0)
    events = summary["event_prevalence"].fillna(0) * max(alerts.max(), 1.0)
    ax.bar(x - 0.18, alerts, width=0.36, color=DEFAULT_STYLE.palette[1], label="Mean alerts")
    ax.bar(x + 0.18, events, width=0.36, color=DEFAULT_STYLE.palette[3], label="Event prev. scaled")
    ax.set_xticks(x, labels, rotation=35, ha="right", fontsize=7)
    ax.set_ylabel("Count / scaled share")
    ax.legend(loc="upper right", fontsize=7)


def _context_panel(ax, summary: pd.DataFrame, metadata: dict[str, Any]) -> None:
    style_card(ax, "Context and Rule Annotation")
    ax.set_xticks([])
    ax.set_yticks([])
    text = [
        f"Label source: {metadata['label_source_detail']}",
        f"Alert burden source: {metadata['alert_burden_source']}",
    ]
    if metadata["rule_summary"]:
        text.append("Rules:")
        text.extend(f"- {rule}" for rule in metadata["rule_summary"])
    else:
        text.append("Explicit labels are summarized as provided; the panel does not infer causality.")
    ax.text(0.04, 0.88, "\n".join(text), transform=ax.transAxes, ha="left", va="top", fontsize=9, wrap=True)


def _participant_context(participants: pd.DataFrame) -> pd.DataFrame:
    participant_col = _role_column(participants, "participant.id", entity="participants")
    if participants.empty or participant_col is None:
        return pd.DataFrame({"participant_id": []})
    context = pd.DataFrame({"participant_id": participants[participant_col].astype(str)})
    ac, _warnings = _boolean_series(participants, "participant.has_ac", required=False)
    context["has_ac"] = ac
    for role_id, output in [
        ("participant.pih_severity", "pih_severity"),
        ("participant.health_literacy", "health_literacy"),
        ("participant.social_support", "social_support"),
        ("participant.depression", "depression"),
        ("participant.anxiety", "anxiety"),
    ]:
        column = _role_column(participants, role_id, entity="participants")
        if column:
            if registry.get_role(role_id).value_type == "number":
                context[output] = pd.to_numeric(participants[column], errors="coerce")
            else:
                context[output] = participants[column]
        else:
            context[output] = np.nan
    return context


def _participant_high_heat_days(tables: RelationshipEDATables) -> dict[str, int]:
    joined, _source, _warning = _daily_with_heat_index(tables)
    participant_col = _role_column(joined, "vital.participant_id", entity="daily_vitals") if not joined.empty else None
    if joined.empty or participant_col is None or "heat_index_c" not in joined:
        return {}
    heat = pd.to_numeric(joined["heat_index_c"], errors="coerce")
    if heat.dropna().empty:
        return {}
    threshold = float(heat.dropna().quantile(0.75))
    local = joined.assign(__high_heat=heat.ge(threshold).fillna(False))
    return local.groupby(local[participant_col].astype(str))["__high_heat"].sum().astype(int).to_dict()


def _alert_counts(tables: RelationshipEDATables) -> dict[str, int]:
    participant_col = _role_column(tables.alerts, "alert.participant_id", entity="alerts")
    if tables.alerts.empty or participant_col is None:
        return {}
    return tables.alerts.groupby(tables.alerts[participant_col].astype(str)).size().astype(int).to_dict()


def _expected_days(daily: pd.DataFrame, participant_col: str) -> dict[str, int]:
    if "__study_day" not in daily:
        return {}
    expected: dict[str, int] = {}
    for participant_id, group in daily.groupby(daily[participant_col].astype(str)):
        days = pd.to_numeric(group["__study_day"], errors="coerce").dropna()
        expected[str(participant_id)] = int(days.max() - days.min() + 1) if not days.empty else len(group)
    return expected


def _late_missingness(daily: pd.DataFrame, participant_col: str, vital_cols: list[str]) -> dict[str, float]:
    values: dict[str, float] = {}
    for participant_id, group in daily.groupby(daily[participant_col].astype(str)):
        days = pd.to_numeric(group["__study_day"], errors="coerce")
        if days.dropna().empty:
            values[str(participant_id)] = 0.0
            continue
        split = days.min() + (days.max() - days.min()) / 2
        late = group.loc[days >= split, vital_cols]
        values[str(participant_id)] = float(late.isna().sum().sum()) / max(late.size, 1)
    return values


def _participant_date(participants: pd.DataFrame, role_id: str) -> pd.Series:
    column = _role_column(participants, role_id, entity="participants")
    if column is None:
        return pd.Series(pd.NaT, index=participants.index)
    return pd.to_datetime(participants[column], errors="coerce").dt.normalize()


def _recruitment_dates(recruitment: pd.DataFrame) -> pd.Series:
    participant_col = _role_column(recruitment, "recruitment.participant_id", entity="recruitment")
    date_col = _role_column(recruitment, "recruitment.date", entity="recruitment")
    if recruitment.empty or participant_col is None or date_col is None:
        return pd.Series(dtype="datetime64[ns]")
    local = recruitment.copy()
    local["__date"] = pd.to_datetime(local[date_col], errors="coerce").dt.normalize()
    enrolled_col = _role_column(local, "recruitment.enrolled", entity="recruitment")
    if enrolled_col:
        parsed = parse_domain_boolean_series(local[enrolled_col], DomainBooleanParsePolicy(role="recruitment.enrolled", required=False), source_column=enrolled_col)
        local = local.loc[parsed.true_mask | parsed.missing_mask]
    return local.dropna(subset=["__date"]).groupby(local[participant_col].astype(str))["__date"].min()


def _daily_date_bounds(daily: pd.DataFrame) -> tuple[dict[str, pd.Timestamp], dict[str, pd.Timestamp]]:
    participant_col = _role_column(daily, "vital.participant_id", entity="daily_vitals")
    date_col = _role_column(daily, "vital.date", entity="daily_vitals")
    if daily.empty or participant_col is None or date_col is None:
        return {}, {}
    dates = pd.to_datetime(daily[date_col], errors="coerce").dt.normalize()
    grouped = dates.groupby(daily[participant_col].astype(str))
    return grouped.min().dropna().to_dict(), grouped.max().dropna().to_dict()


def _timeline_environment_frame(tables: RelationshipEDATables) -> pd.DataFrame:
    if tables.environment.empty:
        return pd.DataFrame()
    env_frame, _warnings = prepare_environment_frame(tables.environment)
    if env_frame.empty or not env_frame["date"].notna().any():
        return pd.DataFrame()
    high_heat, definition, _high_warnings = classify_high_heat(tables.environment, env_frame)
    return env_frame.assign(high_heat=high_heat, high_heat_definition=definition)


def _participant_window_panel(ax, timeline: pd.DataFrame, env_frame: pd.DataFrame, warnings: list[str], metadata: dict[str, Any]) -> None:
    style_card(ax, "Enrollment Dates, Observation Windows, and Delivery")
    display = timeline.copy()
    if len(display) > 75:
        positions = np.linspace(0, len(display) - 1, 75, dtype=int)
        display = display.iloc[sorted(set(positions))].copy()
        warnings.append("participant timeline display downsampled; metadata counts all participants")
        metadata["display_downsampled"] = True
        metadata["display_participants"] = int(len(display))
    else:
        metadata["display_downsampled"] = False
        metadata["display_participants"] = int(len(display))
    add_heat_shading(ax, env_frame)
    y = np.arange(len(display))
    for idx, (_, row) in enumerate(display.iterrows()):
        start = row["observation_start"] if pd.notna(row["observation_start"]) else row["timeline_enrollment"]
        end = row["observation_end"] if pd.notna(row["observation_end"]) else start
        if pd.notna(start) and pd.notna(end):
            ax.hlines(idx, start, end, color=DEFAULT_STYLE.palette[0], linewidth=1.5, alpha=0.75)
        if pd.notna(row["timeline_enrollment"]):
            ax.scatter(row["timeline_enrollment"], idx, marker="o", s=22, color=DEFAULT_STYLE.palette[2], label="Enrollment" if idx == 0 else None)
        if pd.notna(row["delivery_date"]):
            ax.scatter(row["delivery_date"], idx, marker="D", s=18, color=DEFAULT_STYLE.warning_color, label="Delivery" if idx == 0 else None)
    ax.set_yticks([])
    ax.set_xlabel("Calendar date")
    ax.set_ylabel("Participants")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    ax.legend(loc="upper left", fontsize=7)
    ax.text(0.02, 0.04, "Lines show observation windows; dots enrollment; diamonds delivery. Shading marks high heat when environment data exist.", transform=ax.transAxes, fontsize=8, color=DEFAULT_STYLE.muted_text_color)


def _timeline_source_panel(ax, metadata: dict[str, Any], warnings: list[str]) -> None:
    style_card(ax, "Timeline Source")
    ax.set_xticks([])
    ax.set_yticks([])
    lines = [
        f"Participants: {metadata.get('participants', 0):,}",
        f"Recruitment source: {metadata.get('recruitment_source', 'unavailable')}",
        f"Observation density: {metadata.get('observation_density_source', 'unavailable')}",
        f"Missing enrollment dates: {metadata.get('participants_missing_timeline_enrollment', 0):,}",
    ]
    if warnings:
        lines.append("Warnings:")
        lines.extend(f"- {warning}" for warning in warnings[:4])
    ax.text(0.05, 0.90, "\n".join(lines), transform=ax.transAxes, ha="left", va="top", fontsize=9, wrap=True)


def _cumulative_enrollment_panel(ax, timeline: pd.DataFrame, env_frame: pd.DataFrame) -> None:
    style_card(ax, "Participant Count Enrolled Over Time")
    add_heat_shading(ax, env_frame)
    dates = timeline["timeline_enrollment"].dropna().sort_values()
    if dates.empty:
        ax.text(0.04, 0.70, "Enrollment dates unavailable.", transform=ax.transAxes, color=DEFAULT_STYLE.warning_color)
        return
    counts = dates.groupby(dates).size().sort_index().cumsum()
    ax.step(counts.index, counts.values, where="post", color=DEFAULT_STYLE.palette[2], linewidth=2)
    ax.scatter(counts.index, counts.values, color=DEFAULT_STYLE.palette[2], s=20)
    ax.set_ylabel("Enrolled participants")
    ax.set_xlabel("Calendar date")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))


def _observation_density_panel(ax, tables: RelationshipEDATables, timeline: pd.DataFrame, env_frame: pd.DataFrame, metadata: dict[str, Any]) -> None:
    style_card(ax, "Cohort Observation Density")
    add_heat_shading(ax, env_frame)
    density = _daily_observation_density(tables.daily_vitals)
    if density.empty:
        density = _window_observation_density(timeline)
        metadata["observation_density_source"] = "participant observation windows"
    if density.empty:
        ax.text(0.04, 0.70, "Observation density unavailable.", transform=ax.transAxes, color=DEFAULT_STYLE.warning_color)
        return
    ax.plot(density["date"], density["count"], color=DEFAULT_STYLE.palette[0], linewidth=1.8)
    ax.fill_between(density["date"], density["count"], color=DEFAULT_STYLE.palette[0], alpha=0.16)
    ax.set_ylabel("Participant-days")
    ax.set_xlabel("Calendar date")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))


def _daily_observation_density(daily: pd.DataFrame) -> pd.DataFrame:
    date_col = _role_column(daily, "vital.date", entity="daily_vitals")
    if daily.empty or date_col is None:
        return pd.DataFrame()
    dates = pd.to_datetime(daily[date_col], errors="coerce").dt.normalize().dropna()
    if dates.empty:
        return pd.DataFrame()
    counts = dates.groupby(dates).size().sort_index()
    return pd.DataFrame({"date": counts.index, "count": counts.values})


def _window_observation_density(timeline: pd.DataFrame) -> pd.DataFrame:
    starts = timeline["observation_start"].dropna()
    ends = timeline["observation_end"].dropna()
    if starts.empty or ends.empty:
        return pd.DataFrame()
    dates = pd.date_range(starts.min(), ends.max(), freq="D")
    counts = []
    for date in dates:
        active = timeline["observation_start"].le(date) & timeline["observation_end"].ge(date)
        counts.append(int(active.sum()))
    return pd.DataFrame({"date": dates, "count": counts})


def _top_category(values: pd.Series) -> str:
    clean = values.dropna().astype(str)
    if clean.empty:
        return "unavailable"
    counts = clean.value_counts()
    return f"{counts.index[0]} ({int(counts.iloc[0])})"


def _pct(value: Any) -> str:
    if pd.isna(value):
        return "unavail"
    return f"{float(value):.0%}"


def _ge(value: Any, threshold: float) -> bool:
    return not pd.isna(value) and float(value) >= threshold


def _lt(value: Any, threshold: float) -> bool:
    return not pd.isna(value) and float(value) < threshold


__all__ = [
    "ARCHETYPE_ORDER",
    "PROVISIONAL_RULE_SUMMARY",
    "prepare_archetype_segments",
    "prepare_recruitment_timeline",
    "render_archetype_explorer",
    "render_recruitment_timeline",
]
