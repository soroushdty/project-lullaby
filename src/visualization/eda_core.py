from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import textwrap

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

from src.visualization import schema_registry as registry
from src.visualization.artifacts import (
    FigureArtifact,
    FigureArtifactManifest,
    create_empty_manifest,
    write_manifest,
)
from src.visualization.design import (
    DEFAULT_STYLE,
    add_dashboard_title,
    configure_style,
    render_warning_panel,
    save_figure,
    style_card,
)


SPEC_ID = "SPEC-006"
PANEL_FILENAMES = {
    "cohort_overview": "01_cohort_overview.png",
    "outcome_prevalence": "02_outcome_prevalence.png",
    "distribution_outliers": "03_distribution_outliers.png",
    "alert_engagement_funnel": "04_alert_engagement_funnel.png",
}


@dataclass(frozen=True)
class EDATables:
    data_dir: Path
    resolved_data_dir: Path
    participants: pd.DataFrame
    daily_vitals: pd.DataFrame
    clinical_outcomes: pd.DataFrame
    alerts: pd.DataFrame
    staff_contacts: pd.DataFrame


@dataclass(frozen=True)
class PanelResult:
    artifact_id: str
    path: Path
    title: str
    warnings: list[str]


def generate_core_dashboards(
    data_dir: str | Path,
    out_dir: str | Path = Path("outputs/figures/eda"),
    *,
    manifest_path: str | Path = Path("outputs/figures/manifest.json"),
) -> list[PanelResult]:
    tables = load_eda_tables(data_dir)
    output_dir = Path(out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    results = [
        render_cohort_overview(tables, output_dir),
        render_outcome_prevalence(tables, output_dir),
        render_distribution_outliers(tables, output_dir),
        render_alert_engagement_funnel(tables, output_dir),
    ]
    _register_results(results, manifest_path, tables, output_dir)
    return results


def load_eda_tables(data_dir: str | Path) -> EDATables:
    requested = Path(data_dir)
    resolved = _resolve_data_dir(requested)
    return EDATables(
        data_dir=requested,
        resolved_data_dir=resolved,
        participants=_load_entity_or_empty(resolved, "participants"),
        daily_vitals=_load_entity_or_empty(resolved, "daily_vitals"),
        clinical_outcomes=_load_entity_or_empty(resolved, "clinical_outcomes"),
        alerts=_load_entity_or_empty(resolved, "alerts"),
        staff_contacts=_load_entity_or_empty(resolved, "staff_contacts"),
    )


def render_cohort_overview(tables: EDATables, out_dir: Path) -> PanelResult:
    configure_style()
    fig = plt.figure(figsize=(16, 9), constrained_layout=False)
    subtitle = _subtitle(tables, [tables.participants, tables.daily_vitals])
    add_dashboard_title(fig, "Cohort Overview", subtitle)
    gs = fig.add_gridspec(4, 4, left=0.04, right=0.98, top=0.88, bottom=0.06, wspace=0.35, hspace=0.62)
    warnings: list[str] = []
    participants = tables.participants
    n = len(participants)

    _metric_card(fig.add_subplot(gs[0, 0]), "Participants", f"{n:,}", "Canonical participant rows")
    warnings.extend(_age_panel(fig.add_subplot(gs[0, 1]), participants))
    warnings.extend(_count_bar(fig.add_subplot(gs[0, 2]), participants, "pih_severity", "PIH Severity"))
    warnings.extend(_boolean_bar(fig.add_subplot(gs[0, 3]), participants, "has_ac", "AC Availability"))

    fig.text(0.045, 0.705, "Equity-relevant context", fontsize=10, fontweight="bold", color=DEFAULT_STYLE.muted_text_color)
    warnings.extend(_count_bar(fig.add_subplot(gs[1, 0:2]), participants, "race_ethnicity", "Race / Ethnicity"))
    warnings.extend(_count_bar(fig.add_subplot(gs[1, 2:4]), participants, "insurance", "Insurance"))
    warnings.extend(_numeric_distribution(fig.add_subplot(gs[2, 0]), participants, "household_size", "Household Size", unit="people", bins=8))
    warnings.extend(_numeric_distribution(fig.add_subplot(gs[2, 1]), participants, "para", "Parity", unit="births", bins=8))
    warnings.extend(_risk_indicator_panel(fig.add_subplot(gs[2, 2:4]), participants))
    warnings.extend(_psychosocial_panel(fig.add_subplot(gs[3, 0:2]), participants))
    warnings.extend(_optional_outcome_context(fig.add_subplot(gs[3, 2:4]), tables.clinical_outcomes))

    path = out_dir / PANEL_FILENAMES["cohort_overview"]
    save_figure(fig, path)
    plt.close(fig)
    return PanelResult("eda_core_01_cohort_overview", path, "Cohort Overview", warnings)


def render_outcome_prevalence(tables: EDATables, out_dir: Path) -> PanelResult:
    configure_style()
    fig = plt.figure(figsize=(16, 9), constrained_layout=False)
    subtitle = _subtitle(tables, [tables.clinical_outcomes, tables.participants])
    add_dashboard_title(fig, "Outcome Prevalence and Class Imbalance", subtitle)
    gs = fig.add_gridspec(3, 4, left=0.04, right=0.98, top=0.88, bottom=0.07, wspace=0.32, hspace=0.55)
    outcomes = tables.clinical_outcomes
    warnings: list[str] = []
    if outcomes.empty:
        for ax in [fig.add_subplot(gs[:, :])]:
            render_warning_panel(ax, "Clinical outcomes unavailable", "clinical_outcomes table is required for this panel.")
        warnings.append("clinical_outcomes unavailable")
        path = out_dir / PANEL_FILENAMES["outcome_prevalence"]
        save_figure(fig, path)
        plt.close(fig)
        return PanelResult("eda_core_02_outcome_prevalence", path, "Outcome Prevalence", warnings)

    denominator = len(outcomes)
    measures = [
        ("CV Event", _outcome_series(outcomes, "cv_event"), "event_rate.cv_event"),
        ("ED Visit", _outcome_series(outcomes, "ed_visit"), "event_rate.ed_visit"),
        ("Hospitalization", _outcome_series(outcomes, "hospitalized"), "event_rate.hospitalized"),
        ("Heat Illness", _heat_illness_series(outcomes), "event_rate.heat_illness"),
    ]
    for index, (label, series, _) in enumerate(measures):
        count = int(series.sum())
        _metric_card(
            fig.add_subplot(gs[0, index]),
            label,
            f"{count:,}",
            f"{_percent(count, denominator)} of {denominator:,}",
        )

    cv_series = measures[0][1]
    positive = int(cv_series.sum())
    negative = int(denominator - positive)
    _class_imbalance_panel(fig.add_subplot(gs[1, 0:2]), positive, negative)
    _prevalence_panel(fig.add_subplot(gs[1, 2:4]), measures, denominator)
    _rare_outcome_warning(fig.add_subplot(gs[2, 0:2]), positive, denominator)
    _outcome_context_panel(fig.add_subplot(gs[2, 2:4]), measures, denominator)

    path = out_dir / PANEL_FILENAMES["outcome_prevalence"]
    save_figure(fig, path)
    plt.close(fig)
    return PanelResult("eda_core_02_outcome_prevalence", path, "Outcome Prevalence and Class Imbalance", warnings)


def render_distribution_outliers(tables: EDATables, out_dir: Path) -> PanelResult:
    configure_style()
    fig = plt.figure(figsize=(16, 9), constrained_layout=False)
    subtitle = _subtitle(tables, [tables.daily_vitals])
    add_dashboard_title(fig, "Distributions and Capture-Worthy Outliers", subtitle)
    gs = fig.add_gridspec(3, 4, left=0.04, right=0.98, top=0.88, bottom=0.06, wspace=0.32, hspace=0.56)
    daily = tables.daily_vitals
    warnings: list[str] = []
    specs = _vital_specs()
    for index, spec in enumerate(specs):
        ax = fig.add_subplot(gs[index // 3, index % 3])
        warnings.extend(_distribution_card(ax, daily, spec))
    _capture_worthy_table(fig.add_subplot(gs[:, 3]), daily, specs)

    path = out_dir / PANEL_FILENAMES["distribution_outliers"]
    save_figure(fig, path)
    plt.close(fig)
    return PanelResult("eda_core_03_distribution_outliers", path, "Distributions and Capture-Worthy Outliers", warnings)


def render_alert_engagement_funnel(tables: EDATables, out_dir: Path) -> PanelResult:
    configure_style()
    fig = plt.figure(figsize=(16, 9), constrained_layout=False)
    subtitle = _subtitle(tables, [tables.alerts, tables.staff_contacts])
    add_dashboard_title(fig, "Alerts and Engagement Funnel", subtitle)
    gs = fig.add_gridspec(3, 4, left=0.04, right=0.98, top=0.88, bottom=0.07, wspace=0.35, hspace=0.55)
    alerts = tables.alerts
    contacts = tables.staff_contacts
    warnings: list[str] = []

    total_alerts = len(alerts)
    alerting_participants = alerts["participant_id"].nunique() if "participant_id" in alerts else 0
    median_alerts = alerts.groupby("participant_id").size().median() if alerting_participants else 0
    call_attempted = _call_attempted_count(alerts, contacts)
    call_completed = _call_completed_count(alerts, contacts)
    completed_rate = call_completed / call_attempted if call_attempted else 0.0
    tile_data = [
        ("Total Alerts", f"{total_alerts:,}", "Generated alert rows"),
        ("Alerting Participants", f"{alerting_participants:,}", "Participants with >=1 alert"),
        ("Median Alerts", f"{median_alerts:.1f}", "Per alerting participant"),
        ("Completed-Call Rate", _percent(call_completed, call_attempted), f"{call_completed:,}/{call_attempted:,} calls"),
    ]
    for index, (title, value, subtitle_text) in enumerate(tile_data):
        _metric_card(fig.add_subplot(gs[0, index]), title, value, subtitle_text)

    warnings.extend(_count_bar(fig.add_subplot(gs[1, 0]), alerts, "alert_level", "Alert Level"))
    _trigger_reason_panel(fig.add_subplot(gs[1, 1]), alerts)
    _survey_state_panel(fig.add_subplot(gs[1, 2]), alerts)
    _contact_state_panel(fig.add_subplot(gs[1, 3]), contacts)
    _funnel_panel(fig.add_subplot(gs[2, :]), alerts, contacts)

    path = out_dir / PANEL_FILENAMES["alert_engagement_funnel"]
    save_figure(fig, path)
    plt.close(fig)
    return PanelResult("eda_core_04_alert_engagement_funnel", path, "Alerts and Engagement Funnel", warnings)


def _resolve_data_dir(path: Path) -> Path:
    if path.exists():
        return path
    if path.name == "raw" and path.parent.exists():
        return path.parent
    return path


def _load_entity_or_empty(data_dir: Path, entity: str) -> pd.DataFrame:
    try:
        return registry.load_entity(data_dir, entity)
    except registry.SchemaValidationError:
        return pd.DataFrame()


def _subtitle(tables: EDATables, frames: list[pd.DataFrame]) -> str:
    dates: list[pd.Timestamp] = []
    for frame in frames:
        if frame.empty:
            continue
        for column in ("date", "event_ts", "enrollment_date", "observation_start_date", "contact_date", "cv_event_date"):
            if column not in frame:
                continue
            parsed = pd.to_datetime(frame[column], errors="coerce")
            dates.extend(parsed.dropna().tolist())
    source = tables.data_dir.as_posix()
    if dates:
        return f"Source: {source} | Date range: {min(dates).date().isoformat()} to {max(dates).date().isoformat()}"
    return f"Source: {source} | Date range unavailable"


def _metric_card(ax, title: str, value: str, subtitle: str) -> None:
    ax.set_facecolor(DEFAULT_STYLE.panel_background)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color(DEFAULT_STYLE.grid_color)
    ax.text(0.05, 0.68, value, transform=ax.transAxes, ha="left", va="center", fontsize=24, fontweight="bold")
    ax.text(0.05, 0.42, title, transform=ax.transAxes, ha="left", va="center", fontsize=11, fontweight="bold")
    ax.text(0.05, 0.22, subtitle, transform=ax.transAxes, ha="left", va="center", fontsize=8, color=DEFAULT_STYLE.muted_text_color, wrap=True)


def _age_panel(ax, participants: pd.DataFrame) -> list[str]:
    if "age" not in participants:
        render_warning_panel(ax, "Age Distribution", "Unavailable: optional role participant.age is not present.")
        return ["age unavailable"]
    return _numeric_distribution(ax, participants, "age", "Age Distribution", unit="years", bins=12, annotate_median=True)


def _numeric_distribution(
    ax,
    frame: pd.DataFrame,
    column: str,
    title: str,
    *,
    unit: str = "",
    bins: int = 10,
    annotate_median: bool = False,
) -> list[str]:
    if frame.empty or column not in frame:
        render_warning_panel(ax, title, f"Unavailable: optional column {column} is not present.")
        return [f"{column} unavailable"]
    values = pd.to_numeric(frame[column], errors="coerce").dropna()
    if values.empty:
        render_warning_panel(ax, title, f"Unavailable: {column} has no observed values.")
        return [f"{column} empty"]
    style_card(ax, title)
    ax.hist(values, bins=min(bins, max(3, int(values.nunique()))), color=DEFAULT_STYLE.palette[0], alpha=0.82)
    ax.set_ylabel("Participants")
    ax.set_xlabel(unit)
    median = float(values.median())
    ax.axvline(median, color=DEFAULT_STYLE.warning_color, linewidth=1.8)
    missing = int(frame[column].isna().sum())
    annotation = f"Observed {len(values):,}/{len(frame):,}; missing {missing:,}"
    if annotate_median:
        annotation = f"Median {median:g}; range {values.min():g}-{values.max():g} {unit}\n{annotation}"
    ax.text(0.03, 0.96, annotation, transform=ax.transAxes, ha="left", va="top", fontsize=8, color=DEFAULT_STYLE.muted_text_color)
    return []


def _count_bar(ax, frame: pd.DataFrame, column: str, title: str) -> list[str]:
    if frame.empty or column not in frame:
        render_warning_panel(ax, title, f"Unavailable: optional column {column} is not present.")
        return [f"{column} unavailable"]
    values = frame[column].fillna("Missing").astype(str)
    counts = values.value_counts(dropna=False).sort_values(ascending=True)
    if counts.empty:
        render_warning_panel(ax, title, "Unavailable: no rows present.")
        return [f"{column} empty"]
    style_card(ax, title)
    bars = ax.barh(range(len(counts)), counts.values, color=DEFAULT_STYLE.palette[: len(counts)])
    ax.set_yticks(range(len(counts)), [_wrap_label(label) for label in counts.index])
    ax.set_xlabel("Count")
    ax.set_xlim(0, max(float(counts.max()) * 1.22, 1.0))
    total = int(counts.sum())
    for bar, count in zip(bars, counts.values, strict=False):
        xmax = ax.get_xlim()[1]
        if bar.get_width() > xmax * 0.72:
            ax.text(
                bar.get_width() - xmax * 0.02,
                bar.get_y() + bar.get_height() / 2,
                f"{count:,} ({count / total:.0%})",
                va="center",
                ha="right",
                fontsize=8,
                color="white",
            )
        else:
            ax.text(bar.get_width(), bar.get_y() + bar.get_height() / 2, f" {count:,} ({count / total:.0%})", va="center", fontsize=8)
    return []


def _boolean_bar(ax, frame: pd.DataFrame, column: str, title: str) -> list[str]:
    if frame.empty or column not in frame:
        render_warning_panel(ax, title, f"Unavailable: optional column {column} is not present.")
        return [f"{column} unavailable"]
    mapped = frame[column].map(lambda value: "Missing" if pd.isna(value) else "Yes" if _as_bool(value) else "No")
    local = pd.DataFrame({column: mapped})
    return _count_bar(ax, local, column, title)


def _risk_indicator_panel(ax, participants: pd.DataFrame) -> list[str]:
    indicators = [
        ("Prior PIH", "prior_pih"),
        ("Prior GDM", "prior_gdm"),
        ("Gestational Diabetes", "gestational_diabetes"),
        ("Prior CV History", "prior_cv_history"),
        ("FHx Hypertension", "fhx_hypertension"),
        ("Antihypertensives", "on_antihypertensives"),
    ]
    available = [(label, col) for label, col in indicators if col in participants]
    if not available:
        render_warning_panel(ax, "Comorbidities / Risk Indicators", "Unavailable: optional risk indicator columns are not present.")
        return ["risk indicators unavailable"]
    counts = [int(participants[col].map(_as_bool).sum()) for _, col in available]
    style_card(ax, "Comorbidities / Risk Indicators")
    bars = ax.barh(range(len(available)), counts, color=DEFAULT_STYLE.palette[2])
    ax.set_yticks(range(len(available)), [label for label, _ in available])
    ax.set_xlabel("Participants")
    ax.set_xlim(0, max(float(max(counts)) * 1.22, 1.0))
    total = len(participants)
    for bar, count in zip(bars, counts, strict=False):
        ax.text(bar.get_width(), bar.get_y() + bar.get_height() / 2, f" {count:,} ({count / total:.0%})", va="center", fontsize=8)
    return []


def _psychosocial_panel(ax, participants: pd.DataFrame) -> list[str]:
    columns = [
        ("BHLS", _first_present(participants, "bhls_health_literacy", "health_literacy")),
        ("MSPSS", _first_present(participants, "mspss_social_support", "social_support")),
        ("EPDS", _first_present(participants, "epds_depression", "depression")),
        ("PASS", _first_present(participants, "pass_anxiety", "anxiety")),
    ]
    available = [(label, col) for label, col in columns if col]
    if not available:
        render_warning_panel(ax, "Baseline Psychosocial Measures", "Unavailable: BHLS, MSPSS, EPDS, and PASS columns are absent.")
        return ["psychosocial unavailable"]
    medians = [float(pd.to_numeric(participants[col], errors="coerce").median()) for _, col in available]
    style_card(ax, "Baseline Psychosocial Measures")
    bars = ax.bar([label for label, _ in available], medians, color=DEFAULT_STYLE.palette[3])
    ax.set_ylabel("Median score")
    for bar, value in zip(bars, medians, strict=False):
        ax.text(bar.get_x() + bar.get_width() / 2, value, f"{value:.1f}", ha="center", va="bottom", fontsize=8)
    return []


def _optional_outcome_context(ax, outcomes: pd.DataFrame) -> list[str]:
    if outcomes.empty:
        render_warning_panel(ax, "Clinical Outcomes Context", "Unavailable: optional clinical_outcomes table not found.")
        return ["clinical outcomes unavailable for cohort overview"]
    cv = _outcome_series(outcomes, "cv_event")
    ed = _outcome_series(outcomes, "ed_visit")
    hosp = _outcome_series(outcomes, "hospitalized")
    data = pd.Series({"CV event": int(cv.sum()), "ED visit": int(ed.sum()), "Hospitalized": int(hosp.sum())})
    style_card(ax, "Clinical Outcomes Context")
    bars = ax.barh(range(len(data)), data.values, color=DEFAULT_STYLE.palette[1])
    ax.set_yticks(range(len(data)), data.index)
    ax.set_xlim(0, max(float(data.max()) * 1.22, 1.0))
    total = len(outcomes)
    for bar, count in zip(bars, data.values, strict=False):
        ax.text(bar.get_width(), bar.get_y() + bar.get_height() / 2, f" {count:,} ({count / total:.0%})", va="center", fontsize=8)
    return []


def _outcome_series(outcomes: pd.DataFrame, column: str) -> pd.Series:
    if column not in outcomes:
        return pd.Series([False] * len(outcomes), index=outcomes.index)
    return outcomes[column].map(_as_bool).fillna(False).astype(bool)


def _heat_illness_series(outcomes: pd.DataFrame) -> pd.Series:
    if "heat_illness" in outcomes:
        return outcomes["heat_illness"].map(_as_bool).fillna(False).astype(bool)
    if "heat_illness_episodes" in outcomes:
        return pd.to_numeric(outcomes["heat_illness_episodes"], errors="coerce").fillna(0).gt(0)
    return pd.Series([False] * len(outcomes), index=outcomes.index)


def _class_imbalance_panel(ax, positive: int, negative: int) -> None:
    style_card(ax, "CV Event Class Imbalance")
    total = positive + negative
    labels = ["CV positive", "CV negative"]
    values = [positive, negative]
    bars = ax.bar(labels, values, color=[DEFAULT_STYLE.warning_color, DEFAULT_STYLE.palette[0]])
    ax.set_ylabel("Participants")
    for bar, value in zip(bars, values, strict=False):
        ax.text(bar.get_x() + bar.get_width() / 2, value, f"{value:,} ({_percent(value, total)})", ha="center", va="bottom", fontsize=10, fontweight="bold")
    if total and abs(positive / total - 0.075) <= 0.02:
        ax.text(0.02, 0.92, f"Near target rare-event rate: {positive}/{total} ({positive / total:.1%})", transform=ax.transAxes, ha="left", va="top", fontsize=9, color=DEFAULT_STYLE.warning_color)


def _prevalence_panel(ax, measures: list[tuple[str, pd.Series, str]], denominator: int) -> None:
    style_card(ax, "Outcome Prevalence")
    labels = [label for label, _, _ in measures]
    values = [int(series.sum()) for _, series, _ in measures]
    bars = ax.barh(range(len(labels)), values, color=DEFAULT_STYLE.palette[: len(labels)])
    ax.set_yticks(range(len(labels)), labels)
    ax.set_xlabel("Participants")
    ax.set_xlim(0, max(float(max(values)) * 1.22, 1.0))
    for bar, value in zip(bars, values, strict=False):
        ax.text(bar.get_width(), bar.get_y() + bar.get_height() / 2, f" {value:,} ({_percent(value, denominator)})", va="center", fontsize=9)


def _rare_outcome_warning(ax, positive: int, denominator: int) -> None:
    render_warning_panel(
        ax,
        "Rare Outcome",
        "Rare outcome: interpret model performance with precision-recall metrics and uncertainty intervals.",
    )
    if denominator:
        ax.text(0.03, 0.20, f"CV event positives: {positive:,}/{denominator:,} ({positive / denominator:.1%})", transform=ax.transAxes, fontsize=10, fontweight="bold")


def _outcome_context_panel(ax, measures: list[tuple[str, pd.Series, str]], denominator: int) -> None:
    style_card(ax, "Count and Percent Tiles")
    ax.set_xticks([])
    ax.set_yticks([])
    for idx, (label, series, _) in enumerate(measures):
        x = 0.05 + (idx % 2) * 0.48
        y = 0.72 - (idx // 2) * 0.42
        count = int(series.sum())
        ax.text(x, y, f"{count:,}", transform=ax.transAxes, fontsize=20, fontweight="bold")
        ax.text(x, y - 0.12, f"{label}: {_percent(count, denominator)}", transform=ax.transAxes, fontsize=9)


def _vital_specs() -> list[dict[str, str]]:
    return [
        {"role": "vital.systolic_bp", "title": "Systolic BP"},
        {"role": "vital.diastolic_bp", "title": "Diastolic BP"},
        {"role": "vital.heart_rate", "title": "Heart Rate"},
        {"role": "vital.respiratory_rate", "title": "Respiratory Rate"},
        {"role": "vital.skin_temperature_c", "title": "Skin Temperature"},
        {"role": "vital.weight_kg", "title": "Weight"},
        {"role": "vital.body_water_pct", "title": "Body Water"},
        {"role": "vital.sleep_hours", "title": "Sleep"},
        {"role": "vital.steps", "title": "Steps"},
    ]


def _distribution_card(ax, daily: pd.DataFrame, spec: dict[str, str]) -> list[str]:
    role = registry.get_role(spec["role"])
    column = _role_column(daily, spec["role"], entity="daily_vitals")
    title = spec["title"]
    if daily.empty or column is None:
        render_warning_panel(ax, title, f"Unavailable: {role.label} role not present.")
        return [f"{spec['role']} unavailable"]
    values = pd.to_numeric(daily[column], errors="coerce")
    observed = values.dropna()
    if observed.empty:
        render_warning_panel(ax, title, f"Unavailable: {role.label} has no observed values.")
        return [f"{spec['role']} empty"]
    style_card(ax, f"{title} ({role.unit or 'unitless'})")
    ax.hist(observed, bins=20, color=DEFAULT_STYLE.palette[0], alpha=0.78)
    inset = ax.inset_axes([0.08, 0.72, 0.84, 0.18])
    inset.boxplot(observed, orientation="horizontal", widths=0.55, patch_artist=True, boxprops={"facecolor": DEFAULT_STYLE.palette[5], "alpha": 0.65})
    inset.set_yticks([])
    inset.tick_params(axis="x", labelsize=6)
    ax.set_ylabel("Rows")
    ax.set_xlabel(role.unit or "")
    missing = int(values.isna().sum())
    ax.text(0.03, 0.66, f"Observed {len(observed):,}/{len(values):,}\nMissing {missing:,}", transform=ax.transAxes, ha="left", va="top", fontsize=8, color=DEFAULT_STYLE.muted_text_color)
    return []


def _capture_worthy_table(ax, daily: pd.DataFrame, specs: list[dict[str, str]]) -> None:
    ax.set_facecolor(DEFAULT_STYLE.panel_background)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color(DEFAULT_STYLE.grid_color)
    ax.set_title("Top Capture-Worthy Values", loc="left", fontsize=11, fontweight="bold")
    rows = _capture_worthy_rows(daily, specs)
    if not rows:
        ax.text(0.04, 0.78, "No capture-worthy extremes detected.", transform=ax.transAxes, fontsize=10, fontweight="bold")
        ax.text(0.04, 0.63, "Missing values are retained in denominators and are not imputed.", transform=ax.transAxes, fontsize=9, color=DEFAULT_STYLE.muted_text_color, wrap=True)
        return
    headers = ["Participant", "Day", "Measure", "Value", "Context"]
    table_data = [[row.get(key, "") for key in ["participant_id", "study_day", "measure", "value", "context"]] for row in rows[:10]]
    table = ax.table(
        cellText=table_data,
        colLabels=headers,
        loc="center",
        cellLoc="left",
        colLoc="left",
        colWidths=[0.18, 0.10, 0.20, 0.16, 0.36],
        bbox=[0.0, 0.06, 1.0, 0.84],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(7)
    for (row_idx, _col_idx), cell in table.get_celld().items():
        cell.set_edgecolor(DEFAULT_STYLE.grid_color)
        if row_idx == 0:
            cell.set_text_props(fontweight="bold")
    ax.text(0.04, 0.94, "Flagged as capture-worthy, not data errors, unless outside hard schema bounds.", transform=ax.transAxes, fontsize=8, color=DEFAULT_STYLE.capture_worthy_color, wrap=True)


def _capture_worthy_rows(daily: pd.DataFrame, specs: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if daily.empty:
        return rows
    for spec in specs:
        role = registry.get_role(spec["role"])
        column = _role_column(daily, spec["role"], entity="daily_vitals")
        if column is None:
            continue
        values = pd.to_numeric(daily[column], errors="coerce")
        hard = role.hard_range
        capture = role.capture_worthy_range
        for idx, value in values.dropna().items():
            severity = None
            distance = 0.0
            if _outside(value, hard):
                severity = "impossible by schema"
                distance = _distance_outside(value, hard)
            elif _outside(value, capture):
                severity = "capture-worthy"
                distance = _distance_outside(value, capture)
            if severity is None:
                continue
            source_row = daily.loc[idx]
            participant = str(source_row.get("participant_id", "unknown"))
            day = source_row.get("study_day", "")
            unit = role.unit or ""
            rows.append(
                {
                    "participant_id": participant,
                    "study_day": "" if pd.isna(day) else str(int(day)) if isinstance(day, (int, float, np.integer, np.floating)) else str(day),
                    "measure": spec["title"],
                    "value": f"{float(value):g} {unit}".strip(),
                    "context": f"{severity}; link: {participant} day {day}",
                    "distance": float(distance),
                }
            )
    return sorted(rows, key=lambda row: row["distance"], reverse=True)


def _trigger_reason_panel(ax, alerts: pd.DataFrame) -> None:
    if alerts.empty or "trigger_reasons" not in alerts:
        render_warning_panel(ax, "Trigger Reasons", "Unavailable: trigger reason column not present.")
        return
    reasons: list[str] = []
    for value in alerts["trigger_reasons"].fillna("Missing"):
        parts = [part.strip() for part in str(value).replace(",", ";").split(";") if part.strip()]
        reasons.extend(parts or ["Missing"])
    counts = pd.Series(reasons).value_counts().head(8).sort_values(ascending=True)
    style_card(ax, "Trigger Reasons")
    bars = ax.barh(range(len(counts)), counts.values, color=DEFAULT_STYLE.palette[2])
    ax.set_yticks(range(len(counts)), [_wrap_label(label, width=18) for label in counts.index])
    ax.set_xlabel("Alerts")
    ax.set_xlim(0, max(float(counts.max()) * 1.22, 1.0))
    for bar, count in zip(bars, counts.values, strict=False):
        ax.text(bar.get_width(), bar.get_y() + bar.get_height() / 2, f" {count:,}", va="center", fontsize=8)


def _survey_state_panel(ax, alerts: pd.DataFrame) -> None:
    states = _survey_states(alerts)
    local = pd.DataFrame({"state": states})
    _count_bar(ax, local, "state", "Survey State")


def _contact_state_panel(ax, contacts: pd.DataFrame) -> None:
    if contacts.empty:
        render_warning_panel(ax, "Staff Contact State", "Unavailable: staff_contacts table not present.")
        return
    completion = _completion_series(contacts)
    states = completion.map(lambda value: "Missing/unknown" if pd.isna(value) else "Completed" if value else "Not completed")
    _count_bar(ax, pd.DataFrame({"state": states}), "state", "Staff Contact State")


def _funnel_panel(ax, alerts: pd.DataFrame, contacts: pd.DataFrame) -> None:
    generated = len(alerts)
    survey_completed = int((_survey_states(alerts) == "completed").sum()) if generated else 0
    call_attempted = _call_attempted_count(alerts, contacts)
    call_completed = _call_completed_count(alerts, contacts)
    stages = [
        ("Alert generated", generated, generated),
        ("Survey completed", survey_completed, generated),
        ("Staff call attempted", call_attempted, survey_completed or generated),
        ("Staff contact completed", call_completed, call_attempted),
    ]
    style_card(ax, "Engagement Funnel")
    values = [count for _, count, _ in stages]
    y = np.arange(len(stages))
    bars = ax.barh(y, values, color=[DEFAULT_STYLE.palette[0], DEFAULT_STYLE.palette[2], DEFAULT_STYLE.palette[5], DEFAULT_STYLE.palette[3]])
    ax.set_yticks(y, [stage for stage, _, _ in stages])
    ax.invert_yaxis()
    ax.set_xlabel("Count")
    for bar, (_stage, count, denominator) in zip(bars, stages, strict=False):
        pct = count / denominator if denominator else 0
        ax.text(bar.get_width(), bar.get_y() + bar.get_height() / 2, f" {count:,} ({pct:.0%})", va="center", fontsize=9, fontweight="bold")
    missing_survey = int((_survey_states(alerts) == "missing/unknown").sum()) if generated else 0
    missing_contact = int(_completion_series(contacts).isna().sum()) if not contacts.empty else 0
    ax.text(0.02, 0.05, f"Missing survey state: {missing_survey:,}; missing contact state: {missing_contact:,}. Completion is never inferred from missing state.", transform=ax.transAxes, fontsize=8, color=DEFAULT_STYLE.muted_text_color)


def _survey_states(alerts: pd.DataFrame) -> pd.Series:
    if alerts.empty:
        return pd.Series(dtype=str)
    if "survey_completion" in alerts:
        return alerts["survey_completion"].fillna("missing/unknown").astype(str).str.lower().replace({"": "missing/unknown"})
    if "survey_completed" in alerts:
        return alerts["survey_completed"].map(lambda value: "missing/unknown" if pd.isna(value) else "completed" if _as_bool(value) else "abandoned")
    return pd.Series(["missing/unknown"] * len(alerts), index=alerts.index)


def _call_attempted_count(alerts: pd.DataFrame, contacts: pd.DataFrame) -> int:
    if not alerts.empty and "called_nurse" in alerts:
        return int(alerts["called_nurse"].map(_as_bool).sum())
    if not contacts.empty and "contact_type" in contacts:
        return int(contacts["contact_type"].astype(str).str.contains("call|nurse", case=False, regex=True).sum())
    return 0


def _call_completed_count(alerts: pd.DataFrame, contacts: pd.DataFrame) -> int:
    if not alerts.empty and {"called_nurse", "nurse_outcome"}.issubset(alerts.columns):
        called = alerts["called_nurse"].map(_as_bool)
        return int(alerts.loc[called, "nurse_outcome"].notna().sum())
    if contacts.empty:
        return 0
    completion = _completion_series(contacts)
    if "contact_type" in contacts:
        nurse_mask = contacts["contact_type"].astype(str).str.contains("call|nurse", case=False, regex=True)
        return int(completion[nurse_mask].fillna(False).sum())
    return int(completion.fillna(False).sum())


def _completion_series(contacts: pd.DataFrame) -> pd.Series:
    if "completed" in contacts:
        return contacts["completed"].map(lambda value: np.nan if pd.isna(value) else _as_bool(value))
    if "participant_reached" in contacts:
        return contacts["participant_reached"].map(lambda value: np.nan if pd.isna(value) else _as_bool(value))
    return pd.Series([np.nan] * len(contacts), index=contacts.index)


def _register_results(results: list[PanelResult], manifest_path: str | Path, tables: EDATables, out_dir: Path) -> None:
    if not _is_under_outputs_figures(out_dir):
        return
    for result in results:
        artifact = FigureArtifact(
            artifact_id=_artifact_id(result.artifact_id, out_dir),
            path=_repo_relative(result.path),
            title=result.title,
            spec=SPEC_ID,
            inputs=_inputs_for_result(result.artifact_id),
            required_roles=_required_roles_for_result(result.artifact_id),
            optional_roles_used=_optional_roles_for_result(result.artifact_id),
            warnings=result.warnings,
            deterministic=True,
        )
        _upsert_artifact(manifest_path, artifact)


def _upsert_artifact(manifest_path: str | Path, artifact: FigureArtifact) -> None:
    path = Path(manifest_path)
    manifest = create_empty_manifest(path)
    entry = artifact.to_dict()
    entries = [existing for existing in manifest.entries if existing["artifact_id"] != entry["artifact_id"]]
    entries.append(entry)
    write_manifest(
        path,
        FigureArtifactManifest(
            schema_version=manifest.schema_version,
            manifest_path=manifest.manifest_path,
            entries=entries,
            warnings=manifest.warnings,
        ),
    )


def _artifact_id(base: str, out_dir: Path) -> str:
    if out_dir.as_posix().rstrip("/") == "outputs/figures/eda":
        return base
    suffix = out_dir.name.lower().replace("-", "_")
    return f"{suffix}_{base}"


def _inputs_for_result(artifact_id: str) -> list[str]:
    if "01" in artifact_id:
        return ["participants", "clinical_outcomes"]
    if "02" in artifact_id:
        return ["clinical_outcomes", "participants"]
    if "03" in artifact_id:
        return ["daily_vitals", "participants"]
    return ["alerts", "staff_contacts", "participants"]


def _required_roles_for_result(artifact_id: str) -> list[str]:
    if "01" in artifact_id:
        return ["participant.id"]
    if "02" in artifact_id:
        return ["outcome.participant_id", "outcome.cv_event"]
    if "03" in artifact_id:
        return ["vital.participant_id", "vital.date"]
    return ["alert.id", "alert.participant_id", "alert.level", "contact.type"]


def _optional_roles_for_result(artifact_id: str) -> list[str]:
    if "01" in artifact_id:
        return ["participant.age", "participant.pih_severity", "participant.has_ac"]
    if "02" in artifact_id:
        return ["outcome.ed_visit", "outcome.hospitalized", "outcome.heat_illness"]
    if "03" in artifact_id:
        return [spec["role"] for spec in _vital_specs()]
    return ["alert.trigger_reasons", "alert.called_nurse", "contact.completed"]


def _role_column(df: pd.DataFrame, role_id: str, *, entity: str) -> str | None:
    if df.empty:
        return None
    resolution = registry.resolve_column(df, role_id, entity=entity)
    return resolution.column if resolution.ok else None


def _first_present(df: pd.DataFrame, *columns: str) -> str | None:
    for column in columns:
        if column in df:
            return column
    return None


def _as_bool(value: Any) -> bool:
    if pd.isna(value):
        return False
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value) != 0.0
    text = str(value).strip().lower()
    return text in {"1", "true", "t", "yes", "y", "completed", "reached"}


def _percent(numerator: int | float, denominator: int | float) -> str:
    if not denominator:
        return "0%"
    return f"{float(numerator) / float(denominator):.1%}"


def _wrap_label(label: str, *, width: int = 22) -> str:
    return "\n".join(textwrap.wrap(str(label), width=width, break_long_words=False)) or str(label)


def _outside(value: float, bounds: tuple[float | None, float | None] | None) -> bool:
    if bounds is None:
        return False
    lower, upper = bounds
    return (lower is not None and value < lower) or (upper is not None and value > upper)


def _distance_outside(value: float, bounds: tuple[float | None, float | None] | None) -> float:
    if bounds is None:
        return 0.0
    lower, upper = bounds
    distances = []
    if lower is not None and value < lower:
        distances.append(abs(value - lower))
    if upper is not None and value > upper:
        distances.append(abs(value - upper))
    return max(distances) if distances else 0.0


def _is_under_outputs_figures(path: Path) -> bool:
    rel = Path(_repo_relative(path))
    return len(rel.parts) >= 2 and rel.parts[0] == "outputs" and rel.parts[1] == "figures"


def _repo_relative(path: Path) -> str:
    path = Path(path)
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.as_posix()


__all__ = [
    "EDATables",
    "PanelResult",
    "generate_core_dashboards",
    "load_eda_tables",
    "render_alert_engagement_funnel",
    "render_cohort_overview",
    "render_distribution_outliers",
    "render_outcome_prevalence",
]
