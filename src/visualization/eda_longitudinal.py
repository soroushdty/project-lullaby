from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import math
import warnings as py_warnings

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.colors import ListedColormap

from src.validation.semantics import DomainBooleanParsePolicy, parse_domain_boolean_series
from src.visualization import schema_registry as registry
from src.visualization.artifacts import FigureArtifact, FigureArtifactManifest, create_empty_manifest, write_manifest
from src.visualization.design import DEFAULT_STYLE, add_dashboard_title, configure_style, render_warning_panel, save_figure, style_card
from src.visualization.validation import validate_entity


SPEC_ID = "SPEC-009"
LONGITUDINAL_PANEL_FILENAMES = {
    "vital_trajectories": "05_vital_trajectories.png",
    "missingness_adherence": "06_missingness_adherence.png",
    "patient_timeline": "07_patient_timeline.png",
    "data_quality_scorecard": "08_data_quality_scorecard.png",
    "missingness_mechanism": "09_missingness_mechanism.png",
}
LONGITUDINAL_ARTIFACT_IDS = {
    "vital_trajectories": "eda_longitudinal_05_vital_trajectories",
    "missingness_adherence": "eda_longitudinal_06_missingness_adherence",
    "patient_timeline": "eda_longitudinal_07_patient_timeline",
    "data_quality_scorecard": "eda_longitudinal_08_data_quality_scorecard",
    "missingness_mechanism": "eda_longitudinal_09_missingness_mechanism",
}
LONGITUDINAL_REQUIRED_ROLES: dict[str, tuple[str, ...]] = {
    "participants": ("participant.id",),
    "daily_vitals": ("vital.participant_id", "vital.date", "vital.systolic_bp"),
    "alerts": ("alert.participant_id", "alert.date", "alert.level"),
    "staff_contacts": ("contact.participant_id", "contact.date", "contact.type"),
    "clinical_outcomes": ("outcome.participant_id", "outcome.cv_event", "outcome.cv_event_date"),
}
PANEL_REQUIRED_ROLES: dict[str, list[str]] = {
    LONGITUDINAL_ARTIFACT_IDS["vital_trajectories"]: ["vital.participant_id", "vital.date", "vital.systolic_bp"],
    LONGITUDINAL_ARTIFACT_IDS["missingness_adherence"]: ["vital.participant_id", "vital.date", "contact.type"],
    LONGITUDINAL_ARTIFACT_IDS["patient_timeline"]: [
        "participant.id",
        "vital.participant_id",
        "vital.date",
        "vital.systolic_bp",
        "alert.participant_id",
        "alert.date",
        "alert.level",
        "contact.participant_id",
        "contact.date",
        "contact.type",
        "outcome.participant_id",
        "outcome.cv_event",
        "outcome.cv_event_date",
    ],
    LONGITUDINAL_ARTIFACT_IDS["data_quality_scorecard"]: ["vital.participant_id", "vital.date", "contact.type"],
    LONGITUDINAL_ARTIFACT_IDS["missingness_mechanism"]: ["participant.id", "vital.participant_id", "vital.date", "vital.systolic_bp"],
}
BASE_QUALITY_WEIGHTS = {
    "wear_completeness": 0.40,
    "scale_adherence": 0.25,
    "vital_completeness": 0.20,
    "contact_traceability": 0.15,
}


@dataclass
class LongitudinalRunConfig:
    participant_id: str | None = None
    week_start: int | None = None
    week_end: int | None = None
    overlay_environment: bool = False

    def to_metadata(self) -> dict[str, Any]:
        return {
            "participant_id": self.participant_id,
            "week_start": self.week_start,
            "week_end": self.week_end,
            "overlay_environment": self.overlay_environment,
        }


@dataclass
class LongitudinalEDATables:
    data_dir: Path
    resolved_data_dir: Path
    participants: pd.DataFrame
    daily_vitals: pd.DataFrame
    alerts: pd.DataFrame
    staff_contacts: pd.DataFrame
    clinical_outcomes: pd.DataFrame
    environment: pd.DataFrame
    load_warnings: dict[str, list[str]] = field(default_factory=dict)


@dataclass(frozen=True)
class SelectedParticipantContext:
    participant_id: str
    selection_mode: str
    observed_vital_days: int
    distinct_alert_days: int
    distinct_outcome_events: int
    observed_vital_variable_count: int
    selection_score: int
    tie_breakers_applied: list[str] = field(default_factory=list)

    def to_metadata(self) -> dict[str, Any]:
        return {
            "participant_id": self.participant_id,
            "selection_mode": self.selection_mode,
            "observed_vital_days": self.observed_vital_days,
            "distinct_alert_days": self.distinct_alert_days,
            "distinct_outcome_events": self.distinct_outcome_events,
            "observed_vital_variable_count": self.observed_vital_variable_count,
            "selection_score": self.selection_score,
            "tie_breakers_applied": self.tie_breakers_applied,
        }


@dataclass(frozen=True)
class LongitudinalPanelResult:
    artifact_id: str
    path: Path
    title: str
    warnings: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)


class LongitudinalInputError(RuntimeError):
    pass


