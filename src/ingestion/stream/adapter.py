"""Reference synchronous stream adapter for canonical ingestion windows."""

from __future__ import annotations

import logging
import math
import time
from collections.abc import Iterator
from datetime import datetime, timezone
from typing import Generic, TypeVar

import pandas as pd
from pydantic import Field

from src.ingestion.adapters.base import AdapterConfig, BatchAdapter
from src.ingestion.stream.errors import StreamAdapterError
from src.schemas.base import SchemaContract, TableContract
from src.validation import engine as validation_engine
from src.validation.semantics import DomainBooleanParsePolicy, parse_domain_boolean_series

logger = logging.getLogger(__name__)

C = TypeVar("C", bound=AdapterConfig)
_ARRIVAL_ORDER_COLUMN = "_stream_arrival_order"
_PENDING_COLUMN = "_stream_pending"


class StreamAdapterConfig(AdapterConfig):
    cadence_s: int = Field(default=60, ge=1)
    skew_tolerance_s: int = Field(default=300, ge=0)
    speed_factor: float = Field(default=1.0, gt=0)
    backpressure_timeout_s: float = Field(default=30.0, gt=0)


class StreamAdapter(Generic[C]):
    """Replay a BatchAdapter source as deterministic canonical windows."""

    def __init__(
        self,
        batch_adapter: BatchAdapter[C],
        source_config: C,
        schema: SchemaContract,
        config: StreamAdapterConfig | None = None,
    ) -> None:
        self._batch_adapter = batch_adapter
        self._source_config = source_config
        self._schema = schema
        self._config = config or StreamAdapterConfig()
        self.late_arrival_count = 0

    def __iter__(self) -> Iterator[tuple[datetime, dict[str, pd.DataFrame]]]:
        source_frames = self._batch_adapter.load(self._source_config)
        self._pending_timestamps: list[pd.Timestamp] = []
        prepared = self._prepare_source_frames(source_frames)
        window_index = self._window_index(prepared)
        timeline = self._build_timeline(prepared, window_index)

        for index, window_start in enumerate(timeline):
            frames = self._window_frames(
                prepared,
                window_index,
                window_start,
                is_first=index == 0,
            )
            if frames:
                self._validate_window(frames)

            t_yield = time.monotonic()
            yield window_start, frames
            elapsed = time.monotonic() - t_yield
            if elapsed > self._config.backpressure_timeout_s:
                raise StreamAdapterError(
                    "Backpressure timeout: consumer held window "
                    f"{window_start.isoformat()} for {elapsed:.1f}s "
                    f"(limit={self._config.backpressure_timeout_s}s)"
                )

        self._raise_on_pending_buffer()

    def _prepare_source_frames(
        self,
        source_frames: dict[str, pd.DataFrame],
    ) -> dict[str, pd.DataFrame]:
        prepared: dict[str, pd.DataFrame] = {}
        for table in self._schema.table_names():
            contract = self._schema.table_contract(table)
            df = source_frames.get(table, self._empty_frame(contract)).copy()
            self._raise_on_missing_required(table, contract, df)
            if contract.timestamp_column:
                df = self._parse_timestamp_column(table, contract, df)
                df = self._extract_pending_records(table, contract, df)
                df = self._exclude_late_arrivals(table, contract, df)
            prepared[table] = df.reset_index(drop=True)
        return prepared

    def _raise_on_missing_required(
        self,
        table: str,
        contract: TableContract,
        df: pd.DataFrame,
    ) -> None:
        missing = [col for col in contract.required_columns if col not in df.columns]
        if missing:
            raise StreamAdapterError(
                f"Schema-invalid record in table '{table}': missing required columns {missing}"
            )

    def _parse_timestamp_column(
        self,
        table: str,
        contract: TableContract,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        col = contract.timestamp_column
        parsed = pd.to_datetime(df[col], utc=True, errors="coerce")
        bad_count = int(parsed.isna().sum())
        if bad_count:
            raise StreamAdapterError(
                f"Null timestamp in table '{table}': {bad_count} record(s) "
                f"with NaT timestamp_column='{col}'"
            )
        result = df.copy()
        result[col] = parsed
        return result

    def _extract_pending_records(
        self,
        table: str,
        contract: TableContract,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        if _PENDING_COLUMN not in df.columns:
            return df

        parsed_pending = parse_domain_boolean_series(
            df[_PENDING_COLUMN],
            DomainBooleanParsePolicy(role="_stream_pending", required=False),
            source_column=_PENDING_COLUMN,
        )
        if parsed_pending.warnings:
            raise StreamAdapterError(
                f"Schema-invalid pending flag in table '{table}': "
                + "; ".join(parsed_pending.warnings)
            )
        pending_mask = parsed_pending.true_mask
        if pending_mask.any():
            self._pending_timestamps.extend(
                pd.Timestamp(ts) for ts in df.loc[pending_mask, contract.timestamp_column]
            )

        return df.loc[~pending_mask].drop(columns=[_PENDING_COLUMN]).copy()

    def _exclude_late_arrivals(
        self,
        table: str,
        contract: TableContract,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        if df.empty:
            return df

        ts_col = contract.timestamp_column
        order_col = _ARRIVAL_ORDER_COLUMN if _ARRIVAL_ORDER_COLUMN in df.columns else ts_col
        ordered = df.sort_values(order_col, kind="mergesort")
        keep_indexes: list[int] = []
        stream_clock: pd.Timestamp | None = None
        for idx, ts in ordered[ts_col].items():
            timestamp = pd.Timestamp(ts)
            if stream_clock is None:
                stream_clock = timestamp

            skew_s = (stream_clock - timestamp).total_seconds()
            if skew_s > self._config.skew_tolerance_s:
                self.late_arrival_count += 1
                logger.warning(
                    "LateArrivalWarning adapter=%s table=%s record_ts=%s skew_s=%.3f",
                    type(self).__name__,
                    table,
                    timestamp.isoformat(),
                    skew_s,
                )
                continue

            keep_indexes.append(idx)
            if timestamp > stream_clock:
                stream_clock = timestamp

        result = df.loc[keep_indexes].copy()
        if _ARRIVAL_ORDER_COLUMN in result.columns:
            result = result.drop(columns=[_ARRIVAL_ORDER_COLUMN])
        return result

    def _raise_on_pending_buffer(self) -> None:
        if not self._pending_timestamps:
            return
        min_ts = min(self._pending_timestamps).isoformat()
        max_ts = max(self._pending_timestamps).isoformat()
        raise StreamAdapterError(
            "Stream exhausted with "
            f"{len(self._pending_timestamps)} undeliverable future-timestamp "
            f"record(s) in pending buffer; ts range=[{min_ts}, {max_ts}]"
        )

    def _window_index(
        self,
        frames: dict[str, pd.DataFrame],
    ) -> dict[str, dict[datetime, pd.DataFrame]]:
        index: dict[str, dict[datetime, pd.DataFrame]] = {}
        for table in self._schema.table_names():
            contract = self._schema.table_contract(table)
            if not contract.timestamp_column:
                continue
            df = frames[table]
            if df.empty:
                index[table] = {}
                continue

            assigned = df[contract.timestamp_column].map(
                lambda ts: _epoch_floor(ts, self._config.cadence_s)
            )
            index[table] = {
                window_start: df.loc[assigned == window_start].copy()
                for window_start in sorted(set(assigned))
            }
        return index

    def _build_timeline(
        self,
        frames: dict[str, pd.DataFrame],
        window_index: dict[str, dict[datetime, pd.DataFrame]],
    ) -> list[datetime]:
        starts: list[datetime] = []
        has_static_rows = False

        for table in self._schema.table_names():
            contract = self._schema.table_contract(table)
            df = frames[table]
            if not contract.timestamp_column:
                has_static_rows = has_static_rows or not df.empty
                continue
            starts.extend(window_index.get(table, {}).keys())

        if not starts:
            if has_static_rows:
                return [datetime.fromtimestamp(0, tz=timezone.utc)]
            return []

        min_start = min(starts)
        max_start = max(starts)
        timeline: list[datetime] = []
        current = min_start
        while current <= max_start:
            timeline.append(current)
            current = datetime.fromtimestamp(
                current.timestamp() + self._config.cadence_s,
                tz=timezone.utc,
            )
        return timeline

    def _window_frames(
        self,
        frames: dict[str, pd.DataFrame],
        window_index: dict[str, dict[datetime, pd.DataFrame]],
        window_start: datetime,
        is_first: bool,
    ) -> dict[str, pd.DataFrame]:
        window_frames: dict[str, pd.DataFrame] = {}
        has_rows = False

        for table in self._schema.table_names():
            contract = self._schema.table_contract(table)
            df = frames[table]

            if not contract.timestamp_column:
                in_window = df if is_first else df.head(0)
            else:
                in_window = window_index.get(table, {}).get(window_start, df.head(0))

            in_window = _dedup_and_sort(in_window, contract)
            has_rows = has_rows or not in_window.empty
            window_frames[table] = in_window

        if not has_rows:
            return {}
        return window_frames

    def _validate_window(self, frames: dict[str, pd.DataFrame]) -> None:
        non_empty_frames = {
            table: df for table, df in frames.items() if not df.empty
        }
        if not non_empty_frames:
            return
        try:
            validation_engine.validate(self._schema, non_empty_frames)
        except validation_engine.ValidationError as exc:
            raise StreamAdapterError(
                f"Schema-invalid record in table '{exc.table}': {exc.cause}"
            ) from exc

    def _empty_frame(self, contract: TableContract) -> pd.DataFrame:
        columns = list(dict.fromkeys(contract.required_columns + contract.optional_columns))
        return pd.DataFrame(columns=columns)


def _epoch_floor(ts, cadence_s: int) -> datetime:
    timestamp = pd.Timestamp(ts)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize(timezone.utc)
    else:
        timestamp = timestamp.tz_convert(timezone.utc)
    floored = math.floor(timestamp.timestamp() / cadence_s) * cadence_s
    return datetime.fromtimestamp(floored, tz=timezone.utc)


def _dedup_and_sort(df: pd.DataFrame, contract: TableContract) -> pd.DataFrame:
    result = df.copy()
    pk = [col for col in contract.primary_key if col in result.columns]
    if pk:
        result = result.drop_duplicates(subset=pk, keep="last")

    if contract.timestamp_column and contract.timestamp_column in result.columns:
        result = result.sort_values(contract.timestamp_column)
    elif pk:
        result = result.sort_values(pk)

    return result.reset_index(drop=True)
