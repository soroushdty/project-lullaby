"""Unit detection, coercion helpers, and UnitAmbiguityError (FR-016)."""

from __future__ import annotations

import pandas as pd

from src.ingestion.adapters.base import UnitAmbiguityError


def fahrenheit_to_celsius(series: pd.Series) -> pd.Series:
    """Convert °F values to °C. Returns a new Series."""
    return (series - 32) * 5 / 9


def lbs_to_kg(series: pd.Series) -> pd.Series:
    """Convert lb values to kg. Returns a new Series."""
    return series * 0.453592


def check_temperature_unit(
    series: pd.Series,
    declared_unit: str | None,
    column_name: str,
) -> pd.Series:
    """Return series in °C, converting from declared_unit if needed.

    - declared_unit='C' or 'celsius' → return as-is
    - declared_unit='F' or 'fahrenheit' → convert to °C
    - declared_unit=None → raise UnitAmbiguityError
    """
    if declared_unit is None:
        sample = str(series.dropna().iloc[0]) if not series.dropna().empty else "N/A"
        raise UnitAmbiguityError(column=column_name, sample_value=sample)
    normalized = declared_unit.strip().upper()
    if normalized in ("F", "FAHRENHEIT"):
        return fahrenheit_to_celsius(series)
    if normalized in ("C", "CELSIUS"):
        return series
    sample = str(series.dropna().iloc[0]) if not series.dropna().empty else "N/A"
    raise UnitAmbiguityError(column=column_name, sample_value=sample)
