"""Azure Blob Storage batch ingestion adapter (FR-005)."""

from __future__ import annotations

import io
import logging

import pandas as pd
from pydantic import SecretStr

from src.ingestion.adapters.base import (
    AdapterConfig,
    AuthConfigError,
    BatchAdapter,
    ConnectorError,
    UnsupportedFormatError,
)

logger = logging.getLogger(__name__)

_SUPPORTED_SUFFIXES = frozenset({".csv", ".xlsx", ".xls"})


class AzureAdapterConfig(AdapterConfig):
    container: str
    prefix: str = ""
    connection_string: SecretStr | None = None
    account_url: str | None = None
    # If None, uses DefaultAzureCredential with account_url


class AzureAdapter(BatchAdapter[AzureAdapterConfig]):
    """Load CSV/XLSX blobs from Azure Blob Storage into canonical DataFrames."""

    def load(self, config: AzureAdapterConfig) -> dict[str, pd.DataFrame]:
        self._log_start()
        try:
            from azure.core.exceptions import ClientAuthenticationError
            from azure.identity import DefaultAzureCredential
            from azure.storage.blob import BlobServiceClient

            try:
                if config.connection_string is not None:
                    client = BlobServiceClient.from_connection_string(
                        config.connection_string.get_secret_value()
                    )
                elif config.account_url is not None:
                    client = BlobServiceClient(
                        account_url=config.account_url,
                        credential=DefaultAzureCredential(),
                    )
                else:
                    raise AuthConfigError(
                        adapter=self._name,
                        credential_env_var="AZURE_CLIENT_ID / DefaultAzureCredential",
                    )
            except ClientAuthenticationError as exc:
                raise AuthConfigError(
                    adapter=self._name,
                    credential_env_var="AZURE_CLIENT_ID",
                ) from exc

            frames = self._list_and_load(client, config)
        except (AuthConfigError, UnsupportedFormatError, ConnectorError):
            raise
        except Exception as exc:
            self._log_error(exc)
            raise ConnectorError(adapter=self._name, cause=exc, attempts=1) from exc

        self._log_done(frames)
        return frames

    def _list_and_load(self, client, config: AzureAdapterConfig) -> dict[str, pd.DataFrame]:
        frames: dict[str, pd.DataFrame] = {}
        container_client = client.get_container_client(config.container)
        for blob in container_client.list_blobs(name_starts_with=config.prefix):
            name: str = blob.name
            suffix = "." + name.rsplit(".", 1)[-1].lower() if "." in name else ""
            if suffix not in _SUPPORTED_SUFFIXES:
                logger.info("adapter=%s skipping unsupported blob=%s", self._name, name)
                continue
            stem = name.rsplit("/", 1)[-1].rsplit(".", 1)[0]
            data = container_client.download_blob(name).readall()
            if suffix == ".csv":
                frames[stem] = pd.read_csv(io.BytesIO(data))
            else:
                frames[stem] = pd.read_excel(io.BytesIO(data), engine="openpyxl")
        return frames
