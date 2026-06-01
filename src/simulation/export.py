from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import json

import numpy as np
import pandas as pd
import yaml

from src.simulation.cohort import SimulationTables, generate_cohort_tables
from src.simulation.config import SimulationConfig, load_simulation_config
from src.simulation.physiology import simple_auc
from src.validation.semantics import DomainBooleanParsePolicy, ParsedBooleanSeries, parse_domain_boolean_series
from src.visualization.validation import ValidationResult, validate_data_dir


CSV_FILENAMES = {
    "participants": "participants.csv",
    "daily_vitals": "daily_vitals.csv",
    "alerts": "alerts.csv",
    "staff_contacts": "staff_contacts.csv",
    "clinical_outcomes": "clinical_outcomes.csv",
    "environment": "environment.csv",
    "recruitment": "recruitment.csv",
}


@dataclass(frozen=True)
class DiagnosticCheck:
    name: str
    required: bool
    target: float | str | bool | None
    observed: float | str | bool | None
    tolerance: float | None
    denominator: int
    status: str
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "required": self.required,
            "target": self.target,
            "observed": self.observed,
            "tolerance": self.tolerance,
            "denominator": self.denominator,
            "status": self.status,
            "details": self.details,
        }


@dataclass(frozen=True)
class SimulationRunResult:
    output_dir: Path
    config: SimulationConfig
    tables: SimulationTables
    validation: ValidationResult
    summary: dict[str, Any]

    @property
    def ready_for_downstream(self) -> bool:
        return bool(self.summary.get("ready_for_downstream"))


def generate_synthetic(
    config_path: str | Path = "config/simulation.yaml",
    *,
    out_dir: str | Path | None = None,
    seed: int | None = None,
) -> SimulationRunResult:
    config = load_simulation_config(config_path, seed=seed, output_dir=out_dir)
    tables = generate_cohort_tables(config)
    return write_output_package(tables, config, config.output_dir)


