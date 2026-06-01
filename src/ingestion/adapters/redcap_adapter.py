"""REDCap Data Export API adapter (FR-008)."""

from __future__ import annotations

import logging
import os

import pandas as pd
import requests
from pydantic import AnyHttpUrl, SecretStr

from src.ingestion.adapters.base import (
    AdapterConfig,
    AuthConfigError,
    BatchAdapter,
    ConnectorError,
    make_retry,
    raise_for_http,
)

logger = logging.getLogger(__name__)


class REDCapAdapterConfig(AdapterConfig):
    api_url: AnyHttpUrl
    token: SecretStr | None = None
    # instrument_event_map: optional mapping of instrument name -> event name for flattening
    instrument_event_map: dict[str, str] | None = None


class REDCapAdapter(BatchAdapter[REDCapAdapterConfig]):
    """Export records from REDCap via the Data Export API.

    Reads REDCAP_TOKEN from environment if config.token is not provided.
    Flattens repeated instruments to row-per-event before returning.
    """

    def load(self, config: REDCapAdapterConfig) -> dict[str, pd.DataFrame]:
        self._log_start()

        token = (
            config.token.get_secret_value()
            if config.token is not None
            else os.environ.get("REDCAP_TOKEN")
        )
        if not token:
            raise AuthConfigError(adapter=self._name, credential_env_var="REDCAP_TOKEN")

        retry_deco = make_retry(self._name, config.max_attempts)

        @retry_deco
        def _fetch() -> requests.Response:
            resp = requests.post(
                str(config.api_url),
                data={
                    "token": token,
                    "content": "record",
                    "format": "json",
                    "type": "flat",
                },
                timeout=60,
            )
            raise_for_http(resp, self._name, config)
            return resp

        try:
            response = _fetch()
            records = response.json()
            frames = self._flatten(records)
        except (AuthConfigError, ConnectorError):
            raise
        except Exception as exc:
            self._log_error(exc)
            raise ConnectorError(
                adapter=self._name, cause=exc, attempts=config.max_attempts
            ) from exc

        self._log_done(frames)
        return frames

    def _flatten(self, records: list[dict]) -> dict[str, pd.DataFrame]:
        """Group records into canonical table frames.

        REDCap exports all instruments in a single flat record list.
        Each record has a 'redcap_repeat_instrument' field indicating its table.
        Non-repeated records map to 'participants'.
        """
        buckets: dict[str, list[dict]] = {}
        for row in records:
            instrument = row.get("redcap_repeat_instrument") or "participants"
            buckets.setdefault(instrument, []).append(row)
        return {name: pd.DataFrame(rows) for name, rows in buckets.items()}
