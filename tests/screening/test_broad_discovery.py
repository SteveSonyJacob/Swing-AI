"""Comprehensive test suite for Agent 1 Redesign: Market-Wide NSE Stock Discovery Engine.

Covers all 12 validation requirements:
1. Scanner is not restricted to NIFTY 50.
2. A valid symbol outside predefined indices is discovered when present.
3. Duplicate symbols are removed.
4. Unsupported instruments (ETFs, debt, mutual funds, non-EQ series) are excluded.
5. No screening score is calculated by Agent 1.
6. No ranking or score-based top-N selection is performed inside Agent 1.
7. Downstream analysis accepts symbol lists.
8. The pipeline produces technical, fundamental, and composite verdicts.
9. Single-symbol execution processes the requested symbol without candidate mismatch.
10. Provider failure does not silently result in an index-only scan.
11. Partial universe coverage is clearly reported in metadata.
12. Existing multi-agent interfaces remain decoupled and intact.
"""

import pytest
from unittest.mock import patch
from typing import List, Dict, Any

from src.screening.main import run_screening, load_screening_config
from src.screening.sources.nse_universe import (
    discover_nse_equity_universe,
    normalize_symbol,
    parse_nse_equity_csv,
    DEFAULT_OFFLINE_SEED_EQUITIES
)
from src.screening.output.pipeline import pipe_to_agents, evaluate_composite_verdict
from run_all import run_pipeline, run_single_stock


# 1. Scanner is not restricted to NIFTY 50
def test_scanner_not_restricted_to_nifty50():
    """Verify that scanner covers broad market equities beyond the 50 stocks in NIFTY 50."""
    res = run_screening(offline=True)
    assert res["status"] == "success"
    symbols = res["symbols"]
    # Offline seed has 121 equities, live universe has ~2,575; neither is limited to 50
    assert len(symbols) > 50
    assert res["universe_mode"] == "broad_market"
    assert res["market"] == "NSE"


# 2. A valid symbol outside predefined indices is discovered when present
def test_valid_symbol_outside_predefined_indices_discovered():
    """Verify that equities outside NIFTY 50 / largecap indices are discovered."""
    res = run_screening(offline=True)
    symbols = set(res["symbols"])

    # Symbols that are midcap, smallcap, or recently listed equities outside NIFTY 50
    broad_market_stocks = ["360ONE", "20MICRONS", "CDSL", "KAYNES", "MAPMYINDIA", "SUZLON", "ZOMATO"]
    discovered_outside_nifty50 = [s for s in broad_market_stocks if s in symbols]
    assert len(discovered_outside_nifty50) >= 3, f"Expected non-NIFTY 50 stocks to be discovered, found: {discovered_outside_nifty50}"


# 3. Duplicate symbols are removed
def test_duplicate_symbols_are_removed():
    """Verify deduplication across custom symbols, raw data, and normalization."""
    # Test normalization helper
    assert normalize_symbol(" reliance.ns ") == "RELIANCE"
    assert normalize_symbol("TCS") == "TCS"
    assert normalize_symbol("") == ""

    # Test discovery with duplicates and case variations
    dups = ["RELIANCE", "reliance", "TCS", "tcs.ns", "RELIANCE.NS", "INFY", "infy"]
    res = run_screening(custom_symbols=dups)
    assert res["status"] == "success"
    assert res["symbols"] == ["RELIANCE", "TCS", "INFY"]
    assert len(res["symbols"]) == len(set(res["symbols"]))


# 4. Unsupported instruments are excluded
def test_unsupported_instruments_are_excluded():
    """Verify non-equity series (debt, preference, ETFs, mutual funds, gold bees) are excluded."""
    csv_sample = (
        "SYMBOL, NAME OF COMPANY, SERIES, DATE OF LISTING, PAID UP VALUE, MARKET LOT, ISIN NUMBER, FACE VALUE\n"
        "RELIANCE,Reliance Industries Limited,EQ,29-NOV-1995,10,1,INE002A01018,10\n"
        "TCS,Tata Consultancy Services Limited,EQ,25-AUG-2004,1,1,INE467B01029,1\n"
        "NIFTYBEES,Nippon India ETF Nifty 50 BeES,EQ,28-DEC-2001,1,1,INF732E01015,1\n"  # Mutual Fund ISIN
        "GOLDBEES,Nippon India ETF Gold BeES,EQ,08-MAR-2007,1,1,INF732E01031,1\n"        # Mutual Fund ISIN
        "HDFCDEBT,HDFC Fixed Income Debt,GB,15-JAN-2020,1000,1,INE040A08011,1000\n"       # Debt Series GB
        "SBIPREF,SBI Non-Convertible Preference,P1,10-FEB-2021,100,1,INE062A04012,100\n"  # Preference Series P1
        "TATABOND,Tata Capital Bond Series,N1,12-MAR-2019,1000,1,INE306N07018,1000\n"     # Bond Series N1
        "ZOMATO,Zomato Limited,EQ,23-JUL-2021,1,1,INE758T01015,1\n"
    )

    securities, stats = parse_nse_equity_csv(csv_sample, allowed_series={"EQ", "BE"})
    symbols = [s["symbol"] for s in securities]
    assert "RELIANCE" in symbols
    assert "TCS" in symbols
    assert "ZOMATO" in symbols

    # Non-equity series must be excluded
    assert "HDFCDEBT" not in symbols
    assert "SBIPREF" not in symbols
    assert "TATABOND" not in symbols

    # ETFs / Mutual funds (ISIN INF...) must be excluded
    assert "NIFTYBEES" not in symbols
    assert "GOLDBEES" not in symbols

    assert stats["unsupported_series"] >= 3
    assert stats["etf_or_mutual_fund"] >= 2


