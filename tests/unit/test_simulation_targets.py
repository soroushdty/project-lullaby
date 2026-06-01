from __future__ import annotations

import json
from dataclasses import replace

import pandas as pd

from src.simulation import generate_synthetic
from src.simulation.export import build_diagnostics, build_summary
from src.validation.semantics import DomainBooleanParsePolicy, parse_domain_boolean_series


def test_event_rates_archetypes_heat_and_follow_up_targets(simulation_output_dir):
    result = generate_synthetic("config/simulation.yaml", out_dir=simulation_output_dir, seed=20260601)
    checks = {check["name"]: check for check in result.summary["target_checks"]}
    outcomes = pd.read_csv(simulation_output_dir / "clinical_outcomes.csv")
    participants = pd.read_csv(simulation_output_dir / "participants.csv")
    environment = pd.read_csv(simulation_output_dir / "environment.csv")
    alerts = pd.read_csv(simulation_output_dir / "alerts.csv")

    assert checks["event_rate.cv_event"]["status"] == "pass"
    assert checks["event_rate.heat_illness"]["status"] == "pass"
    assert outcomes["cv_event"].mean() == 0.075
    assert set(participants["archetype"]) >= {"heat_stressed", "silent_decliner"}
    assert environment["heat_wave"].any()
    assert alerts["survey_completed"].mean() > 0.35
    assert alerts["called_nurse"].mean() > 0.25


def test_cv_heat_and_overlap_physiology_targets(simulation_output_dir):
    result = generate_synthetic("config/simulation.yaml", out_dir=simulation_output_dir, seed=20260601)
    daily = pd.read_csv(simulation_output_dir / "daily_vitals.csv")
    checks = {check["name"]: check for check in result.summary["target_checks"]}

    assert checks["physiology.cv_body_water_pre_event_positive"]["status"] == "pass"
    assert checks["physiology.heat_strain_direction"]["status"] == "pass"
    assert checks["physiology.overlap_body_water_auc"]["observed"] <= 0.90
    cv_window_mask = parse_domain_boolean_series(
        daily["cv_event_window"],
        DomainBooleanParsePolicy(role="daily_vitals.cv_event_window", required=True),
        source_column="cv_event_window",
    ).true_mask
    cv_window = daily.loc[cv_window_mask]
    assert cv_window.groupby("participant_id")["body_water_pct"].agg(lambda s: s.dropna().iloc[-1] > s.dropna().iloc[0]).mean() >= 0.8
    assert daily["overlap_day"].any()


def test_adherence_and_non_random_missingness_diagnostics(simulation_output_dir):
    result = generate_synthetic("config/simulation.yaml", out_dir=simulation_output_dir, seed=20260601)
    checks = {check["name"]: check for check in result.summary["target_checks"]}

    assert checks["adherence.wear_hours_decline"]["status"] == "pass"
    assert checks["adherence.scale_use_decline"]["status"] == "pass"
    assert checks["missingness.by_archetype_spread"]["status"] == "pass"
    assert checks["missingness.by_heat_exposure_spread"]["status"] == "pass"
    assert checks["missingness.worsening_state_lift"]["status"] == "pass"


def test_summary_shape_and_required_diagnostic_fields(simulation_output_dir):
    generate_synthetic("config/simulation.yaml", out_dir=simulation_output_dir, seed=20260601)
    summary = json.loads((simulation_output_dir / "simulation_summary.json").read_text())

    assert summary["ready_for_downstream"] is True
    assert summary["synthetic_data"] is True
    assert summary["contains_phi"] is False
    assert "no real PHI" in summary["synthetic_data_notice"]
    assert summary["status"] in {"pass", "warn"}
    assert summary["target_checks"]
    for check in summary["target_checks"]:
        assert {"target", "observed", "tolerance", "denominator", "status"}.issubset(check)


def test_simulator_diagnostics_match_native_and_csv_string_booleans(simulation_output_dir):
    result = generate_synthetic("config/simulation.yaml", out_dir=simulation_output_dir, seed=20260601)
    tables = result.tables
    string_tables = replace(
        tables,
        clinical_outcomes=tables.clinical_outcomes.assign(
            cv_event=tables.clinical_outcomes["cv_event"].map(lambda value: "True" if value else "False"),
            heat_illness=tables.clinical_outcomes["heat_illness"].map(lambda value: "1" if value else "0"),
            ed_visit=tables.clinical_outcomes["ed_visit"].map(lambda value: "yes" if value else "no"),
            hospitalized=tables.clinical_outcomes["hospitalized"].map(lambda value: "t" if value else "f"),
        ),
        daily_vitals=tables.daily_vitals.assign(
            scale_used=tables.daily_vitals["scale_used"].map(lambda value: "" if pd.isna(value) else "true" if value else "false"),
            cv_event_window=tables.daily_vitals["cv_event_window"].map(lambda value: "" if pd.isna(value) else "1" if value else "0"),
            heat_strain_day=tables.daily_vitals["heat_strain_day"].map(lambda value: "" if pd.isna(value) else "yes" if value else "no"),
        ),
    )

    native = {check.name: check for check in build_diagnostics(result.config, tables, result.validation)}
    stringy = {check.name: check for check in build_diagnostics(result.config, string_tables, result.validation)}

    for name in ["event_rate.cv_event", "event_rate.heat_illness", "adherence.scale_use_decline"]:
        assert stringy[name].observed == native[name].observed
        assert stringy[name].status == native[name].status


def test_invalid_required_diagnostic_boolean_fails_readiness(simulation_output_dir):
    result = generate_synthetic("config/simulation.yaml", out_dir=simulation_output_dir, seed=20260601)
    bad_tables = replace(
        result.tables,
        clinical_outcomes=result.tables.clinical_outcomes.assign(
            cv_event=["maybe"] + result.tables.clinical_outcomes["cv_event"].iloc[1:].tolist()
        ),
    )

    diagnostics = build_diagnostics(result.config, bad_tables, result.validation)
    summary = build_summary(result.config, simulation_output_dir, result.validation, diagnostics)
    checks = {check.name: check for check in diagnostics}

    assert checks["event_rate.cv_event"].status == "fail"
    assert "Invalid boolean token" in checks["event_rate.cv_event"].details["errors"][0]
    assert summary["ready_for_downstream"] is False
