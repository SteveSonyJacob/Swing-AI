"""Chart data extraction service connecting to real market data and technical indicators."""

import logging
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

from src.data.market_data import fetch_market_data
from src.indicators.moving_averages import add_moving_averages
from src.indicators.momentum import add_momentum_indicators
from src.indicators.volume import add_volume_indicators

logger = logging.getLogger(__name__)


def get_stock_chart_data(
    symbol: str,
    limit: int = 90,
    offline: bool = False
) -> Dict[str, Any]:
    """
    Fetches real daily market data and calculated indicators (EMAs, RSI, MACD, Volume)
    for interactive visual chart rendering. Returns actual historical data only.
    """
    sym = symbol.strip().upper().replace(".NS", "")
    try:
        daily_df = fetch_market_data(
            symbol=sym,
            timeframe="daily",
            min_candles=max(limit + 50, 150),
            offline=offline
        )

        if daily_df.empty:
            return {
                "status": "error",
                "symbol": sym,
                "error": f"No market data available for {sym}"
            }

        # Calculate indicators on the full dataset
        daily_df = add_moving_averages(daily_df, short_period=20, medium_period=50, long_period=200)
        daily_df = add_momentum_indicators(daily_df, rsi_period=14, macd_fast=12, macd_slow=26, macd_signal=9)
        daily_df = add_volume_indicators(daily_df, lookback=20)

        # Slice to the requested limit
        tail_df = daily_df.tail(limit)

        candles: List[Dict[str, Any]] = []
        for idx, row in tail_df.iterrows():
            date_str = str(idx).split(" ")[0] if not isinstance(idx, (int, float)) else f"Day {idx}"
            if isinstance(idx, pd.Timestamp):
                date_str = idx.strftime("%Y-%m-%d")

            open_val = float(row.get("open", 0.0))
            high_val = float(row.get("high", 0.0))
            low_val = float(row.get("low", 0.0))
            close_val = float(row.get("close", 0.0))
            vol_val = int(row.get("volume", 0))

            ema20 = float(row.get("ema_20", np.nan))
            ema50 = float(row.get("ema_50", np.nan))
            ema200 = float(row.get("ema_200", np.nan))
            rsi = float(row.get("rsi_14", np.nan))
            macd = float(row.get("macd_line", np.nan))
            macd_sig = float(row.get("macd_signal", np.nan))
            macd_hist = float(row.get("macd_histogram", np.nan))
            rvol = float(row.get("rvol", np.nan))

            candles.append({
                "date": date_str,
                "open": round(open_val, 2),
                "high": round(high_val, 2),
                "low": round(low_val, 2),
                "close": round(close_val, 2),
                "volume": vol_val,
                "ema_20": round(ema20, 2) if not np.isnan(ema20) else None,
                "ema_50": round(ema50, 2) if not np.isnan(ema50) else None,
                "ema_200": round(ema200, 2) if not np.isnan(ema200) else None,
                "rsi_14": round(rsi, 1) if not np.isnan(rsi) else None,
                "macd": round(macd, 2) if not np.isnan(macd) else None,
                "macd_signal": round(macd_sig, 2) if not np.isnan(macd_sig) else None,
                "macd_hist": round(macd_hist, 2) if not np.isnan(macd_hist) else None,
                "rvol": round(rvol, 2) if not np.isnan(rvol) else None
            })

        latest_price = candles[-1]["close"] if candles else 0.0
        prev_price = candles[-2]["close"] if len(candles) >= 2 else latest_price
        change_pct = round(((latest_price - prev_price) / prev_price) * 100, 2) if prev_price > 0 else 0.0

        return {
            "status": "success",
            "symbol": sym,
            "market": "NSE",
            "is_offline": offline,
            "candle_count": len(candles),
            "latest_price": latest_price,
            "change_pct": change_pct,
            "candles": candles
        }

    except Exception as e:
        logger.warning(f"Failed to generate chart data for {sym}: {e}")
        return {
            "status": "error",
            "symbol": sym,
            "error": str(e)
        }
