"""Official National Stock Exchange of India (NSE) broad equity universe discovery.

Fetches the complete exchange-published equity master list (EQUITY_L.csv),
filters by allowed series (e.g. EQ, BE), deduplicates symbols, and manages
a local cache with configurable TTL.
"""

import os
import csv
import io
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Tuple
import requests

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CACHE_FILE = DATA_DIR / "nse_equity_universe.json"

DEFAULT_NSE_URL = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
DEFAULT_FALLBACK_URL = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"

# Comprehensive offline seed universe (120+ symbols across large, mid, small caps, and recent listings)
# Used only when network is unavailable and no local cache exists, clearly reported as partial coverage.
DEFAULT_OFFLINE_SEED_EQUITIES: List[Dict[str, str]] = [
    {"symbol": "RELIANCE", "name": "Reliance Industries Limited", "series": "EQ", "isin": "INE002A01018"},
    {"symbol": "TCS", "name": "Tata Consultancy Services Limited", "series": "EQ", "isin": "INE467B01029"},
    {"symbol": "HDFCBANK", "name": "HDFC Bank Limited", "series": "EQ", "isin": "INE040A01034"},
    {"symbol": "INFY", "name": "Infosys Limited", "series": "EQ", "isin": "INE009A01021"},
    {"symbol": "ICICIBANK", "name": "ICICI Bank Limited", "series": "EQ", "isin": "INE090A01021"},
    {"symbol": "BHARTIARTL", "name": "Bharti Airtel Limited", "series": "EQ", "isin": "INE397D01024"},
    {"symbol": "SBIN", "name": "State Bank of India", "series": "EQ", "isin": "INE062A01020"},
    {"symbol": "LICI", "name": "Life Insurance Corporation Of India", "series": "EQ", "isin": "INE323A01015"},
    {"symbol": "ITC", "name": "ITC Limited", "series": "EQ", "isin": "INE154A01025"},
    {"symbol": "HINDUNILVR", "name": "Hindustan Unilever Limited", "series": "EQ", "isin": "INE030A01027"},
    {"symbol": "LT", "name": "Larsen & Toubro Limited", "series": "EQ", "isin": "INE018A01030"},
    {"symbol": "BAJFINANCE", "name": "Bajaj Finance Limited", "series": "EQ", "isin": "INE296A01024"},
    {"symbol": "HCLTECH", "name": "HCL Technologies Limited", "series": "EQ", "isin": "INE860A01027"},
    {"symbol": "MARUTI", "name": "Maruti Suzuki India Limited", "series": "EQ", "isin": "INE585B01010"},
    {"symbol": "SUNPHARMA", "name": "Sun Pharmaceutical Industries Limited", "series": "EQ", "isin": "INE044A01036"},
    {"symbol": "ADANIENT", "name": "Adani Enterprises Limited", "series": "EQ", "isin": "INE423A01024"},
    {"symbol": "KOTAKBANK", "name": "Kotak Mahindra Bank Limited", "series": "EQ", "isin": "INE237A01028"},
    {"symbol": "TITAN", "name": "Titan Company Limited", "series": "EQ", "isin": "INE280A01028"},
    {"symbol": "ONGC", "name": "Oil & Natural Gas Corporation Limited", "series": "EQ", "isin": "INE213A01029"},
    {"symbol": "TATAMOTORS", "name": "Tata Motors Limited", "series": "EQ", "isin": "INE155A01022"},
    {"symbol": "NTPC", "name": "NTPC Limited", "series": "EQ", "isin": "INE733E01010"},
    {"symbol": "AXISBANK", "name": "Axis Bank Limited", "series": "EQ", "isin": "INE238A01034"},
    {"symbol": "ADANIPORTS", "name": "Adani Ports and Special Economic Zone Limited", "series": "EQ", "isin": "INE742F01042"},
    {"symbol": "POWERGRID", "name": "Power Grid Corporation of India Limited", "series": "EQ", "isin": "INE752E01010"},
    {"symbol": "COALINDIA", "name": "Coal India Limited", "series": "EQ", "isin": "INE522F01014"},
    {"symbol": "BAJAJFINSV", "name": "Bajaj Finserv Limited", "series": "EQ", "isin": "INE918I01026"},
    {"symbol": "ULTRACEMCO", "name": "UltraTech Cement Limited", "series": "EQ", "isin": "INE481G01011"},
    {"symbol": "ASIANPAINT", "name": "Asian Paints Limited", "series": "EQ", "isin": "INE021A01026"},
    {"symbol": "M&M", "name": "Mahindra & Mahindra Limited", "series": "EQ", "isin": "INE101A01026"},
    {"symbol": "TATASTEEL", "name": "Tata Steel Limited", "series": "EQ", "isin": "INE081A01020"},
    {"symbol": "NESTLEIND", "name": "Nestle India Limited", "series": "EQ", "isin": "INE239A01024"},
    {"symbol": "JSWEGY", "name": "JSW Energy Limited", "series": "EQ", "isin": "INE121E01018"},
    {"symbol": "JSWSTEEL", "name": "JSW Steel Limited", "series": "EQ", "isin": "INE019A01038"},
    {"symbol": "TECHM", "name": "Tech Mahindra Limited", "series": "EQ", "isin": "INE669C01036"},
    {"symbol": "GRASIM", "name": "Grasim Industries Limited", "series": "EQ", "isin": "INE047A01021"},
    {"symbol": "SBILIFE", "name": "SBI Life Insurance Company Limited", "series": "EQ", "isin": "INE123W01016"},
    {"symbol": "CIPLA", "name": "Cipla Limited", "series": "EQ", "isin": "INE059A01026"},
    {"symbol": "WIPRO", "name": "Wipro Limited", "series": "EQ", "isin": "INE075A01022"},
    {"symbol": "HINDALCO", "name": "Hindalco Industries Limited", "series": "EQ", "isin": "INE038A01020"},
    {"symbol": "EICHERMOT", "name": "Eicher Motors Limited", "series": "EQ", "isin": "INE066A01021"},
    {"symbol": "BPCL", "name": "Bharat Petroleum Corporation Limited", "series": "EQ", "isin": "INE029A01011"},
    {"symbol": "DRREDDY", "name": "Dr. Reddy's Laboratories Limited", "series": "EQ", "isin": "INE089A01023"},
    {"symbol": "TRENT", "name": "Trent Limited", "series": "EQ", "isin": "INE849A01020"},
    {"symbol": "BEL", "name": "Bharat Electronics Limited", "series": "EQ", "isin": "INE263A01024"},
    {"symbol": "SHRIRAMFIN", "name": "Shriram Finance Limited", "series": "EQ", "isin": "INE721A01013"},
    {"symbol": "HEROMOTOCO", "name": "Hero MotoCorp Limited", "series": "EQ", "isin": "INE158A01026"},
    {"symbol": "APOLLOHOSP", "name": "Apollo Hospitals Enterprise Limited", "series": "EQ", "isin": "INE437A01024"},
    {"symbol": "TATACONSUM", "name": "Tata Consumer Products Limited", "series": "EQ", "isin": "INE192A01025"},
    {"symbol": "BRITANNIA", "name": "Britannia Industries Limited", "series": "EQ", "isin": "INE216A01030"},
    {"symbol": "INDUSINDBK", "name": "IndusInd Bank Limited", "series": "EQ", "isin": "INE095A01012"},
    {"symbol": "VBL", "name": "Varun Beverages Limited", "series": "EQ", "isin": "INE200M01021"},
    {"symbol": "CHOLAFIN", "name": "Cholamandalam Investment and Finance Company", "series": "EQ", "isin": "INE121A01024"},
    {"symbol": "ZOMATO", "name": "Zomato Limited", "series": "EQ", "isin": "INE758T01015"},
    {"symbol": "HAL", "name": "Hindustan Aeronautics Limited", "series": "EQ", "isin": "INE066F01020"},
    {"symbol": "DLF", "name": "DLF Limited", "series": "EQ", "isin": "INE271C01023"},
    {"symbol": "SIEMENS", "name": "Siemens Limited", "series": "EQ", "isin": "INE003A01024"},
    {"symbol": "ABB", "name": "ABB India Limited", "series": "EQ", "isin": "INE117A01022"},
    {"symbol": "BANKBARODA", "name": "Bank of Baroda", "series": "EQ", "isin": "INE028A01039"},
    {"symbol": "PIDILITIND", "name": "Pidilite Industries Limited", "series": "EQ", "isin": "INE318A01026"},
    {"symbol": "GAIL", "name": "GAIL (India) Limited", "series": "EQ", "isin": "INE129A01019"},
    {"symbol": "AMBUJACEM", "name": "Ambuja Cements Limited", "series": "EQ", "isin": "INE079A01024"},
    {"symbol": "JIOFIN", "name": "Jio Financial Services Limited", "series": "EQ", "isin": "INE758E01017"},
    {"symbol": "TORNTPHARM", "name": "Torrent Pharmaceuticals Limited", "series": "EQ", "isin": "INE685A01028"},
    {"symbol": "TVSMOTOR", "name": "TVS Motor Company Limited", "series": "EQ", "isin": "INE494B01023"},
    {"symbol": "PNB", "name": "Punjab National Bank", "series": "EQ", "isin": "INE160A01022"},
    {"symbol": "HAVELLS", "name": "Havells India Limited", "series": "EQ", "isin": "INE176B01034"},
    {"symbol": "INDIGO", "name": "InterGlobe Aviation Limited", "series": "EQ", "isin": "INE646L01027"},
    {"symbol": "CANBK", "name": "Canara Bank", "series": "EQ", "isin": "INE476A01022"},
    {"symbol": "MOTHERSON", "name": "Samvardhana Motherson International Limited", "series": "EQ", "isin": "INE775A01035"},
    {"symbol": "POLYCAB", "name": "Polycab India Limited", "series": "EQ", "isin": "INE455K01017"},
    {"symbol": "DABUR", "name": "Dabur India Limited", "series": "EQ", "isin": "INE016A01026"},
    {"symbol": "BOSCHLTD", "name": "Bosch Limited", "series": "EQ", "isin": "INE323A01026"},
    {"symbol": "MUTHOOTFIN", "name": "Muthoot Finance Limited", "series": "EQ", "isin": "INE414G01012"},
    {"symbol": "GODREJCP", "name": "Godrej Consumer Products Limited", "series": "EQ", "isin": "INE102D01028"},
    {"symbol": "RECLTD", "name": "REC Limited", "series": "EQ", "isin": "INE020B01018"},
    {"symbol": "PERSISTENT", "name": "Persistent Systems Limited", "series": "EQ", "isin": "INE262H01013"},
    {"symbol": "COFORGE", "name": "Coforge Limited", "series": "EQ", "isin": "INE591G01017"},
    {"symbol": "LTTS", "name": "L&T Technology Services Limited", "series": "EQ", "isin": "INE010V01017"},
    {"symbol": "FEDERALBNK", "name": "The Federal Bank Limited", "series": "EQ", "isin": "INE171A01029"},
    {"symbol": "ASHOKLEY", "name": "Ashok Leyland Limited", "series": "EQ", "isin": "INE214T01019"},
    {"symbol": "VOLTAS", "name": "Voltas Limited", "series": "EQ", "isin": "INE226A01021"},
    {"symbol": "ASTRAL", "name": "Astral Limited", "series": "EQ", "isin": "INE006I01046"},
    {"symbol": "AUROPHARMA", "name": "Aurobindo Pharma Limited", "series": "EQ", "isin": "INE406A01037"},
    {"symbol": "BALKRISIND", "name": "Balkrishna Industries Limited", "series": "EQ", "isin": "INE787D01026"},
    {"symbol": "BHEL", "name": "Bharat Heavy Electricals Limited", "series": "EQ", "isin": "INE257A01026"},
    {"symbol": "DIXON", "name": "Dixon Technologies (India) Limited", "series": "EQ", "isin": "INE935N01020"},
    {"symbol": "ESCORTS", "name": "Escorts Kubota Limited", "series": "EQ", "isin": "INE042A01014"},
    {"symbol": "GMRINFRA", "name": "GMR Airports Infrastructure Limited", "series": "EQ", "isin": "INE776C01039"},
    {"symbol": "IDFCFIRSTB", "name": "IDFC First Bank Limited", "series": "EQ", "isin": "INE092T01019"},
    {"symbol": "KPITTECH", "name": "KPIT Technologies Limited", "series": "EQ", "isin": "INE046L01019"},
    {"symbol": "MPHASIS", "name": "Mphasis Limited", "series": "EQ", "isin": "INE356A01018"},
    {"symbol": "NMDC", "name": "NMDC Limited", "series": "EQ", "isin": "INE584A01023"},
    {"symbol": "OBEROIRLTY", "name": "Oberoi Realty Limited", "series": "EQ", "isin": "INE093I01010"},
    {"symbol": "PETRONET", "name": "Petronet LNG Limited", "series": "EQ", "isin": "INE347G01014"},
    {"symbol": "SUPREMEIND", "name": "Supreme Industries Limited", "series": "EQ", "isin": "INE195A01028"},
    {"symbol": "HFCL", "name": "HFCL Limited", "series": "EQ", "isin": "INE548A01028"},
    {"symbol": "ANGELONE", "name": "Angel One Limited", "series": "EQ", "isin": "INE732I01013"},
    {"symbol": "HONASA", "name": "Honasa Consumer Limited", "series": "EQ", "isin": "INE07T801019"},
    {"symbol": "PGEL", "name": "PG Electroplast Limited", "series": "EQ", "isin": "INE457L01011"},
    {"symbol": "HEG", "name": "HEG Limited", "series": "EQ", "isin": "INE545A01016"},
    {"symbol": "TEGA", "name": "Tega Industries Limited", "series": "EQ", "isin": "INE011K01018"},
    {"symbol": "20MICRONS", "name": "20 Microns Limited", "series": "EQ", "isin": "INE144J01027"},
    {"symbol": "360ONE", "name": "360 ONE WAM LIMITED", "series": "EQ", "isin": "INE466L01038"},
    {"symbol": "3BBLACKBIO", "name": "3B Blackbio Dx Limited", "series": "EQ", "isin": "INE994E01018"},
    {"symbol": "5PAISA", "name": "5Paisa Capital Limited", "series": "EQ", "isin": "INE618L01018"},
    {"symbol": "63MOONS", "name": "63 moons technologies limited", "series": "EQ", "isin": "INE111A01025"},
    {"symbol": "IDEA", "name": "Vodafone Idea Limited", "series": "EQ", "isin": "INE669E01016"},
    {"symbol": "SUZLON", "name": "Suzlon Energy Limited", "series": "EQ", "isin": "INE040H01021"},
    {"symbol": "IRFC", "name": "Indian Railway Finance Corporation Limited", "series": "EQ", "isin": "INE053F01010"},
    {"symbol": "RVNL", "name": "Rail Vikas Nigam Limited", "series": "EQ", "isin": "INE415G01027"},
    {"symbol": "MAZDOCK", "name": "Mazagon Dock Shipbuilders Limited", "series": "EQ", "isin": "INE249Z01012"},
    {"symbol": "COCHINSHIP", "name": "Cochin Shipyard Limited", "series": "EQ", "isin": "INE704P01025"},
    {"symbol": "NYKAA", "name": "FSN E-Commerce Ventures Limited", "series": "EQ", "isin": "INE388Y01029"},
    {"symbol": "PAYTM", "name": "One 97 Communications Limited", "series": "EQ", "isin": "INE982J01020"},
    {"symbol": "DELHIVERY", "name": "Delhivery Limited", "series": "EQ", "isin": "INE148O01028"},
    {"symbol": "KALYANKJIL", "name": "Kalyan Jewellers India Limited", "series": "EQ", "isin": "INE303R01014"},
    {"symbol": "MANKIND", "name": "Mankind Pharma Limited", "series": "EQ", "isin": "INE634S01028"},
    {"symbol": "POLICYBZR", "name": "PB Fintech Limited", "series": "EQ", "isin": "INE417T01026"},
    {"symbol": "CDSL", "name": "Central Depository Services (India) Limited", "series": "EQ", "isin": "INE736A01011"},
    {"symbol": "BSE", "name": "BSE Limited", "series": "EQ", "isin": "INE118H01025"},
    {"symbol": "CAMS", "name": "Computer Age Management Services Limited", "series": "EQ", "isin": "INE596I01012"}
]


