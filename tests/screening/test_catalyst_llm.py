"""Unit and integration tests for Agent 1 LLM qualitative news and catalyst analysis."""

import io
import sys
import pytest
from src.screening.llm.news_fetcher import fetch_candidate_news, get_offline_news
from src.screening.llm.catalyst_analyzer import (
    analyze_catalyst_with_llm,
    heuristic_catalyst_evaluation
)
from src.screening.scoring.screening_score import compute_screening_score
from src.screening.main import run_screening
from src.screening.output.formatter import print_screening_summary_table


def test_fetch_candidate_news_offline():
    """Verify offline deterministic news retrieval."""
    news_trent = fetch_candidate_news("TRENT", max_items=3, offline=True)
    assert len(news_trent) > 0
    assert any("Westside" in n["title"] or "profit" in n["title"].lower() for n in news_trent)

    news_unknown = fetch_candidate_news("XYZUNKNOWN", max_items=2, offline=True)
    assert len(news_unknown) > 0
    assert "XYZUNKNOWN" in news_unknown[0]["title"]


def test_heuristic_catalyst_positive():
    """Verify bullish catalyst detection from headlines."""
    headlines = [
        {"title": "BHEL secures mega thermal power equipment order worth Rs 6,100 crore", "source": "Livemint"},
        {"title": "Order book expands to new historic peak", "source": "Economic Times"}
    ]
    res = heuristic_catalyst_evaluation("BHEL", headlines)
    assert res["catalyst_score"] >= 8
    assert res["sentiment"] == "BULLISH"
    assert res["catalyst_type"] in ["ORDER_WIN", "EXPANSION"]
    assert "Positive news trigger" in res["summary"]


def test_heuristic_catalyst_negative():
    """Verify bearish catalyst detection from headlines."""
    headlines = [
        {"title": "Tax department conducts raid on corporate headquarters following probe", "source": "Reuters"},
        {"title": "SEBI notice issued regarding governance irregularities", "source": "Livemint"}
    ]
    res = heuristic_catalyst_evaluation("TESTSYM", headlines)
    assert res["catalyst_score"] <= 3
    assert res["sentiment"] == "BEARISH"
    assert res["catalyst_type"] == "REGULATORY_LEGAL"
    assert "Negative news headwind" in res["summary"]


def test_heuristic_catalyst_corporate_calendar_boost():
    """Verify earnings calendar proximity provides catalyst weight boost."""
    headlines = [{"title": "Company prepares for quarterly earnings release", "source": "Market News"}]
    res_boost = heuristic_catalyst_evaluation("TESTSYM", headlines, corporate_context={"days_to_results": 4})
    res_normal = heuristic_catalyst_evaluation("TESTSYM", headlines, corporate_context={"days_to_results": 60})
    assert res_boost["catalyst_score"] > res_normal["catalyst_score"]


def test_llm_catalyst_integration_in_screening_score():
    """Verify that compute_screening_score integrates llm_catalyst correctly."""
    cand = {
        "price": 2880.0,
        "change_pct": 5.0,
        "volume": 2000000,
        "turnover_cr": 100.0,
        "llm_catalyst": {
            "catalyst_score": 9,
            "sentiment": "BULLISH",
            "catalyst_type": "ORDER_WIN",
            "summary": "Major contract win"
        }
    }
    res = compute_screening_score(cand)
    assert res["score_breakdown"]["catalyst"] == 9
    assert "LLM_CATALYST_BULLISH" in res["tags"]
    assert res["catalyst_status"] == "bullish_catalyst"

    # Bearish catalyst test
    cand_bearish = {
        "price": 2880.0,
        "change_pct": 5.0,
        "volume": 2000000,
        "turnover_cr": 100.0,
        "llm_catalyst": {
            "catalyst_score": 2,
            "sentiment": "BEARISH",
            "catalyst_type": "REGULATORY_LEGAL",
            "summary": "SEBI penalty"
        }
    }
    res_b = compute_screening_score(cand_bearish)
    assert res_b["score_breakdown"]["catalyst"] == 2
    assert "LLM_CATALYST_BEARISH" in res_b["tags"]
    assert res_b["catalyst_status"] == "bearish_catalyst"


def test_run_screening_with_llm_offline():
    """End-to-end screening pipeline with enable_llm=True in offline mode."""
    res = run_screening(
        universe="nifty50",
        min_score=50,
        top_n=3,
        offline=True,
        enable_llm=True
    )
    assert res["status"] == "success"
    assert len(res["candidates"]) > 0

    # Candidates should have llm_catalyst attached
    first = res["candidates"][0]
    assert "llm_catalyst" in first
    assert "catalyst_score" in first["llm_catalyst"]
    assert "sentiment" in first["llm_catalyst"]
    assert "summary" in first["llm_catalyst"]


def test_formatter_displays_llm_catalyst():
    """Verify CLI table formatter displays AI catalyst analysis without encoding issues."""
    sample_data = {
        "status": "success",
        "universe": "nifty50",
        "total_scanned": 10,
        "candidates": [
            {
                "symbol": "TRENT",
                "current_price": 2880.0,
                "change_pct": 4.5,
                "screening_score": 85,
                "category": "PRIME_SETUP",
                "tags": ["VOLUME_SHOCKER"],
                "llm_catalyst": {
                    "catalyst_score": 9,
                    "sentiment": "BULLISH",
                    "catalyst_type": "ORDER_WIN",
                    "provider": "heuristic",
                    "summary": "Q2 profit surges 46% YoY with strong retail demand."
                }
            }
        ]
    }

    buf = io.StringIO()
    old_stdout = sys.stdout
    try:
        sys.stdout = buf
        print_screening_summary_table(sample_data)
    finally:
        sys.stdout = old_stdout

    out = buf.getvalue()
    assert "AI QUALITATIVE CATALYST & NEWS ANALYSIS" in out
    assert "[TRENT] Catalyst Score: 9/10" in out
    assert "BULLISH" in out
    # Verify cp1252 compatibility
    assert len(out.encode("cp1252")) > 0
