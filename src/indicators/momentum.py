"""Momentum indicators: RSI (Wilder's) and MACD."""

from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculates RSI using Wilder's exponential smoothing method.
    """
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # Wilder's smoothing is ewm with alpha=1/period
    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi


def interpret_rsi(rsi_value: float) -> str:
    """Interprets RSI value according to Section 10 thresholds."""
    if np.isnan(rsi_value):
        return "unknown"
    if rsi_value < 30.0:
        return "oversold"
    elif rsi_value < 50.0:
        return "weak"
    elif rsi_value < 60.0:
        return "positive"
    elif rsi_value <= 70.0:
        return "strong_momentum"
    else:
        return "potentially_extended"


def calculate_macd(
    series: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculates MACD line, Signal line, and Histogram.
    """
    fast_ema = series.ewm(span=fast_period, adjust=False).mean()
    slow_ema = series.ewm(span=slow_period, adjust=False).mean()
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def add_momentum_indicators(
    df: pd.DataFrame,
    rsi_period: int = 14,
    macd_fast: int = 12,
    macd_slow: int = 26,
    macd_signal: int = 9
) -> pd.DataFrame:
    """Appends RSI and MACD indicators to the DataFrame."""
    res = df.copy()
    close = res["close"]

    res[f"rsi_{rsi_period}"] = calculate_rsi(close, rsi_period)

    macd_line, signal_line, hist = calculate_macd(close, macd_fast, macd_slow, macd_signal)
    res["macd_line"] = macd_line
    res["macd_signal"] = signal_line
    res["macd_histogram"] = hist

    # Crossover detection
    prev_macd = res["macd_line"].shift(1)
    prev_signal = res["macd_signal"].shift(1)
    res["macd_bullish_crossover"] = (prev_macd <= prev_signal) & (res["macd_line"] > res["macd_signal"])
    res["macd_bearish_crossover"] = (prev_macd >= prev_signal) & (res["macd_line"] < res["macd_signal"])

    return res
