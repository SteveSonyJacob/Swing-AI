"""Regression tests for CLI output formatting and cross-platform encoding."""

import io
import pytest
from src.screening.output.formatter import print_screening_summary_table, format_screening_output


def test_cli_summary_table_encodes_cp1252():
    """Verify that print_screening_summary_table can be encoded in cp1252 (Windows default) without UnicodeEncodeError."""
    sample_data = {
        "status": "success",
        "market": "NSE",
        "discovery_timestamp": "2026-10-15T12:00:00",
        "universe_mode": "broad_market",
        "total_eligible": 2,
        "symbols": ["RELIANCE", "TCS"],
        "metadata": {
            "total_discovered": 2,
            "total_eligible": 2,
            "coverage_status": "complete",
            "data_source": "NSE_EQUITY_MASTER"
        }
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
    assert "AGENT 1 - STOCK DISCOVERY REPORT" in output_str
    assert "RELIANCE" in output_str
    assert "TCS" in output_str

    # Must encode cleanly to cp1252 and ascii without exception
    encoded_cp1252 = output_str.encode("cp1252")
    assert len(encoded_cp1252) > 0


def test_cli_summary_table_empty_candidates():
    sample_data = {
        "status": "success",
        "market": "NSE",
        "universe_mode": "broad_market",
        "total_eligible": 0,
        "symbols": [],
        "metadata": {
            "total_discovered": 0,
            "total_eligible": 0,
            "coverage_status": "empty"
        }
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
    assert "No eligible equity symbols discovered." in output_str
