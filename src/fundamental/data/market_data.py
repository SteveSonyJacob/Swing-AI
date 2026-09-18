"""Market and valuation data retrieval."""

from typing import Dict, Any, Optional
import yfinance as yf


def fetch_valuation_metrics(symbol: str, info_dict: Optional[Dict[str, Any]] = None) -> Dict[str, Optional[float]]:
    """Fetches key market valuation multiples."""
    if info_dict is None:
        try:
            ticker_sym = symbol if "." in symbol or "^" in symbol else f"{symbol}.NS"
            t = yf.Ticker(ticker_sym)
            info_dict = t.info or {}
        except Exception:
            info_dict = {}

    pe = info_dict.get("trailingPE")
    forward_pe = info_dict.get("forwardPE")
    pb = info_dict.get("priceToBook")
    ev_ebitda = info_dict.get("enterpriseToEbitda")
    div_yield = info_dict.get("dividendYield")
    if div_yield is not None and div_yield > 0:
        # Convert to percentage if < 1.0 (e.g. 0.015 -> 1.5%)
        if div_yield < 1.0:
            div_yield = div_yield * 100.0

    current_price = info_dict.get("currentPrice") or info_dict.get("regularMarketPrice")

    return {
        "current_price": round(float(current_price), 2) if current_price is not None else None,
        "pe": round(float(pe), 2) if pe is not None and pe > 0 else None,
        "forward_pe": round(float(forward_pe), 2) if forward_pe is not None and forward_pe > 0 else None,
        "pb": round(float(pb), 2) if pb is not None and pb > 0 else None,
        "ev_ebitda": round(float(ev_ebitda), 2) if ev_ebitda is not None and ev_ebitda > 0 else None,
        "dividend_yield": round(float(div_yield), 2) if div_yield is not None else None
    }
