"""Documented stubs for adapters not yet implemented (FR-011)."""

from __future__ import annotations

import pandas as pd

from src.ingestion.adapters.base import AdapterConfig, BatchAdapter


class DropboxAdapterConfig(AdapterConfig):
    share_url: str
    # OAuth token or API key would go here when implemented


class DropboxAdapter(BatchAdapter["DropboxAdapterConfig"]):
    """Stub: Dropbox share-link adapter. See contracts/batch-adapter-interface.md."""

    def load(self, config: DropboxAdapterConfig) -> dict[str, pd.DataFrame]:
        raise NotImplementedError(
            "DropboxAdapter is not implemented. "
            "See specs/002-batch-ingestion-adapters/contracts/batch-adapter-interface.md"
        )


class OneDriveAdapterConfig(AdapterConfig):
    share_url: str
    # OAuth token would go here when implemented


class OneDriveAdapter(BatchAdapter["OneDriveAdapterConfig"]):
    """Stub: OneDrive share-link adapter. See contracts/batch-adapter-interface.md."""

    def load(self, config: OneDriveAdapterConfig) -> dict[str, pd.DataFrame]:
        raise NotImplementedError(
            "OneDriveAdapter is not implemented. "
            "See specs/002-batch-ingestion-adapters/contracts/batch-adapter-interface.md"
        )


class GenericFallbackAdapterConfig(AdapterConfig):
    source_description: str = ""


class GenericFallbackAdapter(BatchAdapter["GenericFallbackAdapterConfig"]):
    """Stub: Generic fallback adapter for unsupported sources."""

    def load(self, config: GenericFallbackAdapterConfig) -> dict[str, pd.DataFrame]:
        raise NotImplementedError(
            "GenericFallbackAdapter is not implemented. "
            "See specs/002-batch-ingestion-adapters/contracts/batch-adapter-interface.md"
        )
