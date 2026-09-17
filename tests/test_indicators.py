"""Unit tests for technical indicators."""

import pytest
import pandas as pd
import numpy as np
from src.indicators.moving_averages import calculate_ema, calculate_ema_slope, add_moving_averages
from src.indicators.momentum import calculate_rsi, calculate_macd, interpret_rsi, add_momentum_indicators
from src.indicators.volume import calculate_relative_volume, add_volume_indicators
from src.indicators.volatility import calculate_atr, add_volatility_indicators


@pytest.fixture
def sample_ohlcv():
    dates = pd.date_range("2024-01-01", periods=250, freq="B")
    price = 100.0 + np.cumsum(np.random.normal(0.5, 1.0, 250))
    # Ensure all prices > 0
    price = np.maximum(price, 10.0)
    
    df = pd.DataFrame({
        "open": price,
        "high": price + 2.0,
        "low": price - 2.0,
        "close": price + 0.5,
        "volume": np.random.randint(10000, 50000, 250)
    }, index=dates)
    return df


def test_ema_and_slopes(sample_ohlcv):
    df = add_moving_averages(sample_ohlcv, short_period=20, medium_period=50, long_period=200)
    assert "ema_20" in df.columns
    assert "ema_50" in df.columns
    assert "ema_200" in df.columns
    assert "ema_20_slope" in df.columns
    
    # EMA should be non-null after warmup
    assert not df["ema_20"].isna().any()
    assert not df["ema_200"].isna().any()


def test_rsi_bounds_and_interpretation(sample_ohlcv):
    rsi = calculate_rsi(sample_ohlcv["close"], period=14)
    valid_rsi = rsi.dropna()
    assert (valid_rsi >= 0.0).all() and (valid_rsi <= 100.0).all()

    assert interpret_rsi(25.0) == "oversold"
    assert interpret_rsi(45.0) == "weak"
    assert interpret_rsi(55.0) == "positive"
    assert interpret_rsi(65.0) == "strong_momentum"
    assert interpret_rsi(75.0) == "potentially_extended"


def test_macd(sample_ohlcv):
    df = add_momentum_indicators(sample_ohlcv)
    assert "macd_line" in df.columns
    assert "macd_signal" in df.columns
    assert "macd_histogram" in df.columns
    
    # Check histogram = macd_line - signal_line
    diff = (df["macd_line"] - df["macd_signal"]) - df["macd_histogram"]
    assert np.allclose(diff.dropna(), 0.0)


def test_relative_volume(sample_ohlcv):
    # Artificially spike the last candle volume to 3x mean
    sample_ohlcv.iloc[-1, sample_ohlcv.columns.get_loc("volume")] = 150000
    df = add_volume_indicators(sample_ohlcv, lookback=20)
    
    assert "rvol" in df.columns
    latest_rvol = df["rvol"].iloc[-1]
    assert latest_rvol > 2.0
    assert df["volume_expansion"].iloc[-1] == True


def test_atr(sample_ohlcv):
    df = add_volatility_indicators(sample_ohlcv, period=14)
    assert "atr_14" in df.columns
    assert "atr_percent" in df.columns
    
    atr_vals = df["atr_14"].dropna()
    assert (atr_vals > 0).all()
    atr_pct = df["atr_percent"].dropna()
    assert (atr_pct > 0).all()