def write_output_package(
    tables: SimulationTables,
    config: SimulationConfig,
    output_dir: str | Path,
) -> SimulationRunResult:
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    _write_csvs(tables, out_path)
    _write_effective_config(config, out_path / "simulation_config_used.yaml")
    validation = validate_data_dir(out_path, report_path=out_path / "artifacts" / "validation-report.json")
    diagnostics = build_diagnostics(config, tables, validation)
    summary = build_summary(config, out_path, validation, diagnostics)
    (out_path / "simulation_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return SimulationRunResult(out_path, config, tables, validation, summary)


def build_summary(
    config: SimulationConfig,
    output_dir: Path,
    validation: ValidationResult,
    diagnostics: list[DiagnosticCheck],
) -> dict[str, Any]:
    failed_checks = [check for check in diagnostics if check.required and check.status == "fail"]
    schema_failed = validation.status == "fail"
    warnings = list(config.warnings) + validation.warnings + [
        f"capture-worthy {item['entity']}:{item['role']} value={item['value']}"
        for item in validation.capture_worthy_values[:25]
    ]
    errors = list(validation.errors) + [
        f"range violation {item['entity']}:{item['role']} value={item['value']}"
        for item in validation.range_violations
    ] + [f"{check.name} failed" for check in failed_checks]
    ready = not schema_failed and not failed_checks
    status = "fail" if not ready else "warn" if warnings or validation.status == "warn" else "pass"
    return {
        "status": status,
        "ready_for_downstream": ready,
        "seed": config.seed,
        "n_participants": config.n_participants,
        "study_days": config.study_days,
        "output_dir": str(output_dir),
        "schema_validation_status": validation.status,
        "target_checks": [check.to_dict() for check in diagnostics],
        "warnings": warnings,
        "errors": errors,
        "synthetic_data": True,
        "contains_phi": False,
        "synthetic_data_notice": "Generated synthetic data for Project Lullaby; contains no real PHI.",
        "generated_at_utc": datetime.now(UTC).isoformat(),
    }


def build_diagnostics(
    config: SimulationConfig,
    tables: SimulationTables,
    validation: ValidationResult,
) -> list[DiagnosticCheck]:
    checks: list[DiagnosticCheck] = []
    checks.extend(_event_rate_checks(config, tables.clinical_outcomes))
    checks.extend(_archetype_checks(config, tables.participants))
    checks.extend(_adherence_checks(tables.daily_vitals))
    checks.extend(_physiology_checks(config, tables.daily_vitals, tables.clinical_outcomes))
    checks.extend(_missingness_checks(tables.daily_vitals))
    checks.append(
        DiagnosticCheck(
            name="schema_validation.status",
            required=True,
            target="not fail",
            observed=validation.status,
            tolerance=None,
            denominator=len(validation.entities),
            status="fail" if validation.status == "fail" else "pass",
            details={"errors": validation.errors, "range_violations": validation.range_violations},
        )
    )
    return checks


def _event_rate_checks(config: SimulationConfig, outcomes: pd.DataFrame) -> list[DiagnosticCheck]:
    tolerance = _rate_tolerance(config.n_participants, base=0.03)
    fields = {
        "cv_event": config.event_rate.cv_event,
        "heat_illness": config.event_rate.heat_illness,
        "ed_visit": config.event_rate.ed_visit,
        "hospitalized": config.event_rate.hospitalization,
    }
    checks = []
    for field, target in fields.items():
        parsed = _required_bool(outcomes, field, f"clinical_outcomes.{field}")
        if parsed.errors:
            checks.append(_semantic_failure_check(f"event_rate.{field}", target, len(outcomes), parsed.errors))
            continue
        observed = float(parsed.true_mask.sum() / len(outcomes)) if len(outcomes) else 0.0
        check = _absolute_check(f"event_rate.{field}", target, observed, tolerance, len(outcomes))
        check.details["missing_unknown"] = parsed.counts["missing_unknown"]
        checks.append(check)
    return checks


def _archetype_checks(config: SimulationConfig, participants: pd.DataFrame) -> list[DiagnosticCheck]:
    tolerance = _rate_tolerance(config.n_participants, base=0.05)
    observed = participants["archetype"].value_counts(normalize=True).to_dict()
    return [
            _absolute_check(
                f"archetype_proportion.{item.name}",
            item.normalized_weight,
            float(observed.get(item.name, 0.0)),
            tolerance,
            len(participants),
        )
        for item in config.archetypes
    ]


def _adherence_checks(daily: pd.DataFrame) -> list[DiagnosticCheck]:
    early = daily.loc[daily["week"] <= 2]
    late = daily.loc[daily["week"] >= max(daily["week"].max() - 1, 1)]
    early_wear = float(pd.to_numeric(early["sensor_wear_hours"], errors="coerce").mean())
    late_wear = float(pd.to_numeric(late["sensor_wear_hours"], errors="coerce").mean())
    early_scale_parsed = _required_bool(early, "scale_used", "daily_vitals.scale_used")
    late_scale_parsed = _required_bool(late, "scale_used", "daily_vitals.scale_used")
    scale_errors = early_scale_parsed.errors + late_scale_parsed.errors
    early_scale = _parsed_rate(early_scale_parsed)
    late_scale = _parsed_rate(late_scale_parsed)
    return [
        DiagnosticCheck(
            "adherence.wear_hours_decline",
            True,
            "late < early",
            round(late_wear - early_wear, 4),
            None,
            len(daily),
            "pass" if late_wear < early_wear else "fail",
            {"early_mean": early_wear, "late_mean": late_wear},
        ),
        DiagnosticCheck(
            "adherence.scale_use_decline",
            True,
            "late < early",
            round(late_scale - early_scale, 4),
            None,
            len(daily),
            "fail" if scale_errors else "pass" if late_scale < early_scale else "fail",
            {
                "early_rate": early_scale,
                "late_rate": late_scale,
                "early_missing_unknown": early_scale_parsed.counts["missing_unknown"],
                "late_missing_unknown": late_scale_parsed.counts["missing_unknown"],
                "errors": scale_errors,
            },
        ),
    ]


def _physiology_checks(
    config: SimulationConfig,
    daily: pd.DataFrame,
    outcomes: pd.DataFrame,
) -> list[DiagnosticCheck]:
    checks: list[DiagnosticCheck] = []
    cv_events = _required_bool(outcomes, "cv_event", "clinical_outcomes.cv_event")
    cv_windows = _required_bool(daily, "cv_event_window", "daily_vitals.cv_event_window")
    heat_days = _required_bool(daily, "heat_strain_day", "daily_vitals.heat_strain_day")
    parse_errors = cv_events.errors + cv_windows.errors + heat_days.errors
    if parse_errors:
        checks.append(_semantic_failure_check("physiology.cv_body_water_pre_event_positive", 0.80, len(daily), parse_errors))
        checks.append(_semantic_failure_check("physiology.heat_strain_direction", 0.55, len(daily), parse_errors))
        checks.append(_semantic_failure_check("physiology.overlap_body_water_auc", "<=0.90", len(daily), parse_errors))
        return checks
    cv_ids = outcomes.loc[cv_events.true_mask, "participant_id"].tolist()
    positive_slopes = 0
    slope_denominator = 0
    for participant_id in cv_ids:
        participant_days = daily.loc[
            (daily["participant_id"] == participant_id) & cv_windows.true_mask
        ].sort_values("study_day")
        values = pd.to_numeric(participant_days["body_water_pct"], errors="coerce").dropna()
        if len(values) >= 4:
            slope_denominator += 1
            if values.iloc[-1] > values.iloc[0]:
                positive_slopes += 1
    slope_rate = positive_slopes / slope_denominator if slope_denominator else 1.0
    checks.append(
        _minimum_check("physiology.cv_body_water_pre_event_positive", 0.80, slope_rate, 0.20, slope_denominator)
    )
    heat_rows = daily.loc[heat_days.true_mask].sort_values(["participant_id", "study_day"])
    heat_success = 0
    heat_denominator = 0
    for row in heat_rows.itertuples(index=False):
        prev = daily.loc[
            (daily["participant_id"] == row.participant_id) & (daily["study_day"] == int(row.study_day) - 1)
        ]
        if prev.empty:
            continue
        prev_row = prev.iloc[0]
        needed = [row.body_water_pct, row.heart_rate, row.skin_temperature_c, prev_row["body_water_pct"], prev_row["heart_rate"], prev_row["skin_temperature_c"]]
        if any(pd.isna(value) for value in needed):
            continue
        heat_denominator += 1
        if (
            float(row.body_water_pct) < float(prev_row["body_water_pct"])
            and float(row.heart_rate) > float(prev_row["heart_rate"])
            and float(row.skin_temperature_c) > float(prev_row["skin_temperature_c"])
        ):
            heat_success += 1
    heat_rate = heat_success / heat_denominator if heat_denominator else (0.0 if config.event_rate.heat_illness > 0 else 1.0)
    checks.append(_minimum_check("physiology.heat_strain_direction", 0.55, heat_rate, 0.10, heat_denominator))
    body_water = pd.to_numeric(daily["body_water_pct"], errors="coerce")
    valid_label_mask = cv_windows.valid_mask
    auc_values = body_water.loc[valid_label_mask]
    labels = cv_windows.true_mask.loc[valid_label_mask]
    auc = simple_auc(auc_values.fillna(np.nan).tolist(), labels.tolist())
    checks.append(
        DiagnosticCheck(
            "physiology.overlap_body_water_auc",
            True,
            "<=0.90",
            round(auc, 4),
            None,
            int(body_water.loc[valid_label_mask].notna().sum()),
            "pass" if auc <= 0.90 else "fail",
            {"interpretation": "single raw body-water measure is useful but not trivially separable"},
        )
    )
    return checks


def _missingness_checks(daily: pd.DataFrame) -> list[DiagnosticCheck]:
    observed_missing = daily["systolic_bp"].isna() | daily["heart_rate"].isna() | daily["body_water_pct"].isna()
    archetype_rates = observed_missing.groupby(daily["archetype"]).mean()
    archetype_spread = float(archetype_rates.max() - archetype_rates.min()) if len(archetype_rates) else 0.0
    heat_rates = observed_missing.groupby(daily["heat_exposure_level"].isin(["high", "extreme"])).mean()
    heat_spread = float(heat_rates.max() - heat_rates.min()) if len(heat_rates) > 1 else 0.0
    cv_windows = _required_bool(daily, "cv_event_window", "daily_vitals.cv_event_window")
    heat_days = _required_bool(daily, "heat_strain_day", "daily_vitals.heat_strain_day")
    errors = cv_windows.errors + heat_days.errors
    if errors:
        return [
            _minimum_check("missingness.by_archetype_spread", 0.05, archetype_spread, 0.05, len(daily)),
            _minimum_check("missingness.by_heat_exposure_spread", 0.02, heat_spread, 0.02, len(daily)),
            _semantic_failure_check("missingness.worsening_state_lift", 0.01, len(daily), errors),
        ]
    worsening_mask = cv_windows.true_mask | heat_days.true_mask
    worsening_rate = float(pd.to_numeric(daily.loc[worsening_mask, "latent_missingness_probability"], errors="coerce").mean())
    baseline_rate = float(pd.to_numeric(daily.loc[~worsening_mask, "latent_missingness_probability"], errors="coerce").mean())
    return [
        _minimum_check("missingness.by_archetype_spread", 0.05, archetype_spread, 0.05, len(daily)),
        _minimum_check("missingness.by_heat_exposure_spread", 0.02, heat_spread, 0.02, len(daily)),
        _minimum_check("missingness.worsening_state_lift", 0.01, worsening_rate - baseline_rate, 0.05, len(daily)),
    ]


def _required_bool(frame: pd.DataFrame, column: str, role: str) -> ParsedBooleanSeries:
    if column not in frame:
        index = frame.index
        false = pd.Series(False, index=index)
        return ParsedBooleanSeries(
            true_mask=false,
            false_mask=false.copy(),
            missing_mask=pd.Series(True, index=index),
            invalid_mask=false.copy(),
            errors=[f"Missing required boolean column for {role}: {column}"],
        )
    return parse_domain_boolean_series(
        frame[column],
        DomainBooleanParsePolicy(role=role, required=True),
        source_column=column,
    )


def _parsed_rate(parsed: ParsedBooleanSeries) -> float:
    denominator = int(parsed.valid_mask.sum())
    if not denominator:
        return 0.0
    return float(parsed.true_mask.sum() / denominator)


def _semantic_failure_check(
    name: str,
    target: float | str,
    denominator: int,
    errors: list[str],
) -> DiagnosticCheck:
    return DiagnosticCheck(
        name=name,
        required=True,
        target=target,
        observed=None,
        tolerance=None,
        denominator=int(denominator),
        status="fail",
        details={"errors": errors},
    )


def _absolute_check(
    name: str,
    target: float,
    observed: float,
    tolerance: float,
    denominator: int,
) -> DiagnosticCheck:
    status = "pass" if abs(float(observed) - float(target)) <= float(tolerance) else "fail"
    return DiagnosticCheck(
        name=name,
        required=True,
        target=round(float(target), 6),
        observed=round(float(observed), 6),
        tolerance=round(float(tolerance), 6),
        denominator=int(denominator),
        status=status,
        details={"difference": round(float(observed) - float(target), 6)},
    )


def _minimum_check(
    name: str,
    target: float,
    observed: float,
    tolerance: float,
    denominator: int,
) -> DiagnosticCheck:
    status = "pass" if float(observed) + float(tolerance) >= float(target) else "fail"
    return DiagnosticCheck(
        name=name,
        required=True,
        target=round(float(target), 6),
        observed=round(float(observed), 6),
        tolerance=round(float(tolerance), 6),
        denominator=int(denominator),
        status=status,
        details={"difference": round(float(observed) - float(target), 6)},
    )


def _rate_tolerance(n_participants: int, *, base: float) -> float:
    return max(0.01, float(base) * float(np.sqrt(200 / max(n_participants, 1))))


def _write_csvs(tables: SimulationTables, output_dir: Path) -> None:
    for name, filename in CSV_FILENAMES.items():
        df = tables.as_dict()[name]
        df.to_csv(output_dir / filename, index=False, na_rep="")


def _write_effective_config(config: SimulationConfig, path: Path) -> None:
    payload = config.to_effective_dict()
    path.write_text(yaml.safe_dump(payload, sort_keys=True))
