/**
 * Swing-AI — Frontend Application Logic
 * Desktop-first financial research terminal connecting to real multi-agent backend.
 */

class SwingAIApp {
  constructor() {
    this.currentView = "overview";
    this.universePage = 1;
    this.universeQuery = "";
    this.universeTotalPages = 1;
    this.scanPollInterval = null;
    this.priceChart = null;
    this.rsiChart = null;
    this.historyCache = [];

    this.init();
  }

  init() {
    this.setupNav();
    this.setupQuickSearch();
    this.loadHealthAndOverview();
    this.loadRecentAnalyses();
    this.loadUniverse(1);

    // Global refresh button
    document.getElementById("btn-global-refresh").addEventListener("click", () => {
      this.loadHealthAndOverview();
      this.loadRecentAnalyses();
      this.showToast("System state refreshed.", "info");
    });
  }

  /* -------------------------------------------------------------------------
     Navigation
     ------------------------------------------------------------------------- */
  setupNav() {
    const navItems = document.querySelectorAll(".nav-item");
    navItems.forEach(item => {
      item.addEventListener("click", () => {
        const view = item.getAttribute("data-view");
        this.navTo(view);
      });
    });
  }

  navTo(viewName) {
    this.currentView = viewName;
    document.querySelectorAll(".nav-item").forEach(item => {
      item.classList.toggle("active", item.getAttribute("data-view") === viewName);
    });

    document.querySelectorAll(".view-section").forEach(sec => {
      sec.classList.remove("active");
    });

    const targetSec = document.getElementById(`view-${viewName}`);
    if (targetSec) targetSec.classList.add("active");

    const titles = {
      overview: "Overview",
      scanner: "Market Scanner",
      analysis: "Stock Analysis",
      history: "Analysis History"
    };
    document.getElementById("page-title").innerText = titles[viewName] || "Swing-AI";

    if (viewName === "history") {
      this.loadFullHistory();
    }
  }

