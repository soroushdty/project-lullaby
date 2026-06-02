"""Contract tests: SchemaContract interface from contracts/schema-interface.md."""
import pandera.pandas as pa
import pytest

from src.schemas.base import SchemaContract, SchemaContractError, TableContract
from src.schemas.lullaby import LullabySchema
from src.schemas.registry import resolve

CANONICAL_TABLES = [
    "participants", "daily_vitals", "alerts", "clinical_outcomes", "staff_contacts"
]


@pytest.fixture
def schema():
    return LullabySchema()


class TestSchemaContractInterface:
    def test_lullaby_schema_has_name(self, schema):
        assert isinstance(schema.name, str) and schema.name

    def test_lullaby_schema_has_version(self, schema):
        assert isinstance(schema.version, str) and schema.version

    def test_table_names_returns_list(self, schema):
        assert isinstance(schema.table_names(), list)

    def test_table_contract_returns_table_contract_instance(self, schema):
        for table in CANONICAL_TABLES:
            tc = schema.table_contract(table)
            assert isinstance(tc, TableContract)

    def test_pandera_schema_returns_dataframe_schema(self, schema):
        for table in CANONICAL_TABLES:
            ps = schema.pandera_schema(table)
            assert isinstance(ps, pa.DataFrameSchema)

    def test_data_dictionary_returns_dict(self, schema):
        for table in CANONICAL_TABLES:
            dd = schema.data_dictionary(table)
            assert isinstance(dd, dict)

    def test_default_schema_provides_all_five_canonical_tables(self, schema):
        assert set(schema.table_names()) == set(CANONICAL_TABLES)

    def test_missing_method_on_non_conforming_class_raises_schema_contract_error(self):
        with pytest.raises(SchemaContractError):
            resolve("src.schemas.base:TableContract")
