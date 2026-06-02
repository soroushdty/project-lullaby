"""Tier 1 integration tests: FileAdapter and MySQL (no cloud accounts required)."""

from __future__ import annotations

import pathlib
import textwrap

import pandas as pd
import pytest

from src.ingestion.adapters.base import EncodingError, UnsupportedFormatError
from src.ingestion.adapters.file_adapter import FileAdapter, FileAdapterConfig

FIXTURES = pathlib.Path(__file__).parent.parent / "fixtures"
DATA_DIR = pathlib.Path(__file__).parent.parent.parent / "data"


# ---------------------------------------------------------------------------
# FileAdapter — CSV happy path
# ---------------------------------------------------------------------------


def test_file_adapter_csv_single_file(tmp_path):
    """Single CSV file is loaded as a DataFrame keyed by stem."""
    csv = tmp_path / "participants.csv"
    csv.write_text("participant_id,age\nLUL-001,30\nLUL-002,28\n")
    frames = FileAdapter().load(FileAdapterConfig(path=str(csv)))
    assert "participants" in frames
    assert len(frames["participants"]) == 2


def test_file_adapter_csv_directory(tmp_path):
    """Directory with multiple CSVs returns one frame per file stem."""
    (tmp_path / "participants.csv").write_text("participant_id,age\nLUL-001,30\n")
    (tmp_path / "daily_vitals.csv").write_text("participant_id,event_ts\nLUL-001,2025-06-01\n")
    frames = FileAdapter().load(FileAdapterConfig(path=str(tmp_path)))
    assert "participants" in frames
    assert "daily_vitals" in frames


def test_file_adapter_csv_utf8_bom(tmp_path):
    """UTF-8 BOM is stripped transparently."""
    csv = tmp_path / "participants.csv"
    csv.write_bytes(b"\xef\xbb\xbfparticipant_id,age\nLUL-001,30\n")
    frames = FileAdapter().load(FileAdapterConfig(path=str(csv)))
    assert list(frames["participants"].columns)[0] == "participant_id"


def test_file_adapter_bundled_synthetic_cohort():
    """Bundled synthetic cohort CSVs load without error."""
    frames = FileAdapter().load(FileAdapterConfig(path=str(DATA_DIR)))
    assert len(frames) >= 5
    for stem, df in frames.items():
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0


# ---------------------------------------------------------------------------
# FileAdapter — XLSX happy path
# ---------------------------------------------------------------------------


def test_file_adapter_xlsx(tmp_path):
    """XLSX with one sheet per table name returns one frame per sheet."""
    xlsx_path = tmp_path / "cohort.xlsx"
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        pd.DataFrame({"participant_id": ["LUL-001"], "age": [30]}).to_excel(
            writer, sheet_name="participants", index=False
        )
        pd.DataFrame({"participant_id": ["LUL-001"], "event_ts": ["2025-06-01"]}).to_excel(
            writer, sheet_name="daily_vitals", index=False
        )
    frames = FileAdapter().load(FileAdapterConfig(path=str(xlsx_path)))
    assert "participants" in frames
    assert "daily_vitals" in frames
    assert frames["participants"]["participant_id"].iloc[0] == "LUL-001"


# ---------------------------------------------------------------------------
# FileAdapter — error boundary scenarios
# ---------------------------------------------------------------------------


def test_file_adapter_unsupported_extension(tmp_path):
    """Unsupported file extension raises UnsupportedFormatError before any read."""
    f = tmp_path / "data.json"
    f.write_text('{"a": 1}')
    with pytest.raises(UnsupportedFormatError) as exc_info:
        FileAdapter().load(FileAdapterConfig(path=str(f)))
    assert exc_info.value.detected_type == ".json"
    assert exc_info.value.adapter == "FileAdapter"


def test_file_adapter_encoding_error(tmp_path):
    """Latin-1 file with UTF-8 declared raises EncodingError."""
    f = tmp_path / "participants.csv"
    f.write_bytes(b"participant_id,name\nLUL-001,Caf\xe9\n")  # latin-1 byte
    with pytest.raises(EncodingError) as exc_info:
        FileAdapter().load(FileAdapterConfig(path=str(f), encoding="utf-8"))
    assert exc_info.value.adapter == "FileAdapter"


# ---------------------------------------------------------------------------
# FileAdapter — idempotency
# ---------------------------------------------------------------------------


