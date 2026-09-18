"""Corporate events and earnings calendar analysis."""

from typing import Dict, Any, Optional
from datetime import datetime
import pandas as pd
import yfinance as yf


def check_upcoming_results(symbol: str, as_of_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Checks if earnings results are scheduled in the near future (e.g. within 30 days).
    """
    upcoming = False
    days_to_results = None

    curr_dt = pd.to_datetime(as_of_date) if as_of_date else pd.Timestamp.now()

    try:
        ticker_sym = symbol if "." in symbol or "^" in symbol else f"{symbol}.NS"
        t = yf.Ticker(ticker_sym)
        cal = t.calendar
        if cal is not None:
            # yfinance returns calendar as dict or DataFrame
            earnings_date = None
            if isinstance(cal, dict) and "Earnings Date" in cal:
                dates = cal["Earnings Date"]
                if dates and len(dates) > 0:
                    earnings_date = pd.to_datetime(dates[0])
            elif hasattr(cal, "loc") and "Earnings Date" in cal.index:
                dates = cal.loc["Earnings Date"]
                if not dates.empty:
                    earnings_date = pd.to_datetime(dates.iloc[0])

            if earnings_date is not None:
                # remove tz if needed
                if earnings_date.tz is not None:
                    earnings_date = earnings_date.tz_localize(None)
                if curr_dt.tz is not None:
                    curr_dt = curr_dt.tz_localize(None)

                delta = (earnings_date - curr_dt).days
                if 0 <= delta <= 30:
                    upcoming = True
                    days_to_results = delta
    except Exception:
        pass

    return {
        "upcoming_results": upcoming,
        "days_to_results": days_to_results
    }
