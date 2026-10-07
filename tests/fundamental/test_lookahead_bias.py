"""Unit and regression tests for point-in-time publication lag and look-ahead bias prevention."""

import pytest
import pandas as pd
from src.fundamental.data.financial_data import (
    get_publication_date,
    fetch_financial_statements
)


def test_explicit_publication_date_lookahead_prevention():
    """Test that a statement with known publication date is unavailable before publication, but available after."""
    custom_pub_dates = {
        "2025-03-31": "2025-05-10"
    }

    # As of 2025-04-01: period has ended, but results have NOT been published
    financials_before = fetch_financial_statements(
        symbol="TEST",
        as_of_date="2025-04-01",
        offline=True,
        custom_publication_dates=custom_pub_dates
    )
    # The 2025-03-31 statements MUST NOT be available
    assert "2025-03-31" not in financials_before["quarterly_is"]
    assert "2025-03-31" not in financials_before["annual_is"]

    # As of 2025-05-15: results were published on 2025-05-10, so they MUST be available
    financials_after = fetch_financial_statements(
        symbol="TEST",
        as_of_date="2025-05-15",
        offline=True,
        custom_publication_dates=custom_pub_dates
    )
    assert "2025-03-31" in financials_after["quarterly_is"] or "2025-03-31" in financials_after["annual_is"]


def test_missing_publication_date_statutory_fallback():
    """Test that when explicit publication date is missing, statutory reporting lag is enforced."""
    # Quarterly period ended 2025-06-30: 45 days statutory lag falls on 2025-08-14
    pub_dt_quarterly = get_publication_date("2025-06-30", is_annual=False)
    assert pub_dt_quarterly == pd.to_datetime("2025-06-30") + pd.Timedelta(days=45)

    # Annual period ended 2025-03-31: 60 days statutory lag falls on 2025-05-30
    pub_dt_annual = get_publication_date("2025-03-31", is_annual=True)
    assert pub_dt_annual == pd.to_datetime("2025-03-31") + pd.Timedelta(days=60)

    # Simulated analysis 10 days after quarter end (2025-07-10) should NOT have 2025-06-30 results
    financials_early = fetch_financial_statements(
        symbol="TEST",
        as_of_date="2025-07-10",
        offline=True,
        custom_publication_dates={}
    )
    assert "2025-06-30" not in financials_early["quarterly_is"]

    # Simulated analysis after statutory window (2025-08-20) should have results
    financials_late = fetch_financial_statements(
        symbol="TEST",
        as_of_date="2025-08-20",
        offline=True,
        custom_publication_dates={}
    )
    assert "2025-06-30" in financials_late["quarterly_is"]
