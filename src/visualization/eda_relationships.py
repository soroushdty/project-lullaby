from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import textwrap
import warnings as py_warnings

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

from src.validation.semantics import DomainBooleanParsePolicy, ParsedBooleanSeries, parse_domain_boolean_series
from src.visualization import schema_registry as registry
from src.visualization.artifacts import FigureArtifact, FigureArtifactManifest, create_empty_manifest, write_manifest
from src.visualization.design import DEFAULT_STYLE, add_dashboard_title, configure_style, render_warning_panel, save_figure, style_card
from src.visualization.validation import validate_entity


SPEC_ID = "SPEC-010"
RELATIONSHIP_PANEL_FILENAMES = {
    "relationships": "10_relationships.png",
    "heat_environment": "11_heat_environment.png",
    "archetype_explorer": "12_archetype_explorer.png",
    "recruitment_timeline": "13_recruitment_timeline.png",
}
RELATIONSHIP_ARTIFACT_IDS = {
    "relationships": "eda_relationships_10_relationships",
    "heat_environment": "eda_relationships_11_heat_environment",
    "archetype_explorer": "eda_relationships_12_archetype_explorer",
    "recruitment_timeline": "eda_relationships_13_recruitment_timeline",
}
RELATIONSHIP_REQUIRED_ROLES: dict[str, tuple[str, ...]] = {
    "participants": ("participant.id",),
    "daily_vitals": ("vital.participant_id", "vital.date", "vital.systolic_bp"),
}
PANEL_REQUIRED_ROLES: dict[str, list[str]] = {
    RELATIONSHIP_ARTIFACT_IDS["relationships"]: ["vital.participant_id", "vital.date", "vital.systolic_bp"],
    RELATIONSHIP_ARTIFACT_IDS["heat_environment"]: [
        "environment.date",
        "environment.ambient_temp_c",
        "environment.heat_index_c",
        "participant.id",
        "vital.participant_id",
        "vital.date",
    ],
    RELATIONSHIP_ARTIFACT_IDS["archetype_explorer"]: ["participant.id", "vital.participant_id", "vital.date"],
    RELATIONSHIP_ARTIFACT_IDS["recruitment_timeline"]: ["participant.id"],
}


@dataclass(frozen=True)
class RelationshipEDATables:
    data_dir: Path
    resolved_data_dir: Path
    participants: pd.DataFrame
    daily_vitals: pd.DataFrame
    clinical_outcomes: pd.DataFrame
    environment: pd.DataFrame
    recruitment: pd.DataFrame
    alerts: pd.DataFrame
    load_warnings: dict[str, list[str]] = field(default_factory=dict)


@dataclass(frozen=True)
class RelationshipPanelResult:
    artifact_id: str
    path: Path
    title: str
    warnings: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)


class RelationshipInputError(RuntimeError):
    pass


def generate_relationship_dashboards(
    data_dir: str | Path,
    out_dir: str | Path = Path("outputs/figures/eda"),
    *,
    manifest_path: str | Path = Path("outputs/figures/manifest.json"),
) -> list[RelationshipPanelResult]:
    tables = load_relationship_tables(data_dir, required_roles=RELATIONSHIP_REQUIRED_ROLES)
    output_dir = Path(out_dir)

    from src.visualization.eda_archetypes import render_archetype_explorer, render_recruitment_timeline
    from src.visualization.eda_environment import render_heat_environment

    results = [
        render_relationships_dashboard(tables, output_dir),
        render_heat_environment(tables, output_dir),
        render_archetype_explorer(tables, output_dir),
        render_recruitment_timeline(tables, output_dir),
    ]
    output_dir.mkdir(parents=True, exist_ok=True)
    _register_results(results, manifest_path, tables, output_dir)
    return results


