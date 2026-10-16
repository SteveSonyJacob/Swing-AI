"""Screening API endpoints for broad market discovery and universe querying."""

import math
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from src.screening.main import run_screening
from src.api.schemas.models import ScanRequest
from src.api.services.scan_manager import scan_manager

router = APIRouter(prefix="/api/screening", tags=["Screening & Discovery"])


@router.get("/universe")
def get_universe(
    query: Optional[str] = Query(None, description="Search query to filter symbols"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=10, le=500, description="Items per page"),
    offline: bool = Query(False, description="Use offline cached seed")
):
    """
    Returns discovered NSE equity symbols with search filtering and pagination.
    Does NOT return screening scores or rankings (Agent 1 pure discovery contract).
    """
    try:
        discovery = run_screening(offline=offline)
        all_symbols = discovery.get("symbols", [])
        meta = discovery.get("metadata", {})

        # Apply search filter
        if query:
            q = query.strip().upper()
            filtered_symbols = [s for s in all_symbols if q in s]
        else:
            filtered_symbols = all_symbols

        total_matching = len(filtered_symbols)
        total_pages = max(1, math.ceil(total_matching / page_size))
        current_page = min(page, total_pages)

        start_idx = (current_page - 1) * page_size
        end_idx = start_idx + page_size
        paged_symbols = filtered_symbols[start_idx:end_idx]

        return {
            "status": "success",
            "market": "NSE",
            "universe_mode": discovery.get("universe_mode", "broad_market"),
            "total_discovered": len(all_symbols),
            "total_matching": total_matching,
            "page": current_page,
            "page_size": page_size,
            "total_pages": total_pages,
            "symbols": paged_symbols,
            "metadata": meta
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve universe: {str(e)}")


@router.post("/refresh")
def refresh_universe():
    """
    Forces an immediate download and refresh of the official NSE equity master list.
    """
    try:
        res = run_screening(refresh_universe=True, offline=False)
        return {
            "status": "success",
            "message": "NSE equity universe successfully refreshed from exchange archives.",
            "total_eligible": len(res.get("symbols", [])),
            "metadata": res.get("metadata", {})
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh universe: {str(e)}")


@router.post("/scan")
def trigger_market_scan(req: ScanRequest):
    """
    Triggers a background multi-agent scan across the discovered market universe.
    """
    started = scan_manager.start_scan(
        universe=req.universe,
        max_symbols=req.max_symbols,
        refresh_universe=req.refresh_universe,
        offline=req.offline,
        symbols=req.symbols
    )
    if not started:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A market scan is already in progress. Please wait for it to complete."
        )

    return {
        "status": "started",
        "message": "Market scan initiated in the background.",
        "mode": "offline" if req.offline else "live",
        "max_symbols": req.max_symbols
    }


@router.get("/status")
def get_scan_status():
    """
    Returns the real-time status of the current or most recent market scan.
    """
    return scan_manager.get_status()


@router.get("/results")
def get_scan_results():
    """
    Returns the full results of the most recent market scan.
    """
    results = scan_manager.get_results()
    if results is None:
        return {
            "status": "no_results",
            "message": "No scan results available yet. Run a scan to generate results.",
            "screening": None,
            "multi_agent_pipeline": []
        }
    return results
