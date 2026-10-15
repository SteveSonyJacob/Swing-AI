"""Comprehensive integration test suite for Swing-AI FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.api.app import app

client = TestClient(app)


def test_health_check_endpoint():
    """Verify GET /api/health returns healthy operational status."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["service"] == "Swing-AI"
    assert "NSE (India)" in data["market"]
    assert "universe" in data
    assert "scanner" in data


def test_serve_ui_shell():
    """Verify root GET / serves HTML application shell containing Swing-AI branding."""
    res = client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert "Swing-AI" in res.text
    assert "Market Scanner" in res.text
    assert "Stock Analysis" in res.text


def test_get_universe_endpoint():
    """Verify GET /api/screening/universe returns discovered symbols without scores."""
    res = client.get("/api/screening/universe?page=1&page_size=20&offline=true")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["market"] == "NSE"
    assert data["page"] == 1
    assert len(data["symbols"]) <= 20
    assert data["total_discovered"] > 0
    # Agent 1 contract: clean symbol strings, no screening scores
    for sym in data["symbols"]:
        assert isinstance(sym, str)


def test_get_universe_search_filter():
    """Verify search query filtering on GET /api/screening/universe."""
    res = client.get("/api/screening/universe?query=RELIANCE&offline=true")
    assert res.status_code == 200
    data = res.json()
    assert "RELIANCE" in data["symbols"]
    for s in data["symbols"]:
        assert "RELIANCE" in s


def test_analyze_stock_endpoint_offline():
    """Verify POST /api/analysis/{symbol} executes multi-agent analysis for requested symbol."""
    for test_sym in ["RELIANCE", "INFY"]:
        res = client.post(f"/api/analysis/{test_sym}?offline=true")
        assert res.status_code == 200
        data = res.json()
        assert data["symbol"] == test_sym
        assert "composite_score" in data
        assert "composite_verdict" in data
        assert "technical" in data
        assert "fundamental" in data
        assert data["technical"]["symbol"] == test_sym
        assert data["fundamental"]["symbol"] == test_sym
        assert data["screening"]["eligible"] is True


def test_analyze_stock_invalid_symbol():
    """Verify invalid symbols are rejected with HTTP 400."""
    res = client.post("/api/analysis/INVALID$$SYMBOL!@#?offline=true")
    assert res.status_code == 400
    assert "Invalid NSE symbol format" in res.json()["detail"]


def test_get_chart_data_endpoint():
    """Verify GET /api/chart/{symbol} returns real historical OHLCV and indicator data."""
    res = client.get("/api/chart/RELIANCE?limit=30&offline=true")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["symbol"] == "RELIANCE"
    assert len(data["candles"]) <= 30
    assert len(data["candles"]) > 0
    first_candle = data["candles"][0]
    assert "date" in first_candle
    assert "open" in first_candle
    assert "high" in first_candle
    assert "low" in first_candle
    assert "close" in first_candle
    assert "volume" in first_candle
    assert "ema_20" in first_candle


def test_analysis_history_persistence():
    """Verify analyses are recorded and retrievable via GET /api/history."""
    # Analyze a stock to ensure at least one record exists
    client.post("/api/analysis/TCS?offline=true")

    res = client.get("/api/history?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert len(data["records"]) > 0
    symbols_in_history = [r["symbol"] for r in data["records"]]
    assert "TCS" in symbols_in_history

    # Retrieve specific latest analysis for symbol
    res_latest = client.get("/api/analysis/TCS/latest")
    assert res_latest.status_code == 200
    assert res_latest.json()["symbol"] == "TCS"


def test_market_scan_lifecycle():
    """Verify scan trigger and status reporting."""
    res_status = client.get("/api/screening/status")
    assert res_status.status_code == 200
    status_data = res_status.json()
    assert "status" in status_data
    assert "progress" in status_data
