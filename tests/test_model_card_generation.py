"""Tests for SPEC-012 TRIPOD-AI model card generation."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.visualization.model_cards import TRIPOD_AI_REQUIRED_SECTIONS, generate_tripod_ai_card


@pytest.fixture()
def tmp_model_dir(tmp_path):
    d = tmp_path / "modeling"
    d.mkdir()
    summary = {
        "data_source": "raw",
        "seed": 20260601,
        "run_timestamp": "2026-06-01T12:00:00+00:00",
        "models_trained": ["baseline_meows_logistic", "random_forest", "mlp"],
        "n_participants": 200,
        "n_events": 12,
    }
    (d / "bakeoff_summary.json").write_text(json.dumps(summary))
    (d / "bakeoff_config_used.yaml").write_text("seed: 20260601\ntarget: outcome.cv_event\n")
    (d / "metrics_summary.csv").write_text(
        "model_id,metric,mean,sd,ci_lower,ci_upper,n_folds,n_repeats,primary_metric,notes\n"
        "random_forest,auprc,0.35,0.05,0.25,0.45,5,2,True,\n"
    )
    return d


@pytest.fixture()
def tmp_synthetic_model_dir(tmp_path):
    d = tmp_path / "modeling_synthetic"
    d.mkdir()
    summary = {"data_source": "synthetic", "seed": 20260601,
                "run_timestamp": "2026-06-01T12:00:00+00:00",
                "models_trained": ["random_forest"], "n_participants": 200, "n_events": 8}
    (d / "bakeoff_summary.json").write_text(json.dumps(summary))
    (d / "bakeoff_config_used.yaml").write_text("seed: 20260601\n")
    return d


def test_model_card_has_required_sections(tmp_model_dir, tmp_path):
    out = tmp_path / "card.md"
    generate_tripod_ai_card(tmp_model_dir, Path("data/raw"), None, out)
    assert out.exists()
    content = out.read_text()
    for section in TRIPOD_AI_REQUIRED_SECTIONS:
        assert section in content, f"Missing TRIPOD-AI section: {section}"


def test_model_card_synthetic_caveat(tmp_synthetic_model_dir, tmp_path):
    out = tmp_path / "card_synthetic.md"
    generate_tripod_ai_card(tmp_synthetic_model_dir, Path("data/synthetic/longitudinal"), None, out)
    content = out.read_text()
    assert "Synthetic-Data Caveat" in content
    assert "synthetic data" in content.lower()
    assert "not validated" in content.lower() or "do not constitute" in content.lower()


def test_model_card_non_synthetic_no_strong_caveat(tmp_model_dir, tmp_path):
    out = tmp_path / "card_raw.md"
    generate_tripod_ai_card(tmp_model_dir, Path("data/raw"), None, out)
    content = out.read_text()
    # Section heading required; but big ⚠ synthetic-only block must NOT appear for raw data
    assert "Synthetic-Data Caveat" in content
    assert "⚠ **All results in this card were produced on bundled synthetic data.**" not in content


def test_model_card_references_exact_paths(tmp_model_dir, tmp_path):
    out = tmp_path / "card.md"
    generate_tripod_ai_card(tmp_model_dir, Path("data/raw"), Path("config/costs.yaml"), out)
    content = out.read_text()
    assert str(tmp_model_dir) in content or "bakeoff_config_used.yaml" in content
