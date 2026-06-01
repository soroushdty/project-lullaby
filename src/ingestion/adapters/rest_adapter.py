"""Generic REST API batch ingestion adapter (FR-009)."""

from __future__ import annotations

import logging

import pandas as pd
import requests
from pydantic import AnyHttpUrl, SecretStr

from src.ingestion.adapters.base import (
    AdapterConfig,
    BatchAdapter,
    ConnectorError,
    make_retry,
    raise_for_http,
)

logger = logging.getLogger(__name__)


class RESTAdapterConfig(AdapterConfig):
    url: AnyHttpUrl
    method: str = "GET"
    headers: dict[str, SecretStr] = {}
    next_page_field: str | None = None
    table_name: str = "records"


class RESTAdapter(BatchAdapter[RESTAdapterConfig]):
    """Fetch records from a REST API endpoint, paginating until exhausted."""

    def load(self, config: RESTAdapterConfig) -> dict[str, pd.DataFrame]:
        self._log_start()
        retry_deco = make_retry(self._name, config.max_attempts)

        resolved_headers = {k: v.get_secret_value() for k, v in config.headers.items()}

        @retry_deco
        def _fetch(url: str, params: dict | None = None) -> requests.Response:
            resp = requests.request(
                config.method,
                url,
                headers=resolved_headers,
                params=params,
                timeout=60,
            )
            raise_for_http(resp, self._name, config)
            return resp

        try:
            all_records: list[dict] = []
            url = str(config.url)
            cursor: str | None = None

            while True:
                params = {config.next_page_field: cursor} if cursor and config.next_page_field else None
                data = _fetch(url, params).json()

                if isinstance(data, list):
                    all_records.extend(data)
                    break
                elif isinstance(data, dict):
                    records = data.get("results") or data.get("data") or data.get("records") or []
                    all_records.extend(records)
                    if config.next_page_field:
                        cursor = data.get(config.next_page_field)
                    if not cursor:
                        break
                else:
                    break

            frames = {config.table_name: pd.DataFrame(all_records)}
        except ConnectorError:
            raise
        except Exception as exc:
            self._log_error(exc)
            raise ConnectorError(
                adapter=self._name, cause=exc, attempts=config.max_attempts
            ) from exc

        self._log_done(frames)
        return frames
