"""Integration tests for the full ingestion + validation pipeline and CLI exit codes."""
import pathlib
import subprocess
import sys
import tempfile

import pandas as pd
import pytest

from src.ingestion import pipeline
from src.schemas.lullaby import LullabySchema

SYNTHETIC_DIR = str(pathlib.Path(__file__).parents[2] / "data" / "synthetic")


@pytest.fixture
def schema():
    return LullabySchema()


class TestBundledDataIngestion:
    def test_valid_bundled_data_exits_zero(self, schema):
        report = pipeline.run(schema, SYNTHETIC_DIR, run_id="test-valid")
        assert report["status"] == "pass"

    def test_valid_bundled_data_produces_five_table_report(self, schema):
        report = pipeline.run(schema, SYNTHETIC_DIR, run_id="test-five-tables")
        assert set(report["tables"].keys()) == {
            "participants", "daily_vitals", "alerts", "clinical_outcomes", "staff_contacts"
        }

    def test_schema_violation_exits_nonzero(self, schema):
        with tempfile.TemporaryDirectory() as tmp:
            _write_invalid_participants(tmp)
            _copy_valid_tables(tmp, exclude="participants")
            with pytest.raises(Exception):
                pipeline.run(schema, tmp, run_id="test-violation")

    def test_schema_violation_error_includes_table_column_constraint(self, schema):
        with tempfile.TemporaryDirectory() as tmp:
            _write_invalid_participants(tmp)
            _copy_valid_tables(tmp, exclude="participants")
            with pytest.raises(Exception) as exc_info:
                pipeline.run(schema, tmp, run_id="test-detail")
            msg = str(exc_info.value)
            assert "participants" in msg


class TestSchemaInjection:
    def test_conforming_alternate_schema_passes_pipeline(self):
        from tests.conftest import MinimalConformingSchema
        schema = MinimalConformingSchema()
        with tempfile.TemporaryDirectory() as tmp:
            _write_minimal_valid_data(tmp)
            report = pipeline.run(schema, tmp, run_id="test-alt-schema")
            assert report["status"] == "pass"

    def test_non_conforming_schema_raises_schema_contract_error(self):
        from src.schemas.base import SchemaContractError
        from src.schemas.registry import resolve
        with pytest.raises(SchemaContractError):
            resolve("src.schemas.base:TableContract")


class TestCliExitCodes:
    def test_cli_exits_zero_on_valid_data(self):
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.validate_schema",
             "--schema", "lullaby", "--input", SYNTHETIC_DIR],
            capture_output=True,
        )
        assert result.returncode == 0, result.stderr.decode()

    def test_cli_exits_nonzero_on_invalid_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write_invalid_participants(tmp)
            _copy_valid_tables(tmp, exclude="participants")
            result = subprocess.run(
                [sys.executable, "-m", "src.cli.validate_schema",
                 "--schema", "lullaby", "--input", tmp],
                capture_output=True,
            )
            assert result.returncode != 0


# ── helpers ──────────────────────────────────────────────────────────────────

def _write_invalid_participants(directory: str) -> None:
    """Write a participants CSV missing the required site_code column."""
    df = pd.DataFrame({
        "participant_id": ["P-BAD"],
        "enrollment_ts": pd.to_datetime(["2025-06-02"], utc=True),
        # site_code intentionally omitted
    })
    df.to_csv(pathlib.Path(directory) / "participants.csv", index=False)


def _copy_valid_tables(directory: str, exclude: str = "") -> None:
    """Copy valid synthetic CSVs into a temp directory, skipping the excluded table."""
    src = pathlib.Path(SYNTHETIC_DIR)
    dst = pathlib.Path(directory)
    for csv in src.glob("*.csv"):
        if csv.stem != exclude:
            (dst / csv.name).write_bytes(csv.read_bytes())


def _write_minimal_valid_data(directory: str) -> None:
    """Write one-row CSVs matching MinimalConformingSchema's single 'items' table."""
    df = pd.DataFrame({"id": ["X-001"]})
    df.to_csv(pathlib.Path(directory) / "items.csv", index=False)
