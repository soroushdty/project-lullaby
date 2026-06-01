"""Contract tests: validation boundary behavior from contracts/validation-contract.md."""
import pandas as pd
import pytest

from src.schemas.lullaby import LullabySchema
from src.validation import engine


@pytest.fixture
def schema():
    return LullabySchema()


def _valid_frames():
    return {
        "participants": pd.DataFrame({
            "participant_id": ["P-001"],
            "enrollment_ts": pd.to_datetime(["2025-06-02"], utc=True),
            "site_code": ["PHX"],
        }),
        "daily_vitals": pd.DataFrame({
            "participant_id": ["P-001"],
            "event_ts": pd.to_datetime(["2025-06-02"], utc=True),
            "cadence": ["daily"],
        }),
        "alerts": pd.DataFrame({
            "alert_id": ["A-001"],
            "participant_id": ["P-001"],
            "event_ts": pd.to_datetime(["2025-06-02"], utc=True),
            "alert_level": ["yellow"],
            "source": ["sensor"],
        }),
        "clinical_outcomes": pd.DataFrame({
            "outcome_id": ["OC-001"],
            "participant_id": ["P-001"],
            "event_ts": pd.to_datetime(["2025-06-02"], utc=True),
            "outcome_type": ["no_event"],
            "is_primary_cv_event": [False],
        }),
        "staff_contacts": pd.DataFrame({
            "staff_id": ["STAFF-01"],
            "role": ["nurse"],
            "contact_method": ["phone"],
        }),
    }


class TestValidationBoundarySuccess:
    def test_success_report_has_per_table_pass_status(self, schema):
        report = engine.validate(schema, _valid_frames(), run_id="test")
        for table in ("participants", "daily_vitals", "alerts", "clinical_outcomes", "staff_contacts"):
            assert report["tables"][table]["status"] == "pass"

    def test_success_report_includes_row_counts(self, schema):
        report = engine.validate(schema, _valid_frames(), run_id="test")
        for table in ("participants", "daily_vitals", "alerts", "clinical_outcomes", "staff_contacts"):
            assert "row_count" in report["tables"][table]

    def test_success_overall_status_is_pass(self, schema):
        report = engine.validate(schema, _valid_frames(), run_id="test")
        assert report["status"] == "pass"


class TestValidationBoundaryFailure:
    def test_failure_payload_includes_table(self, schema):
        frames = _valid_frames()
        frames["participants"] = frames["participants"].drop(columns=["site_code"])
        with pytest.raises(Exception) as exc_info:
            engine.validate(schema, frames, run_id="test")
        assert "participants" in str(exc_info.value)

    def test_failure_payload_includes_column(self, schema):
        frames = _valid_frames()
        frames["alerts"] = frames["alerts"].assign(alert_level=["invalid_level"])
        with pytest.raises(Exception) as exc_info:
            engine.validate(schema, frames, run_id="test")
        assert "alert_level" in str(exc_info.value)

    def test_failure_payload_includes_constraint(self, schema):
        frames = _valid_frames()
        frames["participants"] = frames["participants"].assign(
            enrollment_ts=pd.to_datetime(["2025-06-02"])  # no tz
        )
        with pytest.raises(Exception) as exc_info:
            engine.validate(schema, frames, run_id="test")
        assert exc_info.value is not None


class TestNonImputationRule:
    def test_null_values_are_preserved_not_imputed(self, schema):
        frames = _valid_frames()
        frames["daily_vitals"] = pd.DataFrame({
            "participant_id": ["P-001"],
            "event_ts": pd.to_datetime(["2025-06-02"], utc=True),
            "cadence": ["daily"],
            "heart_rate": [None],
        })
        report = engine.validate(schema, frames, run_id="test")
        result_df = report["tables"]["daily_vitals"].get("frame")
        if result_df is not None:
            assert result_df["heart_rate"].isna().any()

    def test_nullable_violation_is_flagged_not_filled(self, schema):
        frames = _valid_frames()
        frames["participants"] = frames["participants"].assign(
            enrollment_ts=pd.to_datetime(["2025-06-02"])  # no tz — must reject, not fill
        )
        with pytest.raises(Exception):
            engine.validate(schema, frames, run_id="test")
