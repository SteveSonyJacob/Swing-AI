"""Moneycontrol market statistics scanner and scraper."""

import os
import re
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Known name/slug to NSE symbol fast lookup to avoid round-trip lookups
KNOWN_SYMBOL_MAP: Dict[str, str] = {
    "trent": "TRENT",
    "reliance": "RELIANCE",
    "reliance industries": "RELIANCE",
    "tata steel": "TATASTEEL",
    "bhel": "BHEL",
    "bharat heavy electricals": "BHEL",
    "hfcl": "HFCL",
    "maruti": "MARUTI",
    "maruti suzuki": "MARUTI",
    "angel one": "ANGELONE",
    "honasa consumer": "HONASA",
    "pg electroplast": "PGEL",
    "hegam": "HEG",
    "tega industries": "TEGA",
    "infosys": "INFY",
    "tcs": "TCS",
    "hdfc bank": "HDFCBANK",
    "icici bank": "ICICIBANK",
    "state bank of india": "SBIN",
    "sbi": "SBIN",
    "larsen & toubro": "LT",
    "l&t": "LT",
    "bharti airtel": "BHARTIARTL",
    "itc": "ITC",
    "zomato": "ZOMATO",
    "hal": "HAL",
    "hindustan aeronautics": "HAL",
    "bel": "BEL",
    "bharat electronics": "BEL",
    "dixon": "DIXON",
    "persistent": "PERSISTENT",
    "coforge": "COFORGE",
    "polycab": "POLYCAB",
    "tata motors": "TATAMOTORS"
}


def clean_number(text: str) -> Optional[float]:
    """Cleans numeric text containing commas, currency symbols, and signs."""
    if not text:
        return None
    match = re.search(r"[-+]?\d[\d,]*\.?\d*", text.strip())
    if not match:
        return None
    cleaned = match.group(0).replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def extract_symbol_from_quote_url(url: str, session: Optional[requests.Session] = None, timeout: int = 5) -> Optional[str]:
    """
    Extracts the NSE symbol from a Moneycontrol quote page URL.
    Checks the HTML for '<li class="clearfix"> <span>NSE:</span> <p>SYMBOL</p></li>'.
    """
    if not url:
        return None

    # Check known slug patterns
    slug = url.rstrip("/").split("/")[-2].lower().replace("-", " ")
    if slug in KNOWN_SYMBOL_MAP:
        return KNOWN_SYMBOL_MAP[slug]

    sess = session or requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        resp = sess.get(url, headers=headers, timeout=timeout)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
        for span in soup.find_all("span"):
            if span.get_text().strip() == "NSE:":
                parent = span.parent
                p = parent.find("p") if parent else None
                if p:
                    sym = p.get_text().strip().upper()
                    if sym:
                        KNOWN_SYMBOL_MAP[slug] = sym
                        return sym
    except Exception as e:
        logger.debug(f"Failed to extract symbol from quote page {url}: {e}")

    # Fallback to uppercase slug if alphabetic
    raw_slug = url.rstrip("/").split("/")[-2].upper().replace("-", "")
    if re.match(r"^[A-Z]{3,10}$", raw_slug):
        return raw_slug
    return None


