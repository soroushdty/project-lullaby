from __future__ import annotations

import pandas as pd

from src.schemas.base import SchemaContract
from src.validation.engine import ValidationError


class IngestionState:
    RAW_LOADED = "raw_loaded"
    NORMALIZED = "normalized_to_canonical_columns"
    VALIDATED = "schema_validated"
    REJECTED = "schema_rejected"
    ACCEPTED = "accepted_for_downstream"


def run(
    schema: SchemaContract,
    input_dir: str,
    run_id: str = "",
) -> dict:
    """Execute the full ingestion pipeline for the given input directory.

    States: raw_loaded -> normalized -> schema_validated/schema_rejected -> accepted
    Returns a validation report dict on success; raises ValidationError on rejection.
    """
    from src.ingestion.adapters.csv_adapter import load
    from src.validation import engine

    # raw_loaded
    all_frames = load(input_dir)

    # normalized_to_canonical_columns
    frames: dict[str, pd.DataFrame] = {}
    for table_name in schema.table_names():
        if table_name not in all_frames:
            raise ValueError(
                f"Required table '{table_name}' not found in '{input_dir}'"
            )
        df = all_frames[table_name].copy()
        tc = schema.table_contract(table_name)
        if tc.timestamp_column:
            df = _normalize_timestamp(df, tc.timestamp_column, table_name)
        frames[table_name] = df

    # schema_validated / schema_rejected -> accepted_for_downstream
    return engine.validate(schema, frames, run_id=run_id)


def _normalize_timestamp(
    df: pd.DataFrame, col: str, table_name: str
) -> pd.DataFrame:
    """Parse a timestamp column and enforce UTC. Rejects naive timestamps."""
    if col not in df.columns:
        return df
    parsed = pd.to_datetime(df[col])
    if parsed.dt.tz is None:
        raise ValidationError(
            table=table_name,
            cause=ValueError(
                f"Column '{col}' in table '{table_name}' is missing timezone info (FR-011)"
            ),
        )
    df = df.copy()
    df[col] = parsed.dt.tz_convert("UTC")
    return df