def generate_longitudinal_dashboards(
    data_dir: str | Path,
    out_dir: str | Path = Path("outputs/figures/eda"),
    *,
    manifest_path: str | Path = Path("outputs/figures/manifest.json"),
    participant_id: str | None = None,
    week_start: int | None = None,
    week_end: int | None = None,
    overlay_environment: bool = False,
) -> list[LongitudinalPanelResult]:
    config = LongitudinalRunConfig(
        participant_id=participant_id,
        week_start=week_start,
        week_end=week_end,
        overlay_environment=overlay_environment,
    )
    _validate_week_range(config)
    tables = load_longitudinal_tables(data_dir, required_roles=LONGITUDINAL_REQUIRED_ROLES)
    selected = _resolve_selected_participant(tables, participant_id)
    filtered_tables = _filter_tables_for_weeks(tables, config)
    output_dir = Path(out_dir)
    results = [
        render_vital_trajectories(filtered_tables, output_dir, selected, config),
        render_missingness_adherence(filtered_tables, output_dir, config),
    ]
    from src.visualization.patient_view import render_patient_timeline

    timeline = render_patient_timeline(
        participants=filtered_tables.participants,
        daily_vitals=filtered_tables.daily_vitals,
        alerts=filtered_tables.alerts,
        staff_contacts=filtered_tables.staff_contacts,
        clinical_outcomes=filtered_tables.clinical_outcomes,
        environment=filtered_tables.environment,
        selected=selected,
        data_source=filtered_tables.data_dir.as_posix(),
        out_dir=output_dir,
        overlay_environment=config.overlay_environment,
        week_start=config.week_start,
        week_end=config.week_end,
    )
    results.append(
        LongitudinalPanelResult(
            timeline.artifact_id,
            timeline.path,
            timeline.title,
            timeline.warnings,
            timeline.metadata,
        )
    )
    results.extend(
        [
            render_data_quality_scorecard(filtered_tables, output_dir, config),
            render_missingness_mechanism(filtered_tables, output_dir, config),
        ]
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    _register_results(results, manifest_path, filtered_tables, output_dir)
    return results


def load_longitudinal_tables(
    data_dir: str | Path,
    *,
    required_roles: dict[str, tuple[str, ...]] | None = None,
) -> LongitudinalEDATables:
    required_roles = required_roles or {}
    requested = Path(data_dir)
    resolved = _resolve_data_dir(requested)
    frames: dict[str, pd.DataFrame] = {}
    load_warnings: dict[str, list[str]] = {}
    errors: list[str] = []
    for entity in ("participants", "daily_vitals", "alerts", "staff_contacts", "clinical_outcomes", "environment"):
        required = entity in required_roles
        try:
            frame = registry.load_entity(resolved, entity)
        except registry.SchemaValidationError as exc:
            if required:
                errors.append(_format_input_error(entity, resolved, exc))
            else:
                load_warnings[entity] = [str(exc)]
            frame = pd.DataFrame()
        frames[entity] = frame

    for entity, roles in required_roles.items():
        frame = frames.get(entity, pd.DataFrame())
        if frame.empty and entity not in load_warnings:
            errors.append(f"{entity}: required table in {resolved} has no rows")
            continue
        if frame.empty:
            continue
        entity_result = validate_entity(entity, frame, source_file=str(_entity_source_path(resolved, entity)))
        errors.extend(f"{entity}: {_entity_source_path(resolved, entity)}: {message}" for message in entity_result.errors)
        errors.extend(_missing_required_role_errors(entity, frame, roles, resolved, panel_label="Panel 7" if entity in {"alerts", "staff_contacts", "clinical_outcomes"} else "longitudinal"))
        errors.extend(_required_boolean_errors(entity, frame, roles, resolved))

    if errors:
        joined = "\n".join(f"- {error}" for error in errors)
        raise LongitudinalInputError(f"Required longitudinal EDA input validation failed before artifact generation:\n{joined}")

    return LongitudinalEDATables(
        data_dir=requested,
        resolved_data_dir=resolved,
        participants=frames["participants"],
        daily_vitals=_with_study_day(frames["daily_vitals"], frames["participants"]),
        alerts=frames["alerts"],
        staff_contacts=frames["staff_contacts"],
        clinical_outcomes=frames["clinical_outcomes"],
        environment=frames["environment"],
        load_warnings=load_warnings,
    )


def select_default_participant(tables: LongitudinalEDATables) -> SelectedParticipantContext:
    daily = tables.daily_vitals
    participant_col = _role_column(daily, "vital.participant_id", entity="daily_vitals") or "participant_id"
    if daily.empty or participant_col not in daily:
        raise LongitudinalInputError("Cannot select default participant because daily_vitals participant id is unavailable")
    candidates = sorted(daily[participant_col].dropna().astype(str).unique())
    rows: list[dict[str, Any]] = []
    vital_roles = _available_vital_roles(daily)
    for participant_id in candidates:
        participant_daily = daily[daily[participant_col].astype(str) == participant_id]
        observed_days = _observed_vital_days(participant_daily, vital_roles)
        alert_days = _distinct_event_days(tables.alerts, participant_id, "alert.participant_id", "alert.date")
        outcome_events = _distinct_outcome_events(tables.clinical_outcomes, participant_id)
        variable_count = int(participant_daily[[col for col in (_role_column(daily, role, entity="daily_vitals") for role in vital_roles) if col]].notna().sum().sum())
        rows.append(
            {
                "participant_id": participant_id,
                "observed_vital_days": observed_days,
                "distinct_alert_days": alert_days,
                "distinct_outcome_events": outcome_events,
                "observed_vital_variable_count": variable_count,
                "selection_score": observed_days + alert_days + outcome_events,
            }
        )
    ranked = sorted(
        rows,
        key=lambda row: (
            -row["selection_score"],
            -row["observed_vital_variable_count"],
            row["participant_id"],
        ),
    )
    selected = ranked[0]
    return SelectedParticipantContext(
        participant_id=selected["participant_id"],
        selection_mode="automatic",
        observed_vital_days=selected["observed_vital_days"],
        distinct_alert_days=selected["distinct_alert_days"],
        distinct_outcome_events=selected["distinct_outcome_events"],
        observed_vital_variable_count=selected["observed_vital_variable_count"],
        selection_score=selected["selection_score"],
        tie_breakers_applied=["observed_vital_variable_count", "lexicographic_participant_id"],
    )


def prepare_selected_vital_series(daily_vitals: pd.DataFrame, participant_id: str, role_id: str) -> pd.DataFrame:
    column = _role_column(daily_vitals, role_id, entity="daily_vitals")
    participant_col = _role_column(daily_vitals, "vital.participant_id", entity="daily_vitals") or "participant_id"
    if column is None or participant_col not in daily_vitals:
        return pd.DataFrame({"study_day": [], "value": []})
    daily = _with_study_day(daily_vitals)
    participant = daily[daily[participant_col].astype(str) == str(participant_id)]
    if participant.empty:
        return pd.DataFrame({"study_day": [], "value": []})
    min_day = int(participant["__study_day"].min())
    max_day = int(participant["__study_day"].max())
    indexed = participant.groupby("__study_day")[column].mean()
    full = pd.Series(index=range(min_day, max_day + 1), dtype=float)
    full.loc[indexed.index.astype(int)] = indexed.values
    return pd.DataFrame({"study_day": list(full.index), "value": full.values})


def calculate_quality_scores(tables: LongitudinalEDATables) -> tuple[pd.DataFrame, dict[str, Any], list[str]]:
    daily = _with_study_day(tables.daily_vitals)
    participant_col = _role_column(daily, "vital.participant_id", entity="daily_vitals") or "participant_id"
    participants = sorted(daily[participant_col].dropna().astype(str).unique()) if participant_col in daily else []
    expected = _expected_days_by_participant(daily)
    scores = pd.DataFrame({"participant_id": participants})
    components: dict[str, pd.Series] = {}
    warnings: list[str] = []

    wear_col = _role_column(daily, "vital.sensor_wear_hours", entity="daily_vitals")
    if wear_col:
        wear_sum = daily.groupby(participant_col)[wear_col].sum(min_count=1)
        components["wear_completeness"] = pd.Series(
            {pid: min(float(wear_sum.get(pid, 0.0)) / max(float(expected.get(pid, 0)) * 24.0, 1.0), 1.0) for pid in participants}
        )
    else:
        warnings.append("wear_completeness unavailable: vital.sensor_wear_hours missing")

    scale_col = _role_column(daily, "vital.scale_used", entity="daily_vitals")
    if scale_col:
        parsed = parse_domain_boolean_series(
            daily[scale_col],
            DomainBooleanParsePolicy(role="vital.scale_used", required=False),
            source_column=scale_col,
        )
        scale = daily.assign(__scale_true=parsed.true_mask)
        scale_counts = scale.groupby(participant_col)["__scale_true"].sum()
        components["scale_adherence"] = pd.Series(
            {pid: min(float(scale_counts.get(pid, 0.0)) / max(float(expected.get(pid, 0)), 1.0), 1.0) for pid in participants}
        )
        warnings.extend(parsed.warnings)
    else:
        warnings.append("scale_adherence unavailable: vital.scale_used missing")

    vital_roles = _available_vital_roles(daily)
    vital_cols = [col for col in (_role_column(daily, role, entity="daily_vitals") for role in vital_roles) if col]
    if vital_cols:
        observed_counts = daily.groupby(participant_col)[vital_cols].apply(lambda frame: int(frame.notna().sum().sum()))
        components["vital_completeness"] = pd.Series(
            {pid: min(float(observed_counts.get(pid, 0)) / max(float(expected.get(pid, 0)) * len(vital_cols), 1.0), 1.0) for pid in participants}
        )
    else:
        warnings.append("vital_completeness unavailable: no vital roles present")

    contact_pid = _role_column(tables.staff_contacts, "contact.participant_id", entity="staff_contacts")
    contact_date = _role_column(tables.staff_contacts, "contact.date", entity="staff_contacts")
    if contact_pid and contact_date and not tables.staff_contacts.empty:
        contacts = tables.staff_contacts.copy()
        contacts[contact_pid] = contacts[contact_pid].astype(str)
        contacts["__traceable"] = pd.to_datetime(contacts[contact_date], errors="coerce").notna()
        trace_counts = contacts.groupby(contact_pid)["__traceable"].sum()
        components["contact_traceability"] = pd.Series(
            {
                pid: min(float(trace_counts.get(pid, 0.0)) / max(math.ceil(float(expected.get(pid, 0)) / 7.0), 1.0), 1.0)
                for pid in participants
            }
        )
    else:
        warnings.append("contact_traceability unavailable: staff contact participant/date roles missing")

    unavailable = [component for component in BASE_QUALITY_WEIGHTS if component not in components]
    available_weight = sum(BASE_QUALITY_WEIGHTS[name] for name in components)
    adjusted_weights = {name: BASE_QUALITY_WEIGHTS[name] / available_weight for name in components} if available_weight else {}
    for name, values in components.items():
        scores[name] = scores["participant_id"].map(values).fillna(0.0).clip(0.0, 1.0)
    scores["valid_signal_hours"] = scores["participant_id"].map(_valid_signal_hours(daily)).fillna(0.0)
    gap_stats = _gap_stats(daily)
    scores["gap_count"] = scores["participant_id"].map({pid: stats["gap_count"] for pid, stats in gap_stats.items()}).fillna(0).astype(int)
    scores["gap_duration_days"] = scores["participant_id"].map({pid: stats["gap_duration_days"] for pid, stats in gap_stats.items()}).fillna(0).astype(int)
    if adjusted_weights:
        scores["quality_score"] = sum(scores[name] * weight for name, weight in adjusted_weights.items()).clip(0.0, 1.0)
    else:
        scores["quality_score"] = 0.0
    scores = scores.sort_values(["quality_score", "valid_signal_hours", "participant_id"], ascending=[False, False, True]).reset_index(drop=True)
    metadata = {
        "base_weights": BASE_QUALITY_WEIGHTS,
        "adjusted_weights": adjusted_weights,
        "unavailable_components": unavailable,
        "formula": " + ".join(f"{weight:.4g} * {name}" for name, weight in adjusted_weights.items()) if adjusted_weights else "unavailable",
    }
    return scores, metadata, warnings


def render_vital_trajectories(
    tables: LongitudinalEDATables,
    out_dir: Path,
    selected: SelectedParticipantContext,
    config: LongitudinalRunConfig,
) -> LongitudinalPanelResult:
    configure_style()
    fig = plt.figure(figsize=(16, 9), constrained_layout=False)
    subtitle = _subtitle(tables, [tables.daily_vitals])
    add_dashboard_title(fig, "Vital Trajectories", f"{subtitle} | selected participant: {selected.participant_id}")
    gs = fig.add_gridspec(3, 3, left=0.04, right=0.98, top=0.88, bottom=0.08, wspace=0.28, hspace=0.48)
    warnings: list[str] = []
    metadata: dict[str, Any] = {
        "selected_participant": selected.to_metadata(),
        "week_filter": {"week_start": config.week_start, "week_end": config.week_end},
        "overlay_environment": config.overlay_environment,
        "imputation_performed": False,
        "observed_denominators": {},
    }
    vital_roles = _vital_roles()
    daily = _with_study_day(tables.daily_vitals)
    participant_col = _role_column(daily, "vital.participant_id", entity="daily_vitals") or "participant_id"
    for index, role_id in enumerate(vital_roles):
        ax = fig.add_subplot(gs[index // 3, index % 3])
        role = registry.get_role(role_id)
        column = _role_column(daily, role_id, entity="daily_vitals")
        if column is None:
            render_warning_panel(ax, role.label, f"Unavailable: {role_id} not present.")
            warnings.append(f"{role_id} unavailable")
            continue
        cohort = daily.groupby("__study_day")[column].agg(["mean", "count"]).reset_index()
        selected_series = prepare_selected_vital_series(daily, selected.participant_id, role_id)
        style_card(ax, f"{role.label} ({role.unit or 'unitless'})")
        ax.plot(cohort["__study_day"], cohort["mean"], color=DEFAULT_STYLE.muted_text_color, linewidth=1.5, label="Cohort mean")
        ax.plot(selected_series["study_day"], selected_series["value"], color=DEFAULT_STYLE.palette[0], marker="o", linewidth=1.8, label=selected.participant_id)
        observed_days = int(selected_series["value"].notna().sum())
        total_days = int(len(selected_series))
        metadata["observed_denominators"][role_id] = {"observed_days": observed_days, "expected_days": total_days}
        ax.text(0.02, 0.94, f"Observed days {observed_days}/{total_days}; cohort rows {int(cohort['count'].sum())}", transform=ax.transAxes, ha="left", va="top", fontsize=7, color=DEFAULT_STYLE.muted_text_color)
        if index == 0 and config.overlay_environment:
            overlay = _environment_overlay_series(tables, daily)
            if overlay.empty:
                warnings.append("environment overlay unavailable")
                ax.text(0.02, 0.08, "Environment overlay unavailable", transform=ax.transAxes, fontsize=7, color=DEFAULT_STYLE.warning_color)
            else:
                env_ax = ax.twinx()
                env_ax.plot(overlay["study_day"], overlay["value"], color=DEFAULT_STYLE.warning_color, alpha=0.45, linestyle="--", label=overlay["label"].iloc[0])
                env_ax.set_ylabel(overlay["label"].iloc[0], fontsize=7, color=DEFAULT_STYLE.warning_color)
                env_ax.tick_params(axis="y", labelsize=7)
        if index == 0:
            ax.legend(loc="upper right", fontsize=7)
        ax.set_xlabel("Study day")
        ax.set_ylabel(role.unit or "")
    path = out_dir / LONGITUDINAL_PANEL_FILENAMES["vital_trajectories"]
    save_figure(fig, path)
    plt.close(fig)
    return LongitudinalPanelResult(LONGITUDINAL_ARTIFACT_IDS["vital_trajectories"], path, "Vital Trajectories", warnings, metadata)


def render_missingness_adherence(tables: LongitudinalEDATables, out_dir: Path, config: LongitudinalRunConfig) -> LongitudinalPanelResult:
    configure_style()
    fig = plt.figure(figsize=(16, 9), constrained_layout=False)
    subtitle = _subtitle(tables, [tables.daily_vitals, tables.staff_contacts])
    add_dashboard_title(fig, "Missingness and Adherence", subtitle)
    gs = fig.add_gridspec(3, 4, left=0.04, right=0.98, top=0.88, bottom=0.07, wspace=0.34, hspace=0.55)
    daily = _with_study_day(tables.daily_vitals)
    matrix, matrix_meta = _missingness_matrix(daily)
    display = matrix
    warnings: list[str] = []
    if len(matrix) > 250:
        positions = np.linspace(0, len(matrix) - 1, 250, dtype=int)
        display = matrix.iloc[sorted(set(positions))]
        warnings.append("missingness matrix display rows downsampled; metrics computed on all participants")
    ax = fig.add_subplot(gs[0:2, 0:2])
    style_card(ax, "Participant x Study Day Missingness Matrix")
    if display.empty:
        render_warning_panel(ax, "Missingness Matrix", "No participant-day rows available.")
    else:
        ax.imshow(display.to_numpy(), aspect="auto", interpolation="nearest", cmap=ListedColormap(["#ffffff", DEFAULT_STYLE.palette[0]]), vmin=0, vmax=1)
        ax.set_xlabel("Study day")
        ax.set_ylabel("Participants")
        ax.set_xticks(range(len(display.columns))[:: max(1, len(display.columns) // 8)], [str(col) for col in display.columns[:: max(1, len(display.columns) // 8)]], fontsize=7)
        ax.set_yticks([])
        ax.text(0.02, -0.15, "Present = filled square | Missing = white square | Labels make state explicit beyond color.", transform=ax.transAxes, fontsize=8, color=DEFAULT_STYLE.muted_text_color)
    _trend_panel(fig.add_subplot(gs[0, 2]), daily, "vital.sensor_wear_hours", "Wear Hours Over Time", "hours")
    _scale_adherence_panel(fig.add_subplot(gs[0, 3]), daily)
    _adherence_decline_panel(fig.add_subplot(gs[1, 2]), daily)
    _missingness_by_variable_panel(fig.add_subplot(gs[1, 3]), daily)
    gap_summary, gap_warnings = _gap_cluster_summary(tables)
    warnings.extend(gap_warnings)
    _gap_summary_panel(fig.add_subplot(gs[2, :]), gap_summary)
    metadata = {
        "display_downsampled": len(matrix) > 250,
        "display_rows": int(len(display)),
        "metric_rows": int(len(matrix)),
        "non_color_encoding": ["labels", "legend", "filled_vs_white_square"],
        "gap_cluster_summary": gap_summary,
        "matrix": matrix_meta,
        "imputation_performed": False,
        "week_filter": {"week_start": config.week_start, "week_end": config.week_end},
    }
    path = out_dir / LONGITUDINAL_PANEL_FILENAMES["missingness_adherence"]
    save_figure(fig, path)
    plt.close(fig)
    return LongitudinalPanelResult(LONGITUDINAL_ARTIFACT_IDS["missingness_adherence"], path, "Missingness and Adherence", warnings, metadata)


def render_data_quality_scorecard(tables: LongitudinalEDATables, out_dir: Path, config: LongitudinalRunConfig) -> LongitudinalPanelResult:
    configure_style()
    scores, formula_metadata, warnings = calculate_quality_scores(tables)
    fig = plt.figure(figsize=(16, 9), constrained_layout=False)
    add_dashboard_title(fig, "Data-Quality and Signal-Quality Scorecard", f"{_subtitle(tables, [tables.daily_vitals, tables.staff_contacts])} | ranked by completeness, not clinical risk")
    gs = fig.add_gridspec(3, 4, left=0.04, right=0.98, top=0.88, bottom=0.07, wspace=0.38, hspace=0.55)
    top = scores.head(14)
    ax = fig.add_subplot(gs[:, 0:2])
    style_card(ax, "Participant Completeness Ranking")
    if top.empty:
        render_warning_panel(ax, "Quality Scorecard", "No participant rows available.")
    else:
        bars = ax.barh(range(len(top)), top["quality_score"], color=DEFAULT_STYLE.palette[0])
        ax.set_yticks(range(len(top)), top["participant_id"])
        ax.invert_yaxis()
        ax.set_xlim(0, 1)
        ax.set_xlabel("Quality score (0-1)")
        for bar, value in zip(bars, top["quality_score"], strict=False):
            ax.text(bar.get_width(), bar.get_y() + bar.get_height() / 2, f" {value:.2f}", va="center", fontsize=8)
    _component_panel(fig.add_subplot(gs[0, 2]), scores, "wear_completeness", "Wear Completeness")
    _component_panel(fig.add_subplot(gs[0, 3]), scores, "scale_adherence", "Scale Adherence")
    _component_panel(fig.add_subplot(gs[1, 2]), scores, "vital_completeness", "Vital Completeness")
    _component_panel(fig.add_subplot(gs[1, 3]), scores, "contact_traceability", "Contact Traceability")
    _gap_score_panel(fig.add_subplot(gs[2, 2:4]), scores)
    metadata = {
        "quality_score_formula": formula_metadata,
        "rank_basis": "data completeness and signal quality, not clinical risk",
        "top_participants": top[["participant_id", "quality_score"]].to_dict("records"),
        "week_filter": {"week_start": config.week_start, "week_end": config.week_end},
    }
    if formula_metadata["unavailable_components"]:
        warnings.append(f"quality score components unavailable: {', '.join(formula_metadata['unavailable_components'])}")
    path = out_dir / LONGITUDINAL_PANEL_FILENAMES["data_quality_scorecard"]
    save_figure(fig, path)
    plt.close(fig)
    return LongitudinalPanelResult(LONGITUDINAL_ARTIFACT_IDS["data_quality_scorecard"], path, "Data-Quality and Signal-Quality Scorecard", warnings, metadata)


def render_missingness_mechanism(tables: LongitudinalEDATables, out_dir: Path, config: LongitudinalRunConfig) -> LongitudinalPanelResult:
    configure_style()
    fig = plt.figure(figsize=(16, 9), constrained_layout=False)
    add_dashboard_title(fig, "Missingness-Mechanism Diagnostics", f"{_subtitle(tables, [tables.daily_vitals, tables.participants])} | exploratory signals consistent with hypotheses, not proof")
    gs = fig.add_gridspec(3, 4, left=0.04, right=0.98, top=0.88, bottom=0.07, wspace=0.35, hspace=0.55)
    daily = _with_study_day(tables.daily_vitals)
    warnings: list[str] = []
    day_rates = _missingness_rate_by_day(daily)
    _line_rate_panel(fig.add_subplot(gs[0, 0:2]), day_rates, "Missingness Rate by Study Day")
    context_rates, context_warnings = _context_missingness_rates(tables)
    warnings.extend(context_warnings)
    _context_rates_panel(fig.add_subplot(gs[0, 2:4]), context_rates)
    heat_rates, heat_warnings = _heat_missingness_rates(tables)
    warnings.extend(heat_warnings)
    _context_rates_panel(fig.add_subplot(gs[1, 0:2]), heat_rates, title="Missingness vs Heat Exposure")
    abnormal_rates = _recent_abnormal_vital_missingness(daily)
    _context_rates_panel(fig.add_subplot(gs[1, 2:4]), abnormal_rates, title="Missingness vs Recent Abnormal Vitals")
    render_warning_panel(
        fig.add_subplot(gs[2, :]),
        "Exploratory Mechanism Evidence, Not Proof",
        "Patterns are exploratory signals consistent with MCAR, MAR, or MNAR hypotheses. No imputation, model training, or causal mechanism claim is performed.",
    )
    metadata = {
        "mechanism_label": "exploratory signals consistent with MCAR, MAR, or MNAR hypotheses; not proof",
        "imputation_performed": False,
        "missingness_rate_by_study_day": day_rates.to_dict("records"),
        "context_rates": context_rates,
        "heat_rates": heat_rates,
        "recent_abnormal_vital_rates": abnormal_rates,
        "week_filter": {"week_start": config.week_start, "week_end": config.week_end},
    }
    path = out_dir / LONGITUDINAL_PANEL_FILENAMES["missingness_mechanism"]
    save_figure(fig, path)
    plt.close(fig)
    return LongitudinalPanelResult(LONGITUDINAL_ARTIFACT_IDS["missingness_mechanism"], path, "Missingness-Mechanism Diagnostics", warnings, metadata)


def _filter_tables_for_weeks(tables: LongitudinalEDATables, config: LongitudinalRunConfig) -> LongitudinalEDATables:
    if config.week_start is None and config.week_end is None:
        return tables
    start = 1 if config.week_start is None else config.week_start
    end = math.inf if config.week_end is None else config.week_end
    min_day = (start - 1) * 7 + 1
    max_day = int(end * 7) if math.isfinite(end) else math.inf
    daily = _with_study_day(tables.daily_vitals)
    filtered_daily = daily[daily["__study_day"].between(min_day, max_day if math.isfinite(max_day) else daily["__study_day"].max())].copy()
    env = tables.environment.copy()
    if not env.empty:
        env_day = _environment_study_day(env)
        env = env.assign(__study_day=env_day)
        env = env[env["__study_day"].between(min_day, max_day if math.isfinite(max_day) else env["__study_day"].max())].copy()
    return LongitudinalEDATables(
        tables.data_dir,
        tables.resolved_data_dir,
        tables.participants,
        filtered_daily,
        tables.alerts,
        tables.staff_contacts,
        tables.clinical_outcomes,
        env,
        tables.load_warnings,
    )


def _resolve_selected_participant(tables: LongitudinalEDATables, participant_id: str | None) -> SelectedParticipantContext:
    if participant_id is None:
        return select_default_participant(tables)
    all_ids = _all_known_participant_ids(tables)
    if str(participant_id) not in all_ids:
        raise LongitudinalInputError(f"Unknown participant id for longitudinal rendering: {participant_id}")
    auto = select_default_participant(tables)
    participant_daily = tables.daily_vitals[tables.daily_vitals["participant_id"].astype(str) == str(participant_id)] if "participant_id" in tables.daily_vitals else pd.DataFrame()
    vital_roles = _available_vital_roles(tables.daily_vitals)
    return SelectedParticipantContext(
        participant_id=str(participant_id),
        selection_mode="provided",
        observed_vital_days=_observed_vital_days(participant_daily, vital_roles),
        distinct_alert_days=_distinct_event_days(tables.alerts, str(participant_id), "alert.participant_id", "alert.date"),
        distinct_outcome_events=_distinct_outcome_events(tables.clinical_outcomes, str(participant_id)),
        observed_vital_variable_count=int(participant_daily[[col for col in (_role_column(tables.daily_vitals, role, entity="daily_vitals") for role in vital_roles) if col]].notna().sum().sum()) if not participant_daily.empty else 0,
        selection_score=0,
        tie_breakers_applied=[f"provided participant; automatic default would be {auto.participant_id}"],
    )


def _with_study_day(daily: pd.DataFrame, participants: pd.DataFrame | None = None) -> pd.DataFrame:
    if daily.empty:
        return daily.copy()
    result = daily.copy()
    study_col = _role_column(result, "vital.study_day", entity="daily_vitals")
    if study_col:
        result["__study_day"] = pd.to_numeric(result[study_col], errors="coerce").astype("Int64")
        return result
    date_col = _role_column(result, "vital.date", entity="daily_vitals") or "date"
    participant_col = _role_column(result, "vital.participant_id", entity="daily_vitals") or "participant_id"
    parsed_dates = pd.to_datetime(result[date_col], errors="coerce")
    if participants is not None and not participants.empty and "observation_start_date" in participants.columns:
        starts = pd.to_datetime(participants.set_index("participant_id")["observation_start_date"], errors="coerce")
        result["__start"] = result[participant_col].astype(str).map(starts)
    else:
        result["__start"] = parsed_dates.groupby(result[participant_col].astype(str)).transform("min")
    result["__study_day"] = (parsed_dates - result["__start"]).dt.days.add(1).astype("Int64")
    return result.drop(columns=["__start"])


def _validate_week_range(config: LongitudinalRunConfig) -> None:
    if config.week_start is not None and config.week_start < 1:
        raise LongitudinalInputError("--week-start must be >= 1")
    if config.week_end is not None and config.week_end < 1:
        raise LongitudinalInputError("--week-end must be >= 1")
    if config.week_start is not None and config.week_end is not None and config.week_start > config.week_end:
        raise LongitudinalInputError("--week-start must be less than or equal to --week-end")


def _resolve_data_dir(path: Path) -> Path:
    if path.exists():
        return path
    if path.name == "raw" and path.parent.exists():
        return path.parent
    return path


def _format_input_error(entity: str, data_dir: Path, exc: registry.SchemaValidationError) -> str:
    candidates = ", ".join(exc.candidates) if exc.candidates else "registered source filename"
    role = f" role={exc.role_id}" if exc.role_id else ""
    return f"{entity}: {data_dir}: {exc}{role}; expected {candidates}"


def _entity_source_path(data_dir: Path, entity: str) -> Path:
    spec = registry.get_entity(entity)
    for filename in spec.source_filenames:
        path = data_dir / filename
        if path.exists():
            return path
    return data_dir


def _missing_required_role_errors(entity: str, frame: pd.DataFrame, roles: tuple[str, ...], data_dir: Path, *, panel_label: str) -> list[str]:
    errors: list[str] = []
    for role_id in roles:
        resolution = registry.resolve_column(frame, role_id, entity=entity)
        if resolution.ok:
            continue
        detail = resolution.error or resolution.warning or f"Missing required role {role_id}"
        errors.append(f"{panel_label}: {entity}: {_entity_source_path(data_dir, entity)}: {detail}")
    return errors


def _required_boolean_errors(entity: str, frame: pd.DataFrame, roles: tuple[str, ...], data_dir: Path) -> list[str]:
    errors: list[str] = []
    for role_id in roles:
        resolution = registry.resolve_column(frame, role_id, entity=entity)
        if not resolution.ok or not resolution.column:
            continue
        role = registry.get_role(role_id)
        if role.value_type != "boolean":
            continue
        parsed = parse_domain_boolean_series(
            frame[resolution.column],
            DomainBooleanParsePolicy(role=role_id, required=True),
            source_column=resolution.column,
        )
        errors.extend(f"{entity}: {_entity_source_path(data_dir, entity)}: {message}" for message in parsed.errors)
    return errors


def _role_column(df: pd.DataFrame, role_id: str, *, entity: str) -> str | None:
    if df.empty:
        return None
    resolution = registry.resolve_column(df, role_id, entity=entity)
    return resolution.column if resolution.ok else None


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


def _available_vital_roles(daily: pd.DataFrame) -> list[str]:
    return [role for role in _vital_roles() if _role_column(daily, role, entity="daily_vitals")]


def _observed_vital_days(participant_daily: pd.DataFrame, vital_roles: list[str]) -> int:
    if participant_daily.empty:
        return 0
    daily = _with_study_day(participant_daily)
    columns = [col for col in (_role_column(daily, role, entity="daily_vitals") for role in vital_roles) if col]
    if not columns:
        return 0
    observed = daily[columns].notna().any(axis=1)
    return int(daily.loc[observed, "__study_day"].nunique())


def _distinct_event_days(frame: pd.DataFrame, participant_id: str, participant_role: str, date_role: str) -> int:
    participant_col = _role_column(frame, participant_role, entity=registry.get_role(participant_role).entity)
    date_col = _role_column(frame, date_role, entity=registry.get_role(date_role).entity)
    if frame.empty or participant_col is None or date_col is None:
        return 0
    subset = frame[frame[participant_col].astype(str) == participant_id]
    return int(pd.to_datetime(subset[date_col], errors="coerce", format="ISO8601").dropna().dt.date.nunique())


def _distinct_outcome_events(outcomes: pd.DataFrame, participant_id: str) -> int:
    participant_col = _role_column(outcomes, "outcome.participant_id", entity="clinical_outcomes")
    date_col = _role_column(outcomes, "outcome.cv_event_date", entity="clinical_outcomes")
    if outcomes.empty or participant_col is None:
        return 0
    subset = outcomes[outcomes[participant_col].astype(str) == participant_id]
    if date_col:
        return int(pd.to_datetime(subset[date_col], errors="coerce", format="ISO8601").dropna().nunique())
    return int(len(subset))


def _all_known_participant_ids(tables: LongitudinalEDATables) -> set[str]:
    ids: set[str] = set()
    for frame, role in [
        (tables.participants, "participant.id"),
        (tables.daily_vitals, "vital.participant_id"),
        (tables.alerts, "alert.participant_id"),
        (tables.staff_contacts, "contact.participant_id"),
        (tables.clinical_outcomes, "outcome.participant_id"),
    ]:
        entity = registry.get_role(role).entity
        column = _role_column(frame, role, entity=entity)
        if column:
            ids.update(frame[column].dropna().astype(str))
    return ids


def _subtitle(tables: LongitudinalEDATables, frames: list[pd.DataFrame]) -> str:
    dates: list[pd.Timestamp] = []
    for frame in frames:
        for column in ("date", "contact_date", "cv_event_date", "observation_start_date"):
            if column in frame:
                dates.extend(pd.to_datetime(frame[column], errors="coerce").dropna().tolist())
    if dates:
        return f"Source: {tables.data_dir.as_posix()} | Date range: {min(dates).date().isoformat()} to {max(dates).date().isoformat()}"
    return f"Source: {tables.data_dir.as_posix()} | Date range unavailable"


def _environment_overlay_series(tables: LongitudinalEDATables, daily: pd.DataFrame) -> pd.DataFrame:
    if not tables.environment.empty:
        env = tables.environment.copy()
        day = _environment_study_day(env)
        heat_col = _role_column(env, "environment.heat_index_c", entity="environment")
        temp_col = _role_column(env, "environment.ambient_temp_c", entity="environment")
        column = heat_col or temp_col
        label = "Heat index C" if heat_col else "Ambient C"
        if column:
            return pd.DataFrame({"study_day": day, "value": pd.to_numeric(env[column], errors="coerce"), "label": label}).dropna()
    heat_col = _role_column(daily, "vital.heat_index_c", entity="daily_vitals")
    temp_col = _role_column(daily, "vital.ambient_temperature_c", entity="daily_vitals")
    column = heat_col or temp_col
    if column:
        grouped = daily.groupby("__study_day")[column].mean().reset_index()
        return pd.DataFrame({"study_day": grouped["__study_day"], "value": grouped[column], "label": "Heat index C" if heat_col else "Ambient C"}).dropna()
    return pd.DataFrame()


def _environment_study_day(env: pd.DataFrame) -> pd.Series:
    if "study_day" in env:
        return pd.to_numeric(env["study_day"], errors="coerce").astype("Int64")
    if "date" in env:
        dates = pd.to_datetime(env["date"], errors="coerce")
        return (dates - dates.min()).dt.days.add(1).astype("Int64")
    return pd.Series([pd.NA] * len(env), index=env.index, dtype="Int64")


def _missingness_matrix(daily: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    participant_col = _role_column(daily, "vital.participant_id", entity="daily_vitals") or "participant_id"
    vital_cols = [col for col in (_role_column(daily, role, entity="daily_vitals") for role in _available_vital_roles(daily)) if col]
    if daily.empty or participant_col not in daily or not vital_cols:
        return pd.DataFrame(), {"participants": 0, "study_days": 0}
    daily = _with_study_day(daily)
    present = daily[vital_cols].notna().any(axis=1).astype(int)
    local = daily.assign(__present=present)
    matrix = local.pivot_table(index=participant_col, columns="__study_day", values="__present", aggfunc="max").fillna(0).sort_index()
    columns = list(range(int(daily["__study_day"].min()), int(daily["__study_day"].max()) + 1))
    matrix = matrix.reindex(columns=columns, fill_value=0)
    return matrix, {"participants": int(matrix.shape[0]), "study_days": int(matrix.shape[1])}


def _trend_panel(ax, daily: pd.DataFrame, role_id: str, title: str, unit: str) -> None:
    column = _role_column(daily, role_id, entity="daily_vitals")
    if column is None:
        render_warning_panel(ax, title, f"Unavailable: {role_id} not present.")
        return
    style_card(ax, title)
    grouped = daily.groupby("__study_day")[column].mean()
    ax.plot(grouped.index, grouped.values, marker="o", color=DEFAULT_STYLE.palette[1])
    ax.set_xlabel("Study day")
    ax.set_ylabel(unit)


def _scale_adherence_panel(ax, daily: pd.DataFrame) -> None:
    column = _role_column(daily, "vital.scale_used", entity="daily_vitals")
    if column is None:
        render_warning_panel(ax, "Scale Adherence", "Unavailable: vital.scale_used not present.")
        return
    parsed = parse_domain_boolean_series(daily[column], DomainBooleanParsePolicy(role="vital.scale_used", required=False), source_column=column)
    local = daily.assign(__scale=parsed.true_mask.astype(float))
    grouped = local.groupby("__study_day")["__scale"].mean()
    style_card(ax, "Scale Adherence")
    ax.plot(grouped.index, grouped.values, marker="o", color=DEFAULT_STYLE.palette[2])
    ax.set_ylim(0, 1)
    ax.set_xlabel("Study day")
    ax.set_ylabel("Share")


def _adherence_decline_panel(ax, daily: pd.DataFrame) -> None:
    style_card(ax, "Adherence Decline Summary")
    ax.set_xticks([])
    ax.set_yticks([])
    wear_col = _role_column(daily, "vital.sensor_wear_hours", entity="daily_vitals")
    scale_col = _role_column(daily, "vital.scale_used", entity="daily_vitals")
    max_day = float(daily["__study_day"].max()) if not daily.empty else 0
    split = max_day / 2 if max_day else 0
    text = []
    if wear_col:
        first = pd.to_numeric(daily.loc[daily["__study_day"] <= split, wear_col], errors="coerce").mean()
        second = pd.to_numeric(daily.loc[daily["__study_day"] > split, wear_col], errors="coerce").mean()
        text.append(f"Wear hours: first half {first:.1f}, second half {second:.1f}, change {second - first:+.1f}")
    if scale_col:
        parsed = parse_domain_boolean_series(daily[scale_col], DomainBooleanParsePolicy(role="vital.scale_used", required=False), source_column=scale_col)
        local = daily.assign(__scale=parsed.true_mask.astype(float))
        first = local.loc[local["__study_day"] <= split, "__scale"].mean()
        second = local.loc[local["__study_day"] > split, "__scale"].mean()
        text.append(f"Scale use: first half {first:.0%}, second half {second:.0%}, change {second - first:+.0%}")
    ax.text(0.04, 0.80, "\n".join(text) if text else "Adherence components unavailable.", transform=ax.transAxes, ha="left", va="top", fontsize=10, wrap=True)


def _missingness_by_variable_panel(ax, daily: pd.DataFrame) -> None:
    roles = _available_vital_roles(daily)
    data: dict[str, float] = {}
    for role in roles:
        column = _role_column(daily, role, entity="daily_vitals")
        if column:
            data[registry.get_role(role).label] = float(daily[column].isna().mean())
    if not data:
        render_warning_panel(ax, "Missingness by Variable", "No vital variables available.")
        return
    series = pd.Series(data).sort_values()
    style_card(ax, "Missingness by Variable")
    bars = ax.barh(range(len(series)), series.values, color=DEFAULT_STYLE.palette[3])
    ax.set_yticks(range(len(series)), series.index, fontsize=7)
    ax.set_xlim(0, 1)
    for bar, value in zip(bars, series.values, strict=False):
        ax.text(bar.get_width(), bar.get_y() + bar.get_height() / 2, f" {value:.0%}", va="center", fontsize=7)


def _gap_cluster_summary(tables: LongitudinalEDATables) -> tuple[dict[str, Any], list[str]]:
    daily = _with_study_day(tables.daily_vitals)
    matrix, _meta = _missingness_matrix(daily)
    if matrix.empty:
        return {}, ["gap clustering unavailable: no participant-day matrix"]
    total_missing = int((matrix == 0).sum().sum())
    max_day = int(max(matrix.columns)) if len(matrix.columns) else 0
    late_missing = int((matrix.loc[:, [col for col in matrix.columns if col > max_day * 0.67]] == 0).sum().sum()) if max_day else 0
    hot_days: set[int] = set()
    overlay = _environment_overlay_series(tables, daily)
    if not overlay.empty:
        threshold = float(overlay["value"].quantile(0.75))
        hot_days = set(overlay.loc[overlay["value"] >= threshold, "study_day"].astype(int))
    hot_missing = int((matrix.loc[:, [col for col in matrix.columns if int(col) in hot_days]] == 0).sum().sum()) if hot_days else 0
    summary = {
        "late_study_decline": late_missing,
        "hot_afternoon": hot_missing,
        "overnight": "unavailable",
        "feeding_morning": "unavailable",
        "total_missing_participant_days": total_missing,
    }
    warnings = ["overnight gap clustering unavailable: no overnight timestamp proxy", "feeding/morning gap clustering unavailable: no feeding/morning timestamp proxy"]
    if not hot_days:
        warnings.append("hot afternoon gap clustering unavailable: no heat exposure proxy")
    return summary, warnings


def _gap_summary_panel(ax, summary: dict[str, Any]) -> None:
    style_card(ax, "Gap Clustering Summary")
    ax.set_xticks([])
    ax.set_yticks([])
    if not summary:
        ax.text(0.04, 0.70, "Gap clustering unavailable.", transform=ax.transAxes, fontsize=11, color=DEFAULT_STYLE.warning_color)
        return
    text = "\n".join(f"{key.replace('_', ' ').title()}: {value}" for key, value in summary.items())
    ax.text(0.04, 0.86, text, transform=ax.transAxes, ha="left", va="top", fontsize=10)
    ax.text(0.04, 0.12, "Unsupported clusters are labeled unavailable and recorded as manifest warnings rather than guessed.", transform=ax.transAxes, fontsize=8, color=DEFAULT_STYLE.muted_text_color)


def _component_panel(ax, scores: pd.DataFrame, component: str, title: str) -> None:
    if component not in scores:
        render_warning_panel(ax, title, "Component unavailable; weight redistributed.")
        return
    style_card(ax, title)
    values = scores[component].dropna()
    ax.hist(values, bins=8, color=DEFAULT_STYLE.palette[4], alpha=0.82)
    ax.set_xlim(0, 1)
    ax.set_xlabel("Component score")
    ax.set_ylabel("Participants")


def _gap_score_panel(ax, scores: pd.DataFrame) -> None:
    style_card(ax, "Signal Hours and Gaps")
    if scores.empty:
        ax.text(0.04, 0.70, "No score rows available.", transform=ax.transAxes)
        return
    top = scores.head(8)
    ax.scatter(top["valid_signal_hours"], top["gap_duration_days"], s=70, color=DEFAULT_STYLE.palette[5])
    for _, row in top.iterrows():
        ax.text(row["valid_signal_hours"], row["gap_duration_days"], f" {row['participant_id']}", fontsize=7)
    ax.set_xlabel("Valid-signal hours")
    ax.set_ylabel("Gap duration days")


def _expected_days_by_participant(daily: pd.DataFrame) -> dict[str, int]:
    participant_col = _role_column(daily, "vital.participant_id", entity="daily_vitals") or "participant_id"
    expected: dict[str, int] = {}
    for participant_id, group in daily.groupby(participant_col):
        days = pd.to_numeric(group["__study_day"], errors="coerce").dropna()
        expected[str(participant_id)] = int(days.max() - days.min() + 1) if not days.empty else 0
    return expected


def _valid_signal_hours(daily: pd.DataFrame) -> dict[str, float]:
    participant_col = _role_column(daily, "vital.participant_id", entity="daily_vitals") or "participant_id"
    wear_col = _role_column(daily, "vital.sensor_wear_hours", entity="daily_vitals")
    if wear_col is None or participant_col not in daily:
        return {}
    return pd.to_numeric(daily[wear_col], errors="coerce").groupby(daily[participant_col].astype(str)).sum().to_dict()


def _gap_stats(daily: pd.DataFrame) -> dict[str, dict[str, int]]:
    matrix, _meta = _missingness_matrix(daily)
    stats: dict[str, dict[str, int]] = {}
    for participant_id, row in matrix.iterrows():
        missing = row.eq(0).astype(int).tolist()
        runs = 0
        duration = 0
        in_run = False
        for value in missing:
            if value:
                duration += 1
                if not in_run:
                    runs += 1
                    in_run = True
            else:
                in_run = False
        stats[str(participant_id)] = {"gap_count": runs, "gap_duration_days": duration}
    return stats


def _missingness_rate_by_day(daily: pd.DataFrame) -> pd.DataFrame:
    vital_cols = [col for col in (_role_column(daily, role, entity="daily_vitals") for role in _available_vital_roles(daily)) if col]
    if not vital_cols:
        return pd.DataFrame({"study_day": [], "missingness_rate": []})
    local = daily.assign(__missing=daily[vital_cols].isna().any(axis=1))
    return local.groupby("__study_day")["__missing"].mean().reset_index().rename(columns={"__study_day": "study_day", "__missing": "missingness_rate"})


def _line_rate_panel(ax, rates: pd.DataFrame, title: str) -> None:
    style_card(ax, title)
    if rates.empty:
        ax.text(0.04, 0.70, "Unavailable.", transform=ax.transAxes, color=DEFAULT_STYLE.warning_color)
        return
    ax.plot(rates["study_day"], rates["missingness_rate"], marker="o", color=DEFAULT_STYLE.palette[0])
    ax.set_ylim(0, 1)
    ax.set_xlabel("Study day")
    ax.set_ylabel("Missingness rate")


def _context_missingness_rates(tables: LongitudinalEDATables) -> tuple[dict[str, list[dict[str, Any]]], list[str]]:
    daily = _with_study_day(tables.daily_vitals)
    participants = tables.participants.copy()
    participant_col = _role_column(daily, "vital.participant_id", entity="daily_vitals") or "participant_id"
    vital_cols = [col for col in (_role_column(daily, role, entity="daily_vitals") for role in _available_vital_roles(daily)) if col]
    if not vital_cols:
        return {}, ["context missingness unavailable: no vital roles"]
    daily = daily.assign(__missing=daily[vital_cols].isna().any(axis=1))
    rates: dict[str, list[dict[str, Any]]] = {}
    warnings: list[str] = []
    for label, candidates in {
        "archetype": ("archetype", "risk_archetype"),
        "AC access": ("has_ac",),
        "insurance": ("insurance", "payer"),
        "PIH severity": ("pih_severity",),
        "health literacy": ("bhls_health_literacy", "health_literacy"),
    }.items():
        column = next((col for col in candidates if col in participants.columns), None)
        if column is None and label == "archetype":
            column = next((col for col in candidates if col in daily.columns), None)
        if column is None:
            warnings.append(f"{label} stratifier unavailable")
            continue
        if column in participants.columns:
            stratifiers = participants[["participant_id", column]].rename(columns={column: "__stratifier"})
            merged = daily.merge(stratifiers, left_on=participant_col, right_on="participant_id", how="left")
            group_column = "__stratifier"
        else:
            merged = daily
            group_column = column
        grouped = merged.groupby(group_column)["__missing"].mean().dropna()
        rates[label] = [{"group": str(group), "missingness_rate": float(value)} for group, value in grouped.items()]
    return rates, warnings


def _heat_missingness_rates(tables: LongitudinalEDATables) -> tuple[dict[str, list[dict[str, Any]]], list[str]]:
    daily = _with_study_day(tables.daily_vitals)
    vital_cols = [col for col in (_role_column(daily, role, entity="daily_vitals") for role in _available_vital_roles(daily)) if col]
    if not vital_cols:
        return {}, ["heat missingness unavailable: no vital roles"]
    daily = daily.assign(__missing=daily[vital_cols].isna().any(axis=1))
    heat_col = "heat_exposure_level" if "heat_exposure_level" in daily else None
    if heat_col is None:
        overlay = _environment_overlay_series(tables, daily)
        if overlay.empty:
            return {}, ["heat exposure diagnostic unavailable: environment not available"]
        threshold = overlay["value"].median()
        heat_map = overlay.assign(heat_group=np.where(overlay["value"] >= threshold, "higher heat", "lower heat")).set_index("study_day")["heat_group"]
        daily["heat_group"] = daily["__study_day"].map(heat_map)
        heat_col = "heat_group"
    grouped = daily.groupby(heat_col)["__missing"].mean().dropna()
    return {"heat exposure": [{"group": str(group), "missingness_rate": float(value)} for group, value in grouped.items()]}, []


def _recent_abnormal_vital_missingness(daily: pd.DataFrame) -> dict[str, list[dict[str, Any]]]:
    vital_roles = _available_vital_roles(daily)
    if not vital_roles:
        return {}
    participant_col = _role_column(daily, "vital.participant_id", entity="daily_vitals") or "participant_id"
    local = daily.sort_values([participant_col, "__study_day"]).copy()
    abnormal = pd.Series(False, index=local.index)
    missing = pd.Series(False, index=local.index)
    for role_id in vital_roles:
        column = _role_column(local, role_id, entity="daily_vitals")
        role = registry.get_role(role_id)
        if column is None or role.capture_worthy_range is None:
            continue
        values = pd.to_numeric(local[column], errors="coerce")
        low, high = role.capture_worthy_range
        abnormal |= (low is not None and values < low) | (high is not None and values > high)
        missing |= values.isna()
    local["recent_abnormal"] = abnormal.groupby(local[participant_col]).shift(1).fillna(False).eq(True)
    local["__missing"] = missing
    grouped = local.groupby("recent_abnormal")["__missing"].mean()
    return {
        "recent abnormal vitals": [
            {"group": "after recent abnormal vitals" if bool(group) else "no recent abnormal vitals", "missingness_rate": float(value)}
            for group, value in grouped.items()
        ]
    }


def _context_rates_panel(ax, rates: dict[str, list[dict[str, Any]]], title: str = "Missingness by Participant Context") -> None:
    style_card(ax, title)
    ax.set_xlim(0, 1)
    if not rates:
        ax.text(0.04, 0.70, "Unavailable stratifiers.", transform=ax.transAxes, color=DEFAULT_STYLE.warning_color)
        return
    rows = []
    for category, values in rates.items():
        for value in values:
            rows.append((f"{category}: {value['group']}", value["missingness_rate"]))
    rows = rows[:8]
    bars = ax.barh(range(len(rows)), [value for _, value in rows], color=DEFAULT_STYLE.palette[2])
    ax.set_yticks(range(len(rows)), [_wrap(label, 28) for label, _ in rows], fontsize=7)
    ax.invert_yaxis()
    for bar, (_label, value) in zip(bars, rows, strict=False):
        ax.text(bar.get_width(), bar.get_y() + bar.get_height() / 2, f" {value:.0%}", va="center", fontsize=7)


def _register_results(results: list[LongitudinalPanelResult], manifest_path: str | Path, tables: LongitudinalEDATables, out_dir: Path) -> None:
    import os
    if not _is_repo_relative(out_dir):
        if os.environ.get("LULLABY_TEST_MODE") == "1":
            return
        py_warnings.warn(
            f"Generated artifacts under {out_dir} are outside the repository and were not registered in {manifest_path}",
            RuntimeWarning,
            stacklevel=2,
        )
        return
    for result in results:
        artifact = FigureArtifact(
            artifact_id=_artifact_id(result.artifact_id, out_dir),
            path=_repo_relative(result.path),
            title=result.title,
            spec=SPEC_ID,
            inputs=_inputs_for_result(result.artifact_id),
            required_roles=PANEL_REQUIRED_ROLES[result.artifact_id],
            optional_roles_used=_optional_roles_for_result(result.artifact_id),
            warnings=result.warnings,
            metadata=_jsonable(result.metadata),
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
    if "05" in artifact_id:
        return ["daily_vitals", "participants", "alerts", "clinical_outcomes", "environment"]
    if "06" in artifact_id:
        return ["daily_vitals", "staff_contacts", "alerts"]
    if "07" in artifact_id:
        return ["participants", "daily_vitals", "alerts", "staff_contacts", "clinical_outcomes", "environment"]
    if "08" in artifact_id:
        return ["daily_vitals", "staff_contacts"]
    return ["participants", "daily_vitals", "environment", "clinical_outcomes"]


def _optional_roles_for_result(artifact_id: str) -> list[str]:
    if "05" in artifact_id:
        return _vital_roles() + ["environment.ambient_temp_c", "environment.heat_index_c"]
    if "06" in artifact_id:
        return ["vital.sensor_wear_hours", "vital.scale_used", "alert.hour"]
    if "07" in artifact_id:
        return _vital_roles() + ["participant.insurance", "participant.parity", "participant.health_literacy", "participant.social_support", "participant.depression", "participant.anxiety"]
    if "08" in artifact_id:
        return ["vital.sensor_wear_hours", "vital.scale_used", "contact.completed"]
    return ["participant.archetype", "participant.insurance", "participant.pih_severity", "participant.has_ac", "participant.health_literacy", "environment.heat_exposure_level"]


def _is_repo_relative(path: Path) -> bool:
    return not Path(_repo_relative(path)).is_absolute()


def _repo_relative(path: Path) -> str:
    try:
        return Path(path).resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return Path(path).as_posix()


def _wrap(label: str, width: int) -> str:
    words = str(label).split()
    lines: list[str] = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 > width and current:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    if current:
        lines.append(current)
    return "\n".join(lines) if lines else str(label)


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        if np.isnan(value):
            return None
        return float(value)
    if pd.isna(value) and not isinstance(value, (str, bytes)):
        return None
    return value


__all__ = [
    "LONGITUDINAL_PANEL_FILENAMES",
    "LongitudinalEDATables",
    "LongitudinalInputError",
    "LongitudinalPanelResult",
    "LongitudinalRunConfig",
    "SelectedParticipantContext",
    "calculate_quality_scores",
    "generate_longitudinal_dashboards",
    "load_longitudinal_tables",
    "prepare_selected_vital_series",
    "render_data_quality_scorecard",
    "render_missingness_adherence",
    "render_missingness_mechanism",
    "render_vital_trajectories",
    "select_default_participant",
]
