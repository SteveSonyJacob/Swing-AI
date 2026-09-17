# Agent 2 — Technical Analysis Engine
## Implementation Plan

### 1. Objective

Build a deterministic technical-analysis agent for the swing-trading system.

The agent receives a stock symbol and analysis date, retrieves historical market data, calculates technical indicators across multiple timeframes, detects technical setups, calculates a 0–100 technical score, and returns structured JSON.

The system should **calculate facts deterministically** and use an LLM only for optional natural-language explanation. The LLM must not invent indicator values or independently decide the score.

---

## 2. Scope

### V1 — Core Technical Engine

Implement:

- OHLCV data acquisition
- Daily timeframe analysis
- 1-hour timeframe analysis
- EMA 20 / 50 / 200
- RSI 14
- MACD
- Volume / Relative Volume
- ATR 14
- Basic trend classification
- Basic technical scoring
- Structured JSON output
- Error handling and data validation

### V2 — Setup Detection

Add:

- Support/resistance
- Swing highs/lows
- 20-day / 50-day breakouts
- Breakout volume confirmation
- Higher-high / higher-low detection
- Relative strength versus NIFTY 50
- Relative strength versus sector index
- Entry/stop/target estimation
- Risk/reward calculation

### V3 — Advanced Analysis

Potential additions:

- 15-minute confirmation timeframe
- Volume profile
- Advanced consolidation detection
- Pullback detection
- Trend continuation setups
- Gap analysis
- Divergence detection
- Additional volatility measures
- More robust sector-relative analysis

### V4 — Backtesting

Evaluate whether the scoring system has historical predictive value.

Test:

- 1-day forward return
- 3-day forward return
- 5-day forward return
- 10-day forward return
- Maximum favorable excursion
- Maximum adverse excursion
- Win rate
- Average return
- Average R multiple
- Profit factor
- Maximum drawdown

Use point-in-time data to avoid look-ahead bias.

---

# 3. Architecture

```text
                  Stock Symbol
                       |
                       v
              +------------------+
              | Data Acquisition |
              +--------+---------+
                       |
                       v
              +------------------+
              | Data Validation  |
              +--------+---------+
                       |
          +------------+-------------+
          |            |             |
          v            v             v
       Daily         Hourly       Benchmark
       Analysis      Analysis     Analysis
          |            |             |
          +------------+-------------+
                       |
                       v
              +------------------+
              | Indicator Engine |
              +--------+---------+
                       |
                       v
              +------------------+
              | Setup Detection  |
              +--------+---------+
                       |
                       v
              +------------------+
              | Scoring Engine   |
              +--------+---------+
                       |
                       v
              +------------------+
              | Risk Calculator  |
              +--------+---------+
                       |
                       v
              +------------------+
              | JSON Formatter   |
              +--------+---------+
                       |
                       v
                Agent 2 Output
```

Optional:

```text
Agent 2 JSON
     |
     v
LLM Explanation Layer
     |
     v
Human-readable explanation
```

---

# 4. Recommended Project Structure

```text
technical-agent/
│
├── README.md
├── plan.md
├── requirements.txt
├── .env
├── .gitignore
│
├── config/
│   └── settings.yaml
│
├── data/
│   ├── raw/
│   └── processed/
│
├── src/
│   ├── main.py
│   │
│   ├── data/
│   │   ├── market_data.py
│   │   ├── benchmark_data.py
│   │   └── validator.py
│   │
│   ├── indicators/
│   │   ├── trend.py
│   │   ├── moving_averages.py
│   │   ├── momentum.py
│   │   ├── volume.py
│   │   └── volatility.py
│   │
│   ├── analysis/
│   │   ├── daily_analysis.py
│   │   ├── hourly_analysis.py
│   │   ├── trend_analysis.py
│   │   ├── breakout.py
│   │   ├── support_resistance.py
│   │   └── relative_strength.py
│   │
│   ├── scoring/
│   │   └── technical_score.py
│   │
│   ├── risk/
│   │   └── trade_levels.py
│   │
│   └── output/
│       └── formatter.py
│
├── tests/
│   ├── test_data.py
│   ├── test_indicators.py
│   ├── test_trend.py
│   ├── test_breakout.py
│   ├── test_scoring.py
│   └── test_risk.py
│
└── outputs/
    └── examples/
```