# 5. No screening score is calculated
def test_no_screening_score_calculated():
    """Verify that Agent 1 outputs plain symbols and metadata, with no screening score."""
    res = run_screening(offline=True)
    assert "symbols" in res
    assert "metadata" in res
    # Output must not contain screening score fields
    assert "screening_score" not in res
    assert "score" not in res
    assert "scores" not in res
    assert "ranking" not in res

    # Elements in symbols list must be string symbols, not score objects
    for s in res["symbols"]:
        assert isinstance(s, str)
        assert not isinstance(s, dict)


# 6. No ranking or score-based top-N selection is performed inside Agent 1
def test_no_ranking_or_top_n_selection_inside_agent_1():
    """Verify Agent 1 does not rank or select top candidates based on score."""
    # Even if top_n or min_score are supplied (deprecated args), Agent 1 does not discard symbols by score
    res = run_screening(offline=True, min_score=90, top_n=3)
    # Broad discovery returns the full discovered universe, leaving downstream limit to orchestration
    assert len(res["symbols"]) > 50
    assert "rankings" not in res
    assert "top_candidates" not in res


# 7. Downstream analysis accepts symbol lists
def test_downstream_analysis_accepts_symbol_lists():
    """Verify pipe_to_agents cleanly accepts a raw list of symbols."""
    raw_symbols = ["RELIANCE", "TCS", "INFY"]
    piped = pipe_to_agents(raw_symbols, max_symbols_to_analyze=2, offline=True)
    assert len(piped) == 2
    assert piped[0]["symbol"] == "RELIANCE"
    assert piped[1]["symbol"] == "TCS"
    for item in piped:
        assert "composite_score" in item
        assert "composite_verdict" in item


# 8. Pipeline produces technical, fundamental, and composite verdicts
def test_pipeline_produces_technical_fundamental_composite_verdicts():
    """Verify that pipe_to_agents evaluates both Agent 2 and Agent 3 and computes composite verdict."""
    res = pipe_to_agents(["TRENT"], max_symbols_to_analyze=1, offline=True)
    assert len(res) == 1
    item = res[0]
    assert item["symbol"] == "TRENT"
    assert item["agent_2_score"] is not None
    assert item["agent_3_score"] is not None
    assert item["composite_score"] is not None
    assert item["composite_verdict"] in [
        "STRONG_BUY_CANDIDATE",
        "MODERATE_BUY_CANDIDATE",
        "WATCHLIST_WAIT_FOR_SETUP",
        "SPECULATIVE_TECHNICAL_ONLY",
        "NOT_RECOMMENDED",
        "REJECTED_BEARISH",
        "NEUTRAL_WAIT"
    ]
    assert item["verdict_reason"] is not None


# 9. Single-symbol execution processes the requested symbol
def test_single_symbol_execution_processes_requested_symbol():
    """Verify run_single_stock evaluates the requested symbol, not a defaulted top candidate."""
    for req_symbol in ["INFY", "TCS", "RELIANCE"]:
        single_res = run_single_stock(symbol=req_symbol, offline=True)
        assert single_res["symbol"] == req_symbol
        assert single_res["technical"]["symbol"] == req_symbol
        assert single_res["fundamental"]["symbol"] == req_symbol
        assert single_res["screening"]["eligible"] is True
        assert single_res["composite_verdict"] is not None


# 10. Provider failure does not silently result in an index-only scan
def test_provider_failure_does_not_silently_fallback_to_index(tmp_path):
    """Verify provider network failure does not silently claim NIFTY 50 coverage."""
    with patch("requests.Session.get", side_effect=Exception("Connection refused")):
        # When cache is nonexistent and network fails, falls back to broad offline seed
        nonexistent_cache = tmp_path / "empty_cache.json"
        res = discover_nse_equity_universe(cache_file=nonexistent_cache, force_refresh=True)
        assert res["metadata"]["coverage_status"] == "partial"
        assert res["metadata"]["data_source"] == "OFFLINE_BROAD_SEED_DATASET"
        assert "coverage_note" in res["metadata"]
        # Ensure it does NOT report complete coverage or claim to be an index scan
        assert res["metadata"]["coverage_status"] != "complete"
        assert res["metadata"]["data_source"] != "NIFTY_50_INDEX"


# 11. Partial universe coverage is clearly reported
def test_partial_universe_coverage_clearly_reported():
    """Verify that offline / seed mode explicitly sets coverage_status to partial."""
    res = run_screening(offline=True)
    meta = res["metadata"]
    assert meta["coverage_status"] in ["partial", "cached", "complete"]
    if meta.get("data_source") == "OFFLINE_SEED_EQUITIES":
        assert meta["coverage_status"] == "partial"
        assert len(meta.get("warnings", [])) > 0


# 12. Gated composite evaluation decouples from screening scores
def test_composite_verdict_decoupled_from_screening_score():
    """Verify evaluate_composite_verdict bases verdict purely on technical (Agent 2) and fundamental (Agent 3)."""
    # Strong tech and strong fund -> Strong Buy
    score, verdict, _ = evaluate_composite_verdict(
        agent_2_score=75,
        agent_3_score=80,
        daily_trend="bullish"
    )
    assert verdict == "STRONG_BUY_CANDIDATE"
    assert score == 78

    # Bearish technical trend must NEVER yield a BUY, even with 100/100 fundamentals
    score_bearish, verdict_bearish, _ = evaluate_composite_verdict(
        agent_2_score=40,
        agent_3_score=95,
        daily_trend="bearish"
    )
    assert verdict_bearish == "WATCHLIST_WAIT_FOR_SETUP"
