"""Benchmark data acquisition (NIFTY 50 and sector indices)."""

from typing import Optional, Dict
import pandas as pd
from src.data.market_data import fetch_market_data


def fetch_benchmark_data(
    benchmark_symbol: str = "^NSEI",
    as_of_date: Optional[str] = None,
    offline: bool = False
) -> pd.DataFrame:
    """Fetches benchmark OHLCV data."""
    return fetch_market_data(
        symbol=benchmark_symbol,
        timeframe="daily",
        as_of_date=as_of_date,
        min_candles=100,
        offline=offline
    )


def get_sector_symbol_for_stock(symbol: str, sector_map: Optional[Dict[str, str]] = None) -> Optional[str]:
    """Resolves sector index symbol from configuration map."""
    clean_sym = symbol.upper().replace(".NS", "")
    if sector_map and clean_sym in sector_map:
        return sector_map[clean_sym]
    return None
