"""MySQL batch ingestion adapter via SQLAlchemy (FR-007)."""

from __future__ import annotations

import logging

import pandas as pd
from pydantic import SecretStr

from src.ingestion.adapters.base import (
    AdapterConfig,
    BatchAdapter,
    ConnectorError,
    SchemaMismatchError,
)

logger = logging.getLogger(__name__)

_CANONICAL_TABLES = [
    "participants",
    "daily_vitals",
    "alerts",
    "clinical_outcomes",
    "staff_contacts",
]


class MySQLAdapterConfig(AdapterConfig):
    connection_string: SecretStr
    table_names: list[str] | None = None


class MySQLAdapter(BatchAdapter[MySQLAdapterConfig]):
    """Query canonical tables from a MySQL database via SQLAlchemy."""

    def load(self, config: MySQLAdapterConfig) -> dict[str, pd.DataFrame]:
        self._log_start()
        try:
            from sqlalchemy import create_engine, inspect, text
            from sqlalchemy.exc import OperationalError, SQLAlchemyError

            conn_str = config.connection_string.get_secret_value()
            try:
                engine = create_engine(conn_str)
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
            except OperationalError as exc:
                raise ConnectorError(adapter=self._name, cause=exc, attempts=1) from exc

            tables = config.table_names or _CANONICAL_TABLES
            frames: dict[str, pd.DataFrame] = {}
            with engine.connect() as conn:
                inspector = inspect(engine)
                for table in tables:
                    db_columns = {c["name"] for c in inspector.get_columns(table)}
                    df = pd.read_sql_table(table, conn)
                    frames[table] = df

        except (ConnectorError, SchemaMismatchError):
            raise
        except Exception as exc:
            self._log_error(exc)
            raise ConnectorError(adapter=self._name, cause=exc, attempts=1) from exc

        self._log_done(frames)
        return frames
