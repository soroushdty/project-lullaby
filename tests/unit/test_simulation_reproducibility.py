from __future__ import annotations

from src.simulation import generate_synthetic


CSV_FILES = (
    "participants.csv",
    "daily_vitals.csv",
    "alerts.csv",
    "staff_contacts.csv",
    "clinical_outcomes.csv",
    "environment.csv",
    "recruitment.csv",
)


def test_same_seed_writes_byte_identical_csvs(tmp_path):
    first = tmp_path / "a"
    second = tmp_path / "b"

    result_a = generate_synthetic("config/simulation.yaml", out_dir=first, seed=20260601)
    result_b = generate_synthetic("config/simulation.yaml", out_dir=second, seed=20260601)

    assert result_a.ready_for_downstream
    assert result_b.ready_for_downstream
    for filename in CSV_FILES:
        assert (first / filename).read_bytes() == (second / filename).read_bytes()
