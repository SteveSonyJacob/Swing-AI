# Agent 2 — Technical Analysis Engine

Deterministic technical-analysis agent for swing trading Indian equities (NSE).

Agent 2 ingests stock symbols (e.g. `RELIANCE`, `TCS`, `INFY`), retrieves historical multi-timeframe market data (Daily & 1-Hour), deterministically calculates technical indicators, detects chart patterns and breakouts without look-ahead bias, evaluates market structure, scores the opportunity (0–100), calculates risk/reward levels, and emits machine-readable JSON for downstream agents.

---

## 1. Features

- **Multi-Timeframe Analysis**: Daily macro trend and 1-hour short-term confirmation.
- **Strict Look-Ahead Bias Prevention**: All rolling windows, moving averages, and breakout levels (`high.shift(1).rolling(20).max()`) strictly exclude the current candle. Point-in-time filtering via `--date` ensures historical simulation integrity.
- **Deterministic Indicators**:
  - **Moving Averages**: EMA 20, 50, 200 and normalized slopes.
  - **Momentum**: RSI 14 (Wilder's smoothing) and MACD (12, 26, 9) line/signal/hist with crossover detection.
  - **Volume**: 20-period Relative Volume (RVOL), volume expansion/contraction, and price-volume confirmation.
  - **Volatility**: ATR 14 (Wilder's smoothing) and ATR%.
- **V2 Setup Detection**:
  - 20-day and 50-day breakouts with volume confirmation.
  - Nearest confirmed support and resistance levels.
  - Relative strength (outperformance) versus NIFTY 50 (`^NSEI`) and sectoral indices over 1W, 1M, and 3M.
- **100-Point Scoring Engine**:
  - Daily Trend: 20 pts
  - Hourly Trend: 15 pts
  - Momentum: 15 pts
  - Volume: 15 pts
  - Breakout: 15 pts
  - Support & Resistance: 10 pts
  - Relative Strength: 5 pts
  - Volatility / Trade Quality: 5 pts
- **Trade Setup & Risk Calculator**:
  - Entry zone, Stop loss (`Entry - 1.5 * ATR`), Target 1, Target 2, and Risk/Reward ratio.

---

## 2. Directory Structure

```text
SwingTrade AI/
├── config/
│   └── settings.yaml            # Strategy parameters, weights, and benchmarks
├── data/
│   ├── raw/                     # Cached market data
│   └── processed/
├── outputs/
│   └── examples/
│       └── reliance_analysis.json
├── src/
│   ├── main.py                  # CLI entrypoint
│   ├── data/
│   │   ├── market_data.py       # Data fetcher, caching & synthetic fallback
│   │   ├── benchmark_data.py    # NIFTY 50 & sector index loader
│   │   └── validator.py         # Data validation & sufficiency checks
│   ├── indicators/
│   │   ├── moving_averages.py   # EMA 20/50/200 & slope calculation
│   │   ├── momentum.py          # RSI 14 & MACD 12/26/9
│   │   ├── volume.py            # 20-period Relative Volume (RVOL)
│   │   └── volatility.py        # ATR 14 & ATR%
│   ├── analysis/
│   │   ├── daily_analysis.py    # Daily trend, EMA alignment, swing structure
│   │   ├── hourly_analysis.py   # Hourly trend & alignment
│   │   ├── trend_analysis.py    # Multi-timeframe trend confirmation
│   │   ├── breakout.py          # 20D/50D breakout detection
│   │   ├── support_resistance.py# Support & resistance levels
│   │   └── relative_strength.py # Outperformance vs NIFTY 50 & sector
│   ├── scoring/
│   │   └── technical_score.py   # 100-point scoring engine
│   ├── risk/
│   │   └── trade_levels.py      # Entry, stop loss, targets, risk/reward
│   └── output/
│       └── formatter.py         # JSON schema formatter
├── tests/
│   ├── conftest.py
│   ├── test_validator.py
│   ├── test_indicators.py
│   ├── test_trend.py
│   ├── test_breakout.py
│   ├── test_scoring.py
│   └── test_risk.py
├── plan.md                      # Specification document
├── requirements.txt
└── README.md
```

---

## 3. Installation

```bash
pip install -r requirements.txt
```

---

## 4. Usage

### Run Technical Analysis for a Stock
```bash
# Live analysis for RELIANCE
python src/main.py --symbol RELIANCE

# Offline analysis (using cached or synthetic data)
python src/main.py --symbol RELIANCE --offline

# Point-in-time historical simulation
python src/main.py --symbol TCS --date 2025-06-01

# Emit pure JSON for agent piping
python src/main.py --symbol INFY --json-only
```

### Save Output to File
```bash
python src/main.py --symbol RELIANCE --offline --output outputs/reliance.json
```

---

## 5. Running Tests

Run all unit tests:
```bash
pytest -v tests/
```
