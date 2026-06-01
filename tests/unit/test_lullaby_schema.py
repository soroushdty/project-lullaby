"""Unit tests for LullabySchema table contracts and registry resolution."""
import pytest

from src.schemas.base import SchemaContractError, SchemaTableMissingError, TableContract
from src.schemas.lullaby import LullabySchema
from src.schemas.registry import resolve


@pytest.fixture
def schema():
    return LullabySchema()


class TestLullabySchemaTableContracts:
    def test_table_names_returns_five_canonical_tables(self, schema):
        assert set(schema.table_names()) == {
            "participants", "daily_vitals", "alerts", "clinical_outcomes", "staff_contacts"
        }

    def test_participants_table_contract_fields(self, schema):
        tc = schema.table_contract("participants")
        assert isinstance(tc, TableContract)
        assert "participant_id" in tc.required_columns
        assert "enrollment_ts" in tc.required_columns
        assert "site_code" in tc.required_columns
        assert tc.timestamp_column == "enrollment_ts"
        assert "participant_id" in tc.primary_key

    def test_daily_vitals_table_contract_fields(self, schema):
        tc = schema.table_contract("daily_vitals")
        assert isinstance(tc, TableContract)
        assert "participant_id" in tc.required_columns
        assert "event_ts" in tc.required_columns
        assert "cadence" in tc.required_columns
        assert tc.timestamp_column == "event_ts"
        for col in ("heart_rate", "systolic_bp", "diastolic_bp", "temperature_c"):
            assert col in tc.optional_columns

    def test_alerts_table_contract_fields(self, schema):
        tc = schema.table_contract("alerts")
        assert isinstance(tc, TableContract)
        assert "alert_id" in tc.required_columns
        assert "participant_id" in tc.required_columns
        assert "event_ts" in tc.required_columns
        assert "alert_level" in tc.required_columns
        assert "source" in tc.required_columns
        assert tc.timestamp_column == "event_ts"
        assert "alert_id" in tc.primary_key

    def test_clinical_outcomes_table_contract_fields(self, schema):
        tc = schema.table_contract("clinical_outcomes")
        assert isinstance(tc, TableContract)
        assert "outcome_id" in tc.required_columns
        assert "participant_id" in tc.required_columns
        assert "event_ts" in tc.required_columns
        assert "outcome_type" in tc.required_columns
        assert "is_primary_cv_event" in tc.required_columns
        assert tc.timestamp_column == "event_ts"
        assert "outcome_id" in tc.primary_key

    def test_staff_contacts_table_contract_fields(self, schema):
        tc = schema.table_contract("staff_contacts")
        assert isinstance(tc, TableContract)
        assert "staff_id" in tc.required_columns
        assert "role" in tc.required_columns
        assert "contact_method" in tc.required_columns
        assert "availability_window" in tc.optional_columns
        assert "staff_id" in tc.primary_key

    def test_unknown_table_raises_schema_table_missing_error(self, schema):
        with pytest.raises(SchemaTableMissingError):
            schema.table_contract("nonexistent")


class TestRegistryResolution:
    def test_lullaby_alias_resolves_to_lullaby_schema(self):
        schema = resolve("lullaby")
        assert isinstance(schema, LullabySchema)

    def test_dotted_import_path_resolves_successfully(self):
        schema = resolve("src.schemas.lullaby:LullabySchema")
        assert isinstance(schema, LullabySchema)

    def test_missing_alias_raises_schema_contract_error(self):
        with pytest.raises(SchemaContractError):
            resolve("nonexistent_alias")

    def test_non_conforming_class_raises_schema_contract_error(self):
        with pytest.raises(SchemaContractError):
            resolve("src.schemas.base:TableContract")