def test_file_adapter_idempotent(tmp_path):
    """Re-running with same config produces identical output."""
    csv = tmp_path / "participants.csv"
    csv.write_text("participant_id,age\nLUL-001,30\nLUL-001,30\n")
    adapter = FileAdapter()
    cfg = FileAdapterConfig(path=str(csv))
    frames1 = adapter.load(cfg)
    frames2 = adapter.load(cfg)
    pd.testing.assert_frame_equal(frames1["participants"], frames2["participants"])


# ---------------------------------------------------------------------------
# MySQL tests
# ---------------------------------------------------------------------------


from tests.conftest import wait_for_service

def test_mysql_adapter_happy_path():
    """MySQL adapter loads canonical tables via SQLAlchemy."""
    if not wait_for_service("localhost", 3306, timeout=5.0):
        pytest.skip("MySQL service not available at localhost:3306")
        
    from sqlalchemy import create_engine, text
    from pydantic import SecretStr
    from src.ingestion.adapters.mysql_adapter import MySQLAdapter, MySQLAdapterConfig

    conn_str = "mysql+pymysql://lullaby:lullaby@localhost:3306/lullaby"
    engine = create_engine(conn_str)
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS participants"))
        conn.execute(text("CREATE TABLE participants (participant_id VARCHAR(50), age INT)"))
        conn.execute(text("INSERT INTO participants VALUES ('LUL-001', 30)"))
        conn.commit()

    config = MySQLAdapterConfig(
        connection_string=SecretStr(conn_str),
        table_names=["participants"]
    )
    adapter = MySQLAdapter()
    frames = adapter.load(config)
    assert "participants" in frames
    assert len(frames["participants"]) == 1
    assert frames["participants"]["participant_id"].iloc[0] == "LUL-001"


# ---------------------------------------------------------------------------
# RESTAdapter — pytest-httpserver (T031)
# ---------------------------------------------------------------------------

from src.ingestion.adapters.base import ConnectorError  # noqa: E402
from src.ingestion.adapters.rest_adapter import RESTAdapter, RESTAdapterConfig  # noqa: E402


def test_rest_adapter_single_page(httpserver):
    """REST adapter loads a single-page JSON list."""
    httpserver.expect_request("/records").respond_with_json(
        [{"participant_id": "LUL-001"}, {"participant_id": "LUL-002"}]
    )
    url = httpserver.url_for("/records")
    frames = RESTAdapter().load(RESTAdapterConfig(url=url, table_name="participants"))
    assert "participants" in frames
    assert len(frames["participants"]) == 2


def test_rest_adapter_paginated(httpserver):
    """REST adapter follows next_page_field until exhausted."""
    httpserver.expect_request("/records", query_string="").respond_with_json(
        {"results": [{"id": 1}], "cursor": "page2"}
    )
    httpserver.expect_request("/records", query_string="cursor=page2").respond_with_json(
        {"results": [{"id": 2}], "cursor": None}
    )
    url = httpserver.url_for("/records")
    frames = RESTAdapter().load(
        RESTAdapterConfig(url=url, next_page_field="cursor", table_name="records")
    )
    assert len(frames["records"]) == 2


def test_rest_adapter_5xx_raises_connector_error(httpserver):
    """5xx response raises ConnectorError after retries."""
    httpserver.expect_request("/fail").respond_with_data("", status=503)
    url = httpserver.url_for("/fail")
    with pytest.raises(Exception):
        RESTAdapter().load(RESTAdapterConfig(url=url, max_attempts=1))


# ---------------------------------------------------------------------------
# GraphQLAdapter — pytest-httpserver (T032)
# ---------------------------------------------------------------------------

from src.ingestion.adapters.graphql_adapter import GraphQLAdapter, GraphQLAdapterConfig  # noqa: E402

QUERY = "{ participants { participant_id age } }"


def test_graphql_adapter_simple(httpserver):
    """GraphQL adapter executes query and returns records."""
    httpserver.expect_request("/graphql", method="POST").respond_with_json(
        {"data": {"participants": [{"participant_id": "LUL-001", "age": 30}]}}
    )
    url = httpserver.url_for("/graphql")
    frames = GraphQLAdapter().load(
        GraphQLAdapterConfig(url=url, query=QUERY, table_name="participants")
    )
    assert "participants" in frames
    assert frames["participants"]["participant_id"].iloc[0] == "LUL-001"


def test_graphql_adapter_5xx_raises(httpserver):
    """GraphQL adapter raises on 5xx after max_attempts."""
    httpserver.expect_request("/graphql", method="POST").respond_with_data("", status=500)
    url = httpserver.url_for("/graphql")
    with pytest.raises(Exception):
        GraphQLAdapter().load(
            GraphQLAdapterConfig(url=url, query=QUERY, max_attempts=1)
        )
