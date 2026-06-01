"""Tier 2 integration tests: RemoteLinkAdapter via pytest-httpserver (T023).
Cloud adapter tests (S3/Azure/GCS) require Docker Compose and are skipped here."""

from __future__ import annotations

import pytest

from src.ingestion.adapters.base import ConnectorError, UnsupportedFormatError
from src.ingestion.adapters.remote_link_adapter import RemoteLinkAdapter, RemoteLinkAdapterConfig


# ---------------------------------------------------------------------------
# RemoteLinkAdapter — pytest-httpserver (T023)
# ---------------------------------------------------------------------------


SAMPLE_CSV = b"participant_id,age\nLUL-001,30\nLUL-002,28\n"


def test_remote_link_valid_csv(httpserver):
    """Valid CSV URL returns a DataFrame keyed by URL stem."""
    httpserver.expect_request("/data/participants.csv").respond_with_data(
        SAMPLE_CSV, content_type="text/csv"
    )
    url = httpserver.url_for("/data/participants.csv")
    frames = RemoteLinkAdapter().load(RemoteLinkAdapterConfig(url=url))
    assert "participants" in frames
    assert len(frames["participants"]) == 2


def test_remote_link_404_raises_connector_error(httpserver):
    """404 response raises ConnectorError with URL and status code info."""
    httpserver.expect_request("/missing.csv").respond_with_data("", status=404)
    url = httpserver.url_for("/missing.csv")
    with pytest.raises(ConnectorError) as exc_info:
        RemoteLinkAdapter().load(RemoteLinkAdapterConfig(url=url))
    assert exc_info.value.adapter == "RemoteLinkAdapter"


def test_remote_link_login_redirect_raises_connector_error(httpserver):
    """HTML response (login page) raises ConnectorError."""
    httpserver.expect_request("/drive/file").respond_with_data(
        "<html><body>Sign in</body></html>", content_type="text/html"
    )
    url = httpserver.url_for("/drive/file")
    with pytest.raises(ConnectorError) as exc_info:
        RemoteLinkAdapter().load(RemoteLinkAdapterConfig(url=url))
    assert "Authentication required" in str(exc_info.value)


def test_remote_link_unsupported_content_type_raises_error(httpserver):
    """Unsupported content type (e.g. XML) raises UnsupportedFormatError."""
    httpserver.expect_request("/data.xml").respond_with_data(
        b"<root/>", content_type="application/xml"
    )
    url = httpserver.url_for("/data.xml")
    with pytest.raises(UnsupportedFormatError) as exc_info:
        RemoteLinkAdapter().load(RemoteLinkAdapterConfig(url=url))
    assert exc_info.value.adapter == "RemoteLinkAdapter"


# ---------------------------------------------------------------------------
# Cloud adapter tests — require Docker Compose (tier 2)
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="Requires Docker Compose with MinIO (tier 2)")
def test_s3_adapter_minio():
    pass


@pytest.mark.skip(reason="Requires Docker Compose with Azurite (tier 2)")
def test_azure_adapter_azurite():
    pass


@pytest.mark.skip(reason="Requires Docker Compose with fake-gcs-server (tier 2)")
def test_gcs_adapter_fake_gcs():
    pass