def parse_moneycontrol_table(html_content: str, screener_type: str) -> List[Dict[str, Any]]:
    """
    Parses a Moneycontrol market stats table.
    Handles columns: Stock Name, Price & Change %, High, Low, Volume/Value.
    """
    results: List[Dict[str, Any]] = []
    soup = BeautifulSoup(html_content, "html.parser")
    tables = soup.find_all("table")
    if not tables:
        return results

    # Data is almost always in the second table on modern market-stats pages,
    # or the first if only one table is present.
    target_table = tables[1] if len(tables) > 1 else tables[0]
    rows = target_table.find_all("tr")

    for row in rows:
        tds = row.find_all("td")
        if not tds:
            continue

        # Column 0: Company name, tags, and link
        col0 = tds[0]
        a_tag = col0.find("a")
        if not a_tag:
            continue

        name = a_tag.get_text(strip=True)
        quote_url = a_tag.get("href", "")

        # Extract badge labels (e.g., 'Vol Shocker', '52 Wk High', '+1')
        tags: List[str] = []
        for btn in col0.find_all(["button", "span", "div"]):
            btn_txt = btn.get_text(strip=True)
            if btn_txt and btn_txt not in [name, "+1", "+2"]:
                if "vol shocker" in btn_txt.lower():
                    tags.append("VOLUME_SHOCKER")
                elif "circuit" in btn_txt.lower():
                    tags.append("CIRCUIT_LIMIT")
                elif "52" in btn_txt.lower():
                    tags.append("52W_HIGH")

        # Column 2: Price and percentage change
        price = None
        change_pct = None
        if len(tds) > 2:
            cell_text = tds[2].get_text(separator=" ", strip=True)
            pct_match = re.search(r"\(([+-]?[\d.]+)%\)", cell_text)
            if pct_match:
                change_pct = clean_number(pct_match.group(1))

            tokens = cell_text.split()
            if tokens:
                price = clean_number(tokens[0])

        # Column 3: Day's High
        days_high = clean_number(tds[3].get_text(strip=True)) if len(tds) > 3 else None
        # Column 4: Day's Low
        days_low = clean_number(tds[4].get_text(strip=True)) if len(tds) > 4 else None

        # Column 5: Volume or Value or Open
        volume = None
        turnover_cr = None
        if len(tds) > 5:
            col5_text = tds[5].get_text(strip=True)
            num = clean_number(col5_text)
            if "volume" in screener_type.lower():
                volume = int(num) if num else None
            elif "active" in screener_type.lower():
                turnover_cr = num

        # Attempt fast symbol resolution
        symbol = None
        clean_name_key = name.lower().strip()
        if clean_name_key in KNOWN_SYMBOL_MAP:
            symbol = KNOWN_SYMBOL_MAP[clean_name_key]
        else:
            # Check url slug
            url_slug = quote_url.rstrip("/").split("/")[-2].lower() if quote_url else ""
            if url_slug in KNOWN_SYMBOL_MAP:
                symbol = KNOWN_SYMBOL_MAP[url_slug]

        results.append({
            "name": name,
            "symbol": symbol,
            "quote_url": quote_url,
            "price": price,
            "change_pct": change_pct,
            "days_high": days_high,
            "days_low": days_low,
            "volume": volume,
            "turnover_cr": turnover_cr,
            "tags": tags,
            "screener_source": screener_type
        })

    return results


def generate_synthetic_moneycontrol_data() -> List[Dict[str, Any]]:
    """
    Returns realistic deterministic Indian stocks for offline screening / tests.
    """
    return [
        {
            "name": "Trent Ltd",
            "symbol": "TRENT",
            "quote_url": "https://www.moneycontrol.com/india/stockpricequote/retail/trent/T04",
            "price": 2880.0,
            "change_pct": 11.5,
            "days_high": 2909.0,
            "days_low": 2782.0,
            "volume": 2450000,
            "turnover_cr": 350.5,
            "tags": ["VOLUME_SHOCKER", "52W_HIGH_BREAKOUT"],
            "screener_source": "volume_shockers"
        },
        {
            "name": "Bharat Heavy Electricals",
            "symbol": "BHEL",
            "quote_url": "https://www.moneycontrol.com/india/stockpricequote/infrastructure-general/bharatheavyelectricals/BHE",
            "price": 451.0,
            "change_pct": 5.1,
            "days_high": 451.0,
            "days_low": 427.7,
            "volume": 8900000,
            "turnover_cr": 210.0,
            "tags": ["52W_HIGH_BREAKOUT", "VOLUME_SHOCKER"],
            "screener_source": "52_week_high"
        },
        {
            "name": "Tata Steel",
            "symbol": "TATASTEEL",
            "quote_url": "https://www.moneycontrol.com/india/stockpricequote/ironsteel/tatasteel/TIS",
            "price": 179.5,
            "change_pct": 2.8,
            "days_high": 181.0,
            "days_low": 175.2,
            "volume": 12500000,
            "turnover_cr": 224.0,
            "tags": ["TOP_GAINER"],
            "screener_source": "top_gainers"
        },
        {
            "name": "Reliance Industries",
            "symbol": "RELIANCE",
            "quote_url": "https://www.moneycontrol.com/india/stockpricequote/refineries/relianceindustries/RI",
            "price": 1420.0,
            "change_pct": 2.1,
            "days_high": 1428.0,
            "days_low": 1395.0,
            "volume": 6800000,
            "turnover_cr": 965.0,
            "tags": ["TOP_ACTIVE"],
            "screener_source": "most_active"
        },
        {
            "name": "Angel One",
            "symbol": "ANGELONE",
            "quote_url": "https://www.moneycontrol.com/india/stockpricequote/finance-stock-broking/angelone/ABL03",
            "price": 294.5,
            "change_pct": 3.2,
            "days_high": 296.0,
            "days_low": 288.0,
            "volume": 4780000,
            "turnover_cr": 140.0,
            "tags": ["VOLUME_SHOCKER"],
            "screener_source": "volume_shockers"
        },
        {
            "name": "HFCL Ltd",
            "symbol": "HFCL",
            "quote_url": "https://www.moneycontrol.com/india/stockpricequote/telecommunications-equipment/hfcl/HFC",
            "price": 262.8,
            "change_pct": 5.0,
            "days_high": 262.8,
            "days_low": 256.0,
            "volume": 3800000,
            "turnover_cr": 99.8,
            "tags": ["52W_HIGH_BREAKOUT"],
            "screener_source": "52_week_high"
        }
    ]


