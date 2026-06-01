"""Remote link (HTTP/HTTPS direct-download) batch ingestion adapter (FR-003)."""

from __future__ import annotations

import io
import logging

import pandas as pd
import requests
from pydantic import AnyHttpUrl

from src.ingestion.adapters.base import (
    AdapterConfig,
    BatchAdapter,
    ConnectorError,
    UnsupportedFormatError,
    raise_for_http,
)

logger = logging.getLogger(__name__)

_SUPPORTED_CONTENT_TYPES = frozenset({
    "text/csv",
    "application/csv",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
})

_LOGIN_INDICATORS = (
    "text/html",
    "accounts.google.com",
    "login",
    "signin",
    "auth",
)


class RemoteLinkAdapterConfig(AdapterConfig):
    url: AnyHttpUrl
    timeout_s: int = 30


class RemoteLinkAdapter(BatchAdapter[RemoteLinkAdapterConfig]):
    """Fetch a direct-download URL and load it as a canonical DataFrame.

    Supports CSV and XLSX. OAuth is out of scope — raises ConnectorError if
    the response is an HTML login page (FR-003).
    """

    def load(self, config: RemoteLinkAdapterConfig) -> dict[str, pd.DataFrame]:
        self._log_start()
        try:
            response = requests.get(str(config.url), timeout=config.timeout_s)
            raise_for_http(response, self._name, config)
            self._check_login_redirect(response, config)
            frames = self._parse_response(response, config)
        except (ConnectorError, UnsupportedFormatError):
            raise
        except requests.HTTPError as exc:
            self._log_error(exc)
            raise ConnectorError(adapter=self._name, cause=exc, attempts=1) from exc
        except Exception as exc:
            self._log_error(exc)
            raise ConnectorError(adapter=self._name, cause=exc, attempts=1) from exc

        self._log_done(frames)
        return frames

    def _check_login_redirect(self, response: requests.Response, config: RemoteLinkAdapterConfig) -> None:
        content_type = response.headers.get("Content-Type", "").lower()
        final_url = response.url.lower()
        if "text/html" in content_type or any(ind in final_url for ind in _LOGIN_INDICATORS[1:]):
            exc = ConnectorError(
                adapter=self._name,
                cause=RuntimeError(
                    "Authentication required — direct-download URL expected"
                ),
                attempts=1,
            )
            exc.args = (
                "Authentication required — direct-download URL expected "
                f"({exc.args[0]})",
            )
            raise exc

    def _parse_response(self, response: requests.Response, config: RemoteLinkAdapterConfig) -> dict[str, pd.DataFrame]:
        content_type = response.headers.get("Content-Type", "").lower()
        url_str = str(config.url)

        if "csv" in content_type or url_str.lower().endswith(".csv"):
            stem = url_str.rsplit("/", 1)[-1].rsplit(".", 1)[0]
            df = pd.read_csv(io.BytesIO(response.content))
            return {stem: df}

        if "spreadsheet" in content_type or "excel" in content_type or url_str.lower().endswith((".xlsx", ".xls")):
            xl = pd.ExcelFile(io.BytesIO(response.content), engine="openpyxl")
            return {sheet: xl.parse(sheet) for sheet in xl.sheet_names}

        raise UnsupportedFormatError(
            adapter=self._name,
            detected_type=content_type or "(unknown)",
        )