def normalize_symbol(symbol: str) -> str:
    """Normalizes an equity symbol to standard uppercase NSE format without suffixes."""
    if not symbol:
        return ""
    clean = symbol.strip().upper()
    if clean.endswith(".NS"):
        clean = clean[:-3]
    elif clean.startswith("^"):
        return ""  # Indices are excluded
    # Strip any exchange prefix like NSE:
    if clean.startswith("NSE:"):
        clean = clean[4:]
    return clean.strip()


def parse_nse_equity_csv(csv_text: str, allowed_series: Optional[Set[str]] = None) -> Tuple[List[Dict[str, str]], Dict[str, int]]:
    """
    Parses the NSE EQUITY_L.csv format into a list of normalized equity dictionaries.
    Excludes non-equity instruments and tracks exclusion statistics.
    """
    if allowed_series is None:
        allowed_series = {"EQ", "BE"}

    securities: List[Dict[str, str]] = []
    seen_symbols: Set[str] = set()
    exclusion_stats: Dict[str, int] = {
        "unsupported_series": 0,
        "invalid_symbol": 0,
        "duplicate_symbol": 0,
        "etf_or_mutual_fund": 0
    }

    reader = csv.DictReader(io.StringIO(csv_text.strip()))
    for row in reader:
        # NSE CSV columns often have leading spaces in header names (e.g. ' SERIES')
        clean_row = {k.strip(): v.strip() for k, v in row.items() if k is not None and v is not None}

        raw_sym = clean_row.get("SYMBOL", "")
        series = clean_row.get("SERIES", "").upper()
        name = clean_row.get("NAME OF COMPANY", "")
        isin = clean_row.get("ISIN NUMBER", "")
        listing_date = clean_row.get("DATE OF LISTING", "")

        sym = normalize_symbol(raw_sym)
        if not sym:
            exclusion_stats["invalid_symbol"] += 1
            continue

        if series not in allowed_series:
            exclusion_stats["unsupported_series"] += 1
            continue

        # Exclude Mutual Funds and ETFs (ISIN prefix INF or ETF/BEES nomenclature)
        if isin.startswith("INF") or "ETF" in name.upper() or "BEES" in name.upper() or "ETF" in sym:
            exclusion_stats["etf_or_mutual_fund"] += 1
            continue

        if sym in seen_symbols:
            exclusion_stats["duplicate_symbol"] += 1
            continue

        seen_symbols.add(sym)
        securities.append({
            "symbol": sym,
            "name": name,
            "series": series,
            "isin": isin,
            "listing_date": listing_date
        })

    return securities, exclusion_stats