def load_relationship_tables(
    data_dir: str | Path,
    *,
    required_roles: dict[str, tuple[str, ...]] | None = None,
) -> RelationshipEDATables:
    required_roles = required_roles or {}
    requested = Path(data_dir)
    resolved = _resolve_data_dir(requested)
    frames: dict[str, pd.DataFrame] = {}
    load_warnings: dict[str, list[str]] = {}
    errors: list[str] = []
    for entity in ("participants", "daily_vitals", "clinical_outcomes", "environment", "recruitment", "alerts"):
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
        role_result = registry.require_roles(frame, list(roles), entity=entity)
        errors.extend(f"{entity}: {_entity_source_path(resolved, entity)}: {message}" for message in role_result.errors)
        errors.extend(_required_boolean_errors(entity, frame, role_result.resolved_roles, resolved))

    if errors:
        joined = "\n".join(f"- {error}" for error in errors)
        raise RelationshipInputError(f"Required SPEC-010 EDA input validation failed before artifact generation:\n{joined}")

    return RelationshipEDATables(
        data_dir=requested,
        resolved_data_dir=resolved,
        participants=frames["participants"],
        daily_vitals=_with_study_day(frames["daily_vitals"], frames["participants"]),
        clinical_outcomes=frames["clinical_outcomes"],
        environment=frames["environment"],
        recruitment=frames["recruitment"],
        alerts=frames["alerts"],
        load_warnings=load_warnings,
    )


def render_relationships_dashboard(tables: RelationshipEDATables, out_dir: Path) -> RelationshipPanelResult:
    configure_style()
    fig = plt.figure(figsize=(16, 9), constrained_layout=False)
    add_dashboard_title(
        fig,
        "Relationships and Descriptive Discriminators",
        f"{_subtitle(tables, [tables.daily_vitals, tables.environment])} | observed pairs only; descriptive correlations, not causality",
    )
    gs = fig.add_gridspec(3, 4, left=0.04, right=0.98, top=0.88, bottom=0.07, wspace=0.35, hspace=0.55)
    warnings: list[str] = []
    metadata: dict[str, Any] = {
        "observed_data_policy": "Observed pairs only; pairwise complete observations are used with no imputation or causal interpretation.",
        "pairwise_n": {},
        "heat_source": "unavailable",
        "discriminator_counts": {},
    }

    corr_meta, corr_warnings = _correlation_heatmap(fig.add_subplot(gs[0:2, 0:2]), tables.daily_vitals)
    warnings.extend(corr_warnings)
    metadata["pairwise_n"]["correlation_heatmap"] = corr_meta

    for ax, role_id, title, key in [
        (fig.add_subplot(gs[0, 2]), "vital.systolic_bp", "Body-Water Direction vs Systolic BP", "body_water_vs_sbp"),
        (fig.add_subplot(gs[0, 3]), "vital.heart_rate", "Body-Water Direction vs Heart Rate", "body_water_vs_hr"),
        (fig.add_subplot(gs[1, 2]), "vital.skin_temperature_c", "Body-Water Direction vs Skin Temperature", "body_water_vs_skin_temp"),
    ]:
        pair_meta, pair_warnings = _body_water_direction_panel(ax, tables.daily_vitals, role_id, title)
        warnings.extend(pair_warnings)
        metadata["pairwise_n"][key] = pair_meta

    heat_meta, heat_warnings = _heat_bivariate_panel(fig.add_subplot(gs[1, 3]), tables)
    warnings.extend(heat_warnings)
    metadata["pairwise_n"]["heat_index_bivariates"] = heat_meta.get("pairwise_n", {})
    metadata["heat_source"] = heat_meta.get("source", "unavailable")

    discriminator_counts, discriminator_warnings = _discriminator_summary_panel(fig.add_subplot(gs[2, :]), tables.daily_vitals)
    warnings.extend(discriminator_warnings)
    metadata["discriminator_counts"] = discriminator_counts

    path = out_dir / RELATIONSHIP_PANEL_FILENAMES["relationships"]
    save_figure(fig, path)
    plt.close(fig)
    return RelationshipPanelResult(
        RELATIONSHIP_ARTIFACT_IDS["relationships"],
        path,
        "Relationships and Descriptive Discriminators",
        warnings,
        metadata,
    )


