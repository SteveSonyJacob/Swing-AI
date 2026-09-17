"""Market data acquisition with local caching, point-in-time filtering, and offline synthetic fallback."""

import os
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import yfinance as yf

from src.data.validator import validate_market_data, DataValidationError


DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def format_symbol_for_provider(symbol: str) -> str:
    """Format symbol for yfinance (e.g., append .NS for Indian equities if no suffix)."""
    symbol_upper = symbol.upper().strip()
    if symbol_upper.startswith("^") or "." in symbol_upper:
        return symbol_upper
    return f"{symbol_upper}.NS"


def generate_synthetic_data(
    symbol: str,
    timeframe: str = "daily",
    periods: int = 300,
    end_date: Optional[str] = None
) -> pd.DataFrame:
    """Generates deterministic synthetic OHLCV data for testing and offline execution."""
    rng = np.random.default_rng(seed=abs(hash(symbol)) % (2**32))
    
    if end_date:
        end_dt = pd.to_datetime(end_date)
    else:
        end_dt = pd.Timestamp.now()

    if timeframe == "daily":
        freq = "B"
        dates = pd.date_range(end=end_dt, periods=periods, freq=freq)
        base_price = 1000.0 + (abs(hash(symbol)) % 1000)
        daily_returns = rng.normal(0.0008, 0.015, size=periods)
    else:
        freq = "h"
        dates = pd.date_range(end=end_dt, periods=periods, freq=freq)
        base_price = 1000.0 + (abs(hash(symbol)) % 1000)
        daily_returns = rng.normal(0.0002, 0.006, size=periods)

    price_series = base_price * np.cumprod(1 + daily_returns)
    highs = price_series * (1 + rng.uniform(0.002, 0.02, size=periods))
    lows = price_series * (1 - rng.uniform(0.002, 0.02, size=periods))
    opens = price_series * (1 + rng.normal(0, 0.005, size=periods))
    closes = price_series
    
    # Ensure open/close are within high/low
    highs = np.maximum.reduce([highs, opens, closes])
    lows = np.minimum.reduce([lows, opens, closes])
    
    volumes = rng.integers(100_000, 5_000_000, size=periods)

    df = pd.DataFrame({
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": volumes
    }, index=dates)
    df.index.name = "date"
    return df


def fetch_market_data(
    symbol: str,
    timeframe: str = "daily",
    as_of_date: Optional[str] = None,
    min_candles: Optional[int] = None,
    offline: bool = False
) -> pd.DataFrame:
    """
    Fetches daily or hourly market data for a given symbol.
    Applies local caching, point-in-time truncation, and data validation.
    """
    clean_sym = symbol.replace("^", "").replace(".", "_").upper()
    cache_file = DATA_DIR / f"{clean_sym}_{timeframe}.csv"
    df: Optional[pd.DataFrame] = None

    if min_candles is None:
        min_candles = 200 if timeframe == "daily" else 50

    if not offline:
        try:
            ticker_str = format_symbol_for_provider(symbol)
            ticker = yf.Ticker(ticker_str)
            if timeframe == "daily":
                # Fetch 2 years of daily data
                raw_df = ticker.history(period="2y", interval="1d", auto_adjust=True)
            elif timeframe == "hourly":
                # Fetch up to 730 days of hourly data (yfinance max for 1h is 730d)
                raw_df = ticker.history(period="730d", interval="1h", auto_adjust=True)
            else:
                raise ValueError(f"Unsupported timeframe: {timeframe}")

            if raw_df is not None and not raw_df.empty:
                raw_df.columns = [c.lower() for c in raw_df.columns]
                # Keep standard columns
                keep_cols = [c for c in ["open", "high", "low", "close", "volume"] if c in raw_df.columns]
                df = raw_df[keep_cols].copy()
                # Cache to disk
                df.to_csv(cache_file)
        except Exception as e:
            # Fall back to disk cache if network fails
            if cache_file.exists():
                df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
            else:
                df = None

    if df is None or df.empty:
        if cache_file.exists():
            df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
        elif offline:
            # Generate deterministic synthetic data for offline running
            df = generate_synthetic_data(
                symbol=symbol,
                timeframe=timeframe,
                periods=350 if timeframe == "daily" else 150,
                end_date=as_of_date
            )
        else:
            raise DataValidationError(f"Unable to retrieve data for {symbol} ({timeframe})", symbol=symbol)

    # Point-in-time filtering to avoid look-ahead bias
    if as_of_date:
        as_of_dt = pd.to_datetime(as_of_date)
        # Match timezone awareness if applicable
        if df.index.tz is not None and as_of_dt.tzinfo is None:
            as_of_dt = as_of_dt.tz_localize(df.index.tz)
        elif df.index.tz is None and as_of_dt.tzinfo is not None:
            as_of_dt = as_of_dt.tz_localize(None)
        df = df[df.index <= as_of_dt]

    # Validate data
    is_valid, reason, cleaned_df = validate_market_data(
        df,
        symbol=symbol,
        min_candles=min_candles,
        timeframe=timeframe
    )
    if not is_valid:
        raise DataValidationError(reason or "Validation failed", symbol=symbol)

    return cleaned_df
