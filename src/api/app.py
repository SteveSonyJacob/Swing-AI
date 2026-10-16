"""FastAPI application entry point for Swing-AI financial analytics and research UI."""

import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes.screening_routes import router as screening_router
from src.api.routes.analysis_routes import router as analysis_router
from src.screening.sources.nse_universe import CACHE_FILE, load_cached_universe
from src.api.services.history_service import get_history
from src.api.services.scan_manager import scan_manager

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
UI_DIR = PROJECT_ROOT / "ui"
STATIC_DIR = UI_DIR / "static"
TEMPLATES_DIR = UI_DIR / "templates"

STATIC_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Swing-AI",
    description="Multi-Agent Stock Discovery and Swing Trading Analysis for NSE Equities",
    version="2.0.0"
)

# CORS setup for local access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static assets
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Include API routers
app.include_router(screening_router)
app.include_router(analysis_router)


@app.get("/api/health", tags=["System"])
def health_check():
    """System health check and operational state diagnostics."""
    cached = load_cached_universe(CACHE_FILE) if CACHE_FILE.exists() else None
    cached_count = len(cached.get("symbols", [])) if cached else 0
    history_records = get_history(limit=10)

    scan_status = scan_manager.get_status()

    return {
        "status": "healthy",
        "service": "Swing-AI",
        "market": "NSE (India)",
        "version": "2.0.0",
        "universe": {
            "is_cached": cached is not None,
            "cached_symbols_count": cached_count,
            "cache_file": str(CACHE_FILE),
            "coverage_status": cached.get("metadata", {}).get("coverage_status", "unknown") if cached else "uncached"
        },
        "history": {
            "recent_count": len(history_records)
        },
        "scanner": {
            "status": scan_status.get("status")
        }
    }


@app.get("/", response_class=HTMLResponse, tags=["UI Shell"])
def serve_ui(request: Request):
    """Serves the desktop-first Swing-AI terminal interface."""
    return templates.TemplateResponse(request=request, name="index.html")
