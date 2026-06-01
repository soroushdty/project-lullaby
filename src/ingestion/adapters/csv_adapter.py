from __future__ import annotations

import pathlib

import pandas as pd


def load(input_dir: str) -> dict[str, pd.DataFrame]:
    """Load all CSV files from input_dir, keyed by stem (table name)."""
    path = pathlib.Path(input_dir)
    frames: dict[str, pd.DataFrame] = {}
    for csv_file in sorted(path.glob("*.csv")):
        frames[csv_file.stem] = pd.read_csv(csv_file)
    return frames
