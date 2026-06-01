"""Unit tests for streaming adapter edge cases and accumulation."""

from __future__ import annotations

import logging

import pandas as pd
import pandera as pa
import pytest

from src.ingestion.adapters.base import AdapterConfig, BatchAdapter
from src.ingestion.stream import (
    StreamAccumulator,
    StreamAdapter,
    StreamAdapterConfig,
    StreamAdapterError,
)
from src.schemas.base import SchemaContract, SchemaTableMissingError, TableContract


class TimestampedTestSchema(SchemaContract):
    @property
    def name(self) -> str:
        return "timestamped-test"

    @property
    def version(self) -> str:
        return "0.0.1"

    def table_names(self) -> list[str]:
        return ["events", "staff"]

    def table_contract(self, table_name: str) -> TableContract:
        if table_name == "events":
            return TableContract(
                table_name="events",
                required_columns=["id", "event_ts", "value"],
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
                    "value": pa.Column(int),
                }
            )
        if table_name == "staff":
            return pa.DataFrameSchema(
                {"staff_id": pa.Column(str), "role": pa.Column(str)}
            )
        raise SchemaTableMissingError(table_name)

    def data_dictionary(self, table_name: str) -> dict[str, dict]:
        return {}


class InMemoryAdapter(BatchAdapter[AdapterConfig]):
    def __init__(self, frames: dict[str, pd.DataFrame]) -> None:
        self._frames = frames

    def load(self, config: AdapterConfig) -> dict[str, pd.DataFrame]:
        return {table: df.copy() for table, df in self._frames.items()}


def _adapter(
    frames: dict[str, pd.DataFrame],
    config: StreamAdapterConfig | None = None,
) -> StreamAdapter[AdapterConfig]:
    return StreamAdapter(
        batch_adapter=InMemoryAdapter(frames),
        source_config=AdapterConfig(),
        schema=TimestampedTestSchema(),
        config=config or StreamAdapterConfig(cadence_s=60, skew_tolerance_s=300),
    )


