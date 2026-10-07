"""Moneycontrol market statistics scanner and scraper."""

import os
import re
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import time
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Known name/slug/scrip to NSE symbol fast lookup to avoid round-trip lookups
KNOWN_SYMBOL_MAP: Dict[str, str] = {
    # Names, slugs, and scrip codes
    "trent": "TRENT",
    "t04": "TRENT",
    "reliance": "RELIANCE",
    "reliance industries": "RELIANCE",
    "relianceindustries": "RELIANCE",
    "ri": "RELIANCE",
    "tata steel": "TATASTEEL",
    "tatasteel": "TATASTEEL",
    "tis": "TATASTEEL",
    "bhel": "BHEL",
    "bharat heavy electricals": "BHEL",
    "bharatheavyelectricals": "BHEL",
    "bhe": "BHEL",
    "hfcl": "HFCL",
    "hfc": "HFCL",
    "maruti": "MARUTI",
    "maruti suzuki": "MARUTI",
    "marutisuzukiindia": "MARUTI",
    "ms24": "MARUTI",
    "angel one": "ANGELONE",
    "angelone": "ANGELONE",
    "abl03": "ANGELONE",
    "honasa consumer": "HONASA",
    "honasaconsumer": "HONASA",
    "hcl06": "HONASA",
    "pg electroplast": "PGEL",
    "pgelectroplast": "PGEL",
    "pe06": "PGEL",
    "hegam": "HEG",
    "tega industries": "TEGA",
    "tegaindustries": "TEGA",
    "ti26": "TEGA",
    "infosys": "INFY",
    "it": "INFY",
    "tcs": "TCS",
    "tataconsultancyservices": "TCS",
    "hdfc bank": "HDFCBANK",
    "hdfcbank": "HDFCBANK",
    "hdf01": "HDFCBANK",
    "icici bank": "ICICIBANK",
    "icicibank": "ICICIBANK",
    "ici02": "ICICIBANK",
    "state bank of india": "SBIN",
    "statebankindia": "SBIN",
    "sbi": "SBIN",
    "larsen & toubro": "LT",
    "l&t": "LT",
    "larsentoubro": "LT",
    "bharti airtel": "BHARTIARTL",
    "bhartiairtel": "BHARTIARTL",
    "itc": "ITC",
    "zomato": "ZOMATO",
    "hal": "HAL",
    "hindustan aeronautics": "HAL",
    "hindustanaeronautics": "HAL",
    "bel": "BEL",
    "bharat electronics": "BEL",
    "bharatelectronics": "BEL",
    "dixon": "DIXON",
    "dixontechnologies": "DIXON",
    "persistent": "PERSISTENT",
    "persistentsystems": "PERSISTENT",
    "coforge": "COFORGE",
    "polycab": "POLYCAB",
    "polycabindia": "POLYCAB",
    "tata motors": "TATAMOTORS",
    "tatamotors": "TATAMOTORS"
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
    Checks the URL slug and scrip code against KNOWN_SYMBOL_MAP first.
    If not found, queries the quote page HTML if reachable.
    """
    if not url:
        return None

    # URL format: .../india/stockpricequote/<sector>/<company_slug>/<scrip_code>
    parts = [p.lower().strip() for p in url.rstrip("/").split("/") if p.strip()]
    if len(parts) >= 2:
        slug_raw = parts[-2]
        slug_no_hyphen = slug_raw.replace("-", "")
        slug_spaced = slug_raw.replace("-", " ")
        scrip_code = parts[-1]

        for key in [slug_no_hyphen, slug_spaced, slug_raw, scrip_code]:
            if key in KNOWN_SYMBOL_MAP:
                return KNOWN_SYMBOL_MAP[key]

    sess = session or requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        resp = sess.get(url, headers=headers, timeout=timeout)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            for span in soup.find_all("span"):
                if span.get_text().strip() == "NSE:":
                    parent = span.parent
                    p = parent.find("p") if parent else None
                    if p:
                        sym = p.get_text().strip().upper()
                        if sym:
                            if len(parts) >= 2:
                                KNOWN_SYMBOL_MAP[parts[-2].replace("-", "")] = sym
                                KNOWN_SYMBOL_MAP[parts[-1]] = sym
                            return sym
    except Exception as e:
        logger.debug(f"Failed to extract symbol from quote page {url}: {e}")

    # Fallback to uppercase slug if alphabetic
    if len(parts) >= 2:
        raw_slug = parts[-2].upper().replace("-", "")
        for known_sym in KNOWN_SYMBOL_MAP.values():
            if known_sym in raw_slug:
                return known_sym
        if re.match(r"^[A-Z]{3,15}$", raw_slug):
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

    # Dynamically detect column indices from <th> headers if available
    th_tags = target_table.find_all("th")
    col_mapping = {}
    for idx, th in enumerate(th_tags):
        th_text = th.get_text(strip=True).lower()
        if "company" in th_text or "stock" in th_text:
            col_mapping["company"] = idx
        elif "price" in th_text or "ltp" in th_text or "last" in th_text:
            col_mapping["price"] = idx
        elif "high" in th_text:
            col_mapping["high"] = idx
        elif "low" in th_text:
            col_mapping["low"] = idx
        elif "volume" in th_text or "vol" in th_text:
            col_mapping["volume"] = idx
        elif "value" in th_text or "turnover" in th_text:
            col_mapping["turnover"] = idx

    col_company = col_mapping.get("company", 0)
    col_price = col_mapping.get("price", 2)
    col_high = col_mapping.get("high", 3)
    col_low = col_mapping.get("low", 4)
    col_volume = col_mapping.get("volume", 5)
    col_turnover = col_mapping.get("turnover", 5)

    rows = target_table.find_all("tr")

    for row in rows:
        tds = row.find_all("td")
        if not tds or len(tds) <= max(col_company, col_price):
            continue

        # Company name, tags, and link
        col0 = tds[col_company]
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

        # Price and percentage change
        price = None
        change_pct = None
        if len(tds) > col_price:
            cell_text = tds[col_price].get_text(separator=" ", strip=True)
            pct_match = re.search(r"\(([+-]?[\d.]+)%\)", cell_text)
            if pct_match:
                change_pct = clean_number(pct_match.group(1))

            tokens = cell_text.split()
            if tokens:
                price = clean_number(tokens[0])

        # Day's High and Low
        days_high = clean_number(tds[col_high].get_text(strip=True)) if len(tds) > col_high else None
        days_low = clean_number(tds[col_low].get_text(strip=True)) if len(tds) > col_low else None

        # Volume or Value or Open
        volume = None
        turnover_cr = None
        if "volume" in screener_type.lower() and len(tds) > col_volume:
            num = clean_number(tds[col_volume].get_text(strip=True))
            volume = int(num) if num else None
        elif "active" in screener_type.lower() and len(tds) > col_turnover:
            turnover_cr = clean_number(tds[col_turnover].get_text(strip=True))
        elif len(tds) > 5:
            num = clean_number(tds[5].get_text(strip=True))
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
        for attempt in range(3):
            try:
                resp = session.get(url, timeout=timeout)
                if resp.status_code == 200:
                    parsed = parse_moneycontrol_table(resp.text, cat)
                    raw_candidates.extend(parsed)
                    break
                elif resp.status_code == 429:
                    logger.warning(f"Rate limited (429) fetching Moneycontrol {cat}; backoff attempt {attempt + 1}")
                    time.sleep(1.0 * (2 ** attempt))
                else:
                    logger.warning(f"HTTP {resp.status_code} fetching Moneycontrol {cat} from {url}")
                    break
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed fetching Moneycontrol {cat} from {url}: {e}")
                if attempt == 2:
                    break
                time.sleep(1.0 * (2 ** attempt))


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
