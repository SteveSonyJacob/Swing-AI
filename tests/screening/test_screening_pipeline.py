"""Unit tests for the end-to-end Agent 1 pipeline and multi-agent dispatcher."""

import pytest
from src.screening.main import run_screening, load_screening_config
from src.screening.output.pipeline import pipe_to_agents


def test_load_screening_config():
    cfg = load_screening_config()
    assert "scoring" in cfg
    assert "thresholds" in cfg
    assert "universes" in cfg
    assert "nifty50" in cfg["universes"]


def test_run_screening_offline_pipeline():
    res = run_screening(universe="nifty50", source="all", min_score=40, top_n=5, offline=True)
    assert res["status"] == "success"
    assert res["market"] == "NSE"
    assert res["total_scanned"] > 0
    assert len(res["candidates"]) <= 5
    for cand in res["candidates"]:
        assert "symbol" in cand
        assert "screening_score" in cand
        assert "score_breakdown" in cand
        assert "suggested_action" in cand
        assert cand["screening_score"] >= 40


def test_run_screening_source_filters():
    res_mc = run_screening(source="moneycontrol", offline=True)
    assert res_mc["status"] == "success"
    assert len(res_mc["candidates"]) > 0

    res_yf = run_screening(source="yfinance", universe="nifty50", offline=True)
    assert res_yf["status"] == "success"
    assert len(res_yf["candidates"]) > 0


def test_pipe_to_agents_offline():
    candidates = [
        {"symbol": "RELIANCE", "screening_score": 82},
        {"symbol": "TCS", "screening_score": 75}
    ]
    piped = pipe_to_agents(candidates, top_n=2, run_technical=True, run_fundamental=True, offline=True)
    assert len(piped) == 2
    for item in piped:
        assert item["symbol"] in ["RELIANCE", "TCS"]
        assert "agent_1_score" in item
        assert "composite_score" in item
        assert "composite_verdict" in item
        assert item["agent_2_score"] is not None
        assert item["agent_3_score"] is not None
