"""Streaming ingestion exception hierarchy."""

from __future__ import annotations

from src.ingestion.adapters.base import BatchAdapterError


class StreamAdapterError(BatchAdapterError):
    """Root exception for streaming adapter failures."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)