def _correlation_heatmap(ax, daily: pd.DataFrame) -> tuple[dict[str, dict[str, int]], list[str]]:
    columns: list[str] = []
    labels: list[str] = []
    warnings: list[str] = []
    for role_id in _vital_roles():
        column = _role_column(daily, role_id, entity="daily_vitals")
        if column is None:
            continue
        role = registry.get_role(role_id)
        columns.append(column)
        labels.append(_role_label(role_id, include_unit=False))
    if len(columns) < 2:
        render_warning_panel(ax, "Descriptive Correlation Heatmap", "Unavailable: at least two numeric vital variables are required.")
        return {}, ["correlation heatmap unavailable: fewer than two numeric vital variables"]

    values = daily[columns].apply(pd.to_numeric, errors="coerce")
    corr = values.corr(min_periods=2)
    observed = values.notna().astype(int)
    pair_counts = observed.T.dot(observed)
    metadata = {
        labels[i]: {labels[j]: int(pair_counts.iloc[i, j]) for j in range(len(labels))}
        for i in range(len(labels))
    }

    style_card(ax, "Descriptive Pairwise Correlations")
    image = ax.imshow(corr.to_numpy(dtype=float), cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(range(len(labels)), [_wrap(label, 12) for label in labels], rotation=45, ha="right", fontsize=7)
    ax.set_yticks(range(len(labels)), [_wrap(label, 14) for label in labels], fontsize=7)
    for i in range(len(labels)):
        for j in range(len(labels)):
            value = corr.iloc[i, j]
            n = int(pair_counts.iloc[i, j])
            text = "NA" if pd.isna(value) else f"{value:.2f}"
            ax.text(j, i, f"{text}\nN={n}", ha="center", va="center", fontsize=5.8, color=DEFAULT_STYLE.text_color)
    cbar = ax.figure.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    cbar.ax.tick_params(labelsize=7)
    cbar.set_label("Pearson r", fontsize=8)
    ax.text(0.01, -0.18, "Each cell uses observed pairs only; correlations are descriptive.", transform=ax.transAxes, fontsize=8, color=DEFAULT_STYLE.muted_text_color)
    return metadata, warnings


def _body_water_direction_panel(ax, daily: pd.DataFrame, y_role: str, title: str) -> tuple[dict[str, Any], list[str]]:
    role = registry.get_role(y_role)
    direction = _direction_frame(daily, "vital.body_water_pct", y_role)
    if direction.empty:
        render_warning_panel(ax, title, f"Unavailable: observed body-water and {role.label} changes are required.")
        return {"observed_pairs": 0}, [f"{title} unavailable: observed pair N=0"]
    style_card(ax, f"{title} ({role.unit or 'unitless'})")
    x = direction["x_delta"]
    y = direction["y_delta"]
    colors = np.where((x.gt(0)) & (y.gt(0)), DEFAULT_STYLE.warning_color, DEFAULT_STYLE.palette[0])
    ax.scatter(x, y, s=28, alpha=0.62, c=colors, edgecolors="none")
    ax.axvline(0, color=DEFAULT_STYLE.grid_color, linewidth=1)
    ax.axhline(0, color=DEFAULT_STYLE.grid_color, linewidth=1)
    ax.set_xlabel("Body water change (percentage points)")
    ax.set_ylabel(f"{role.label} change ({role.unit or 'unitless'})")
    corr = float(x.corr(y)) if len(direction) >= 2 and x.nunique(dropna=True) > 1 and y.nunique(dropna=True) > 1 else np.nan
    corr_text = "NA" if pd.isna(corr) else f"{corr:.2f}"
    ax.text(
        0.03,
        0.95,
        f"Observed pairs N={len(direction):,}\nDescriptive r={corr_text}",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8,
        color=DEFAULT_STYLE.muted_text_color,
    )
    return {"observed_pairs": int(len(direction)), "descriptive_r": None if pd.isna(corr) else corr}, []


def _heat_bivariate_panel(ax, tables: RelationshipEDATables) -> tuple[dict[str, Any], list[str]]:
    joined, source, source_warning = _daily_with_heat_index(tables)
    warnings = [source_warning] if source_warning else []
    hr_col = _role_column(joined, "vital.heart_rate", entity="daily_vitals") if not joined.empty else None
    temp_col = _role_column(joined, "vital.skin_temperature_c", entity="daily_vitals") if not joined.empty else None
    if joined.empty or "heat_index_c" not in joined or (hr_col is None and temp_col is None):
        render_warning_panel(ax, "Heat Index vs HR / Skin Temp", "Unavailable: environment heat index and HR or skin temperature are required.")
        warnings.append("heat-index bivariate views unavailable")
        return {"source": source, "pairwise_n": {"heart_rate": 0, "skin_temperature_c": 0}}, warnings
    style_card(ax, "Heat Index vs HR / Skin Temp")
    heat = pd.to_numeric(joined["heat_index_c"], errors="coerce")
    pairwise: dict[str, int] = {}
    if hr_col:
        hr = pd.to_numeric(joined[hr_col], errors="coerce")
        mask = heat.notna() & hr.notna()
        ax.scatter(heat[mask], hr[mask], s=28, marker="o", alpha=0.62, color=DEFAULT_STYLE.palette[1], label="Heart rate")
        pairwise["heart_rate"] = int(mask.sum())
    else:
        pairwise["heart_rate"] = 0
    if temp_col:
        temp = pd.to_numeric(joined[temp_col], errors="coerce")
        mask = heat.notna() & temp.notna()
        temp_scaled = temp[mask] * 3.0
        ax.scatter(heat[mask], temp_scaled, s=32, marker="^", alpha=0.62, color=DEFAULT_STYLE.palette[2], label="Skin temp x3")
        pairwise["skin_temperature_c"] = int(mask.sum())
    else:
        pairwise["skin_temperature_c"] = 0
    ax.set_xlabel("Heat index (C)")
    ax.set_ylabel("Heart rate (bpm) / skin temp x3")
    ax.legend(loc="upper left", fontsize=7)
    ax.text(
        0.03,
        0.05,
        f"Source: {source}\nObserved N HR={pairwise['heart_rate']:,}; skin temp={pairwise['skin_temperature_c']:,}",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=7,
        color=DEFAULT_STYLE.muted_text_color,
    )
    return {"source": source, "pairwise_n": pairwise}, warnings


def _discriminator_summary_panel(ax, daily: pd.DataFrame) -> tuple[dict[str, int], list[str]]:
    style_card(ax, "CV-vs-Heat Descriptive Discriminator")
    ax.set_xticks([])
    ax.set_yticks([])
    warnings: list[str] = []
    cv_frame = _multi_direction_frame(daily, ["vital.body_water_pct", "vital.systolic_bp", "vital.heart_rate"])
    heat_frame = _multi_direction_frame(daily, ["vital.body_water_pct", "vital.heart_rate", "vital.skin_temperature_c"])
    cv_like = int(((cv_frame["vital.body_water_pct"] > 0) & (cv_frame["vital.systolic_bp"] > 0) & (cv_frame["vital.heart_rate"] > 0)).sum()) if not cv_frame.empty else 0
    heat_like = int(((heat_frame["vital.body_water_pct"] < 0) & (heat_frame["vital.heart_rate"] > 0) & (heat_frame["vital.skin_temperature_c"] > 0)).sum()) if not heat_frame.empty else 0
    if cv_frame.empty:
        warnings.append("CV-risk discriminator unavailable: body water, systolic BP, and HR direction pairs required")
    if heat_frame.empty:
        warnings.append("heat-strain discriminator unavailable: body water, HR, and skin-temperature direction pairs required")

    ax.text(0.03, 0.73, "Body water rising + BP and HR rising", transform=ax.transAxes, fontsize=13, fontweight="bold", color=DEFAULT_STYLE.warning_color)
    ax.text(0.03, 0.55, f"{cv_like:,} observed intervals match this CV-risk-like descriptive trajectory.", transform=ax.transAxes, fontsize=10)
    ax.text(0.52, 0.73, "Body water falling + HR and skin temp rising", transform=ax.transAxes, fontsize=13, fontweight="bold", color=DEFAULT_STYLE.palette[1])
    ax.text(0.52, 0.55, f"{heat_like:,} observed intervals match this heat-strain-like descriptive trajectory.", transform=ax.transAxes, fontsize=10)
    ax.text(
        0.03,
        0.24,
        "These are descriptive discriminators for EDA review. They do not prove mechanism, estimate risk, or imply that heat causes vital changes.",
        transform=ax.transAxes,
        fontsize=10,
        color=DEFAULT_STYLE.muted_text_color,
        wrap=True,
    )
    return {
        "cv_risk_like_intervals": cv_like,
        "heat_strain_like_intervals": heat_like,
        "cv_risk_observed_intervals": int(len(cv_frame)),
        "heat_strain_observed_intervals": int(len(heat_frame)),
    }, warnings


def _direction_frame(daily: pd.DataFrame, x_role: str, y_role: str) -> pd.DataFrame:
    x_col = _role_column(daily, x_role, entity="daily_vitals")
    y_col = _role_column(daily, y_role, entity="daily_vitals")
    participant_col = _role_column(daily, "vital.participant_id", entity="daily_vitals") or "participant_id"
    if daily.empty or x_col is None or y_col is None or participant_col not in daily:
        return pd.DataFrame()
    local = _with_sort_key(daily)
    local[x_col] = pd.to_numeric(local[x_col], errors="coerce")
    local[y_col] = pd.to_numeric(local[y_col], errors="coerce")
    local["x_delta"] = local.groupby(participant_col, sort=False)[x_col].diff()
    local["y_delta"] = local.groupby(participant_col, sort=False)[y_col].diff()
    return local.loc[local["x_delta"].notna() & local["y_delta"].notna(), [participant_col, "x_delta", "y_delta"]].copy()


def _multi_direction_frame(daily: pd.DataFrame, roles: list[str]) -> pd.DataFrame:
    participant_col = _role_column(daily, "vital.participant_id", entity="daily_vitals") or "participant_id"
    columns = {role_id: _role_column(daily, role_id, entity="daily_vitals") for role_id in roles}
    if daily.empty or participant_col not in daily or any(column is None for column in columns.values()):
        return pd.DataFrame()
    local = _with_sort_key(daily)
    result = pd.DataFrame(index=local.index)
    for role_id, column in columns.items():
        assert column is not None
        values = pd.to_numeric(local[column], errors="coerce")
        result[role_id] = values.groupby(local[participant_col], sort=False).diff()
    return result.dropna(how="any")


def _daily_with_heat_index(tables: RelationshipEDATables) -> tuple[pd.DataFrame, str, str]:
    daily = tables.daily_vitals.copy()
    if daily.empty:
        return pd.DataFrame(), "unavailable", ""
    heat_col = _role_column(tables.environment, "environment.heat_index_c", entity="environment")
    env_date_col = _role_column(tables.environment, "environment.date", entity="environment")
    env_day_col = _role_column(tables.environment, "environment.study_day", entity="environment")
    daily_date_col = _role_column(daily, "vital.date", entity="daily_vitals")
    daily_day_col = _role_column(daily, "vital.study_day", entity="daily_vitals")
    if heat_col and not tables.environment.empty:
        env = tables.environment.copy()
        env["heat_index_c"] = pd.to_numeric(env[heat_col], errors="coerce")
        if env_date_col and daily_date_col:
            env["__date"] = pd.to_datetime(env[env_date_col], errors="coerce").dt.normalize()
            daily["__date"] = pd.to_datetime(daily[daily_date_col], errors="coerce").dt.normalize()
            merged = daily.merge(env[["__date", "heat_index_c"]].dropna(subset=["__date"]), on="__date", how="left", suffixes=("", "__environment"))
            if "heat_index_c__environment" in merged:
                merged["heat_index_c"] = merged["heat_index_c__environment"]
            return merged, "environment table", ""
        if env_day_col and daily_day_col:
            env["__study_day"] = pd.to_numeric(env[env_day_col], errors="coerce")
            daily["__study_day_key"] = pd.to_numeric(daily[daily_day_col], errors="coerce")
            merged = daily.merge(env[["__study_day", "heat_index_c"]], left_on="__study_day_key", right_on="__study_day", how="left", suffixes=("", "__environment"))
            if "heat_index_c__environment" in merged:
                merged["heat_index_c"] = merged["heat_index_c__environment"]
            return merged, "environment table", ""
    daily_heat_col = _role_column(daily, "vital.heat_index_c", entity="daily_vitals")
    if daily_heat_col:
        daily["heat_index_c"] = pd.to_numeric(daily[daily_heat_col], errors="coerce")
        return daily, "daily_vitals heat_index_c proxy", "environment table unavailable; heat-index bivariate uses observed daily_vitals heat_index_c proxy"
    return pd.DataFrame(), "unavailable", ""


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
    if participants is not None and not participants.empty and "observation_start_date" in participants.columns and participant_col in result:
        starts = pd.to_datetime(participants.set_index("participant_id")["observation_start_date"], errors="coerce")
        result["__start"] = result[participant_col].astype(str).map(starts)
    elif participant_col in result:
        result["__start"] = parsed_dates.groupby(result[participant_col].astype(str)).transform("min")
    else:
        result["__start"] = parsed_dates.min()
    result["__study_day"] = (parsed_dates - result["__start"]).dt.days.add(1).astype("Int64")
    return result.drop(columns=["__start"])


def _with_sort_key(daily: pd.DataFrame) -> pd.DataFrame:
    result = _with_study_day(daily)
    participant_col = _role_column(result, "vital.participant_id", entity="daily_vitals") or "participant_id"
    date_col = _role_column(result, "vital.date", entity="daily_vitals")
    if date_col:
        result["__sort_date"] = pd.to_datetime(result[date_col], errors="coerce")
    else:
        result["__sort_date"] = pd.NaT
    sort_cols = [col for col in [participant_col, "__sort_date", "__study_day"] if col in result]
    return result.sort_values(sort_cols).copy()


def _subtitle(tables: RelationshipEDATables, frames: list[pd.DataFrame]) -> str:
    dates: list[pd.Timestamp] = []
    for frame in frames:
        if frame.empty:
            continue
        for column in ("date", "event_ts", "recruitment_date", "enrollment_date", "delivery_date", "observation_start_date", "cv_event_date"):
            if column in frame:
                dates.extend(pd.to_datetime(frame[column], errors="coerce").dropna().tolist())
    if dates:
        return f"Source: {tables.data_dir.as_posix()} | Date range: {min(dates).date().isoformat()} to {max(dates).date().isoformat()}"
    return f"Source: {tables.data_dir.as_posix()} | Date range unavailable"


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
        "vital.active_minutes",
    ]


