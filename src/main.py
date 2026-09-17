"""Main entry point for Agent 2 — Technical Analysis Engine."""

import sys
import os
from pathlib import Path
import argparse
import json
from datetime import datetime
from typing import Dict, Any, Optional
import yaml
import pandas as pd

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.market_data import fetch_market_data
from src.data.benchmark_data import fetch_benchmark_data, get_sector_symbol_for_stock
from src.data.validator import DataValidationError
from src.indicators.moving_averages import add_moving_averages
from src.indicators.momentum import add_momentum_indicators, interpret_rsi
from src.indicators.volume import add_volume_indicators
from src.indicators.volatility import add_volatility_indicators
from src.analysis.daily_analysis import analyze_daily_trend
from src.analysis.hourly_analysis import analyze_hourly_trend
from src.analysis.trend_analysis import evaluate_trend_confirmation
from src.analysis.breakout import detect_breakouts
from src.analysis.support_resistance import identify_key_levels
from src.analysis.relative_strength import analyze_relative_strength
from src.scoring.technical_score import compute_technical_score
from src.risk.trade_levels import calculate_trade_levels
from src.output.formatter import format_agent_output, format_error_output


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Loads settings.yaml configuration."""
    if config_path is None:
        config_path = PROJECT_ROOT / "config" / "settings.yaml"

    if not config_path.exists():
        return {}

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def run_technical_analysis(
    symbol: str,
    as_of_date: Optional[str] = None,
    offline: bool = False,
    market: str = "NSE",
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Executes the deterministic end-to-end technical analysis pipeline for a symbol.
    """
    if config is None:
        config = load_config()

    ind_cfg = config.get("indicators", {})
    ema_cfg = ind_cfg.get("ema", {})
    rsi_cfg = ind_cfg.get("rsi", {})
    macd_cfg = ind_cfg.get("macd", {})
    atr_cfg = ind_cfg.get("atr", {})
    vol_cfg = ind_cfg.get("volume", {})
    breakout_cfg = config.get("breakouts", {})
    bench_cfg = config.get("benchmarks", {})
    weights_cfg = config.get("scoring", {}).get("weights", {})

    try:
        # 1. Fetch Daily Data
        daily_df = fetch_market_data(
            symbol=symbol,
            timeframe="daily",
            as_of_date=as_of_date,
            min_candles=200,
            offline=offline
        )

        # 2. Fetch Hourly Data
        hourly_df = fetch_market_data(
            symbol=symbol,
            timeframe="hourly",
            as_of_date=as_of_date,
            min_candles=30,
            offline=offline
        )

        # 3. Fetch Benchmarks (NIFTY 50 and Sector)
        benchmark_sym = bench_cfg.get("market", "^NSEI")
        sector_sym = get_sector_symbol_for_stock(symbol, bench_cfg.get("sector_map", {}))

        try:
            nifty_df = fetch_benchmark_data(
                benchmark_symbol=benchmark_sym,
                as_of_date=as_of_date,
                offline=offline
            )
        except Exception:
            nifty_df = None

        sector_df = None
        if sector_sym:
            try:
                sector_df = fetch_benchmark_data(
                    benchmark_symbol=sector_sym,
                    as_of_date=as_of_date,
                    offline=offline
                )
            except Exception:
                sector_df = None

    except DataValidationError as e:
        return e.to_dict()
    except Exception as e:
        return format_error_output(symbol, str(e))

    # 4. Calculate Indicators on Daily
    daily_df = add_moving_averages(
        daily_df,
        short_period=ema_cfg.get("short", 20),
        medium_period=ema_cfg.get("medium", 50),
        long_period=ema_cfg.get("long", 200),
        slope_window=ema_cfg.get("slope_window", 5)
    )
    daily_df = add_momentum_indicators(
        daily_df,
        rsi_period=rsi_cfg.get("period", 14),
        macd_fast=macd_cfg.get("fast", 12),
        macd_slow=macd_cfg.get("slow", 26),
        macd_signal=macd_cfg.get("signal", 9)
    )
    daily_df = add_volume_indicators(
        daily_df,
        lookback=vol_cfg.get("lookback", 20),
        breakout_threshold=vol_cfg.get("breakout_multiplier", 1.5),
        expansion_threshold=vol_cfg.get("expansion_threshold", 1.2),
        contraction_threshold=vol_cfg.get("contraction_threshold", 0.8)
    )
    daily_df = add_volatility_indicators(
        daily_df,
        period=atr_cfg.get("period", 14)
    )

    # 5. Calculate Indicators on Hourly
    hourly_df = add_moving_averages(
        hourly_df,
        short_period=ema_cfg.get("short", 20),
        medium_period=ema_cfg.get("medium", 50),
        long_period=min(ema_cfg.get("long", 200), len(hourly_df) - 1),
        slope_window=ema_cfg.get("slope_window", 5)
    )
    hourly_df = add_momentum_indicators(
        hourly_df,
        rsi_period=rsi_cfg.get("period", 14),
        macd_fast=macd_cfg.get("fast", 12),
        macd_slow=macd_cfg.get("slow", 26),
        macd_signal=macd_cfg.get("signal", 9)
    )
    hourly_df = add_volume_indicators(
        hourly_df,
        lookback=vol_cfg.get("lookback", 20)
    )

    # 6. Trend Analysis
    daily_trend = analyze_daily_trend(daily_df)
    hourly_trend = analyze_hourly_trend(hourly_df)
    trend_conf = evaluate_trend_confirmation(daily_trend["trend"], hourly_trend["trend"])

    # 7. Momentum & Volume Snapshots
    latest_daily = daily_df.iloc[-1]
    latest_hourly = hourly_df.iloc[-1]

    daily_momentum = {
        "rsi": float(latest_daily.get(f"rsi_{rsi_cfg.get('period', 14)}", 50.0)),
        "macd_line": float(latest_daily.get("macd_line", 0.0)),
        "macd_signal": float(latest_daily.get("macd_signal", 0.0)),
        "macd_histogram": float(latest_daily.get("macd_histogram", 0.0)),
        "macd_bullish_crossover": bool(latest_daily.get("macd_bullish_crossover", False))
    }

    hourly_momentum = {
        "rsi": float(latest_hourly.get(f"rsi_{rsi_cfg.get('period', 14)}", 50.0)),
        "macd_line": float(latest_hourly.get("macd_line", 0.0)),
        "macd_signal": float(latest_hourly.get("macd_signal", 0.0)),
        "macd_histogram": float(latest_hourly.get("macd_histogram", 0.0))
    }

    volume_data = {
        "rvol": float(latest_daily.get("rvol", 1.0)),
        "volume_expansion": bool(latest_daily.get("volume_expansion", False)),
        "volume_contraction": bool(latest_daily.get("volume_contraction", False)),
        "price_volume_confirmation": bool(latest_daily.get("price_volume_confirmation", False))
    }

    # 8. Breakout Detection (excluding current candle for prior highs)
    breakout_data = detect_breakouts(
        daily_df,
        short_window=breakout_cfg.get("short", 20),
        long_window=breakout_cfg.get("long", 50),
        volume_threshold=vol_cfg.get("breakout_multiplier", 1.5)
    )

    # 9. Support & Resistance Levels
    levels_data = identify_key_levels(daily_df)

    # 10. Volatility
    atr_val = float(latest_daily.get(f"atr_{atr_cfg.get('period', 14)}", 0.0))
    atr_pct = float(latest_daily.get("atr_percent", 0.0))
    volatility_data = {
        "atr_14": atr_val,
        "atr_percent": atr_pct
    }

    # 11. Relative Strength vs Benchmarks
    rs_data = analyze_relative_strength(daily_df, nifty_df, sector_df)

    # 12. Scoring Engine
    scoring_result = compute_technical_score(
        daily_analysis=daily_trend,
        hourly_analysis=hourly_trend,
        momentum_data=daily_momentum,
        volume_data=volume_data,
        breakout_data=breakout_data,
        sr_levels=levels_data,
        rs_data=rs_data,
        atr_percent=atr_pct,
        weights=weights_cfg
    )

    technical_score = scoring_result["technical_score"]
    score_breakdown = scoring_result["score_breakdown"]

    # 13. Risk Management & Trade Levels
    trade_setup = calculate_trade_levels(
        current_close=float(latest_daily["close"]),
        atr=atr_val,
        levels=levels_data,
        trend=daily_trend["trend"],
        stop_atr_multiplier=atr_cfg.get("stop_multiplier", 1.5),
        technical_score=technical_score
    )

    # 14. Format Final Canonical Output
    analysis_ts = str(latest_daily.name) if hasattr(latest_daily, "name") else datetime.now().isoformat()
    if isinstance(analysis_ts, pd.Timestamp):
        analysis_ts = analysis_ts.isoformat()

    final_json = format_agent_output(
        symbol=symbol,
        market=market,
        analysis_timestamp=analysis_ts,
        technical_score=technical_score,
        score_breakdown=score_breakdown,
        daily_trend=daily_trend,
        hourly_trend=hourly_trend,
        daily_momentum=daily_momentum,
        hourly_momentum=hourly_momentum,
        volume_data=volume_data,
        breakout_data=breakout_data,
        levels_data=levels_data,
        volatility_data=volatility_data,
        relative_strength_data=rs_data,
        trade_setup_data=trade_setup
    )

    return final_json


