from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


class SplitError(ValueError):
    """Raised when grouped cross-validation cannot be constructed."""


@dataclass
class SplitAssignment:
    repeat: int
    fold: int
    train_indices: np.ndarray
    validation_indices: np.ndarray
    train_participant_ids: set[str]
    validation_participant_ids: set[str]
    class_counts: dict[str, int]
    warnings: list[str] = field(default_factory=list)


def _effective_splits(y: np.ndarray, n_splits: int) -> tuple[int, list[str]]:
    positives = int(np.sum(y == 1))
    negatives = int(np.sum(y == 0))
    groups = len(y)
    if positives == 0 or negatives == 0:
        raise SplitError("Grouped CV requires at least one positive and one negative participant")
    max_balanced = min(positives, negatives, groups)
    effective = min(int(n_splits), max_balanced)
    warnings: list[str] = []
    if effective < 2:
        raise SplitError("Grouped CV requires at least two feasible folds")
    if effective < n_splits:
        warnings.append(
            f"Requested {n_splits} splits reduced to {effective} due to rare positive/negative participant groups"
        )
    return effective, warnings


def assert_no_group_leakage(assignments: list[SplitAssignment]) -> None:
    for assignment in assignments:
        overlap = assignment.train_participant_ids & assignment.validation_participant_ids
        if overlap:
            raise SplitError(
                f"Participant leakage in repeat {assignment.repeat} fold {assignment.fold}: {sorted(overlap)[:5]}"
            )


def make_repeated_grouped_stratified_splits(
    participant_ids: list[str],
    y: np.ndarray,
    *,
    n_splits: int,
    n_repeats: int,
    seed: int,
) -> list[SplitAssignment]:
    y = np.asarray(y).astype(int)
    if len(participant_ids) != len(y):
        raise SplitError("participant_ids and y must have the same length")
    effective_splits, base_warnings = _effective_splits(y, int(n_splits))
    assignments: list[SplitAssignment] = []
    all_indices = np.arange(len(y))
    pos_indices = all_indices[y == 1]
    neg_indices = all_indices[y == 0]
    for repeat in range(int(n_repeats)):
        rng = np.random.default_rng(int(seed) + repeat * 104729)
        pos = rng.permutation(pos_indices)
        neg = rng.permutation(neg_indices)
        fold_bins = [[] for _ in range(effective_splits)]
        for i, idx in enumerate(pos):
            fold_bins[i % effective_splits].append(int(idx))
        for i, idx in enumerate(neg):
            fold_bins[i % effective_splits].append(int(idx))
        for fold, validation in enumerate(fold_bins):
            validation_indices = np.array(sorted(validation), dtype=int)
            train_indices = np.array(sorted(set(all_indices.tolist()) - set(validation_indices.tolist())), dtype=int)
            train_ids = {participant_ids[i] for i in train_indices}
            validation_ids = {participant_ids[i] for i in validation_indices}
            assignment = SplitAssignment(
                repeat=repeat,
                fold=fold,
                train_indices=train_indices,
                validation_indices=validation_indices,
                train_participant_ids=train_ids,
                validation_participant_ids=validation_ids,
                class_counts={
                    "train_positive": int(np.sum(y[train_indices] == 1)),
                    "train_negative": int(np.sum(y[train_indices] == 0)),
                    "validation_positive": int(np.sum(y[validation_indices] == 1)),
                    "validation_negative": int(np.sum(y[validation_indices] == 0)),
                },
                warnings=base_warnings.copy(),
            )
            assignments.append(assignment)
    assert_no_group_leakage(assignments)
    return assignments
