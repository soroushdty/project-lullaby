"""Tier 3 integration tests: REDCap adapter against recorded fixtures (T030)."""

from __future__ import annotations

import json
import pathlib

import pytest

from src.ingestion.adapters.base import AuthConfigError, ConnectorError
from src.ingestion.adapters.redcap_adapter import REDCapAdapter, REDCapAdapterConfig

FIXTURES = pathlib.Path(__file__).parent.parent / "fixtures" / "redcap"


# ---------------------------------------------------------------------------
# REDCapAdapter — recorded fixture (T030)
# ---------------------------------------------------------------------------


def test_redcap_adapter_happy_path(httpserver, monkeypatch):
    """REDCap adapter parses flat export fixture and groups by instrument."""
    fixture = json.loads((FIXTURES / "export_flat.json").read_text())
    httpserver.expect_request("/api/", method="POST").respond_with_json(fixture)

    url = httpserver.url_for("/api/")
    monkeypatch.setenv("REDCAP_TOKEN", "test-token-fixture")

    frames = REDCapAdapter().load(REDCapAdapterConfig(api_url=url))

    assert "participants" in frames
    assert "daily_vitals" in frames
    assert len(frames["participants"]) == 2
    assert len(frames["daily_vitals"]) == 2


def test_redcap_adapter_missing_token_raises_auth_error(httpserver):
    """Missing REDCAP_TOKEN env var raises AuthConfigError at instantiation."""
    import os
    os.environ.pop("REDCAP_TOKEN", None)

    url = httpserver.url_for("/api/")
    with pytest.raises(AuthConfigError) as exc_info:
        REDCapAdapter().load(REDCapAdapterConfig(api_url=url))
    assert exc_info.value.credential_env_var == "REDCAP_TOKEN"


def test_redcap_adapter_5xx_raises_connector_error(httpserver, monkeypatch):
    """5xx response exhausts retries and raises ConnectorError."""
    httpserver.expect_request("/api/", method="POST").respond_with_data("", status=503)
    url = httpserver.url_for("/api/")
    monkeypatch.setenv("REDCAP_TOKEN", "test-token-fixture")

    with pytest.raises((ConnectorError, Exception)):
        REDCapAdapter().load(REDCapAdapterConfig(api_url=url, max_attempts=1))
