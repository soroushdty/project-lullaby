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

import boto3
import os
from src.ingestion.adapters.s3_adapter import S3Adapter, S3AdapterConfig
from src.ingestion.adapters.azure_adapter import AzureAdapter, AzureAdapterConfig
from src.ingestion.adapters.gcs_adapter import GCSAdapter, GCSAdapterConfig

from tests.conftest import wait_for_service

S3_ENDPOINT = "http://localhost:9000"
AZURE_URL = "http://localhost:10000/devstoreaccount1"
GCS_ENDPOINT = "http://localhost:4443"

@pytest.fixture(scope="module")
def s3_service():
    if not wait_for_service("localhost", 9000, timeout=5.0):
        pytest.skip("MinIO service not available at localhost:9000")
    return S3_ENDPOINT

@pytest.fixture(scope="module")
def azure_service():
    if not wait_for_service("localhost", 10000, timeout=5.0):
        pytest.skip("Azurite service not available at localhost:10000")
    return AZURE_URL

@pytest.fixture(scope="module")
def gcs_service():
    if not wait_for_service("localhost", 4443, timeout=5.0):
        pytest.skip("fake-gcs-server service not available at localhost:4443")
    return GCS_ENDPOINT

def test_s3_adapter_minio(s3_service):
    """S3 adapter loads CSV from MinIO emulator."""
    s3 = boto3.client("s3", endpoint_url=s3_service, 
                      aws_access_key_id="minioadmin", 
                      aws_secret_access_key="minioadmin")
    bucket = "test-bucket-s3"
    try:
        s3.create_bucket(Bucket=bucket)
    except:
        pass
    s3.put_object(Bucket=bucket, Key="participants.csv", Body="participant_id,age\nLUL-001,30\n")
    
    os.environ["AWS_ACCESS_KEY_ID"] = "minioadmin"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "minioadmin"
    
    config = S3AdapterConfig(bucket=bucket, endpoint_url=s3_service)
    frames = S3Adapter().load(config)
    assert "participants" in frames
    assert frames["participants"]["participant_id"].iloc[0] == "LUL-001"


def test_azure_adapter_azurite(azure_service):
    """Azure adapter loads CSV from Azurite emulator."""
    from azure.storage.blob import BlobServiceClient
    conn_str = "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
    service = BlobServiceClient.from_connection_string(conn_str)
    container = "test-container"
    try:
        service.create_container(container)
    except:
        pass
    blob = service.get_blob_client(container=container, blob="participants.csv")
    blob.upload_blob("participant_id,age\nLUL-001,30\n", overwrite=True)
    
    from pydantic import SecretStr
    config = AzureAdapterConfig(container=container, connection_string=SecretStr(conn_str))
    frames = AzureAdapter().load(config)
    assert "participants" in frames
    assert frames["participants"]["participant_id"].iloc[0] == "LUL-001"


def test_gcs_adapter_fake_gcs(gcs_service):
    """GCS adapter loads CSV from fake-gcs-server emulator."""
    from google.cloud import storage
    # fake-gcs-server doesn't need real auth
    os.environ["STORAGE_EMULATOR_HOST"] = gcs_service
    client = storage.Client()
    bucket_name = "test-bucket-gcs"
    try:
        client.create_bucket(bucket_name)
    except:
        pass
    bucket = client.bucket(bucket_name)
    blob = bucket.blob("participants.csv")
    blob.upload_from_string("participant_id,age\nLUL-001,30\n")
    
    config = GCSAdapterConfig(bucket=bucket_name, api_endpoint=gcs_service)
    frames = GCSAdapter().load(config)
    assert "participants" in frames
    assert frames["participants"]["participant_id"].iloc[0] == "LUL-001"
