"""Unit tests for market data validation."""

import pytest
import pandas as pd
import numpy as np
from src.data.validator import validate_market_data, DataValidationError


def test_validator_empty_data():
    is_valid, reason, df = validate_market_data(pd.DataFrame(), symbol="TEST")
    assert not is_valid
    assert "empty" in reason.lower()


def test_validator_missing_columns():
    df = pd.DataFrame({
        "open": [100, 101],
        "close": [102, 103]
    })
    is_valid, reason, _ = validate_market_data(df, symbol="TEST")
    assert not is_valid
    assert "missing required columns" in reason.lower()


def test_validator_insufficient_candles():
    dates = pd.date_range("2025-01-01", periods=50, freq="B")
    df = pd.DataFrame({
        "open": np.linspace(100, 150, 50),
        "high": np.linspace(102, 152, 50),
        "low": np.linspace(98, 148, 50),
        "close": np.linspace(101, 151, 50),
        "volume": np.full(50, 1000)
    }, index=dates)

    is_valid, reason, _ = validate_market_data(df, symbol="TEST", min_candles=200)
    assert not is_valid
    assert "not enough" in reason.lower()


def test_validator_cleans_and_sorts_data():
    # Out of order dates with duplicates and bad volume
    dates = pd.to_datetime(["2025-01-03", "2025-01-01", "2025-01-02", "2025-01-02"])
    df = pd.DataFrame({
        "open": [103, 101, 102, 102.5],
        "high": [105, 103, 104, 104.5],
        "low": [100, 99, 100, 100.5],
        "close": [104, 102, 103, 103.5],
        "volume": [1000, -50, 2000, 3000]
    }, index=dates)

    is_valid, reason, cleaned = validate_market_data(df, symbol="TEST", min_candles=3)
    assert is_valid
    assert len(cleaned) == 3
    assert cleaned.index.is_monotonic_increasing
    assert (cleaned["volume"] >= 0).all()
