"""Unit tests for the end-to-end Agent 1 broad discovery pipeline and multi-agent dispatcher."""

import pytest
from src.screening.main import run_screening, load_screening_config
from src.screening.output.pipeline import pipe_to_agents


def test_load_screening_config():
    cfg = load_screening_config()
    assert cfg.get("market") == "NSE"
    assert "universe" in cfg
    assert cfg["universe"].get("mode") == "broad_market"
    assert "primary_source_url" in cfg["universe"]


def test_run_screening_offline_pipeline():
    res = run_screening(offline=True)
    assert res["status"] == "success"
    assert res["market"] == "NSE"
    assert res["universe_mode"] == "broad_market"
    assert len(res["symbols"]) > 0
    assert "metadata" in res
    assert res["metadata"]["coverage_status"] in ["partial", "complete", "cached"]
    for sym in res["symbols"]:
        assert isinstance(sym, str)
        assert len(sym) >= 1
        assert all(c.isalnum() or c in ["&", "-", "_"] for c in sym)


def test_run_screening_custom_symbols():
    res = run_screening(custom_symbols=["reliance", "TCS", "reliance.ns", "INFY"])
    assert res["status"] == "success"
    # Normalization and deduplication
    assert res["symbols"] == ["RELIANCE", "TCS", "INFY"]
    assert res["universe_mode"] == "custom"


def test_pipe_to_agents_offline():
    symbols = ["RELIANCE", "TCS"]
    piped = pipe_to_agents(symbols, max_symbols_to_analyze=2, run_technical=True, run_fundamental=True, offline=True)
    assert len(piped) == 2
    for item in piped:
        assert item["symbol"] in ["RELIANCE", "TCS"]
        assert "composite_score" in item
        assert "composite_verdict" in item
        assert item["agent_2_score"] is not None
        assert item["agent_3_score"] is not None
        # Composite score must be derived from Agent 2 and Agent 3
        assert item["composite_score"] >= 0