  setupQuickSearch() {
    const input = document.getElementById("quick-symbol-input");
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        const sym = input.value.trim().toUpperCase();
        if (sym) {
          input.value = "";
          this.setAnalysisSymbol(sym);
          this.runAnalysis();
        }
      }
    });
  }

  /* -------------------------------------------------------------------------
     Health & State
     ------------------------------------------------------------------------- */
  async loadHealthAndOverview() {
    try {
      const res = await fetch("/api/health");
      if (!res.ok) throw new Error("Health endpoint error");
      const data = await res.json();

      const univ = data.universe || {};
      const count = univ.cached_symbols_count || 0;
      document.getElementById("ov-stat-discovered").innerText = count ? count.toLocaleString() : "--";
      document.getElementById("ov-stat-coverage").innerText = (univ.coverage_status || "UNKNOWN").toUpperCase();
      document.getElementById("ov-stat-cache").innerText = univ.is_cached ? "Exchange Master Cached (24h)" : "Uncached";

      // Scanner status badge
      const sStatus = data.scanner ? data.scanner.status : "idle";
      this.updateScannerBadge(sStatus);
    } catch (e) {
      console.warn("Could not load health info:", e);
    }
  }

  updateScannerBadge(status) {
    const badge = document.getElementById("scan-status-badge");
    if (!badge) return;
    badge.innerText = status.toUpperCase();
    badge.className = "badge " + (status === "running" ? "badge-watchlist" : (status === "completed" ? "badge-strong-buy" : "badge-hold"));
  }

  /* -------------------------------------------------------------------------
     Overview & Recent Analyses
     ------------------------------------------------------------------------- */
  async loadRecentAnalyses() {
    try {
      const res = await fetch("/api/history?limit=10");
      if (!res.ok) return;
      const data = await res.json();
      const records = data.records || [];

      document.getElementById("ov-stat-analyzed").innerText = records.length;
      const strongCount = records.filter(r => r.composite_verdict && r.composite_verdict.includes("BUY")).length;
      document.getElementById("ov-stat-setups").innerText = strongCount;

      const tbody = document.getElementById("ov-results-tbody");
      if (records.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="7" class="empty-state">
              <div class="empty-state-title">No stock analyses recorded yet</div>
              <div class="empty-state-desc">Run a market scan or analyze an individual stock to generate results.</div>
            </td>
          </tr>`;
        return;
      }

      tbody.innerHTML = records.map(r => `
        <tr>
          <td><strong class="mono" style="font-size: 14px;">${r.symbol}</strong></td>
          <td class="mono">${r.technical_score !== null ? r.technical_score + '/100' : '-'}</td>
          <td class="mono">${r.fundamental_score !== null ? r.fundamental_score + '/100' : '-'}</td>
          <td class="mono"><strong>${r.composite_score !== null ? r.composite_score + '/100' : '-'}</strong></td>
          <td>${this.formatVerdictBadge(r.composite_verdict)}</td>
          <td><span class="badge ${r.mode === 'offline' ? 'badge-watchlist' : 'badge-strong-buy'}">${(r.mode || 'live').toUpperCase()}</span></td>
          <td><button class="btn btn-secondary btn-sm" onclick="app.inspectSymbol('${r.symbol}')">Inspect</button></td>
        </tr>
      `).join("");
    } catch (e) {
      console.error("Failed to load recent analyses:", e);
    }
  }

  /* -------------------------------------------------------------------------
     Market Scanner: Universe Browser
     ------------------------------------------------------------------------- */
  async loadUniverse(page = 1) {
    this.universePage = page;
    const mode = document.getElementById("scan-mode-select").value;
    const offline = mode === "offline";
    const tbody = document.getElementById("universe-tbody");
    tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 20px;">Fetching discovered NSE equities...</td></tr>`;

    try {
      const q = encodeURIComponent(this.universeQuery || "");
      const res = await fetch(`/api/screening/universe?page=${page}&page_size=50&query=${q}&offline=${offline}`);
      if (!res.ok) throw new Error("Failed to load universe");
      const data = await res.json();

      this.universeTotalPages = data.total_pages || 1;
      const symbols = data.symbols || [];
      const meta = data.metadata || {};

      // Update Diagnostics
      document.getElementById("diag-source").innerText = meta.data_source || "NSE Archive";
      document.getElementById("diag-coverage").innerText = (meta.coverage_status || "COMPLETE").toUpperCase();
      document.getElementById("diag-discovered").innerText = (data.total_discovered || symbols.length).toLocaleString();
      document.getElementById("diag-excluded").innerText = meta.excluded_count !== undefined ? meta.excluded_count : "--";

      // Pagination Controls
      document.getElementById("page-indicator").innerText = `Page ${data.page} of ${data.total_pages}`;
      document.getElementById("universe-pagination-info").innerText = `Showing ${symbols.length} of ${data.total_matching.toLocaleString()} matching equities`;
      document.getElementById("btn-prev-page").disabled = data.page <= 1;
      document.getElementById("btn-next-page").disabled = data.page >= data.total_pages;

      if (symbols.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 20px; color: var(--text-dim);">No equities matched your search query.</td></tr>`;
        return;
      }

      const startNum = (data.page - 1) * data.page_size + 1;
      tbody.innerHTML = symbols.map((sym, idx) => `
        <tr>
          <td class="mono" style="color: var(--text-dim); font-size: 11px;">${startNum + idx}</td>
          <td><strong class="mono" style="font-size: 13px;">${sym}</strong></td>
          <td>NSE (India)</td>
          <td><span class="badge badge-hold">EQ / BE</span></td>
          <td>Ordinary Listed Equity</td>
          <td>
            <button class="btn btn-secondary btn-sm" onclick="app.inspectSymbol('${sym}')">
              Analyze Deeply
            </button>
          </td>
        </tr>
      `).join("");

    } catch (e) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--accent-red); padding: 20px;">Error loading universe: ${e.message}</td></tr>`;
    }
  }

  prevUniversePage() {
    if (this.universePage > 1) {
      this.loadUniverse(this.universePage - 1);
    }
  }

  nextUniversePage() {
    if (this.universePage < this.universeTotalPages) {
      this.loadUniverse(this.universePage + 1);
    }
  }

  onUniverseSearch(val) {
    this.universeQuery = val.trim();
    if (this._searchDebounce) clearTimeout(this._searchDebounce);
    this._searchDebounce = setTimeout(() => {
      this.loadUniverse(1);
    }, 300);
  }

  async refreshUniverse() {
    this.showToast("Contacting NSE official archives for security master refresh...", "info");
    try {
      const res = await fetch("/api/screening/refresh", { method: "POST" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Refresh failed");
      this.showToast(`Universe refreshed! ${data.total_eligible} ordinary equities ready.`, "success");
      this.loadUniverse(1);
      this.loadHealthAndOverview();
    } catch (e) {
      this.showToast(`Universe refresh error: ${e.message}`, "error");
    }
  }

  /* -------------------------------------------------------------------------
     Market Scanner: Execution & Background Polling
     ------------------------------------------------------------------------- */
  async startMarketScan() {
    const mode = document.getElementById("scan-mode-select").value;
    const offline = mode === "offline";
    const maxSymbols = parseInt(document.getElementById("scan-max-symbols").value, 10) || 10;
    const refreshUniv = document.getElementById("scan-refresh-univ").checked;

    const btn = document.getElementById("btn-run-scan");
    btn.disabled = true;

    try {
      const res = await fetch("/api/screening/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          universe: "broad_market",
          max_symbols: maxSymbols,
          refresh_universe: refreshUniv,
          offline: offline
        })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Failed to start scan");
      }

      this.showToast("Market scan started in background.", "info");
      this.pollScanProgress();
    } catch (e) {
      this.showToast(`Scan start failed: ${e.message}`, "error");
      btn.disabled = false;
    }
  }

  pollScanProgress() {
    if (this.scanPollInterval) clearInterval(this.scanPollInterval);

    const btn = document.getElementById("btn-run-scan");
    const progressText = document.getElementById("scan-progress-text");

    this.scanPollInterval = setInterval(async () => {
      try {
        const res = await fetch("/api/screening/status");
        if (!res.ok) return;
        const status = await res.json();

        this.updateScannerBadge(status.status);
        progressText.innerText = status.progress || "Scanning...";

        if (status.status === "completed") {
          clearInterval(this.scanPollInterval);
          btn.disabled = false;
          this.showToast("Market scan finished successfully!", "success");
          this.loadScanResults();
          this.loadRecentAnalyses();
        } else if (status.status === "error") {
          clearInterval(this.scanPollInterval);
          btn.disabled = false;
          this.showToast(`Scan error: ${status.error}`, "error");
        }
      } catch (e) {
        console.warn("Polling error:", e);
      }
    }, 1500);
  }

  async loadScanResults() {
    try {
      const res = await fetch("/api/screening/results");
      if (!res.ok) return;
      const data = await res.json();
      const pipeline = data.multi_agent_pipeline || [];
      const tbody = document.getElementById("scan-results-tbody");

      if (pipeline.length === 0) {
        tbody.innerHTML = `<tr><td colspan="9" class="empty-state">No candidates evaluated in this scan.</td></tr>`;
        return;
      }

      tbody.innerHTML = pipeline.map(item => {
        const t = item.agent_2_technical || {};
        const setup = t.trade_setup || {};
        return `
          <tr>
            <td><strong class="mono" style="font-size: 14px;">${item.symbol}</strong></td>
            <td class="mono">${item.agent_2_score !== null ? item.agent_2_score + '/100' : '-'}</td>
            <td class="mono">${item.agent_3_score !== null ? item.agent_3_score + '/100' : '-'}</td>
            <td class="mono"><strong>${item.composite_score !== null ? item.composite_score + '/100' : '-'}</strong></td>
            <td>${this.formatVerdictBadge(item.composite_verdict)}</td>
            <td class="mono">${setup.entry_zone || 'None'}</td>
            <td class="mono" style="color: var(--accent-red);">${setup.stop_loss || 'None'}</td>
            <td class="mono" style="color: var(--accent-green);">${setup.target_1 || 'None'}</td>
            <td>
              <button class="btn btn-secondary btn-sm" onclick="app.inspectSymbol('${item.symbol}')">Inspect</button>
            </td>
          </tr>
        `;
      }).join("");
    } catch (e) {
      console.error("Failed to load scan results:", e);
    }
  }

  /* -------------------------------------------------------------------------
     Stock Analysis
     ------------------------------------------------------------------------- */
  setAnalysisSymbol(symbol) {
    document.getElementById("analysis-symbol-input").value = symbol.toUpperCase();
    this.navTo("analysis");
  }

  inspectSymbol(symbol) {
    this.setAnalysisSymbol(symbol);
    this.runAnalysis();
  }

  analyzePromptSymbol() {
    const sym = prompt("Enter an NSE equity symbol to analyze (e.g. RELIANCE, INFY, 360ONE):");
    if (sym && sym.trim()) {
      this.inspectSymbol(sym.trim());
    }
  }

  async runAnalysis() {
    const input = document.getElementById("analysis-symbol-input");
    const sym = input.value.trim().toUpperCase();
    if (!sym) {
      this.showToast("Please enter a valid stock symbol.", "error");
      return;
    }

    const mode = document.getElementById("analysis-mode-select").value;
    const offline = mode === "offline";

    const emptyBox = document.getElementById("analysis-empty-placeholder");
    const loadingBox = document.getElementById("analysis-loading");
    const contentBox = document.getElementById("analysis-content-workspace");
    const btn = document.getElementById("btn-run-analysis");

    emptyBox.style.display = "none";
    contentBox.style.display = "none";
    loadingBox.style.display = "block";
    btn.disabled = true;

    try {
      const res = await fetch(`/api/analysis/${sym}?offline=${offline}`, { method: "POST" });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Analysis request failed.");
      }

      this.renderAnalysis(data);
      this.renderChart(sym, offline);
      this.loadRecentAnalyses();
      this.showToast(`Analysis complete for ${sym}`, "success");
    } catch (e) {
      this.showToast(`Analysis error: ${e.message}`, "error");
      emptyBox.style.display = "block";
    } finally {
      loadingBox.style.display = "none";
      btn.disabled = false;
    }
  }

  renderAnalysis(res) {
    const contentBox = document.getElementById("analysis-content-workspace");
    contentBox.style.display = "block";

    const sym = res.symbol;
    const t = res.technical || {};
    const f = res.fundamental || {};
    const s = res.screening || {};

    // Header Callouts
    document.getElementById("an-symbol").innerText = sym;
    const vBadge = document.getElementById("an-verdict-badge");
    vBadge.innerText = res.composite_verdict || "NEUTRAL_WAIT";
    vBadge.className = "badge " + this.getVerdictClass(res.composite_verdict);

    const setup = t.trade_setup || {};
    const dBadge = document.getElementById("an-direction-badge");
    const dir = (setup.direction || "NONE").toUpperCase();
    dBadge.innerText = `DIRECTION: ${dir}`;
    dBadge.className = "badge " + (dir === "LONG" ? "badge-strong-buy" : "badge-hold");

    document.getElementById("an-composite-score").innerText = `${res.composite_score !== null ? res.composite_score : '--'}/100`;
    document.getElementById("an-verdict-reason").innerText = res.verdict_reason || "Multi-agent confirmation parameters satisfied.";

    // Agent Scores
    const a1Eligible = s.eligible !== false;
    document.getElementById("an-a1-status").innerText = a1Eligible ? "Discovered & Eligible" : "Unverified / Excluded";
    document.getElementById("an-a2-score").innerText = `${t.technical_score !== undefined ? t.technical_score : '--'}/100`;
    document.getElementById("an-a2-trend").innerText = `Daily: ${(t.trend && t.trend.daily) || '--'} | Hourly: ${(t.trend && t.trend.hourly) || '--'}`;
    document.getElementById("an-a3-score").innerText = `${f.fundamental_score !== undefined ? f.fundamental_score : '--'}/100`;
    document.getElementById("an-a3-assessment").innerText = (f.valuation && f.valuation.valuation_assessment) ? `Valuation: ${f.valuation.valuation_assessment}` : "Quality Assessment";

    // Technical Setup Section
    const trend = t.trend || {};
    const mom = t.momentum || {};
    const vol = t.volume || {};
    const lvl = t.levels || {};

    document.getElementById("t-daily-trend").innerText = trend.daily || "--";
    document.getElementById("t-hourly-trend").innerText = trend.hourly || "--";
    document.getElementById("tech-trend-badge").innerText = (trend.daily || "NEUTRAL").toUpperCase();
    document.getElementById("tech-trend-badge").className = "badge " + (trend.daily === "bullish" ? "badge-strong-buy" : (trend.daily === "bearish" ? "badge-not-recommended" : "badge-hold"));

    document.getElementById("t-rsi").innerText = mom.daily_rsi ? `${mom.daily_rsi} (Status: ${mom.daily_rsi > 70 ? 'Overbought' : (mom.daily_rsi < 30 ? 'Oversold' : 'Neutral')})` : "--";
    document.getElementById("t-macd").innerText = mom.daily_macd ? `${mom.daily_macd}` : "--";
    document.getElementById("t-rvol").innerText = vol.relative_volume ? `${vol.relative_volume}x (Confirmed: ${vol.confirmation ? 'Yes' : 'No'})` : "--";
    document.getElementById("t-sr").innerText = `Support: ${lvl.support || 'N/A'} | Resistance: ${lvl.resistance || 'N/A'}`;

    document.getElementById("t-entry").innerText = setup.entry_zone || "N/A";
    document.getElementById("t-stop").innerText = setup.stop_loss || "N/A";
    document.getElementById("t-targets").innerText = setup.target_1 ? `${setup.target_1} / ${setup.target_2 || 'N/A'}` : "N/A";
    document.getElementById("t-rr").innerText = setup.risk_reward ? `${setup.risk_reward} R:R` : "N/A";

    // Fundamental Quality Section
    const gr = f.growth || {};
    const prof = f.profitability || {};
    const bs = f.balance_sheet || {};
    const val = f.valuation || {};
    const own = f.ownership || {};

    document.getElementById("f-rev-growth").innerText = gr.revenue_yoy !== undefined ? `${gr.revenue_yoy}% YoY` : "--";
    document.getElementById("f-pat-growth").innerText = gr.pat_yoy !== undefined ? `${gr.pat_yoy}% YoY` : "--";
    document.getElementById("f-roe").innerText = prof.roe !== undefined ? `ROE: ${prof.roe}% | ROCE: ${prof.roce || '--'}%` : "--";
    document.getElementById("f-margin").innerText = prof.operating_margin !== undefined ? `${prof.operating_margin}%` : "--";

    if (bs.is_financial) {
      document.getElementById("f-de").innerText = "Financial Institution (Corporate D/E Exempt)";
    } else {
      document.getElementById("f-de").innerText = bs.debt_equity !== undefined ? `D/E: ${bs.debt_equity} | Current Ratio: ${bs.current_ratio || '--'}` : "--";
    }

    document.getElementById("f-pe").innerText = val.pe !== undefined ? `P/E: ${val.pe} (Sector: ${val.sector_pe || '--'})` : "--";
    document.getElementById("fund-val-badge").innerText = (val.valuation_assessment || "FAIR").toUpperCase();

    document.getElementById("f-own").innerText = own.insider_holding !== undefined ? `Promoters: ${own.insider_holding}% | Inst: ${own.institutional_holding || '--'}%` : "--";

    // Warnings
    const warnBox = document.getElementById("fund-warnings-box");
    const warnList = document.getElementById("fund-warnings-list");
    if (f.warnings && f.warnings.length > 0) {
      warnBox.style.display = "block";
      warnList.innerHTML = f.warnings.map(w => `<li>${w}</li>`).join("");
    } else {
      warnBox.style.display = "none";
    }

    // Catalyst card
    const catCard = document.getElementById("catalyst-card");
    const cat = s.llm_catalyst || res.catalyst;
    if (cat && cat.summary) {
      catCard.style.display = "block";
      document.getElementById("catalyst-summary-text").innerText = cat.summary;
      const cBadge = document.getElementById("catalyst-sentiment-badge");
      cBadge.innerText = cat.sentiment || "NEUTRAL";
      cBadge.className = "badge " + (cat.sentiment === "BULLISH" ? "badge-strong-buy" : (cat.sentiment === "BEARISH" ? "badge-not-recommended" : "badge-hold"));
    } else {
      catCard.style.display = "none";
    }
  }

  /* -------------------------------------------------------------------------
     Real Price & Indicator Chart Rendering
     ------------------------------------------------------------------------- */
  async renderChart(symbol, offline) {
    if (typeof Chart === "undefined") {
      console.warn("Chart.js is not loaded.");
      return;
    }

    try {
      const res = await fetch(`/api/chart/${symbol}?limit=75&offline=${offline}`);
      if (!res.ok) return;
      const data = await res.json();
      const candles = data.candles || [];
      if (candles.length === 0) return;

      const labels = candles.map(c => c.date);
      const closes = candles.map(c => c.close);
      const ema20s = candles.map(c => c.ema_20);
      const ema50s = candles.map(c => c.ema_50);
      const ema200s = candles.map(c => c.ema_200);
      const rsis = candles.map(c => c.rsi_14);

      // Destroy prior chart instances
      if (this.priceChart) this.priceChart.destroy();
      if (this.rsiChart) this.rsiChart.destroy();

      // Main Price Chart
      const priceCtx = document.getElementById("price-chart-canvas").getContext("2d");
      this.priceChart = new Chart(priceCtx, {
        type: "line",
        data: {
          labels: labels,
          datasets: [
            {
              label: "Close Price (INR)",
              data: closes,
              borderColor: "#10b981",
              borderWidth: 2,
              pointRadius: 0,
              tension: 0.1,
              order: 1
            },
            {
              label: "EMA 20",
              data: ema20s,
              borderColor: "#3b82f6",
              borderWidth: 1.5,
              pointRadius: 0,
              borderDash: [2, 2],
              order: 2
            },
            {
              label: "EMA 50",
              data: ema50s,
              borderColor: "#f59e0b",
              borderWidth: 1.5,
              pointRadius: 0,
              borderDash: [4, 4],
              order: 3
            },
            {
              label: "EMA 200",
              data: ema200s,
              borderColor: "#ef4444",
              borderWidth: 1.5,
              pointRadius: 0,
              order: 4
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: { mode: "index", intersect: false },
          plugins: {
            legend: { display: false },
            tooltip: {
              backgroundColor: "#1e293b",
              titleColor: "#f8fafc",
              bodyColor: "#94a3b8",
              borderColor: "#334155",
              borderWidth: 1,
              padding: 10
            }
          },
          scales: {
            x: {
              grid: { color: "rgba(51, 65, 85, 0.2)" },
              ticks: { color: "#64748b", maxTicksLimit: 10, font: { size: 10 } }
            },
            y: {
              position: "right",
              grid: { color: "rgba(51, 65, 85, 0.2)" },
              ticks: { color: "#94a3b8", font: { family: "SF Mono, monospace", size: 10 } }
            }
          }
        }
      });

      // Subchart: RSI (14)
      const rsiCtx = document.getElementById("rsi-chart-canvas").getContext("2d");
      this.rsiChart = new Chart(rsiCtx, {
        type: "line",
        data: {
          labels: labels,
          datasets: [
            {
              label: "RSI(14)",
              data: rsis,
              borderColor: "#8b5cf6",
              borderWidth: 1.5,
              pointRadius: 0,
              tension: 0.1
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              backgroundColor: "#1e293b",
              titleColor: "#f8fafc",
              bodyColor: "#94a3b8",
              borderColor: "#334155",
              borderWidth: 1
            }
          },
          scales: {
            x: {
              grid: { display: false },
              ticks: { display: false }
            },
            y: {
              min: 0,
              max: 100,
              position: "right",
              grid: { color: "rgba(51, 65, 85, 0.2)" },
              ticks: {
                stepSize: 30,
                color: "#64748b",
                font: { family: "SF Mono, monospace", size: 9 }
              }
            }
          }
        }
      });

    } catch (e) {
      console.warn("Could not render chart:", e);
    }
  }

  /* -------------------------------------------------------------------------
     Analysis History
     ------------------------------------------------------------------------- */
  async loadFullHistory() {
    try {
      const res = await fetch("/api/history?limit=100");
      if (!res.ok) return;
      const data = await res.json();
      this.historyCache = data.records || [];
      this.renderHistoryTable(this.historyCache);
    } catch (e) {
      console.error("Failed to load full history:", e);
    }
  }

  filterHistory(query) {
    const q = query.trim().toUpperCase();
    if (!q) {
      this.renderHistoryTable(this.historyCache);
      return;
    }
    const filtered = this.historyCache.filter(item =>
      (item.symbol && item.symbol.toUpperCase().includes(q)) ||
      (item.composite_verdict && item.composite_verdict.toUpperCase().includes(q))
    );
    this.renderHistoryTable(filtered);
  }

  renderHistoryTable(records) {
    const tbody = document.getElementById("history-tbody");
    if (!records || records.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="8" class="empty-state">
            <div class="empty-state-title">No matching history records</div>
            <div class="empty-state-desc">Analyses saved across sessions will appear here.</div>
          </td>
        </tr>`;
      return;
    }

    tbody.innerHTML = records.map(r => `
      <tr>
        <td class="mono" style="font-size: 11px; color: var(--text-dim);">${r.timestamp ? r.timestamp.replace('T', ' ').slice(0, 19) : '--'}</td>
        <td><strong class="mono" style="font-size: 13px;">${r.symbol}</strong></td>
        <td class="mono">${r.technical_score !== null ? r.technical_score + '/100' : '-'}</td>
        <td class="mono">${r.fundamental_score !== null ? r.fundamental_score + '/100' : '-'}</td>
        <td class="mono"><strong>${r.composite_score !== null ? r.composite_score + '/100' : '-'}</strong></td>
        <td>${this.formatVerdictBadge(r.composite_verdict)}</td>
        <td><span class="badge ${r.mode === 'offline' ? 'badge-watchlist' : 'badge-strong-buy'}">${(r.mode || 'live').toUpperCase()}</span></td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="app.loadAnalysisFromHistory('${r.id}')">
            Reopen
          </button>
        </td>
      </tr>
    `).join("");
  }

  async loadAnalysisFromHistory(recordId) {
    try {
      const res = await fetch(`/api/history/${recordId}`);
      if (!res.ok) throw new Error("Could not load history record.");
      const data = await res.json();
      this.navTo("analysis");
      this.renderAnalysis(data);
      this.renderChart(data.symbol, data.mode === "offline");
      this.showToast(`Loaded saved analysis for ${data.symbol}`, "info");
    } catch (e) {
      this.showToast(`Error opening record: ${e.message}`, "error");
    }
  }

  /* -------------------------------------------------------------------------
     Helpers & Badges
     ------------------------------------------------------------------------- */
  getVerdictClass(verdict) {
    if (!verdict) return "badge-hold";
    const v = verdict.toUpperCase();
    if (v.includes("STRONG_BUY")) return "badge-strong-buy";
    if (v.includes("MODERATE_BUY")) return "badge-moderate-buy";
    if (v.includes("WATCHLIST")) return "badge-watchlist";
    if (v.includes("SPECULATIVE")) return "badge-speculative";
    if (v.includes("REJECTED") || v.includes("NOT_RECOMMENDED")) return "badge-not-recommended";
    return "badge-hold";
  }

  formatVerdictBadge(verdict) {
    if (!verdict) return `<span class="badge badge-hold">UNKNOWN</span>`;
    const cls = this.getVerdictClass(verdict);
    return `<span class="badge ${cls}">${verdict}</span>`;
  }

  showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.innerText = message;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transition = "opacity 0.3s ease";
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }
}

// Global initialization
window.app = null;
document.addEventListener("DOMContentLoaded", () => {
  window.app = new SwingAIApp();
});
