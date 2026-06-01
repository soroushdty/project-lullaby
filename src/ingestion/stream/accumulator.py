"""Helpers for accumulating stream windows into canonical stores."""

from __future__ import annotations

import pandas as pd

from src.ingestion.stream.adapter import _dedup_and_sort
from src.schemas.base import SchemaContract, TableContract


class StreamAccumulator:
    """Consume stream windows and merge them with batch-compatible semantics."""

    @staticmethod
    def accumulate(adapter, schema: SchemaContract) -> dict[str, pd.DataFrame]:
        pieces: dict[str, list[pd.DataFrame]] = {
            table: [] for table in schema.table_names()
        }

        for _, frames in adapter:
            for table in schema.table_names():
                if table in frames:
                    pieces[table].append(frames[table])

        accumulated: dict[str, pd.DataFrame] = {}
        for table in schema.table_names():
            contract = schema.table_contract(table)
            if pieces[table]:
                merged = pd.concat(pieces[table], ignore_index=True)
            else:
                merged = _empty_frame(contract)
            accumulated[table] = _dedup_and_sort(merged, contract)
        return accumulated


def _empty_frame(contract: TableContract) -> pd.DataFrame:
    columns = list(dict.fromkeys(contract.required_columns + contract.optional_columns))
    return pd.DataFrame(columns=columns)
