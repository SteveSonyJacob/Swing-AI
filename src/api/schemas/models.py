"""Pydantic schemas for the Swing-AI API layer."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
import re


def clean_symbol(v: str) -> str:
    """Normalize and validate an NSE symbol."""
    if not v:
        raise ValueError("Symbol cannot be empty.")
    s = v.strip().upper().replace(".NS", "")
    if s.startswith("NSE:"):
        s = s[4:]
    # Allow alphanumeric, &, -, and _
    if not re.match(r"^[A-Z0-9&\-_]{1,20}$", s):
        raise ValueError(f"Invalid NSE symbol format: '{v}'")
    return s


try:
    from pydantic import field_validator
except ImportError:
    from pydantic import validator as field_validator


class SingleStockRequest(BaseModel):
    symbol: str = Field(..., description="Stock symbol to analyze (e.g. RELIANCE, INFY, TCS)")
    offline: bool = Field(default=False, description="Use deterministic offline data without external API calls")
    enable_llm: bool = Field(default=False, description="Enable AI news catalyst analysis if available")

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v):
        return clean_symbol(v)


class ScanRequest(BaseModel):
    universe: str = Field(default="broad_market", description="Universe mode (default: broad_market)")
    max_symbols: int = Field(default=10, ge=1, le=100, description="Max symbols to evaluate downstream")
    refresh_universe: bool = Field(default=False, description="Force refresh the official NSE equity universe")
    offline: bool = Field(default=False, description="Use deterministic offline data")
    symbols: Optional[List[str]] = Field(default=None, description="Optional custom list of symbols to scan")

    @field_validator("symbols")
    @classmethod
    def validate_custom_symbols(cls, v):
        if v:
            return [clean_symbol(s) for s in v if s]
        return v


class UniverseQuery(BaseModel):
    query: Optional[str] = Field(default=None, description="Filter symbols by prefix or substring")
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=50, ge=5, le=500, description="Items per page")
