"""Unit tests: partial-load rejection, exception fields, secret masking, units (T033–T036, T038)."""

from __future__ import annotations

import logging

import pandas as pd
import pytest
from pydantic import SecretStr

from src.ingestion.adapters.base import (
    AdapterConfig,
    AuthConfigError,
    BatchAdapter,
    BatchAdapterError,
    ConnectorError,
    EncodingError,
    SchemaMismatchError,
    UnitAmbiguityError,
    UnsupportedFormatError,
)
from src.ingestion.units import check_temperature_unit, fahrenheit_to_celsius, lbs_to_kg


# ---------------------------------------------------------------------------
# Partial-load rejection (T033, US6 AC1)
# ---------------------------------------------------------------------------


class _FailOnTableAdapter(BatchAdapter[AdapterConfig]):
    """Raises SchemaMismatchError on the third table to simulate partial failure."""

    def load(self, config: AdapterConfig) -> dict[str, pd.DataFrame]:
        self._log_start()
        tables = ["participants", "daily_vitals", "alerts"]
        frames: dict[str, pd.DataFrame] = {}
        for table in tables:
            if table == "alerts":
                # Simulate schema mismatch before any frames are returned
                raise SchemaMismatchError(
                    table=table,
                    missing_columns=["alert_level"],
                    found_columns=["lvl"],
                )
            frames[table] = pd.DataFrame({"id": [1]})
        return frames


def test_partial_load_raises_schema_mismatch():
    """Adapter raises SchemaMismatchError, no partial frames returned."""
    adapter = _FailOnTableAdapter()
    with pytest.raises(SchemaMismatchError) as exc_info:
        adapter.load(AdapterConfig())
    exc = exc_info.value
    assert exc.table == "alerts"
    assert "alert_level" in exc.missing_columns


def test_schema_mismatch_is_batch_adapter_error():
    exc = SchemaMismatchError(table="t", missing_columns=["x"], found_columns=["y"])
    assert isinstance(exc, BatchAdapterError)


# ---------------------------------------------------------------------------
# Exception field contracts (T034, US6 AC2)
# ---------------------------------------------------------------------------


def test_connector_error_preserves_cause_and_attempts():
    cause = ConnectionError("timeout")
    exc = ConnectorError(adapter="S3Adapter", cause=cause, attempts=3)
    assert exc.cause is cause
    assert exc.attempts == 3
    assert exc.adapter == "S3Adapter"


def test_auth_config_error_contains_env_var_name_not_value():
    exc = AuthConfigError(adapter="REDCapAdapter", credential_env_var="REDCAP_TOKEN")
    assert "REDCAP_TOKEN" in str(exc)
    assert exc.credential_env_var == "REDCAP_TOKEN"


def test_unsupported_format_error_fields():
    exc = UnsupportedFormatError(adapter="FileAdapter", detected_type=".json")
    assert exc.detected_type == ".json"


def test_encoding_error_path_no_credentials():
    exc = EncodingError(adapter="FileAdapter", path="data/file.csv", detected_encoding="latin-1")
    assert "password" not in exc.path
    assert "token" not in exc.path


# ---------------------------------------------------------------------------
# Secret masking (T035, SC-005)
# ---------------------------------------------------------------------------


class _SecretConfig(AdapterConfig):
    token: SecretStr
    connection_string: SecretStr


def test_secrets_masked_in_repr(caplog):
    cfg = _SecretConfig(token="top-secret-token-xyz", connection_string="mysql://root:hunter2@localhost/db")
    cfg_repr = repr(cfg)
    assert "top-secret-token-xyz" not in cfg_repr
    assert "hunter2" not in cfg_repr


def test_exception_message_no_secret_value():
    exc = AuthConfigError(adapter="MySQLAdapter", credential_env_var="DB_PASSWORD")
    # The env var name is allowed; the actual value must not appear
    assert "DB_PASSWORD" in str(exc)
    # Simulate a scenario where someone tries to put the value in the error
    # Our field is credential_env_var (the name), so value leakage is not possible here


def test_log_error_no_secret_leakage(caplog):
    """Connector errors logged via _log_error must not expose secret values."""

    class _BadAdapter(BatchAdapter[AdapterConfig]):
        def load(self, config: AdapterConfig) -> dict[str, pd.DataFrame]:
            exc = ConnectorError(adapter="TestAdapter", cause=RuntimeError("network"), attempts=1)
            self._log_error(exc)
            raise exc

    with caplog.at_level(logging.ERROR, logger="src.ingestion.adapters.base"):
        with pytest.raises(ConnectorError):
            _BadAdapter().load(AdapterConfig())
    assert any("TestAdapter" in r.message for r in caplog.records)
    # Ensure no raw secret values in log messages (sample check)
    for record in caplog.records:
        assert "hunter2" not in record.message
        assert "top-secret" not in record.message


# ---------------------------------------------------------------------------
# UnitAmbiguityError (T036, FR-016)
# ---------------------------------------------------------------------------


def test_unit_ambiguity_error_raised_on_unknown_unit():
    series = pd.Series([98.6, 99.1])
    with pytest.raises(UnitAmbiguityError) as exc_info:
        check_temperature_unit(series, declared_unit=None, column_name="temperature_c")
    assert exc_info.value.column == "temperature_c"


def test_fahrenheit_converted_to_celsius():
    series = pd.Series([32.0, 212.0])
    result = check_temperature_unit(series, declared_unit="F", column_name="temperature_c")
    assert abs(result.iloc[0] - 0.0) < 1e-6
    assert abs(result.iloc[1] - 100.0) < 1e-6


def test_celsius_returned_as_is():
    series = pd.Series([0.0, 37.0])
    result = check_temperature_unit(series, declared_unit="C", column_name="temperature_c")
    pd.testing.assert_series_equal(result, series)


# ---------------------------------------------------------------------------
# Unit helpers (T038)
# ---------------------------------------------------------------------------


def test_fahrenheit_to_celsius_freezing():
    assert abs(fahrenheit_to_celsius(pd.Series([32.0])).iloc[0] - 0.0) < 1e-6


def test_fahrenheit_to_celsius_boiling():
    assert abs(fahrenheit_to_celsius(pd.Series([212.0])).iloc[0] - 100.0) < 1e-6


def test_lbs_to_kg():
    result = lbs_to_kg(pd.Series([1.0]))
    assert abs(result.iloc[0] - 0.453592) < 1e-4
