"""News and headline scraper for Indian equity catalyst analysis."""

import logging
from typing import Dict, Any, List, Optional
import requests
from bs4 import BeautifulSoup
import yfinance as yf

logger = logging.getLogger(__name__)

# Deterministic offline mock news database for testing and offline runs
OFFLINE_NEWS_DATABASE: Dict[str, List[Dict[str, str]]] = {
    "TRENT": [
        {"title": "Trent Q2 profit surges 46% YoY driven by robust Westside & Zudio expansion", "source": "Economic Times"},
        {"title": "Trent adds 35 new stores, management signals bullish festive demand", "source": "Moneycontrol"},
        {"title": "Brokerages raise target price on Trent following retail momentum", "source": "CNBC-TV18"}
    ],
    "RELIANCE": [
        {"title": "Reliance Jio and Retail drive steady consolidated revenue growth", "source": "Business Standard"},
        {"title": "Reliance Industries signs key green energy and clean power consortium agreement", "source": "Livemint"},
        {"title": "Morgan Stanley reiterates overweight rating on Reliance ahead of AGM", "source": "Reuters"}
    ],
    "TATASTEEL": [
        {"title": "Tata Steel UK transition advances with government green grant agreement", "source": "Financial Express"},
        {"title": "Indian steel demand remains robust with higher quarterly production", "source": "Economic Times"}
    ],
    "BHEL": [
        {"title": "BHEL secures mega thermal power equipment order worth Rs 6,100 crore", "source": "Livemint"},
        {"title": "BHEL rallies 4% as PSU order book crosses record high watermark", "source": "Moneycontrol"}
    ],
    "BAJFINANCE": [
        {"title": "Bajaj Finance assets under management surge 29% YoY in quarterly update", "source": "CNBC-TV18"},
        {"title": "RBI lifts restriction on Bajaj Finance digital lending products", "source": "Economic Times"}
    ],
    "APOLLOHOSP": [
        {"title": "Apollo Hospitals expands digital health network, margins expand 140 bps", "source": "Livemint"},
        {"title": "Hospital occupancy reaches multi-quarter peak in key tier-1 metros", "source": "Business Standard"}
    ],
    "EICHERMOT": [
        {"title": "Royal Enfield monthly domestic sales volume climbs 11% YoY", "source": "Autocar India"},
        {"title": "Eicher Motors management guides steady export recovery for FY25", "source": "Economic Times"}
    ],
    "HFCL": [
        {"title": "HFCL wins optical fiber export orders worth Rs 450 crore in Europe", "source": "Moneycontrol"},
        {"title": "HFCL expanding 5G indigenous telecom gear manufacturing capacity", "source": "Business Line"}
    ]
}


def fetch_candidate_news(
    symbol: str,
    max_items: int = 5,
    offline: bool = False,
    timeout: int = 4
) -> List[Dict[str, str]]:
    """
    Fetches recent news headlines for an Indian equity symbol.
    
    Order of preference:
      1. If offline: returns deterministic synthetic news.
      2. If live: queries Google News RSS for Indian equities.
      3. If RSS fails: falls back to yfinance ticker news.
      4. Fallback: returns synthetic or generic headlines.
    """
    sym = symbol.strip().upper().replace(".NS", "")

    if offline:
        return get_offline_news(sym, max_items)

    # 1. Google News RSS search
    try:
        url = f"https://news.google.com/rss/search?q={sym}+NSE+stock+India&hl=en-IN&gl=IN&ceid=IN:en"
        resp = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            timeout=timeout
        )
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, "xml")
            items = soup.find_all("item")[:max_items]
            headlines: List[Dict[str, str]] = []
            for item in items:
                title = item.title.get_text(strip=True) if item.title else ""
                source_tag = item.find("source")
                source = source_tag.get_text(strip=True) if source_tag else "Google News"
                if title:
                    headlines.append({"title": title, "source": source})
            if headlines:
                return headlines
    except Exception as e:
        logger.debug(f"Google News RSS query failed for {sym}: {e}")

    # 2. yfinance news fallback
    try:
        ticker = yf.Ticker(f"{sym}.NS")
        yf_news = getattr(ticker, "news", []) or []
        headlines = []
        for n in yf_news[:max_items]:
            t = n.get("title")
            pub = n.get("publisher", "Yahoo Finance")
            if t:
                headlines.append({"title": t, "source": pub})
        if headlines:
            return headlines
    except Exception as e:
        logger.debug(f"yfinance news fetch failed for {sym}: {e}")

    # 3. Fallback to offline synthetic news
    return get_offline_news(sym, max_items)


def get_offline_news(symbol: str, max_items: int = 5) -> List[Dict[str, str]]:
    """Returns deterministic synthetic news for testing or offline mode."""
    sym = symbol.strip().upper().replace(".NS", "")
    if sym in OFFLINE_NEWS_DATABASE:
        return OFFLINE_NEWS_DATABASE[sym][:max_items]

    # Generic deterministic placeholder
    return [
        {
            "title": f"{sym} announces upcoming quarterly board meeting and business review",
            "source": "Exchange Filing"
        },
        {
            "title": f"Market analysts note active trading interest in {sym} shares on NSE",
            "source": "Market News"
        }
    ][:max_items]
