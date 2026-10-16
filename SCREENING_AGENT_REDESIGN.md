# SwingTrade AI — Agent 1: Screening Agent Redesign Summary
**Architecture Transition: From Index-Bound Filter to Market-Wide Stock Discovery Engine**

---

## 1. Overview & Objective

The objective of this redesign was to modify **Agent 1 (Screening Agent)** so that it strictly adheres to a single responsibility:
> **Discover eligible stocks across the broadest supported universe of NSE-listed equities and return their stock symbols to downstream analysis agents.**

Agent 1 is **strictly prohibited** from calculating 0–100 screening scores, ranking candidates by attractiveness, sorting stocks by composite scores, or picking "top trading opportunities." All qualitative, technical, and fundamental evaluations belong solely to Agent 2 (Technical Engine), Agent 3 (Fundamental Engine), and the Decision Engine.

---

## 2. Old Behavior vs. New Behavior

| Dimension | Old Behavior (Pre-Redesign) | New Behavior (Post-Redesign) |
|---|---|---|
| **Universe Scope** | Restricted to hard-coded index presets: `nifty50` (50 stocks), `nifty_next50` (50 stocks), or small synthetic picks. | **Market-wide NSE coverage**: ~2,575 ordinary listed equities fetched directly from official exchange archives. |
| **Data Source** | Moneycontrol web scrapers and static constituent lists. | **Official NSE Security Master Equity List** (`EQUITY_L.csv`) with automatic archive fallback and broad offline seed. |
| **Agent 1 Responsibility** | Calculated a 0–100 `screening_score` based on price momentum, RVOL, 52W proximity, penny stock penalties, and news catalysts. Ranked candidates and selected Top N. | **Pure Stock Discovery & Eligibility**: Fetches universe, normalizes/deduplicates symbols, filters series (`EQ`, `BE`), and returns clean symbol list. |
| **Scoring & Ranking** | Agent 1 produced scores and sorted candidates. | **No screening score or ranking**: Agent 1 produces zero scores and zero rankings. |
| **Downstream Interface** | Downstream pipeline expected candidate dicts with `screening_score`. Composite score was `0.30 * a1 + 0.40 * a2 + 0.30 * a3`. | Downstream pipeline (`pipe_to_agents`) accepts raw symbol lists. Composite score is derived strictly from Technical (Agent 2) and Fundamental (Agent 3). |
| **Single Stock Mode** | `run_all.py --symbol XYZ` executed screening with `top_n=1` and grabbed `candidates[0]`, resulting in candidate mismatches (e.g. returning `TRENT` regardless of symbol). | Directly verifies symbol eligibility and executes Agent 2 and Agent 3 on the exact requested symbol. |
| **Failure Handling** | Failed web scraping caused fallback to hard-coded Nifty 50 or empty candidate lists. | Failures report explicit coverage diagnostics (`coverage_status: partial` or `failed`), with no silent fallback to index presets. |

---

## 3. Data Source Selection

- **Primary Source:** National Stock Exchange of India (NSE) official security master archive:  
  `https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv`
- **Fallback Source:** Secondary NSE archive mirror:  
  `https://archives.nseindia.com/content/equities/EQUITY_L.csv`
- **Rationale:** 
  1. Official, authoritative exchange master list covering every equity admitted to trading on NSE.
  2. Delineates series cleanly: allows ordinary equities (`EQ`) and trade-for-trade / SME equities (`BE`) while excluding non-equity series:
     - Debt / Bonds (Series `GB`, `N1` to `NZ`)
     - Preference shares (Series `P1` to `P9`)
     - Mutual funds and ETFs (ISIN prefix `INF`, Series `MF`)
  3. Includes full metadata: Symbol, Company Name, Series, ISIN, Face Value, Listing Date.
  4. Avoids fragile web scraping of third-party portals for universe discovery.

---

## 4. Universe Caching & Refresh Mechanism

- **Cache File:** `data/raw/nse_equity_universe.json`
- **Cache TTL:** Configurable (default: 24 hours in `config/screening_settings.yaml`).
- **Refresh Mechanisms:**
  1. **Automatic TTL Refresh:** When the cache is older than `cache_ttl_hours`, the engine fetches the latest exchange master list.
  2. **Explicit CLI Flag:** `--refresh-universe` on both `run_screening.py` and `run_all.py` bypasses cache and downloads fresh exchange archives.
  3. **Programmatic Refresh:** `discover_nse_equity_universe(force_refresh=True)` or `run_screening(refresh_universe=True)`.
  4. **Broad Offline Seed Dataset:** When network access is unavailable and no local cache exists, an offline broad seed dataset of 121 equities (covering large, mid, small caps, and recent listings) is utilized. The engine explicitly flags this in metadata as `coverage_status: "partial"`, never claiming complete coverage.

