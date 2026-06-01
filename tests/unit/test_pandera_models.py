"""Unit tests for Pandera model field types, nullability, and constraints."""
import pandas as pd
import pandera as pa
import pytest

from src.schemas.lullaby import LullabySchema

VALID_TS = "2025-06-02T00:00:00+00:00"


def _utc_df(**cols) -> pd.DataFrame:
    return pd.DataFrame(cols)


@pytest.fixture
def schema():
    return LullabySchema()


class TestParticipantsPanderaSchema:
    def test_required_columns_present(self, schema):
        ps = schema.pandera_schema("participants")
        assert isinstance(ps, pa.DataFrameSchema)
        assert "participant_id" in ps.columns
        assert "enrollment_ts" in ps.columns
        assert "site_code" in ps.columns

    def test_enrollment_ts_must_be_utc(self, schema):
        ps = schema.pandera_schema("participants")
        df = pd.DataFrame({
            "participant_id": ["P-001"],
            "enrollment_ts": pd.to_datetime(["2025-06-02"], utc=True),
            "site_code": ["PHX"],
        })
        ps.validate(df)  # must not raise

    def test_missing_timezone_fails_validation(self, schema):
        ps = schema.pandera_schema("participants")
        df = pd.DataFrame({
            "participant_id": ["P-001"],
            "enrollment_ts": pd.to_datetime(["2025-06-02"]),  # no tz
            "site_code": ["PHX"],
        })
        with pytest.raises(pa.errors.SchemaError):
            ps.validate(df)

    def test_participant_id_is_unique(self, schema):
        ps = schema.pandera_schema("participants")
        df = pd.DataFrame({
            "participant_id": ["P-001", "P-001"],
            "enrollment_ts": pd.to_datetime(["2025-06-02", "2025-06-03"], utc=True),
            "site_code": ["PHX", "PHX"],
        })
        with pytest.raises(pa.errors.SchemaError):
            ps.validate(df)


class TestDailyVitalsPanderaSchema:
    def test_required_columns_present(self, schema):
        ps = schema.pandera_schema("daily_vitals")
        assert isinstance(ps, pa.DataFrameSchema)
        for col in ("participant_id", "event_ts", "cadence"):
            assert col in ps.columns

    def test_event_ts_must_be_utc(self, schema):
        ps = schema.pandera_schema("daily_vitals")
        df = pd.DataFrame({
            "participant_id": ["P-001"],
            "event_ts": pd.to_datetime(["2025-06-02"], utc=True),
            "cadence": ["daily"],
        })
        ps.validate(df)  # must not raise

    def test_nullable_vital_columns_allow_null(self, schema):
        ps = schema.pandera_schema("daily_vitals")
        df = pd.DataFrame({
            "participant_id": ["P-001"],
            "event_ts": pd.to_datetime(["2025-06-02"], utc=True),
            "cadence": ["daily"],
            "heart_rate": [None],
            "systolic_bp": [None],
            "diastolic_bp": [None],
            "temperature_c": [None],
        })
        ps.validate(df)  # must not raise

    def test_missing_timezone_fails_validation(self, schema):
        ps = schema.pandera_schema("daily_vitals")
        df = pd.DataFrame({
            "participant_id": ["P-001"],
            "event_ts": pd.to_datetime(["2025-06-02"]),  # no tz
            "cadence": ["daily"],
        })
        with pytest.raises(pa.errors.SchemaError):
            ps.validate(df)


class TestAlertsPanderaSchema:
    def test_required_columns_present(self, schema):
        ps = schema.pandera_schema("alerts")
        for col in ("alert_id", "participant_id", "event_ts", "alert_level", "source"):
            assert col in ps.columns

    def test_alert_level_enum_constraint(self, schema):
        ps = schema.pandera_schema("alerts")
        df = pd.DataFrame({
            "alert_id": ["A-001"],
            "participant_id": ["P-001"],
            "event_ts": pd.to_datetime(["2025-06-02"], utc=True),
            "alert_level": ["invalid_level"],
            "source": ["sensor"],
        })
        with pytest.raises(pa.errors.SchemaError):
            ps.validate(df)


class TestClinicalOutcomesPanderaSchema:
    def test_required_columns_present(self, schema):
        ps = schema.pandera_schema("clinical_outcomes")
        for col in ("outcome_id", "participant_id", "event_ts", "outcome_type", "is_primary_cv_event"):
            assert col in ps.columns

    def test_is_primary_cv_event_is_bool(self, schema):
        ps = schema.pandera_schema("clinical_outcomes")
        df = pd.DataFrame({
            "outcome_id": ["OC-001"],
            "participant_id": ["P-001"],
            "event_ts": pd.to_datetime(["2025-06-02"], utc=True),
            "outcome_type": ["hypertensive_crisis"],
            "is_primary_cv_event": [True],
        })
        ps.validate(df)  # must not raise


class TestStaffContactsPanderaSchema:
    def test_required_columns_present(self, schema):
        ps = schema.pandera_schema("staff_contacts")
        for col in ("staff_id", "role", "contact_method"):
            assert col in ps.columns