def _events(rows: list[tuple[str, str, int]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["id", "event_ts", "value"])


def _staff(rows: list[tuple[str, str]] | None = None) -> pd.DataFrame:
    return pd.DataFrame(rows or [], columns=["staff_id", "role"])


def test_deterministic_replay_and_speed_factor_does_not_change_output():
    frames = {
        "events": _events(
            [
                ("A", "2025-06-01T00:00:00+00:00", 1),
                ("B", "2025-06-01T00:01:00+00:00", 2),
            ]
        ),
        "staff": _staff([("S2", "nurse"), ("S1", "physician")]),
    }
    first = list(_adapter(frames, StreamAdapterConfig(cadence_s=60, speed_factor=1.0)))
    second = list(_adapter(frames, StreamAdapterConfig(cadence_s=60, speed_factor=100.0)))

    assert [w for w, _ in first] == [w for w, _ in second]
    for (_, left), (_, right) in zip(first, second, strict=True):
        assert set(left.keys()) == set(right.keys())
        for table in left:
            pd.testing.assert_frame_equal(left[table], right[table])


def test_per_window_duplicate_primary_key_last_write_wins():
    windows = list(
        _adapter(
            {
                "events": _events(
                    [
                        ("A", "2025-06-01T00:00:10+00:00", 1),
                        ("A", "2025-06-01T00:00:20+00:00", 9),
                    ]
                ),
                "staff": _staff(),
            }
        )
    )
    frame = windows[0][1]["events"]
    assert len(frame) == 1
    assert frame["value"].iloc[0] == 9


def test_timestamp_and_static_primary_key_ordering():
    windows = list(
        _adapter(
            {
                "events": _events(
                    [
                        ("B", "2025-06-01T00:00:20+00:00", 2),
                        ("A", "2025-06-01T00:00:10+00:00", 1),
                    ]
                ),
                "staff": _staff([("S2", "nurse"), ("S1", "physician")]),
            }
        )
    )

    assert windows[0][1]["events"]["id"].tolist() == ["A", "B"]
    assert windows[0][1]["staff"]["staff_id"].tolist() == ["S1", "S2"]


def test_accumulator_cross_window_duplicate_primary_key_collapse():
    accumulated = StreamAccumulator.accumulate(
        _adapter(
            {
                "events": _events(
                    [
                        ("A", "2025-06-01T00:00:00+00:00", 1),
                        ("A", "2025-06-01T00:01:00+00:00", 2),
                    ]
                ),
                "staff": _staff(),
            }
        ),
        TimestampedTestSchema(),
    )
    assert len(accumulated["events"]) == 1
    assert accumulated["events"]["value"].iloc[0] == 2


def test_within_tolerance_late_record_accepted_into_target_window():
    events = _events(
        [
            ("B", "2025-06-01T00:05:00+00:00", 2),
            ("A", "2025-06-01T00:03:00+00:00", 1),
        ]
    )
    events["_stream_arrival_order"] = [0, 1]
    windows = list(
        _adapter(
            {
                "events": events,
                "staff": _staff(),
            },
            StreamAdapterConfig(cadence_s=60, skew_tolerance_s=300),
        )
    )
    rows_by_window = {
        window_start.minute: frames["events"]["id"].tolist()
        for window_start, frames in windows
        if frames
    }
    assert "A" in rows_by_window[3]


def test_beyond_tolerance_late_record_excluded_and_logged(caplog):
    events = _events(
        [
            ("B", "2025-06-01T00:10:00+00:00", 2),
            ("A", "2025-06-01T00:00:00+00:00", 1),
        ]
    )
    events["_stream_arrival_order"] = [0, 1]
    adapter = _adapter(
        {
            "events": events,
            "staff": _staff(),
        },
        StreamAdapterConfig(cadence_s=60, skew_tolerance_s=300),
    )

    with caplog.at_level(logging.WARNING, logger="src.ingestion.stream.adapter"):
        accumulated = StreamAccumulator.accumulate(adapter, TimestampedTestSchema())

    assert adapter.late_arrival_count == 1
    assert "A" not in accumulated["events"]["id"].tolist()
    assert any("LateArrivalWarning" in record.message for record in caplog.records)


def test_future_timestamp_waits_until_target_window():
    windows = list(
        _adapter(
            {
                "events": _events(
                    [
                        ("A", "2025-06-01T00:00:00+00:00", 1),
                        ("B", "2025-06-01T00:02:00+00:00", 2),
                    ]
                ),
                "staff": _staff(),
            }
        )
    )
    assert windows[0][1]["events"]["id"].tolist() == ["A"]
    assert windows[1][1] == {}
    assert windows[2][1]["events"]["id"].tolist() == ["B"]


def test_non_empty_pending_buffer_raises_at_end_of_stream():
    events = _events(
        [
            ("A", "2025-06-01T00:00:00+00:00", 1),
            ("B", "2025-06-01T00:10:00+00:00", 2),
        ]
    )
    events["_stream_pending"] = [False, True]

    with pytest.raises(StreamAdapterError, match="pending buffer.*ts range"):
        list(_adapter({"events": events, "staff": _staff()}))


def test_pending_buffer_parses_string_and_numeric_boolean_tokens():
    events = _events(
        [
            ("A", "2025-06-01T00:00:00+00:00", 1),
            ("B", "2025-06-01T00:01:00+00:00", 2),
            ("C", "2025-06-01T00:02:00+00:00", 3),
            ("D", "2025-06-01T00:03:00+00:00", 4),
            ("E", "2025-06-01T00:04:00+00:00", 5),
        ]
    )
    events["_stream_pending"] = ["False", "0", 0, None, "true"]

    with pytest.raises(StreamAdapterError, match="1 undeliverable"):
        windows = list(_adapter({"events": events, "staff": _staff()}))


def test_pending_buffer_invalid_token_fails_loudly():
    events = _events([("A", "2025-06-01T00:00:00+00:00", 1)])
    events["_stream_pending"] = ["later-ish"]

    with pytest.raises(StreamAdapterError, match="Invalid boolean token.*_stream_pending"):
        list(_adapter({"events": events, "staff": _staff()}))


def test_static_table_emitted_once_in_first_window():
    windows = list(
        _adapter(
            {
                "events": _events(
                    [
                        ("A", "2025-06-01T00:00:00+00:00", 1),
                        ("B", "2025-06-01T00:01:00+00:00", 2),
                    ]
                ),
                "staff": _staff([("S1", "nurse")]),
            }
        )
    )
    assert len(windows[0][1]["staff"]) == 1
    assert windows[1][1]["staff"].empty


def test_null_timestamp_raises_before_any_yield():
    iterator = iter(
        _adapter(
            {
                "events": pd.DataFrame(
                    {"id": ["A"], "event_ts": [None], "value": [1]}
                ),
                "staff": _staff(),
            }
        )
    )
    with pytest.raises(StreamAdapterError, match="Null timestamp"):
        next(iterator)


def test_unparseable_timestamp_raises_before_any_yield():
    iterator = iter(
        _adapter(
            {
                "events": _events([("A", "not-a-date", 1)]),
                "staff": _staff(),
            }
        )
    )
    with pytest.raises(StreamAdapterError, match="Null timestamp"):
        next(iterator)


def test_schema_invalid_window_raises_no_partial_output():
    iterator = iter(
        _adapter(
            {
                "events": pd.DataFrame(
                    {"id": ["A"], "event_ts": ["2025-06-01T00:00:00+00:00"]}
                ),
                "staff": _staff(),
            }
        )
    )
    with pytest.raises(StreamAdapterError, match="Schema-invalid"):
        next(iterator)


def test_backpressure_below_timeout_continues_and_above_timeout_fails(monkeypatch):
    adapter = _adapter(
        {
            "events": _events(
                [
                    ("A", "2025-06-01T00:00:00+00:00", 1),
                    ("B", "2025-06-01T00:01:00+00:00", 2),
                    ("C", "2025-06-01T00:02:00+00:00", 3),
                ]
            ),
            "staff": _staff(),
        },
        StreamAdapterConfig(cadence_s=60, backpressure_timeout_s=5.0),
    )
    ticks = iter([0.0, 1.0, 2.0, 8.5])
    monkeypatch.setattr("src.ingestion.stream.adapter.time.monotonic", lambda: next(ticks))

    iterator = iter(adapter)
    first_start, first_frames = next(iterator)
    second_start, second_frames = next(iterator)

    assert first_frames["events"]["id"].tolist() == ["A"]
    assert second_frames["events"]["id"].tolist() == ["B"]
    assert second_start > first_start
    with pytest.raises(StreamAdapterError, match="Backpressure timeout"):
        next(iterator)


def test_stream_adapter_error_message_does_not_include_secret_value():
    exc = StreamAdapterError("Schema-invalid record in table 'events'")
    assert "hunter2" not in str(exc)
    assert "secret" not in str(exc)
