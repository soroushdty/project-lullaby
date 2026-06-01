"""Integration tests proving stream/batch canonical equivalence."""

from __future__ import annotations

import pathlib
import time

import pandas as pd
import pytest

from src.ingestion.adapters.file_adapter import FileAdapter, FileAdapterConfig
from src.ingestion.stream import StreamAccumulator, StreamAdapter, StreamAdapterConfig
from src.schemas.base import SchemaContract
from src.schemas.lullaby import LullabySchema

SYNTHETIC_DIR = pathlib.Path(__file__).parents[2] / "data" / "synthetic"


def _canonical_batch_frames(schema: SchemaContract) -> dict[str, pd.DataFrame]:
    frames = FileAdapter().load(FileAdapterConfig(path=str(SYNTHETIC_DIR)))
    canonical: dict[str, pd.DataFrame] = {}
    for table in schema.table_names():
        contract = schema.table_contract(table)
        df = frames[table].copy()
        if contract.timestamp_column:
            df[contract.timestamp_column] = pd.to_datetime(
                df[contract.timestamp_column], utc=True, errors="raise"
            )
        canonical[table] = df
    return canonical


def _sorted_for_compare(
    frames: dict[str, pd.DataFrame],
    schema: SchemaContract,
) -> dict[str, pd.DataFrame]:
    result: dict[str, pd.DataFrame] = {}
    for table, df in frames.items():
        contract = schema.table_contract(table)
        sort_cols = (
            [contract.timestamp_column] + contract.primary_key
            if contract.timestamp_column
            else contract.primary_key
        )
        usable_sort_cols = [col for col in sort_cols if col in df.columns]
        sorted_df = df.sort_values(usable_sort_cols) if usable_sort_cols else df
        result[table] = sorted_df.reset_index(drop=True)
    return result


def _assert_canonical_equal(
    left: dict[str, pd.DataFrame],
    right: dict[str, pd.DataFrame],
    schema: SchemaContract,
) -> None:
    left_sorted = _sorted_for_compare(left, schema)
    right_sorted = _sorted_for_compare(right, schema)
    for table in schema.table_names():
        try:
            pd.testing.assert_frame_equal(
                left_sorted[table],
                right_sorted[table],
                check_like=True,
                check_dtype=False,
            )
        except AssertionError as exc:
            raise AssertionError(
                f"Canonical mismatch table={table} "
                f"left_rows={len(left_sorted[table])} right_rows={len(right_sorted[table])}"
            ) from exc


def test_synthetic_equivalence(caplog):
    schema = LullabySchema()
    adapter = StreamAdapter(
        batch_adapter=FileAdapter(),
        source_config=FileAdapterConfig(path=str(SYNTHETIC_DIR)),
        schema=schema,
        config=StreamAdapterConfig(cadence_s=60, speed_factor=100.0),
    )

    start = time.perf_counter()
    with caplog.at_level("WARNING", logger="src.ingestion.stream.adapter"):
        accumulated = StreamAccumulator.accumulate(adapter, schema)
    elapsed = time.perf_counter() - start

    assert elapsed < 120
    assert adapter.late_arrival_count == 0
    assert not any("LateArrivalWarning" in record.message for record in caplog.records)
    _assert_canonical_equal(accumulated, _canonical_batch_frames(schema), schema)


def test_equivalence_diagnostic_identifies_differing_table_and_row_count():
    schema = LullabySchema()
    batch = _canonical_batch_frames(schema)
    mutated = {table: df.copy() for table, df in batch.items()}
    mutated["alerts"] = mutated["alerts"].iloc[:-1].copy()

    with pytest.raises(AssertionError, match="table=alerts.*left_rows=2.*right_rows=3"):
        _assert_canonical_equal(mutated, batch, schema)
