"""BatchAdapter generic ABC, AdapterConfig base, exception hierarchy, and retry policy."""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

import pandas as pd
import requests
from pydantic import BaseModel, Field, SecretStr  # noqa: F401 — re-exported for adapters
from tenacity import (
    RetryError,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------


class BatchAdapterError(RuntimeError):
    """Root exception for all adapter failures."""


class SchemaMismatchError(BatchAdapterError):
    def __init__(self, table: str, missing_columns: list[str], found_columns: list[str]) -> None:
        self.table = table
        self.missing_columns = missing_columns
        self.found_columns = found_columns
        super().__init__(
            f"Schema mismatch in table '{table}': "
            f"missing={missing_columns}, found={found_columns}"
        )


class ConnectorError(BatchAdapterError):
    def __init__(self, adapter: str, cause: Exception, attempts: int) -> None:
        self.adapter = adapter
        self.cause = cause
        self.attempts = attempts
        super().__init__(
            f"Connector failure in {adapter} after {attempts} attempt(s): "
            f"{type(cause).__name__}"
        )


class AuthConfigError(BatchAdapterError):
    def __init__(self, adapter: str, credential_env_var: str) -> None:
        self.adapter = adapter
        self.credential_env_var = credential_env_var
        super().__init__(
            f"{adapter}: missing or invalid credential '{credential_env_var}'"
        )


class UnsupportedFormatError(BatchAdapterError):
    def __init__(self, adapter: str, detected_type: str) -> None:
        self.adapter = adapter
        self.detected_type = detected_type
        super().__init__(f"{adapter}: unsupported format '{detected_type}'")


class EncodingError(BatchAdapterError):
    def __init__(self, adapter: str, path: str, detected_encoding: str | None) -> None:
        self.adapter = adapter
        self.path = path
        self.detected_encoding = detected_encoding
        super().__init__(
            f"{adapter}: encoding error reading '{path}' "
            f"(detected: {detected_encoding})"
        )


class UnitAmbiguityError(BatchAdapterError):
    def __init__(self, column: str, sample_value: str) -> None:
        self.column = column
        self.sample_value = sample_value
        super().__init__(
            f"Unit ambiguity in column '{column}' (sample: '{sample_value}'): "
            "declare units in AdapterConfig or source metadata"
        )


# ---------------------------------------------------------------------------
# AdapterConfig base
# ---------------------------------------------------------------------------


class AdapterConfig(BaseModel):
    max_attempts: int = Field(default=3, ge=1, le=10)
    rate_limit_default_wait_s: int = Field(default=60, ge=1)


# ---------------------------------------------------------------------------
# Retry helpers
# ---------------------------------------------------------------------------

_TRANSIENT_STATUS_CODES = frozenset({500, 502, 503, 504})
_AUTH_STATUS_CODES = frozenset({401, 403})


def _is_transient(exc: BaseException) -> bool:
    if isinstance(exc, requests.HTTPError):
        code = exc.response.status_code if exc.response is not None else 0
        return code in _TRANSIENT_STATUS_CODES
    return isinstance(exc, (requests.ConnectionError, requests.Timeout))


def _is_rate_limited(exc: BaseException) -> bool:
    return (
        isinstance(exc, requests.HTTPError)
        and exc.response is not None
        and exc.response.status_code == 429
    )


def _is_auth_error(exc: BaseException) -> bool:
    return (
        isinstance(exc, requests.HTTPError)
        and exc.response is not None
        and exc.response.status_code in _AUTH_STATUS_CODES
    )


def raise_for_http(response: requests.Response, adapter_name: str, config: AdapterConfig) -> None:
    """Raise typed exception for non-2xx HTTP responses. Call before consuming body."""
    if response.status_code == 429:
        wait = int(response.headers.get("Retry-After", config.rate_limit_default_wait_s))
        logger.warning("adapter=%s 429 rate-limited; waiting %ds", adapter_name, wait)
        time.sleep(wait)
        response.raise_for_status()  # signal tenacity to retry
    if response.status_code in _AUTH_STATUS_CODES:
        raise AuthConfigError(adapter=adapter_name, credential_env_var="(HTTP credentials)")
    response.raise_for_status()


def make_retry(adapter_name: str, max_attempts: int):
    """Return a tenacity retry decorator for transient HTTP/network errors."""
    return retry(
        retry=retry_if_exception(_is_transient),
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        reraise=True,
    )


# ---------------------------------------------------------------------------
# BatchAdapter generic ABC
# ---------------------------------------------------------------------------

C = TypeVar("C", bound=AdapterConfig)


class BatchAdapter(ABC, Generic[C]):
    """Generic ABC for all batch ingestion adapters.

    Subclass and implement load(config: YourConfig) -> dict[str, pd.DataFrame].
    Always raises a BatchAdapterError subclass on failure — never returns partial output.
    """

    @property
    def _name(self) -> str:
        return type(self).__name__

    @abstractmethod
    def load(self, config: C) -> dict[str, pd.DataFrame]:
        ...

    # ------------------------------------------------------------------
    # Shared helpers available to all concrete adapters
    # ------------------------------------------------------------------

    def _dedup(
        self,
        frames: dict[str, pd.DataFrame],
        schema,
    ) -> dict[str, pd.DataFrame]:
        """Dedup each frame using primary keys from the schema's TableContract."""
        result: dict[str, pd.DataFrame] = {}
        for table_name, df in frames.items():
            pk = schema.table_contract(table_name).primary_key
            if pk:
                df = df.drop_duplicates(subset=pk, keep="last")
            result[table_name] = df
        return result

    def _validate(self, frames: dict[str, pd.DataFrame], schema) -> None:
        """Run SPEC-001 validation engine; raises SchemaMismatchError on failure."""
        from src.validation import engine as ve

        try:
            ve.validate(schema, frames)
        except ve.ValidationError as exc:
            contract = schema.table_contract(exc.table)
            df = frames[exc.table]
            missing = [c for c in contract.required_columns if c not in df.columns]
            raise SchemaMismatchError(
                table=exc.table,
                missing_columns=missing,
                found_columns=list(df.columns),
            ) from exc

    def _log_start(self) -> None:
        logger.info("adapter=%s starting load", self._name)

    def _log_done(self, frames: dict[str, pd.DataFrame]) -> None:
        counts = {t: len(df) for t, df in frames.items()}
        logger.info("adapter=%s loaded %d tables row_counts=%s", self._name, len(frames), counts)

    def _log_error(self, exc: Exception) -> None:
        logger.error("adapter=%s raised %s: %s", self._name, type(exc).__name__, exc)