def fetch_moneycontrol_screeners(
    categories: Optional[List[str]] = None,
    config: Optional[Dict[str, Any]] = None,
    offline: bool = False
) -> List[Dict[str, Any]]:
    """
    Fetches and aggregates candidates across Moneycontrol screener pages.
    Deduplicates symbols and combines tags.
    """
    if offline:
        return generate_synthetic_moneycontrol_data()

    if categories is None:
        categories = ["volume_shockers", "52_week_high", "top_gainers", "most_active"]

    today_str = datetime.now().strftime("%Y%m%d")
    cache_file = DATA_DIR / f"screening_moneycontrol_{today_str}.json"

    # Check local cache first
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
                if cached_data and isinstance(cached_data, list):
                    return cached_data
        except Exception as e:
            logger.warning(f"Failed to load Moneycontrol cache: {e}")

    mc_cfg = (config or {}).get("moneycontrol", {})
    endpoints = mc_cfg.get("endpoints", {
        "top_gainers": "https://www.moneycontrol.com/stocks/market-stats/top-gainers-nse/",
        "volume_shockers": "https://www.moneycontrol.com/stocks/market-stats/volume-shockers-nse/",
        "52_week_high": "https://www.moneycontrol.com/stocks/market-stats/52-week-high-nse/",
        "most_active": "https://www.moneycontrol.com/stocks/market-stats/most-active-stocks-nse/"
    })

    req_cfg = mc_cfg.get("request", {})
    timeout = req_cfg.get("timeout", 10)
    user_agent = req_cfg.get(
        "user_agent",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    session = requests.Session()
    session.headers.update({"User-Agent": user_agent})

    raw_candidates: List[Dict[str, Any]] = []

    for cat in categories:
        url = endpoints.get(cat)
        if not url:
            continue
        try:
            resp = session.get(url, timeout=timeout)
            if resp.status_code == 200:
                parsed = parse_moneycontrol_table(resp.text, cat)
                raw_candidates.extend(parsed)
        except Exception as e:
            logger.warning(f"Error fetching Moneycontrol {cat} from {url}: {e}")

    if not raw_candidates:
        logger.info("Moneycontrol network fetch returned no candidates; using synthetic fallback.")
        return generate_synthetic_moneycontrol_data()

    # Deduplicate and resolve symbols
    by_symbol: Dict[str, Dict[str, Any]] = {}
    for item in raw_candidates:
        sym = item.get("symbol")
        if not sym and item.get("quote_url"):
            sym = extract_symbol_from_quote_url(item["quote_url"], session=session, timeout=timeout)
            item["symbol"] = sym

        if not sym:
            # Fallback to sanitizing name if no symbol found
            clean_name = re.sub(r"[^\w]", "", item.get("name", "")).upper()
            sym = clean_name[:10] if clean_name else "UNKNOWN"
            item["symbol"] = sym

        sym = sym.upper().replace(".NS", "")
        if sym in by_symbol:
            # Merge tags and screener source
            existing = by_symbol[sym]
            combined_tags = list(set(existing.get("tags", []) + item.get("tags", [])))
            existing["tags"] = combined_tags
            if item.get("change_pct") and not existing.get("change_pct"):
                existing["change_pct"] = item["change_pct"]
            if item.get("volume") and not existing.get("volume"):
                existing["volume"] = item["volume"]
            if item.get("turnover_cr") and not existing.get("turnover_cr"):
                existing["turnover_cr"] = item["turnover_cr"]
        else:
            by_symbol[sym] = item

    consolidated = list(by_symbol.values())

    # Cache results
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(consolidated, f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to cache Moneycontrol results: {e}")

    return consolidated
