"""Generic GraphQL batch ingestion adapter (FR-010)."""

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


class GraphQLAdapterConfig(AdapterConfig):
    url: AnyHttpUrl
    query: str
    headers: dict[str, SecretStr] = {}
    cursor_field: str | None = None
    table_name: str = "records"


class GraphQLAdapter(BatchAdapter[GraphQLAdapterConfig]):
    """Execute a GraphQL query, paginating via cursor until exhausted.

    No introspection required — caller supplies the query document (FR-010).
    """

    def load(self, config: GraphQLAdapterConfig) -> dict[str, pd.DataFrame]:
        self._log_start()
        retry_deco = make_retry(self._name, config.max_attempts)

        resolved_headers = {
            "Content-Type": "application/json",
            **{k: v.get_secret_value() for k, v in config.headers.items()},
        }

        @retry_deco
        def _fetch(variables: dict | None = None) -> requests.Response:
            resp = requests.post(
                str(config.url),
                json={"query": config.query, "variables": variables or {}},
                headers=resolved_headers,
                timeout=60,
            )
            raise_for_http(resp, self._name, config)
            return resp

        try:
            all_records: list[dict] = []
            cursor: str | None = None

            while True:
                variables = {config.cursor_field: cursor} if cursor and config.cursor_field else None
                body = _fetch(variables).json()

                if "errors" in body:
                    raise RuntimeError(f"GraphQL errors: {body['errors']}")

                data = body.get("data") or {}
                # Flatten one level: take the first list value found
                records: list[dict] = []
                for v in data.values():
                    if isinstance(v, list):
                        records = v
                        break
                    if isinstance(v, dict):
                        for vv in v.values():
                            if isinstance(vv, list):
                                records = vv
                                break

                all_records.extend(records)

                if config.cursor_field:
                    # Look for cursor in pageInfo or root-level
                    page_info = {}
                    for v in data.values():
                        if isinstance(v, dict):
                            page_info = v.get("pageInfo", {})
                    cursor = page_info.get(config.cursor_field) or data.get(config.cursor_field)

                if not cursor or not records:
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
