from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import yaml

from src.modeling.bakeoff import BakeoffError, load_config
from src.modeling.metrics import select_threshold
from src.modeling.models import ModelSpec, make_pipeline


def test_fold_local_imputation_uses_training_rows_only():
    train_x = pd.DataFrame({"a": [1.0, 2.0, np.nan], "b": [10.0, 10.0, 10.0]})
    train_y = np.array([0, 1, 0])
    val_x = pd.DataFrame({"a": [1000.0, np.nan], "b": [99.0, 99.0]})
    pipeline = make_pipeline(ModelSpec("baseline_meows_logistic", "baseline", True), seed=1, class_weight="balanced")

    pipeline.fit(train_x, train_y)
    pipeline.predict_scores(val_x)

    assert pipeline.medians_[0] == 1.5


def test_pipeline_does_not_mutate_raw_training_frame():
    train_x = pd.DataFrame({"a": [1.0, np.nan, 3.0], "b": [0.0, 1.0, 0.0]})
    original = train_x.copy(deep=True)
    train_y = np.array([0, 1, 0])
    pipeline = make_pipeline(ModelSpec("mlp", "neural", True, supports_class_weight=False), seed=2, class_weight="balanced")

    pipeline.fit(train_x, train_y)

    pd.testing.assert_frame_equal(train_x, original)
    assert any("class_weight" in note for note in pipeline.notes)


def test_non_default_resampling_fails_config_validation(tmp_path, default_modeling_config):
    config = default_modeling_config.copy()
    config["imbalance"] = dict(config["imbalance"])
    config["imbalance"]["resampling"] = "random_oversample"
    config_path = tmp_path / "modeling.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    with pytest.raises(BakeoffError, match="resampling: none"):
        load_config(config_path)


def test_threshold_selection_uses_training_scores_and_fallback():
    train_y = np.array([1, 0, 0, 0])
    train_scores = np.array([0.2, 0.9, 0.8, 0.7])

    threshold = select_threshold(train_y, train_scores, min_precision=0.80)

    assert threshold.target_met is False
    assert threshold.threshold == 0.2
    assert "unmet" in threshold.notes
