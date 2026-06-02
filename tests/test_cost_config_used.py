"""Tests for SPEC-012 Panel 4 cost-config contract."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from src.visualization.analytic_dashboard import render_panel_4


@pytest.fixture()
def tmp_model_dir(tmp_path):
    d = tmp_path / "modeling"
    d.mkdir()
    thresholds = np.linspace(0.1, 0.9, 10)
    rows = [{"model_id": "rf", "threshold": t, "precision": 0.7,
             "recall": 0.6, "specificity": 0.8, "false_positive_rate": 0.2,
             "alerts_per_100_participant_days": t * 3,
             "number_needed_to_alert": 5.0, "estimated_calls": t * 20}
            for t in thresholds]
    pd.DataFrame(rows).to_csv(d / "operating_points.csv", index=False)
    return d


@pytest.fixture()
def tmp_out_dir(tmp_path):
    d = tmp_path / "analytic"
    d.mkdir()
    return d


@pytest.fixture()
def manifest_path(tmp_path):
    return tmp_path / "manifest.json"


@pytest.fixture()
def costs_yaml(tmp_path):
    config = {
        "currency": "USD",
        "nurse_hotline": {"cost_per_call": 42.0, "minutes_per_call": 18, "nurse_hourly_cost": 85.0},
        "alert_workflow": {"survey_review_minutes": 4, "false_positive_call_probability": 0.65,
                           "true_positive_call_probability": 0.90},
        "volume_assumptions": {"participants": 200, "participant_days": 8400, "alerts_to_calls_multiplier": 1.0},
        "sensitivity": {"cost_per_call": [25, 42, 75], "false_positive_call_probability": [0.40, 0.65, 0.85]},
    }
    path = tmp_path / "costs.yaml"
    path.write_text(yaml.dump(config))
    return path


def _png_size(path):
    import struct
    with open(path, "rb") as f:
        f.read(8); f.read(4); f.read(4)
        w = struct.unpack(">I", f.read(4))[0]
        h = struct.unpack(">I", f.read(4))[0]
    return w, h


def test_panel_4_reads_costs_from_yaml(tmp_model_dir, tmp_out_dir, manifest_path, costs_yaml):
    render_panel_4(tmp_model_dir, tmp_out_dir, costs_yaml, manifest_path)
    out = tmp_out_dir / "04_alarm_cost.png"
    assert out.exists()
    w, h = _png_size(out)
    assert w >= 1600 and h >= 900


def test_panel_4_unavailable_if_costs_absent(tmp_model_dir, tmp_out_dir, manifest_path, tmp_path):
    missing_path = tmp_path / "nonexistent_costs.yaml"
    render_panel_4(tmp_model_dir, tmp_out_dir, missing_path, manifest_path)
    out = tmp_out_dir / "04_alarm_cost.png"
    assert out.exists()  # unavailable panel PNG is still written
    w, h = _png_size(out)
    assert w >= 1600 and h >= 900


def test_panel_4_unavailable_if_cost_config_none(tmp_model_dir, tmp_out_dir, manifest_path):
    render_panel_4(tmp_model_dir, tmp_out_dir, None, manifest_path)
    assert (tmp_out_dir / "04_alarm_cost.png").exists()
