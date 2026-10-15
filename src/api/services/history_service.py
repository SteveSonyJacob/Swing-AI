"""Thread-safe persistent analysis history storage using local JSON."""

import json
import logging
from pathlib import Path
from datetime import datetime
from threading import Lock
from typing import Dict, Any, List, Optional
import uuid

logger = logging.getLogger(__name__)

HISTORY_FILE = Path(__file__).resolve().parent.parent.parent.parent / "data" / "analysis_history.json"
MAX_HISTORY_ITEMS = 100
_history_lock = Lock()


def _ensure_history_file() -> None:
    """Ensures data directory and history file exist."""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)
        except Exception as e:
            logger.error(f"Error initializing history file: {e}")


def save_analysis(result: Dict[str, Any]) -> str:
    """
    Saves a completed single-stock analysis or pipeline result record.
    Returns the unique record ID.
    """
    _ensure_history_file()
    record_id = str(uuid.uuid4())[:8]

    symbol = result.get("symbol", "N/A")
    tech = result.get("technical", {}) or {}
    fund = result.get("fundamental", {}) or {}
    comp_score = result.get("composite_score")
    verdict = result.get("composite_verdict", "N/A")
    reason = result.get("verdict_reason", "")
    mode = result.get("mode", "live")
    timestamp = result.get("timestamp") or datetime.now().isoformat()

    record = {
        "id": record_id,
        "symbol": symbol,
        "timestamp": timestamp,
        "composite_score": comp_score,
        "composite_verdict": verdict,
        "verdict_reason": reason,
        "technical_score": tech.get("technical_score"),
        "fundamental_score": fund.get("fundamental_score"),
        "mode": mode,
        "status": "success" if result.get("technical", {}).get("status") != "error" else "warning",
        "full_result": result
    }

    with _history_lock:
        try:
            records: List[Dict[str, Any]] = []
            if HISTORY_FILE.exists():
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    try:
                        records = json.load(f)
                    except json.JSONDecodeError:
                        records = []

            # Prepend newest record
            records.insert(0, record)
            # Cap history size
            records = records[:MAX_HISTORY_ITEMS]

            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist analysis history: {e}")

    return record_id


def get_history(limit: int = 50, query: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves list of previous analyses (without full raw payload for performance)."""
    _ensure_history_file()
    with _history_lock:
        try:
            if not HISTORY_FILE.exists():
                return []
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"Error reading history: {e}")
            return []

    results = []
    q = query.strip().upper() if query else None

    for item in data:
        if q and q not in item.get("symbol", "").upper() and q not in item.get("composite_verdict", "").upper():
            continue
        # Omit full_result in list summary view for lightweight transmission
        summary_item = {
            "id": item.get("id"),
            "symbol": item.get("symbol"),
            "timestamp": item.get("timestamp"),
            "composite_score": item.get("composite_score"),
            "composite_verdict": item.get("composite_verdict"),
            "verdict_reason": item.get("verdict_reason"),
            "technical_score": item.get("technical_score"),
            "fundamental_score": item.get("fundamental_score"),
            "mode": item.get("mode"),
            "status": item.get("status")
        }
        results.append(summary_item)
        if len(results) >= limit:
            break

    return results


def get_analysis_by_id(record_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves the full analysis record by ID."""
    _ensure_history_file()
    with _history_lock:
        try:
            if not HISTORY_FILE.exists():
                return None
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                if item.get("id") == record_id:
                    return item.get("full_result")
        except Exception as e:
            logger.error(f"Error reading analysis record {record_id}: {e}")
    return None


def get_latest_for_symbol(symbol: str) -> Optional[Dict[str, Any]]:
    """Retrieves the most recent full analysis record for a given symbol."""
    _ensure_history_file()
    sym_upper = symbol.strip().upper()
    with _history_lock:
        try:
            if not HISTORY_FILE.exists():
                return None
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                if item.get("symbol", "").upper() == sym_upper:
                    return item.get("full_result")
        except Exception as e:
            logger.error(f"Error reading latest for symbol {symbol}: {e}")
    return None
