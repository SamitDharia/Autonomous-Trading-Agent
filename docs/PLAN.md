# Roadmap (8-Week Plan)

## Status Legend
- ✅ Complete
- 🔄 In Progress
- ⏳ Planned
- ❌ Blocked

---

## Week 1 — Foundation + Parity ✅
**Status**: Complete (Nov 2025)

- ✅ Repo structure created
- ✅ Brain JSON schema v1 defined
- ✅ Feature pipeline parity tests passing
- ✅ Expert model loaders (RSI, MACD, Trend)
- ✅ Ensemble brain loader with fallback

**Deliverables**:
- `/experts/`, `/ensemble/`, `/features/` modules
- `/models/*.json` sample weights
- `tests/test_experts_brain.py` passing

---

## Week 2 — LEAN Local Runtime Setup ✅
**Status**: Complete (Nov 2025)

- ✅ Run Lean Launcher locally
- ✅ Python algorithm skeleton (`algo.py`)
- ✅ Load brain from Object Store (QC) and local JSON
- ✅ Indicator setup (RSI, MACD, EMA, ATR, BB)
- ✅ 5-minute bar consolidation

**Deliverables**:
- `algo.py` runs in QuantConnect Web IDE
- `scripts/local_backtest.py` harness
- Verified Object Store Byte[] decoding

---

## Week 3 — Risk Engine + Bracket Execution ✅
**Status**: Complete (Dec 2025)

- ✅ Position sizing (`risk/position_sizing.py`)
- ✅ Bracket orders (ATR-based stop-loss + take-profit)
- ✅ Daily P&L stop guard (`risk/guards.py`)
- ✅ Indicator readiness checks
- ✅ Minimum hold time (30 minutes)
- ✅ Kill-switch on data/broker errors

**Deliverables**:
- `/risk/` module with guards + sizing
- Bracket order logic in `algo.py`
- Daily stop triggers correctly in backtests

---

## Week 4 — Paper Canary Mode 🔄
**Status**: In Progress (Dec 2025)

- ✅ Alpaca paper trading script (`scripts/paper_trade.py`)
- ✅ CSV trade logging (`alpaca_rsi_log.csv`)
- 🔄 Daily reports (CSV summary, P&L tracking)
- ⏳ Drift monitor (feature distribution checks)
- ⏳ Alert system (Slack/email on stop triggers)

**Current Focus**:
- Run 1-2 week paper trading certification
- Monitor RSI baseline vs. brain performance
- Validate daily stop triggers in live data

**Blockers**:
- None

---

## Week 5–6 — Brain Promotion System ⏳
**Status**: Planned (Q1 2026)

- ⏳ Model versioning (timestamped brain JSONs)
- ⏳ Scheduled retraining pipeline (weekly/monthly)
- ⏳ Automated promotion workflow (AUC threshold check)
- ⏳ Rollback triggers (if new brain underperforms baseline)
- ⏳ A/B testing (run old + new brain in parallel)

**Dependencies**:
- Week 4 paper trading complete
- Brain AUC ≥ 0.55 on hold-out set

**Acceptance Criteria**:
- New brain promoted only if beats RSI baseline + costs
- One-button rollback to previous version
- Automated model refresh (no manual intervention)

---

## Week 7–8 — Robustness Hardening ⏳
**Status**: Planned (Q1 2026)

- ⏳ Walk-forward validation (rolling 3-month train/test)
- ⏳ Regime filters (high volatility = smaller positions)
- ⏳ Multi-symbol support (AAPL, MSFT, SPY)
- ⏳ 60-day certification run (paper trading)
- ⏳ Performance analytics dashboard

**Dependencies**:
- Weeks 5-6 complete
- Stable brain performance (Sharpe ≥ 1.0)

**Acceptance Criteria**:
- 60-day paper run with <2% max drawdown
- Brain consistently beats RSI baseline
- No manual intervention required for 60 days
- Ready for tiny live deployment ($1000 capital)

---

## Completed Milestones

### 2025-12-16: Cleanup & Integration ✅
- Removed 1000+ unused files (30% repo size reduction)
- Integrated feature builder + risk guards into `algo.py`
- Consolidated documentation (PROJECT_BRIEF, INDEX, README)

### 2025-12-15: Alpaca Integration ✅
- Standalone Alpaca bot (`scripts/alpaca_rsi_bot.py`)
- CSV logging for trade history
- Bracket order execution (ATR-based)

### 2025-11-09: Expert Ensemble ✅
- JSON loaders for all experts + brain
- Verified local backtest + paper dry-run
- Sample model weights + passing tests

---

## Open Items (See BACKLOG.md)
- 🔄 Brain retraining (2018-2024 TSLA data, AUC target ≥0.55)
- ⏳ Drift monitor (feature distribution tracking)
- ⏳ Alert system (Slack/email notifications)
- ⏳ Walk-forward pipeline automation
- ⏳ Multi-symbol portfolio optimization

---

## See Also
- **[PROJECT_BRIEF.md](PROJECT_BRIEF.md)** — System goals and architecture
- **[BACKLOG.md](BACKLOG.md)** — Detailed task breakdown
- **[DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md)** — Recent decisions
- **[INDEX.md](INDEX.md)** — Documentation navigation

---

**Last updated**: 2025-12-17  
**Current Week**: Week 4 (Paper Canary Mode)
