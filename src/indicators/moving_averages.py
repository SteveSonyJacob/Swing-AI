"""Moving average indicators: EMA 20, 50, 200 and their slopes."""

from typing import Dict, Tuple, Optional
import pandas as pd
import numpy as np


def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """Calculates Exponential Moving Average for a given period."""
    return series.ewm(span=period, adjust=False).mean()


def calculate_ema_slope(ema_series: pd.Series, window: int = 5) -> pd.Series:
    """
    Calculates normalized slope of EMA over a specified window:
    (EMA_current - EMA_N_periods_ago) / EMA_N_periods_ago
    """
    shift_val = ema_series.shift(window)
    slope = (ema_series - shift_val) / shift_val
    return slope


def add_moving_averages(
    df: pd.DataFrame,
    short_period: int = 20,
    medium_period: int = 50,
    long_period: int = 200,
    slope_window: int = 5
) -> pd.DataFrame:
    """
    Appends EMA 20, 50, 200 and their slopes to the DataFrame.
    """
    res = df.copy()
    close = res["close"]

    res[f"ema_{short_period}"] = calculate_ema(close, short_period)
    res[f"ema_{medium_period}"] = calculate_ema(close, medium_period)
    res[f"ema_{long_period}"] = calculate_ema(close, long_period)

    res[f"ema_{short_period}_slope"] = calculate_ema_slope(res[f"ema_{short_period}"], slope_window)
    res[f"ema_{medium_period}_slope"] = calculate_ema_slope(res[f"ema_{medium_period}"], slope_window)
    res[f"ema_{long_period}_slope"] = calculate_ema_slope(res[f"ema_{long_period}"], slope_window)

    return res
