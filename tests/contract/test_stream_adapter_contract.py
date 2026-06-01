"""Contract tests for the streaming ingestion public API."""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import pandera as pa
import pytest
from pydantic import ValidationError

from src.ingestion.adapters.base import AdapterConfig, BatchAdapter, BatchAdapterError
from src.ingestion.stream import StreamAdapter, StreamAdapterConfig, StreamAdapterError
from src.schemas.base import SchemaContract, SchemaTableMissingError, TableContract


class ContractSchema(SchemaContract):
    @property
    def name(self) -> str:
        return "contract"

    @property
    def version(self) -> str:
        return "0.0.1"

    def table_names(self) -> list[str]:
        return ["events", "staff"]

    def table_contract(self, table_name: str) -> TableContract:
        if table_name == "events":
            return TableContract(
                table_name="events",
                required_columns=["id", "event_ts"],
                optional_columns=[],
                primary_key=["id"],
                timestamp_column="event_ts",
            )
        if table_name == "staff":
            return TableContract(
                table_name="staff",
                required_columns=["staff_id", "role"],
                optional_columns=[],
                primary_key=["staff_id"],
                timestamp_column="",
            )
        raise SchemaTableMissingError(table_name)

    def pandera_schema(self, table_name: str) -> pa.DataFrameSchema:
        if table_name == "events":
            return pa.DataFrameSchema(
                {
                    "id": pa.Column(str),
                    "event_ts": pa.Column(
                        checks=pa.Check(
                            lambda s: hasattr(s, "dt") and s.dt.tz is not None
                        )
                    ),
                }
            )
        if table_name == "staff":
            return pa.DataFrameSchema(
                {"staff_id": pa.Column(str), "role": pa.Column(str)}
            )
        raise SchemaTableMissingError(table_name)

    def data_dictionary(self, table_name: str) -> dict[str, dict]:
        return {}


class MemoryAdapter(BatchAdapter[AdapterConfig]):
    def __init__(self, frames: dict[str, pd.DataFrame]) -> None:
        self._frames = frames

    def load(self, config: AdapterConfig) -> dict[str, pd.DataFrame]:
        return {table: df.copy() for table, df in self._frames.items()}


def _stream(
    events: pd.DataFrame,
    staff: pd.DataFrame | None = None,
    config: StreamAdapterConfig | None = None,
) -> StreamAdapter[AdapterConfig]:
    return StreamAdapter(
        batch_adapter=MemoryAdapter(
            {
                "events": events,
                "staff": staff
                if staff is not None
                else pd.DataFrame(columns=["staff_id", "role"]),
            }
        ),
        source_config=AdapterConfig(),
        schema=ContractSchema(),
        config=config or StreamAdapterConfig(cadence_s=60),
    )


def test_stream_adapter_config_defaults_and_round_trip():
    cfg = StreamAdapterConfig(cadence_s=60, speed_factor=100.0)
    assert cfg.cadence_s == 60
    assert cfg.skew_tolerance_s == 300
    assert cfg.speed_factor == 100.0
    assert cfg.backpressure_timeout_s == 30.0
    assert StreamAdapterConfig.model_validate_json(cfg.model_dump_json()) == cfg


@pytest.mark.parametrize(
    "kwargs",
    [
        {"cadence_s": 0},
        {"skew_tolerance_s": -1},
        {"speed_factor": 0},
        {"backpressure_timeout_s": 0},
    ],
)
def test_stream_adapter_config_constraints(kwargs):
    with pytest.raises(ValidationError):
        StreamAdapterConfig(**kwargs)


def test_stream_adapter_error_inherits_batch_adapter_error():
    assert isinstance(StreamAdapterError("bad window"), BatchAdapterError)


def test_stream_adapter_iter_yields_ordered_window_tuples():
    windows = list(
        _stream(
            pd.DataFrame(
                {
                    "id": ["B", "A"],
                    "event_ts": [
                        "2025-06-01T00:01:00+00:00",
                        "2025-06-01T00:00:00+00:00",
                    ],
                }
            )
        )
    )
    assert [window_start for window_start, _ in windows] == sorted(
        window_start for window_start, _ in windows
    )
    assert isinstance(windows[0][0], datetime)
    assert windows[0][0].tzinfo == timezone.utc
    assert isinstance(windows[0][1], dict)


def test_single_minute_source_empty_interval_and_static_table_contract():
    windows = list(
        _stream(
            pd.DataFrame(
                {
                    "id": ["A", "B"],
                    "event_ts": [
                        "2025-06-01T00:00:00+00:00",
                        "2025-06-01T00:02:00+00:00",
                    ],
                }
            ),
            pd.DataFrame({"staff_id": ["S2", "S1"], "role": ["nurse", "physician"]}),
        )
    )

    assert windows[0][1]["events"]["id"].tolist() == ["A"]
    assert set(windows[0][1]) == {"events", "staff"}
    assert windows[0][1]["staff"]["staff_id"].tolist() == ["S1", "S2"]
    assert windows[1][1] == {}
    assert set(windows[2][1]) == {"events", "staff"}
    assert windows[2][1]["staff"].empty
