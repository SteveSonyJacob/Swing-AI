"""Relative strength analysis against NIFTY 50 and Sectoral Index."""

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np


def calculate_return(df: pd.DataFrame, trading_days: int) -> Optional[float]:
    """Calculates percentage return over the last N trading days."""
    if len(df) < trading_days + 1:
        return None
    close = df["close"]
    latest_close = float(close.iloc[-1])
    past_close = float(close.iloc[-(trading_days + 1)])
    if past_close <= 0:
        return None
    return ((latest_close - past_close) / past_close) * 100.0


def analyze_relative_strength(
    stock_df: pd.DataFrame,
    nifty_df: Optional[pd.DataFrame] = None,
    sector_df: Optional[pd.DataFrame] = None
) -> Dict[str, Optional[float]]:
    """
    Computes outperformance of stock vs NIFTY 50 and sector index over 1 week (5 days),
    1 month (21 days), and 3 months (63 days).
    """
    stock_1w = calculate_return(stock_df, 5)
    stock_1m = calculate_return(stock_df, 21)
    stock_3m = calculate_return(stock_df, 63)

    vs_nifty_1m = None
    vs_nifty_1w = None
    vs_nifty_3m = None

    if nifty_df is not None and not nifty_df.empty:
        nifty_1w = calculate_return(nifty_df, 5)
        nifty_1m = calculate_return(nifty_df, 21)
        nifty_3m = calculate_return(nifty_df, 63)

        if stock_1m is not None and nifty_1m is not None:
            vs_nifty_1m = stock_1m - nifty_1m
        if stock_1w is not None and nifty_1w is not None:
            vs_nifty_1w = stock_1w - nifty_1w
        if stock_3m is not None and nifty_3m is not None:
            vs_nifty_3m = stock_3m - nifty_3m

    vs_sector_1m = None
    if sector_df is not None and not sector_df.empty:
        sector_1m = calculate_return(sector_df, 21)
        if stock_1m is not None and sector_1m is not None:
            vs_sector_1m = stock_1m - sector_1m

    return {
        "vs_nifty_1m": round(vs_nifty_1m, 2) if vs_nifty_1m is not None else None,
        "vs_sector_1m": round(vs_sector_1m, 2) if vs_sector_1m is not None else None,
        "vs_nifty_1w": round(vs_nifty_1w, 2) if vs_nifty_1w is not None else None,
        "vs_nifty_3m": round(vs_nifty_3m, 2) if vs_nifty_3m is not None else None,
        "stock_1m_return": round(stock_1m, 2) if stock_1m is not None else None
    }
