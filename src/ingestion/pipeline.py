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
    aliases = schema.table_aliases()
    for table_name in schema.table_names():
        # Search for exact match or an alias that points to this canonical name
        found_key = None
        if table_name in all_frames:
            found_key = table_name
        else:
            for alias, canonical in aliases.items():
                if canonical == table_name and alias in all_frames:
                    found_key = alias
                    break

        if found_key is None:
            raise ValueError(
                f"Required table '{table_name}' not found in '{input_dir}'"
            )
        df = all_frames[found_key].copy()
        tc = schema.table_contract(table_name)
        
        # Apply column aliases
        for alias, canonical in tc.column_aliases.items():
            if alias in df.columns and canonical not in df.columns:
                df[canonical] = df[alias]
                
        if tc.timestamp_column:
            df = _normalize_timestamp(df, tc.timestamp_column, table_name)
        frames[table_name] = df

    # schema_validated / schema_rejected -> accepted_for_downstream
    return engine.validate(schema, frames, run_id=run_id)


def _normalize_timestamp(
    df: pd.DataFrame, col: str, table_name: str
) -> pd.DataFrame:
    """Parse a timestamp column and enforce UTC. Localizes naive timestamps."""
    if col not in df.columns:
        return df
    parsed = pd.to_datetime(df[col])
    if parsed.dt.tz is None:
        # Localize naive to UTC instead of raising ValidationError
        parsed = parsed.dt.tz_localize("UTC")
        
    df = df.copy()
    df[col] = parsed.dt.tz_convert("UTC")
    return df
