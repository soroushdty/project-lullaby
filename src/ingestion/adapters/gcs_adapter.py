"""Google Cloud Storage batch ingestion adapter (FR-006)."""

from __future__ import annotations

import io
import logging

import pandas as pd

from src.ingestion.adapters.base import (
    AdapterConfig,
    AuthConfigError,
    BatchAdapter,
    ConnectorError,
    UnsupportedFormatError,
)

logger = logging.getLogger(__name__)

_SUPPORTED_SUFFIXES = frozenset({".csv", ".xlsx", ".xls"})


class GCSAdapterConfig(AdapterConfig):
    bucket: str
    prefix: str = ""
    api_endpoint: str | None = None
    # Credentials via Application Default Credentials (GOOGLE_APPLICATION_CREDENTIALS)


class GCSAdapter(BatchAdapter[GCSAdapterConfig]):
    """Load CSV/XLSX objects from a GCS bucket into canonical DataFrames."""

    def load(self, config: GCSAdapterConfig) -> dict[str, pd.DataFrame]:
        self._log_start()
        try:
            from google.auth.exceptions import DefaultCredentialsError
            from google.cloud import storage

            try:
                gcs = storage.Client(client_options={"api_endpoint": config.api_endpoint}) if config.api_endpoint else storage.Client()
            except DefaultCredentialsError as exc:
                raise AuthConfigError(
                    adapter=self._name,
                    credential_env_var="GOOGLE_APPLICATION_CREDENTIALS",
                ) from exc

            frames = self._list_and_load(gcs, config)
        except (AuthConfigError, UnsupportedFormatError, ConnectorError):
            raise
        except Exception as exc:
            self._log_error(exc)
            raise ConnectorError(adapter=self._name, cause=exc, attempts=1) from exc

        self._log_done(frames)
        return frames

    def _list_and_load(self, gcs, config: GCSAdapterConfig) -> dict[str, pd.DataFrame]:
        frames: dict[str, pd.DataFrame] = {}
        bucket = gcs.bucket(config.bucket)
        for blob in gcs.list_blobs(config.bucket, prefix=config.prefix):
            name: str = blob.name
            suffix = "." + name.rsplit(".", 1)[-1].lower() if "." in name else ""
            if suffix not in _SUPPORTED_SUFFIXES:
                logger.info("adapter=%s skipping unsupported object=%s", self._name, name)
                continue
            stem = name.rsplit("/", 1)[-1].rsplit(".", 1)[0]
            data = blob.download_as_bytes()
            if suffix == ".csv":
                frames[stem] = pd.read_csv(io.BytesIO(data))
            else:
                frames[stem] = pd.read_excel(io.BytesIO(data), engine="openpyxl")
        return frames