---

## 5. Output Contract

### Screening Agent Direct Contract
```json
{
  "status": "success",
  "market": "NSE",
  "discovery_timestamp": "2026-10-15T16:54:46.102957",
  "universe_mode": "broad_market",
  "total_eligible": 2575,
  "symbols": [
    "20MICRONS",
    "360ONE",
    "ABB",
    "ACC",
    "RELIANCE",
    "TCS",
    "..."
  ],
  "metadata": {
    "data_source": "NSE_OFFICIAL_EQUITY_MASTER",
    "source_url": "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv",
    "total_discovered": 2605,
    "total_eligible": 2575,
    "excluded_count": 30,
    "exclusion_reasons": {
      "unsupported_series": 30,
      "invalid_symbol": 0,
      "duplicate_symbol": 0,
      "etf_or_mutual_fund": 0
    },
    "allowed_series": ["BE", "EQ"],
    "coverage_status": "complete",
    "is_cached": false,
    "last_refresh": "2026-10-15T16:54:46.102957",
    "failed_sources": []
  }
}
```

### Downstream Multi-Agent Orchestration Contract
```
Screening Agent (Agent 1)
       │
       ▼ [Discovered Equity Symbols: List[str]]
       │
       ├──► Agent 2: Technical Swing Engine (Trend, Momentum, Volume, Trade Setup)
       │
       └──► Agent 3: Fundamental Engine (Growth, Margins, Health, Valuation)
       │
       ▼
Decision Engine: Gated Composite Confirmation
       - Composite Score: Derived purely from Agent 2 & Agent 3
       - Gate 1: Insufficient technical data -> INSUFFICIENT_DATA_HOLD
       - Gate 2: Bearish Trend (<45 or trend="bearish") -> WATCHLIST_WAIT_FOR_SETUP or REJECTED_BEARISH
       - Gate 3: Below-threshold setup (<55) -> NOT_RECOMMENDED
       - Gate 4: Strong tech, weak fundamentals -> SPECULATIVE_TECHNICAL_ONLY
       - Gate 5: Mutual technical & fundamental confirmation -> STRONG_BUY_CANDIDATE
       - Gate 6: Moderate technical & adequate fundamentals -> MODERATE_BUY_CANDIDATE
```

---

## 6. Files Added & Modified

1. **`src/screening/sources/nse_universe.py` (New)**
   - Official NSE equity master parser and fetcher.
   - Handles HTTP requests, header normalization, series filtering (`EQ`, `BE`), ETF/Mutual Fund exclusions (ISIN `INF...`), symbol normalization, deduplication, and cache management with TTL.
   - Provides comprehensive 121-stock offline seed universe for reliable offline execution with explicit partial coverage diagnostics.

2. **`config/screening_settings.yaml` (Modified)**
   - Default universe set to `mode: broad_market`.
   - Primary and fallback NSE URLs configured.
   - Removed obsolete screening score weights and performance ranking parameters.
   - Added orchestration settings (`orchestration.max_symbols_to_analyze: 10`).

3. **`src/screening/output/formatter.py` (Modified)**
   - Redesigned canonical output schema: returns `symbols: List[str]` and separate `metadata` dictionary.
   - CP1252-safe CLI table printer displaying discovery statistics, coverage status, exclusion counts, and symbol preview without scores or ranks.

4. **`src/screening/output/pipeline.py` (Modified)**
   - Refactored `pipe_to_agents()` to accept raw symbol lists, deduplicate symbols, and enforce explicit `max_symbols_to_analyze` limits.
   - Updated `evaluate_composite_verdict()`: composite score is decoupled from Agent 1 screening scores and computed purely from Technical (Agent 2) and Fundamental (Agent 3) metrics, while maintaining backward-compatible argument signatures.

5. **`src/screening/main.py` (Modified)**
   - Main screening entry point redesigned to orchestrate broad discovery.
   - Deprecated `--min-score` and `--top-n` score/rank flags; added `--mode`, `--symbols`, `--refresh-universe`, `--max-symbols`.

