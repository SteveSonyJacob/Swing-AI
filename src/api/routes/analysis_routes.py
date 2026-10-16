"""Analysis API endpoints for single-stock deep dives, charting, and history retrieval."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from run_all import run_single_stock
from src.api.schemas.models import clean_symbol
from src.api.services.chart_service import get_stock_chart_data
from src.api.services.history_service import (
    save_analysis,
    get_history,
    get_analysis_by_id,
    get_latest_for_symbol
)

router = APIRouter(prefix="/api", tags=["Stock Analysis & History"])


@router.post("/analysis/{symbol}")
def analyze_stock(
    symbol: str,
    offline: bool = Query(False, description="Use offline synthetic market data"),
    enable_llm: bool = Query(False, description="Enable news catalyst analysis")
):
    """
    Executes deep multi-agent analysis for a specific requested stock symbol:
    Agent 1 (Discovery & Eligibility) -> Agent 2 (Technical) -> Agent 3 (Fundamental) -> Decision Engine.
    """
    try:
        sym = clean_symbol(symbol)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    try:
        result = run_single_stock(sym, offline=offline, enable_llm=enable_llm)
        # Persist to local history
        save_analysis(result)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed for {sym}: {str(e)}"
        )


@router.get("/analysis/{symbol}/latest")
def get_latest_stock_analysis(symbol: str):
    """
    Retrieves the most recent saved analysis record for a given symbol from local history.
    """
    try:
        sym = clean_symbol(symbol)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    record = get_latest_for_symbol(sym)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No previous analysis found for {sym} in local history."
        )
    return record


@router.get("/chart/{symbol}")
def get_chart_data(
    symbol: str,
    limit: int = Query(90, ge=10, le=250, description="Number of daily candles to return"),
    offline: bool = Query(False, description="Use offline market data")
):
    """
    Returns actual daily OHLC candles, volume, and indicators (EMA 20/50/200, RSI, MACD)
    for interactive visual chart rendering.
    """
    try:
        sym = clean_symbol(symbol)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    res = get_stock_chart_data(sym, limit=limit, offline=offline)
    if res.get("status") == "error":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=res.get("error", f"Could not obtain chart data for {sym}")
        )
    return res


@router.get("/history")
def get_analysis_history(
    limit: int = Query(50, ge=1, le=100, description="Maximum history records to retrieve"),
    query: Optional[str] = Query(None, description="Filter history by symbol or verdict")
):
    """
    Returns the persistent list of past stock analyses.
    """
    return {
        "status": "success",
        "records": get_history(limit=limit, query=query)
    }


@router.get("/history/{record_id}")
def get_history_detail(record_id: str):
    """
    Retrieves the full analysis record by its unique ID.
    """
    record = get_analysis_by_id(record_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"History record with ID '{record_id}' not found."
        )
    return record
