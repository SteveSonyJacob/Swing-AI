"""Company profile and classification."""

from typing import Dict, Any, Optional
import yfinance as yf


def classify_market_cap(mcap: Optional[float]) -> str:
    """Classifies Indian market cap into Large Cap, Mid Cap, Small Cap (in INR Crores)."""
    if mcap is None or mcap <= 0:
        return "Unknown"
    # Assuming mcap is in absolute INR; 1 Cr = 10,000,000
    mcap_cr = mcap / 1e7
    if mcap_cr >= 20000:
        return "Large Cap"
    elif mcap_cr >= 5000:
        return "Mid Cap"
    else:
        return "Small Cap"


def fetch_company_profile(
    symbol: str,
    info_dict: Optional[Dict[str, Any]] = None,
    offline: bool = False
) -> Dict[str, Any]:
    """Retrieves company profile, sector, and industry."""
    if info_dict is None:
        if offline:
            info_dict = {
                "shortName": symbol,
                "sector": "Default",
                "industry": "General",
                "marketCap": 250000000000.0,
                "sharesOutstanding": 1000000000,
                "currency": "INR",
                "heldPercentInsiders": 0.51,
                "heldPercentInstitutions": 0.28
            }
        else:
            try:
                ticker_sym = symbol if "." in symbol or "^" in symbol else f"{symbol}.NS"
                t = yf.Ticker(ticker_sym)
                info_dict = t.info or {}
            except Exception:
                info_dict = {}

    mcap = info_dict.get("marketCap")
    return {
        "symbol": symbol.upper().replace(".NS", ""),
        "name": info_dict.get("shortName") or info_dict.get("longName") or symbol,
        "sector": info_dict.get("sector", "Unknown"),
        "industry": info_dict.get("industry", "Unknown"),
        "market_cap": mcap,
        "market_cap_category": classify_market_cap(mcap),
        "shares_outstanding": info_dict.get("sharesOutstanding"),
        "currency": info_dict.get("currency", "INR"),
        "heldPercentInsiders": info_dict.get("heldPercentInsiders"),
        "heldPercentInstitutions": info_dict.get("heldPercentInstitutions")
    }
