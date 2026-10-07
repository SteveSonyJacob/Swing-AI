"""Regression tests for CLI output formatting and cross-platform encoding."""

import io
import pytest
from src.screening.output.formatter import print_screening_summary_table, format_screening_output


def test_cli_summary_table_encodes_cp1252():
    """Verify that print_screening_summary_table can be encoded in cp1252 (Windows default) without UnicodeEncodeError."""
    sample_data = {
        "status": "success",
        "market": "NSE",
        "scan_timestamp": "2026-10-06T12:00:00",
        "universe": "nifty50",
        "total_scanned": 50,
        "candidates_count": 2,
        "candidates": [
            {
                "symbol": "RELIANCE",
                "current_price": 2450.50,
                "change_pct": 2.15,
                "screening_score": 82,
                "category": "PRIME_SETUP",
                "tags": ["VOLUME_SHOCKER", "52W_HIGH_BREAKOUT"]
            },
            {
                "symbol": "TCS",
                "current_price": 3800.00,
                "change_pct": -0.45,
                "screening_score": 68,
                "category": "WATCHLIST",
                "tags": ["BULLISH_TREND"]
            }
        ]
    }

    # Capture stdout in a string buffer
    buf = io.StringIO()
    import sys
    old_stdout = sys.stdout
    try:
        sys.stdout = buf
        print_screening_summary_table(sample_data)
    finally:
        sys.stdout = old_stdout

    output_str = buf.getvalue()
    assert "AGENT 1 - SCREENING AGENT REPORT" in output_str
    assert "Price (INR)" in output_str
    assert "RELIANCE" in output_str

    # Must encode cleanly to cp1252 and ascii without exception
    encoded_cp1252 = output_str.encode("cp1252")
    assert len(encoded_cp1252) > 0


def test_cli_summary_table_empty_candidates():
    sample_data = {
        "status": "success",
        "universe": "nifty50",
        "total_scanned": 10,
        "candidates": []
    }
    buf = io.StringIO()
    import sys
    old_stdout = sys.stdout
    try:
        sys.stdout = buf
        print_screening_summary_table(sample_data)
    finally:
        sys.stdout = old_stdout

    output_str = buf.getvalue()
    assert "No candidate stocks met the minimum screening criteria." in output_str