6. **`run_all.py` (Modified)**
   - `run_pipeline()` updated to pass discovered symbols to downstream agents with explicit `--max-symbols` orchestration limit.
   - `run_single_stock()` updated to verify requested symbol against discovery and directly evaluate Agent 2 and Agent 3 on that specific symbol.
   - Multi-agent report display updated to show Discovery status (Eligible/NSE) instead of obsolete screening score.

7. **`tests/screening/test_broad_discovery.py` (New)**
   - Comprehensive test suite validating all 12 prompt requirements:
     1. Scanner not restricted to NIFTY 50.
     2. Valid symbols outside predefined indices discovered (e.g. `20MICRONS`, `360ONE`).
     3. Duplicate symbols removed.
     4. Unsupported instruments (ETFs, debt series, preference shares) excluded.
     5. No screening score calculated.
     6. No ranking or score-based top-N selection inside Agent 1.
     7. Downstream analysis accepts symbol lists.
     8. Pipeline produces technical, fundamental, and composite verdicts.
     9. Single-symbol execution processes the requested symbol.
     10. Provider failure does not silently result in an index-only scan.
     11. Partial universe coverage clearly reported.
     12. Composite verdicts decoupled from screening scores.

8. **`tests/screening/test_screening_pipeline.py`, `tests/screening/test_cli_formatter.py`, `tests/screening/test_catalyst_llm.py` (Modified)**
   - Updated assertions to match the redesigned contract (symbols list + metadata, CP1252 safety, removal of obsolete score expectations).

---

## 7. Verification Results

### 1. Test Suite Verification
```bash
python -m pytest -v
```
**Result:** **91 passed in 7.73s (100% pass rate)** across all test modules:
- `tests/screening/test_broad_discovery.py`: 12/12 passed
- `tests/screening/test_screening_pipeline.py`: 4/4 passed
- `tests/screening/test_cli_formatter.py`: 2/2 passed
- `tests/screening/test_catalyst_llm.py`: 8/8 passed
- `tests/screening/test_filters.py`: 4/4 passed
- `tests/screening/test_gated_verdicts.py`: 5/5 passed
- `tests/screening/test_moneycontrol.py`: 5/5 passed
- `tests/screening/test_screening_score.py`: 4/4 passed
- `tests/screening/test_yfinance_scanner.py`: 5/5 passed
- `tests/fundamental/*`: 21/21 passed
- `tests/test_*`: 21/21 passed

### 2. CLI Smoke Tests
- **Broad Market Discovery:**
  ```bash
  python run_screening.py --offline
  ```
  *Output:* Discovered 2,605 securities, filtered 30 non-equity series, returning 2,575 eligible ordinary equities under `NSE_OFFICIAL_EQUITY_MASTER` with CP1252-safe formatting.
- **Raw JSON Output:**
  ```bash
  python run_screening.py --offline --json-only
  ```
  *Output:* Clean JSON containing `symbols: [...]` and diagnostic `metadata: {...}`.
- **End-to-End Multi-Agent Pipeline:**
  ```bash
  python run_all.py --offline --top-n 3
  ```
  *Output:* Discovered full NSE universe, passed first 3 stocks (`20MICRONS`, `21STCENMGM`, `360ONE`) to Agent 2 and Agent 3. Generated gated composite verdicts and execution trade setups with no screening scores.
- **Single Stock Deep Analysis:**
  ```bash
  python run_all.py --symbol RELIANCE --offline
  python run_all.py --symbol INFY --offline
  ```
  *Output:* Each run verified symbol eligibility and executed deep technical and fundamental analysis strictly on the requested symbol (`RELIANCE` and `INFY` respectively), eliminating previous candidate mismatch defects.

---

## 8. Known Limitations & Future Considerations

1. **Exchange Archive Connectivity:** The official NSE archives endpoint (`https://nsearchives.nseindia.com/...`) requires standard browser headers (User-Agent, Accept). Network firewalls or cloud worker IP restrictions could trigger HTTP 403; the engine provides fallback URLs, a local 24-hour cache, and offline seed datasets with clear partial coverage diagnostics to prevent disruptions.
2. **Downstream API Bandwidth:** While Agent 1 discovers 2,500+ symbols in seconds, evaluating thousands of stocks through yfinance in downstream engines requires batching or rate limiting. Orchestration explicitly limits downstream evaluation via `--max-symbols` (default: 10).