def _role_label(role_id: str, *, include_unit: bool = True) -> str:
    role = registry.get_role(role_id)
    if include_unit and role.unit:
        return f"{role.label} ({role.unit})"
    return role.label


def _role_column(df: pd.DataFrame, role_id: str, *, entity: str) -> str | None:
    if df.empty:
        return None
    resolution = registry.resolve_column(df, role_id, entity=entity)
    return resolution.column if resolution.ok else None


def _boolean_series(frame: pd.DataFrame, role_id: str, *, required: bool = False) -> tuple[pd.Series, list[str]]:
    entity = registry.get_role(role_id).entity
    column = _role_column(frame, role_id, entity=entity)
    if frame.empty or column is None:
        return pd.Series(pd.NA, index=frame.index, dtype="boolean"), [f"{role_id} unavailable"]
    parsed = parse_domain_boolean_series(
        frame[column],
        DomainBooleanParsePolicy(role=role_id, required=required),
        source_column=column,
    )
    return parsed.as_nullable_boolean(), parsed.warnings


def _outcome_positive_by_participant(outcomes: pd.DataFrame) -> tuple[dict[str, bool], list[str]]:
    participant_col = _role_column(outcomes, "outcome.participant_id", entity="clinical_outcomes")
    if outcomes.empty or participant_col is None:
        return {}, ["clinical_outcomes unavailable"]
    warnings: list[str] = []
    signals: list[pd.Series] = []
    for role_id in ("outcome.cv_event", "outcome.ed_visit", "outcome.hospitalized"):
        column = _role_column(outcomes, role_id, entity="clinical_outcomes")
        if column is None:
            continue
        parsed = parse_domain_boolean_series(
            outcomes[column],
            DomainBooleanParsePolicy(role=role_id, required=False),
            source_column=column,
        )
        warnings.extend(parsed.warnings)
        signals.append(parsed.true_mask)
    heat_col = _role_column(outcomes, "outcome.heat_illness", entity="clinical_outcomes")
    if heat_col:
        heat_numeric = pd.to_numeric(outcomes[heat_col], errors="coerce")
        signals.append(heat_numeric.gt(0).fillna(False))
    if not signals:
        return {}, warnings + ["clinical outcome event fields unavailable"]
    positive = signals[0].copy()
    for signal in signals[1:]:
        positive |= signal
    event_positive = outcomes.assign(__event_positive=positive).groupby(participant_col)["__event_positive"].max()
    return event_positive.fillna(False).eq(True).to_dict(), warnings


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