---

# 5. Data Acquisition

## Required data

For each stock:

### Daily

At minimum:

- Open
- High
- Low
- Close
- Adjusted Close
- Volume

Recommended historical period:

- 1–2 years

This provides enough history for EMA 200 and historical analysis.

### Hourly

At minimum:

- Open
- High
- Low
- Close
- Volume

Use as much historical hourly data as the selected data provider reliably supports.

### Benchmark

Fetch:

- NIFTY 50
- Relevant sector index

Benchmark data is required for relative-strength analysis.

---

# 6. Data Validation

Before calculating indicators, verify:

- Data is not empty
- Required columns exist
- Timestamps are valid
- Data is sorted chronologically
- Duplicate timestamps are handled
- Missing OHLC values are handled
- Volume is non-negative
- Enough rows exist for EMA 200
- Timeframe is correct
- Market holidays/gaps are not incorrectly treated as missing candles

If insufficient data exists:

```json
{
  "status": "insufficient_data",
  "symbol": "XYZ",
  "reason": "Not enough daily candles for EMA200"
}
```

Never silently generate a score from incomplete data.

---

# 7. Indicator Engine

## Moving averages

Calculate:

- EMA 20
- EMA 50
- EMA 200

For both:

- Daily
- Hourly

Also calculate EMA slopes.

Example:

```text
EMA20_slope =
(EMA20_current - EMA20_N_periods_ago)
/
EMA20_N_periods_ago
```

Use a consistent slope window defined in configuration.

---

# 8. Daily Trend Analysis

Determine:

### Bullish alignment

```text
Price > EMA20
EMA20 > EMA50
EMA50 > EMA200
```

### Bearish alignment

```text
Price < EMA20
EMA20 < EMA50
EMA50 < EMA200
```

Also evaluate:

- EMA slopes
- Recent swing structure
- Higher highs
- Higher lows
- Lower highs
- Lower lows

Return:

```json
{
  "trend": "bullish",
  "ema_alignment": true,
  "ema20_slope": 0.012,
  "ema50_slope": 0.008,
  "market_structure": "higher_highs_higher_lows"
}
```

Do not force bullish/bearish classification when evidence is mixed.

Possible values:

```text
bullish
bearish
neutral
mixed
```

---

# 9. Hourly Trend Analysis

Perform the same analysis on the 1-hour timeframe.

The objective is to determine whether the shorter-term trend confirms the daily trend.

Example:

```text
Daily  = bullish
Hourly = bullish

→ Trend confirmation
```

versus:

```text
Daily  = bullish
Hourly = bearish

→ Short-term countertrend
```

This distinction should affect the score.

---

# 10. Momentum Analysis

## RSI

Calculate:

```text
RSI(14)
```

Suggested interpretation:

```text
< 30       Oversold
30–50       Weak
50–60       Positive
60–70       Strong momentum
> 70        Potentially extended
```

Do not automatically classify RSI > 70 as bearish.

Store the raw RSI value and the interpretation separately.

## MACD

Calculate:

- MACD
- Signal
- Histogram

Detect:

- MACD > Signal
- MACD < Signal
- Bullish crossover
- Bearish crossover
- Positive histogram
- Negative histogram

Do this for daily and hourly data.

---

# 11. Volume Analysis

Calculate:

```text
Relative Volume =
Current Volume / Average Volume
```

Use a configurable lookback, initially:

```text
20 periods
```

Detect:

- Volume expansion
- Volume contraction
- Breakout volume
- Price-volume confirmation

Example:

```text
Price breakout = true
Relative volume = 2.1
```

This should produce stronger confirmation than:

```text
Price breakout = true
Relative volume = 0.7
```

---

# 12. Volatility

Calculate:

```text
ATR(14)
ATR %
```

Where:

```text
ATR% = ATR / Close × 100
```

Use ATR later for:

- Stop-loss estimation
- Position-risk estimation
- Risk/reward
- Avoiding unrealistic setups

---

# 13. Breakout Detection — V2

Implement basic quantitative breakout rules first.

### 20-day breakout

```text
Current close > previous 20-day high
```

### 50-day breakout

```text
Current close > previous 50-day high
```

