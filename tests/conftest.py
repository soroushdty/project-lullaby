"""Shared pytest fixtures and alternate-schema test fixtures."""
import pandera as pa

from src.schemas.base import SchemaContract, TableContract


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
