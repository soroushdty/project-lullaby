from __future__ import annotations

import pandas as pd
import pandera as pa

from src.schemas.base import SchemaContract


class ValidationError(Exception):
    def __init__(self, table: str, cause: Exception) -> None:
        self.table = table
        self.cause = cause
        super().__init__(f"Validation failed for table '{table}': {cause}")


def validate(
    schema: SchemaContract,
    frames: dict[str, pd.DataFrame],
    run_id: str = "",
) -> dict:
    """Validate each frame against its Pandera schema.

    Whole-table rejection policy: the first table that fails raises ValidationError.
    Returns a report dict on full success.
    """
    report: dict = {"run_id": run_id, "status": "pass", "tables": {}}
    for table_name, df in frames.items():
        pandera_schema = schema.pandera_schema(table_name)
        try:
            pandera_schema.validate(df)
        except (pa.errors.SchemaError, pa.errors.SchemaErrors) as exc:
            raise ValidationError(table=table_name, cause=exc) from exc
        report["tables"][table_name] = {"status": "pass", "row_count": len(df)}
    return report