Important:

The breakout reference must exclude the current candle.

Correct:

```python
previous_high = high.shift(1).rolling(20).max()
breakout = close > previous_high
```

This prevents look-ahead errors.

Then check volume confirmation.

---

# 14. Support / Resistance — V2

Identify:

- Recent swing highs
- Recent swing lows
- 20-day high
- 50-day high
- Recent consolidation levels

Return nearest:

```text
support
resistance
```

Avoid claiming exact support/resistance when the data does not provide a clear level.

---

# 15. Relative Strength — V2

Compare stock performance against:

### NIFTY 50

Example:

```text
Stock 1M return = +12%
NIFTY 1M return = +5%

Relative outperformance = +7%
```

Also compare against the relevant sector index.

Calculate configurable periods such as:

- 1 week
- 1 month
- 3 months

---

# 16. Scoring Engine

Initial score:

| Component | Points |
|---|---:|
| Daily trend | 20 |
| Hourly trend | 15 |
| Momentum | 15 |
| Volume | 15 |
| Breakout | 15 |
| Support/resistance | 10 |
| Relative strength | 5 |
| Volatility/trade quality | 5 |
| **Total** | **100** |

## Example scoring

### Daily trend — 20

Possible factors:

```text
Price > EMA20           +4
EMA20 > EMA50           +4
EMA50 > EMA200          +4
Positive EMA slopes     +4
Bullish market structure +4
```

### Hourly trend — 15

```text
Price > EMA20           +4
EMA20 > EMA50           +4
Positive slope          +3
Bullish structure       +4
```

### Momentum — 15

Combine:

- RSI
- MACD
- Momentum confirmation

### Volume — 15

Combine:

- Relative volume
- Price-volume confirmation
- Breakout volume

### Breakout — 15

Reward:

- Confirmed breakout
- Breakout above significant level
- Volume confirmation

Do not award breakout points merely because price is close to resistance.

---

# 17. Score Categories

The numerical score should remain the primary output.

For presentation, optionally map it to:

```text
0–30    Weak
30–50   Neutral
50–70   Positive
70–85   Strong
85–100  Very strong
```

These are internal system categories, not guaranteed return predictions.

---

# 18. Risk / Trade-Level Analysis — V2

For a bullish setup calculate:

```text
Entry zone
Stop loss
Target 1
Target 2
Risk/reward
```

Initially:

```text
Stop =
Entry - 1.5 × ATR
```

Targets should preferably use nearby resistance and/or an ATR-based projection.

Example:

```text
Entry:      ₹1,250
Stop:       ₹1,205
Target 1:   ₹1,330
Target 2:   ₹1,380
```

Calculate:

```text
Risk = Entry - Stop
Reward = Target - Entry
R:R = Reward / Risk
```

Do not produce trade levels when support/resistance or volatility data is insufficient.

---

# 19. Output Schema

Final output should be machine-readable.

Example:

```json
{
  "status": "success",
  "symbol": "RELIANCE",
  "market": "NSE",
  "analysis_timestamp": "2026-09-18T00:00:00+05:30",

  "technical_score": 84,

  "score_breakdown": {
    "daily_trend": 18,
    "hourly_trend": 14,
    "momentum": 13,
    "volume": 13,
    "breakout": 12,
    "support_resistance": 7,
    "relative_strength": 4,
    "volatility": 3
  },

  "trend": {
    "daily": "bullish",
    "hourly": "bullish",
    "daily_ema_alignment": true,
    "hourly_ema_alignment": true,
    "market_structure": "higher_highs_higher_lows"
  },

  "momentum": {
    "daily_rsi": 63.4,
    "hourly_rsi": 61.2,
    "daily_macd": "bullish",
    "hourly_macd": "bullish"
  },

  "volume": {
    "relative_volume": 1.82,
    "confirmation": true
  },

  "breakout": {
    "detected": true,
    "type": "20_day_high",
    "volume_confirmed": true
  },

  "levels": {
    "support": 1410,
    "resistance": 1500
  },

  "volatility": {
    "atr_14": 28.4,
    "atr_percent": 1.96
  },

  "relative_strength": {
    "vs_nifty_1m": 7.2,
    "vs_sector_1m": 4.8
  },

  "trade_setup": {
    "direction": "long",
    "entry_zone": null,
    "stop_loss": null,
    "target_1": null,
    "target_2": null,
    "risk_reward": null
  }
}
```

