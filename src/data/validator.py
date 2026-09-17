"""Data validation module for Agent 2."""

from typing import Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np


REQUIRED_COLUMNS = ["open", "high", "low", "close", "volume"]


class DataValidationError(Exception):
    """Exception raised when market data is structurally invalid or insufficient."""
    def __init__(self, reason: str, symbol: str = ""):
        super().__init__(reason)
        self.reason = reason
        self.symbol = symbol

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": "insufficient_data",
            "symbol": self.symbol,
            "reason": self.reason
        }


def validate_market_data(
    df: Optional[pd.DataFrame],
    symbol: str = "",
    min_candles: int = 200,
    timeframe: str = "daily"
) -> Tuple[bool, Optional[str], pd.DataFrame]:
    """
    Validates and cleans market OHLCV data.

    Returns:
        (is_valid, error_reason, cleaned_dataframe)
    """
    if df is None or df.empty:
        return False, f"Data is empty for {symbol} ({timeframe})", pd.DataFrame()

    cleaned_df = df.copy()

    # Normalize column names to lowercase
    cleaned_df.columns = [str(col).lower().strip() for col in cleaned_df.columns]

    # Verify required columns exist
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in cleaned_df.columns]
    if missing_cols:
        return False, f"Missing required columns: {', '.join(missing_cols)}", cleaned_df

    # Handle datetime index or column
    if not isinstance(cleaned_df.index, pd.DatetimeIndex):
        if "date" in cleaned_df.columns:
            cleaned_df["date"] = pd.to_datetime(cleaned_df["date"])
            cleaned_df.set_index("date", inplace=True)
        elif "datetime" in cleaned_df.columns:
            cleaned_df["datetime"] = pd.to_datetime(cleaned_df["datetime"])
            cleaned_df.set_index("datetime", inplace=True)
        else:
            try:
                cleaned_df.index = pd.to_datetime(cleaned_df.index)
            except Exception as e:
                return False, f"Invalid datetime index or column: {str(e)}", cleaned_df

    # Remove duplicate timestamps
    if cleaned_df.index.has_duplicates:
        cleaned_df = cleaned_df[~cleaned_df.index.duplicated(keep="last")]

    # Ensure chronologically sorted
    cleaned_df.sort_index(inplace=True)

    # Cast numeric columns
    for col in REQUIRED_COLUMNS:
        cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors="coerce")

    # Drop rows with NaN in critical price columns
    cleaned_df.dropna(subset=["open", "high", "low", "close"], inplace=True)

    # Validate non-negative volume
    cleaned_df["volume"] = cleaned_df["volume"].fillna(0)
    cleaned_df.loc[cleaned_df["volume"] < 0, "volume"] = 0

    # High must be >= Low
    invalid_hl = cleaned_df["high"] < cleaned_df["low"]
    if invalid_hl.any():
        # Correct or drop inconsistent candles
        cleaned_df = cleaned_df[~invalid_hl]

    # Check minimum required rows
    if len(cleaned_df) < min_candles:
        return (
            False,
            f"Not enough {timeframe} candles (got {len(cleaned_df)}, requires at least {min_candles})",
            cleaned_df
        )

    return True, None, cleaned_df
