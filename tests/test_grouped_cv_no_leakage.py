from __future__ import annotations

import numpy as np

from src.modeling.datasets import build_modeling_dataset
from src.modeling.splits import make_repeated_grouped_stratified_splits


def test_grouped_cv_has_no_participant_leakage(default_modeling_config):
    dataset = build_modeling_dataset("data/synthetic/longitudinal", default_modeling_config)
    assignments = make_repeated_grouped_stratified_splits(
        dataset.participant_ids,
        dataset.y,
        n_splits=5,
        n_repeats=3,
        seed=20260601,
    )

    for assignment in assignments:
        assert assignment.train_participant_ids.isdisjoint(assignment.validation_participant_ids)
        assert assignment.class_counts["validation_positive"] >= 1
        assert assignment.class_counts["validation_negative"] >= 1


def test_grouped_cv_is_deterministic_by_seed(default_modeling_config):
    dataset = build_modeling_dataset("data/synthetic/longitudinal", default_modeling_config)
    kwargs = dict(participant_ids=dataset.participant_ids, y=dataset.y, n_splits=5, n_repeats=2, seed=20260601)

    first = make_repeated_grouped_stratified_splits(**kwargs)
    second = make_repeated_grouped_stratified_splits(**kwargs)

    assert [a.validation_indices.tolist() for a in first] == [a.validation_indices.tolist() for a in second]


def test_grouped_cv_reduces_infeasible_positive_event_splits():
    participant_ids = [f"P{i:02d}" for i in range(12)]
    y = np.array([1, 1, 1] + [0] * 9)

    assignments = make_repeated_grouped_stratified_splits(participant_ids, y, n_splits=5, n_repeats=1, seed=7)

    assert {a.fold for a in assignments} == {0, 1, 2}
    assert any("reduced" in "; ".join(a.warnings) for a in assignments)
    for assignment in assignments:
        assert assignment.train_participant_ids.isdisjoint(assignment.validation_participant_ids)