Use `null` instead of inventing values.

---

# 20. Configuration

Keep strategy parameters outside the code.

Example:

```yaml
indicators:
  ema:
    short: 20
    medium: 50
    long: 200

  rsi:
    period: 14

  atr:
    period: 14

  volume:
    lookback: 20

breakouts:
  short: 20
  long: 50

scoring:
  daily_trend: 20
  hourly_trend: 15
  momentum: 15
  volume: 15
  breakout: 15
  support_resistance: 10
  relative_strength: 5
  volatility: 5
```

This makes it easy to backtest different configurations later.

---

# 21. Testing Strategy

Every indicator should have unit tests.

Test:

- EMA calculation
- RSI calculation
- MACD calculation
- ATR calculation
- Relative volume
- Breakout detection
- Trend classification
- Score calculation
- Risk/reward calculation

Also test edge cases:

```text
Empty data
Missing candles
Insufficient history
Zero volume
NaN indicators
Duplicate timestamps
Extreme price movements
```

---

# 22. Backtesting Rules

Do not optimize the score using the same period used to evaluate it.

Use:

```text
Historical data
      |
      +---- Training / calibration period
      |
      +---- Validation period
      |
      +---- Final unseen test period
```

Never use future information when calculating a historical score.

For example, when calculating the score on:

```text
2025-06-01
```

the engine must only see information available by the close/time being simulated.

---

# 23. Logging

Every analysis should log:

```text
timestamp
symbol
data source
latest candle timestamp
indicator values
score components
final score
errors/warnings
```

This makes debugging and backtesting much easier.

---

# 24. Development Milestones

## Milestone 1 — Data

- [ ] Choose market-data provider
- [ ] Implement daily data retrieval
- [ ] Implement hourly data retrieval
- [ ] Implement benchmark retrieval
- [ ] Add validation
- [ ] Cache data locally

## Milestone 2 — Indicators

- [ ] EMA 20
- [ ] EMA 50
- [ ] EMA 200
- [ ] EMA slopes
- [ ] RSI 14
- [ ] MACD
- [ ] ATR 14
- [ ] Relative volume

## Milestone 3 — Trend

- [ ] Daily trend
- [ ] Hourly trend
- [ ] Market structure
- [ ] Trend confirmation

## Milestone 4 — Scoring

- [ ] Implement score components
- [ ] Implement 0–100 score
- [ ] Implement score breakdown
- [ ] Add configuration-driven weights

## Milestone 5 — V2 Setups

- [ ] Breakout detection
- [ ] Support/resistance
- [ ] Relative strength
- [ ] Trade levels
- [ ] Risk/reward

## Milestone 6 — Output

- [ ] JSON schema
- [ ] API endpoint
- [ ] Error responses
- [ ] Logging

## Milestone 7 — Backtesting

- [ ] Historical simulation
- [ ] Forward returns
- [ ] Win rate
- [ ] R-multiple analysis
- [ ] Drawdown
- [ ] Parameter testing
- [ ] Out-of-sample validation

---

# 25. Definition of Done

Agent 2 is considered ready for integration with the other agents when:

- [ ] A stock symbol can be submitted programmatically
- [ ] Daily and hourly market data are retrieved successfully
- [ ] All V1 indicators are calculated deterministically
- [ ] Daily and hourly trends are classified
- [ ] Technical score is reproducible
- [ ] Score breakdown is available
- [ ] No future data is used
- [ ] Insufficient/invalid data is handled safely
- [ ] JSON output follows a fixed schema
- [ ] Unit tests pass
- [ ] Historical backtesting pipeline exists
- [ ] Results can be stored for comparison with future performance

---

# 26. Important Design Principle

The technical agent should answer:

> "What does the current market data quantitatively indicate?"

It should **not** answer:

> "This stock will go up."

The final trading system can combine:

```text
Catalyst Agent
      +
Technical Agent
      +
Fundamental Agent
      +
Risk Engine
      ↓
Final opportunity score
```

Agent 2 should remain modular so its technical score can be independently evaluated and backtested before being combined with the other agents.