def main():
    parser = argparse.ArgumentParser(description="Agent 2 — Technical Analysis Engine")
    parser.add_argument("--symbol", type=str, required=True, help="Stock symbol (e.g., RELIANCE, TCS, INFY)")
    parser.add_argument("--date", type=str, default=None, help="Analysis as-of date (YYYY-MM-DD) for backtest/point-in-time analysis")
    parser.add_argument("--offline", action="store_true", help="Run in offline mode with cached or synthetic data")
    parser.add_argument("--json-only", action="store_true", help="Print only raw JSON output to stdout")
    parser.add_argument("--output", type=str, default=None, help="Path to write JSON output")
    args = parser.parse_args()

    result = run_technical_analysis(
        symbol=args.symbol,
        as_of_date=args.date,
        offline=args.offline
    )

    json_str = json.dumps(result, indent=2)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(json_str)

    if args.json_only:
        print(json_str)
    else:
        print("\n=======================================================")
        print(f" AGENT 2 - TECHNICAL ANALYSIS: {result.get('symbol')} ({result.get('status')})")
        print("=======================================================")
        if result.get("status") == "success":
            print(f"Technical Score : {result.get('technical_score')}/100")
            print(f"Daily Trend     : {result['trend']['daily']} (EMA alignment: {result['trend']['daily_ema_alignment']})")
            print(f"Hourly Trend    : {result['trend']['hourly']} (EMA alignment: {result['trend']['hourly_ema_alignment']})")
            print(f"Market Structure: {result['trend']['market_structure']}")
            print(f"Daily RSI (14)  : {result['momentum']['daily_rsi']} | MACD: {result['momentum']['daily_macd']}")
            print(f"Relative Volume : {result['volume']['relative_volume']}x (Confirmed: {result['volume']['confirmation']})")
            print(f"Breakout        : {result['breakout']['detected']} ({result['breakout']['type']}, Volume Confirmed: {result['breakout']['volume_confirmed']})")
            print(f"Support/Resist  : Support: {result['levels']['support']} | Resist: {result['levels']['resistance']}")
            print(f"ATR (14)        : {result['volatility']['atr_14']} ({result['volatility']['atr_percent']}%)")
            print(f"Trade Setup     : Direction: {result['trade_setup']['direction']}, Entry: {result['trade_setup']['entry_zone']}, Stop: {result['trade_setup']['stop_loss']}, Target 1: {result['trade_setup']['target_1']}, R:R: {result['trade_setup']['risk_reward']}")
            print("\nScore Breakdown:")
            for k, v in result['score_breakdown'].items():
                print(f"  - {k:<20}: {v} pts")
        else:
            print(f"Reason: {result.get('reason')}")
        print("=======================================================\n")


if __name__ == "__main__":
    main()
