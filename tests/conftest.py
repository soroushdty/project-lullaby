"""Shared pytest fixtures and alternate-schema test fixtures."""
from __future__ import annotations

import os
import socket
import tempfile
import time
from copy import deepcopy
from pathlib import Path

import pandera.pandas as pa
import pytest
import yaml

from src.schemas.base import SchemaContract, TableContract

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "project-lullaby-matplotlib"))
os.environ.setdefault("LULLABY_TEST_MODE", "1")
os.environ.setdefault("LULLABY_RETRY_STOP", "1")
os.environ.setdefault("LULLABY_RETRY_WAIT_MIN", "0.1")
os.environ.setdefault("LULLABY_RETRY_WAIT_MAX", "0.1")

REPO_ROOT = Path(__file__).resolve().parents[1]


def wait_for_service(host: str, port: int, timeout: float = 10.0) -> bool:
    """Wait for a service to be ready by probing its port."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection((host, port), timeout=1.0):
                return True
        except (OSError, ConnectionRefusedError):
            time.sleep(0.5)
    return False


class MinimalConformingSchema(SchemaContract):
    """Conforming alternate schema with a single 'items' table for injection tests."""

    @property
    def name(self) -> str:
        return "minimal"

    @property
    def version(self) -> str:
        return "0.0.1"

    def table_names(self) -> list[str]:
        return ["items"]

    def table_contract(self, table_name: str) -> TableContract:
        if table_name != "items":
            from src.schemas.base import SchemaTableMissingError
            raise SchemaTableMissingError(table_name)
        return TableContract(
            table_name="items",
            required_columns=["id"],
            optional_columns=[],
            primary_key=["id"],
            timestamp_column="",
        )

    def pandera_schema(self, table_name: str) -> pa.DataFrameSchema:
        if table_name != "items":
            from src.schemas.base import SchemaTableMissingError
            raise SchemaTableMissingError(table_name)
        return pa.DataFrameSchema({"id": pa.Column(str)})

    def data_dictionary(self, table_name: str) -> dict[str, dict]:
        if table_name != "items":
            from src.schemas.base import SchemaTableMissingError
            raise SchemaTableMissingError(table_name)
        return {"id": {"type": "str", "description": "item identifier"}}


@pytest.fixture
def visualization_paths(tmp_path):
    """Temporary report, manifest, and output paths for visualization tests."""
    return {
        "report": tmp_path / "artifacts" / "validation-report.json",
        "manifest": tmp_path / "outputs" / "figures" / "manifest.json",
        "output_root": tmp_path / "outputs" / "figures",
    }


@pytest.fixture
def simulation_output_dir(tmp_path):
    """Temporary output directory for synthetic longitudinal generation tests."""
    return tmp_path / "synthetic" / "longitudinal"


@pytest.fixture
def default_modeling_config():
    """Parsed default modeling config for SPEC-011 tests."""
    with (REPO_ROOT / "config" / "modeling.yaml").open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


@pytest.fixture
def fast_modeling_config_path(tmp_path, default_modeling_config):
    """Small-repeat config so focused bake-off tests stay fast."""
    config = deepcopy(default_modeling_config)
    config["cv"]["n_repeats"] = 2
    config["metrics"]["bootstrap_ci"]["n_bootstrap"] = 100
    path = tmp_path / "modeling.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    return path