def load_cached_universe(cache_file: Path) -> Optional[Dict[str, Any]]:
    """Loads discovered universe from local JSON cache if present and valid."""
    if not cache_file.exists():
        return None
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if data and isinstance(data, dict) and "symbols" in data:
                return data
    except Exception as e:
        logger.warning(f"Failed to read universe cache from {cache_file}: {e}")
    return None


def save_cached_universe(cache_file: Path, payload: Dict[str, Any]) -> None:
    """Saves discovered universe payload to local JSON cache."""
    try:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to cache universe to {cache_file}: {e}")


def discover_nse_equity_universe(
    source_url: str = DEFAULT_NSE_URL,
    fallback_url: str = DEFAULT_FALLBACK_URL,
    allowed_series: Optional[List[str]] = None,
    cache_file: Optional[Path] = None,
    cache_ttl_hours: int = 24,
    force_refresh: bool = False,
    offline: bool = False,
    timeout: int = 10,
    session: Optional[requests.Session] = None
) -> Dict[str, Any]:
    """
    Discovers eligible equities across the complete NSE-listed equity universe.
    
    Returns structured discovery dictionary:
      - symbols: List[str] of valid, deduplicated NSE equity symbols.
      - metadata: Operational diagnostics (coverage status, source, exclusions, cache info).
    """
    if cache_file is None:
        cache_file = CACHE_FILE

    target_series = set(s.upper().strip() for s in allowed_series) if allowed_series else {"EQ", "BE"}
    failed_sources: List[str] = []

    # 1. Check local cache if not forcing refresh
    if not force_refresh:
        cached = load_cached_universe(cache_file)
        if cached is not None:
            ts_str = cached.get("metadata", {}).get("discovery_timestamp")
            is_fresh = True
            if ts_str:
                try:
                    cached_dt = datetime.fromisoformat(ts_str)
                    if datetime.now() - cached_dt > timedelta(hours=cache_ttl_hours):
                        is_fresh = False
                except Exception:
                    is_fresh = False

            if offline or is_fresh:
                # Use cached universe
                symbols = cached.get("symbols", [])
                meta = dict(cached.get("metadata", {}))
                meta["is_cached"] = True
                meta["coverage_status"] = "cached"
                meta["last_refresh"] = ts_str
                return {
                    "symbols": symbols,
                    "metadata": meta
                }

    # 2. If online and not using fresh cache, attempt fetch from exchange archives
    if not offline:
        sess = session or requests.Session()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        }

        urls_to_try = [source_url, fallback_url] if fallback_url and fallback_url != source_url else [source_url]
        for url in urls_to_try:
            try:
                logger.info(f"Fetching official NSE equity master list from {url}...")
                resp = sess.get(url, headers=headers, timeout=timeout)
                if resp.status_code == 200 and "SYMBOL" in resp.text:
                    securities, stats = parse_nse_equity_csv(resp.text, allowed_series=target_series)
                    symbols = [s["symbol"] for s in securities]

                    metadata = {
                        "data_source": "NSE_OFFICIAL_EQUITY_MASTER",
                        "source_url": url,
                        "discovery_timestamp": datetime.now().isoformat(),
                        "total_discovered": len(securities) + sum(stats.values()),
                        "total_eligible": len(symbols),
                        "excluded_count": sum(stats.values()),
                        "exclusion_reasons": stats,
                        "allowed_series": sorted(list(target_series)),
                        "coverage_status": "complete",
                        "is_cached": False,
                        "last_refresh": datetime.now().isoformat(),
                        "failed_sources": failed_sources
                    }

                    payload = {
                        "symbols": symbols,
                        "securities": securities,
                        "metadata": metadata
                    }
                    save_cached_universe(cache_file, payload)
                    return {
                        "symbols": symbols,
                        "metadata": metadata
                    }
                else:
                    failed_sources.append(f"{url} (HTTP {resp.status_code})")
            except Exception as e:
                logger.warning(f"Failed to fetch NSE master list from {url}: {e}")
                failed_sources.append(f"{url} ({str(e)})")

    # 3. Fallback to existing cache if online fetch failed
    cached = load_cached_universe(cache_file)
    if cached is not None:
        logger.warning("Online exchange fetch failed; falling back to local cached universe.")
        meta = dict(cached.get("metadata", {}))
        meta["is_cached"] = True
        meta["coverage_status"] = "cached"
        meta["failed_sources"] = failed_sources
        return {
            "symbols": cached.get("symbols", []),
            "metadata": meta
        }

    # 4. Fallback to broad offline seed dataset (covers 120+ stocks across market caps)
    logger.warning("No cache or live exchange list available. Using partial broad offline seed universe.")
    seed_securities = [
        s for s in DEFAULT_OFFLINE_SEED_EQUITIES
        if s.get("series", "EQ") in target_series
    ]
    symbols = [s["symbol"] for s in seed_securities]

    metadata = {
        "data_source": "OFFLINE_BROAD_SEED_DATASET",
        "discovery_timestamp": datetime.now().isoformat(),
        "total_discovered": len(DEFAULT_OFFLINE_SEED_EQUITIES),
        "total_eligible": len(symbols),
        "excluded_count": len(DEFAULT_OFFLINE_SEED_EQUITIES) - len(symbols),
        "exclusion_reasons": {"unsupported_series": len(DEFAULT_OFFLINE_SEED_EQUITIES) - len(symbols)},
        "allowed_series": sorted(list(target_series)),
        "coverage_status": "partial",  # Explicit partial coverage warning
        "is_cached": False,
        "last_refresh": None,
        "failed_sources": failed_sources,
        "coverage_note": "Partial coverage (offline seed universe). Complete exchange retrieval unavailable offline."
    }

    return {
        "symbols": symbols,
        "metadata": metadata
    }