def _required_boolean_errors(entity: str, frame: pd.DataFrame, resolved_roles: dict[str, str], data_dir: Path) -> list[str]:
    errors: list[str] = []
    for role_id, column in resolved_roles.items():
        role = registry.get_role(role_id)
        if role.value_type != "boolean":
            continue
        parsed = parse_domain_boolean_series(
            frame[column],
            DomainBooleanParsePolicy(role=role_id, required=True),
            source_column=column,
        )
        errors.extend(f"{entity}: {_entity_source_path(data_dir, entity)}: {message}" for message in parsed.errors)
    return errors


def _register_results(results: list[RelationshipPanelResult], manifest_path: str | Path, tables: RelationshipEDATables, out_dir: Path) -> None:
    if not _is_repo_relative(out_dir):
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
    if "10" in artifact_id:
        return ["daily_vitals", "participants", "environment", "clinical_outcomes"]
    if "11" in artifact_id:
        return ["environment", "daily_vitals", "participants"]
    if "12" in artifact_id:
        return ["participants", "daily_vitals", "clinical_outcomes", "alerts"]
    return ["participants", "recruitment", "environment", "daily_vitals"]


def _optional_roles_for_result(artifact_id: str) -> list[str]:
    if "10" in artifact_id:
        return _vital_roles() + ["vital.heat_index_c", "environment.heat_index_c"]
    if "11" in artifact_id:
        return ["environment.heat_wave", "environment.heat_exposure_level", "participant.has_ac", "vital.heart_rate", "vital.skin_temperature_c"]
    if "12" in artifact_id:
        return ["participant.archetype", "participant.has_ac", "participant.pih_severity", "outcome.cv_event", "alert.level", "vital.sensor_wear_hours", "vital.scale_used"]
    return ["participant.enrollment_date", "participant.delivery_date", "participant.observation_start_date", "recruitment.date", "environment.heat_wave", "environment.heat_exposure_level"]


def _is_repo_relative(path: Path) -> bool:
    return not Path(_repo_relative(path)).is_absolute()


def _repo_relative(path: Path) -> str:
    try:
        return Path(path).resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return Path(path).as_posix()


def _wrap(label: str, width: int) -> str:
    return "\n".join(textwrap.wrap(str(label), width=width, break_long_words=False)) or str(label)


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
    "RELATIONSHIP_ARTIFACT_IDS",
    "RELATIONSHIP_PANEL_FILENAMES",
    "RelationshipEDATables",
    "RelationshipInputError",
    "RelationshipPanelResult",
    "generate_relationship_dashboards",
    "load_relationship_tables",
    "render_relationships_dashboard",
]
