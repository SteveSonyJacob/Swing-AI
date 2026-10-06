"""Unit tests for Moneycontrol screener parser and acquisition."""

import pytest
from src.screening.sources.moneycontrol import (
    clean_number,
    parse_moneycontrol_table,
    extract_symbol_from_quote_url,
    fetch_moneycontrol_screeners,
    KNOWN_SYMBOL_MAP
)


def test_clean_number():
    assert clean_number("2,876.50") == 2876.50
    assert clean_number("+11.45%") == 11.45
    assert clean_number("-3.20") == -3.20
    assert clean_number("Rs. 1,234.00") == 1234.00
    assert clean_number("-") is None
    assert clean_number("") is None


def test_parse_moneycontrol_table_synthetic_html():
    html = """
    <table><tr><th>Header</th></tr></table>
    <table>
        <tr>
            <td>
                <div><a href="https://www.moneycontrol.com/india/stockpricequote/retail/trent/T04">Trent</a></div>
                <div><button>Vol Shocker</button></div>
            </td>
            <td><div>empty</div></td>
            <td><p>2,880.00 <span>300.00 (11.50%)</span></p></td>
            <td><p>2,900.00</p></td>
            <td><p>2,780.00</p></td>
            <td><p>2,400,000</p></td>
        </tr>
    </table>
    """
    results = parse_moneycontrol_table(html, "volume_shockers")
    assert len(results) == 1
    item = results[0]
    assert item["name"] == "Trent"
    assert item["symbol"] == "TRENT"
    assert item["price"] == 2880.0
    assert item["change_pct"] == 11.5
    assert item["days_high"] == 2900.0
    assert item["days_low"] == 2780.0
    assert "VOLUME_SHOCKER" in item["tags"]


def test_extract_symbol_known_map(monkeypatch):
    # Ensure network calls fail if attempted, verifying offline map resolution
    def mock_get(*args, **kwargs):
        raise ConnectionError("No network allowed in unit test")
    monkeypatch.setattr("requests.Session.get", mock_get)

    assert extract_symbol_from_quote_url("https://www.moneycontrol.com/india/stockpricequote/refineries/relianceindustries/RI") == "RELIANCE"
    assert extract_symbol_from_quote_url("https://www.moneycontrol.com/india/stockpricequote/retail/trent/T04") == "TRENT"
    assert extract_symbol_from_quote_url("https://www.moneycontrol.com/india/stockpricequote/ironsteel/tatasteel/TIS") == "TATASTEEL"
    assert extract_symbol_from_quote_url("https://www.moneycontrol.com/india/stockpricequote/telecommunications-equipment/hfcl/HFC") == "HFCL"


def test_fetch_moneycontrol_offline():
    candidates = fetch_moneycontrol_screeners(offline=True)
    assert len(candidates) > 0
    symbols = [c["symbol"] for c in candidates]
    assert "TRENT" in symbols
    assert "RELIANCE" in symbols
    assert all(c.get("price") is not None for c in candidates)
