"""Contract tests: BatchAdapter ABC, exception fields, SecretStr masking (T011)."""

from __future__ import annotations

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
from src.ingestion.adapters.stubs import (
    DropboxAdapter,
    DropboxAdapterConfig,
    GenericFallbackAdapter,
    GenericFallbackAdapterConfig,
    OneDriveAdapter,
    OneDriveAdapterConfig,
)


# ---------------------------------------------------------------------------
# ABC contract: all stubs are BatchAdapter subclasses and raise NotImplementedError
# ---------------------------------------------------------------------------


class _ConcreteConfig(AdapterConfig):
    pass


class _ConcreteAdapter(BatchAdapter[_ConcreteConfig]):
    def load(self, config: _ConcreteConfig):
        return {}


def test_concrete_adapter_is_batch_adapter():
    assert isinstance(_ConcreteAdapter(), BatchAdapter)


@pytest.mark.parametrize(
    "adapter_cls,config",
    [
        (DropboxAdapter, DropboxAdapterConfig(share_url="https://dropbox.com/x")),
        (OneDriveAdapter, OneDriveAdapterConfig(share_url="https://1drv.ms/x")),
        (GenericFallbackAdapter, GenericFallbackAdapterConfig()),
    ],
)
def test_stubs_raise_not_implemented(adapter_cls, config):
    with pytest.raises(NotImplementedError, match="not implemented"):
        adapter_cls().load(config)


def test_stubs_are_batch_adapter_subclasses():
    for cls in (DropboxAdapter, OneDriveAdapter, GenericFallbackAdapter):
        assert issubclass(cls, BatchAdapter)


# ---------------------------------------------------------------------------
# Exception field contracts
# ---------------------------------------------------------------------------


def test_schema_mismatch_error_fields():
    exc = SchemaMismatchError(
        table="participants",
        missing_columns=["participant_id"],
        found_columns=["pid"],
    )
    assert exc.table == "participants"
    assert exc.missing_columns == ["participant_id"]
    assert exc.found_columns == ["pid"]
    assert isinstance(exc, BatchAdapterError)


def test_connector_error_fields():
    cause = RuntimeError("timeout")
    exc = ConnectorError(adapter="S3Adapter", cause=cause, attempts=3)
    assert exc.adapter == "S3Adapter"
    assert exc.cause is cause
    assert exc.attempts == 3
    assert isinstance(exc, BatchAdapterError)


def test_auth_config_error_fields():
    exc = AuthConfigError(adapter="REDCapAdapter", credential_env_var="REDCAP_TOKEN")
    assert exc.adapter == "REDCapAdapter"
    assert exc.credential_env_var == "REDCAP_TOKEN"
    assert isinstance(exc, BatchAdapterError)


def test_unsupported_format_error_fields():
    exc = UnsupportedFormatError(adapter="FileAdapter", detected_type=".json")
    assert exc.adapter == "FileAdapter"
    assert exc.detected_type == ".json"
    assert isinstance(exc, BatchAdapterError)


def test_encoding_error_fields():
    exc = EncodingError(adapter="FileAdapter", path="data/file.csv", detected_encoding="latin-1")
    assert exc.adapter == "FileAdapter"
    assert exc.path == "data/file.csv"
    assert exc.detected_encoding == "latin-1"
    assert isinstance(exc, BatchAdapterError)


def test_unit_ambiguity_error_fields():
    exc = UnitAmbiguityError(column="temperature_c", sample_value="98.6")
    assert exc.column == "temperature_c"
    assert exc.sample_value == "98.6"
    assert isinstance(exc, BatchAdapterError)


# ---------------------------------------------------------------------------
# SecretStr masking: credential fields must not appear in repr/str
# ---------------------------------------------------------------------------


class _SecretConfig(AdapterConfig):
    token: SecretStr


def test_secret_str_masked_in_repr():
    cfg = _SecretConfig(token="super-secret-token-abc123")
    assert "super-secret-token-abc123" not in repr(cfg)
    assert "super-secret-token-abc123" not in str(cfg)


def test_secret_str_get_secret_value():
    cfg = _SecretConfig(token="mytoken")
    assert cfg.token.get_secret_value() == "mytoken"


# ---------------------------------------------------------------------------
# AdapterConfig defaults
# ---------------------------------------------------------------------------


def test_adapter_config_defaults():
    cfg = AdapterConfig()
    assert cfg.max_attempts == 3
    assert cfg.rate_limit_default_wait_s == 60
