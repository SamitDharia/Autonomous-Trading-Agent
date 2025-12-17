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

## Week 4 — RSI Phase 1 & Brain Decision ✅
**Status**: Complete (Dec 2025)

- ✅ Alpaca paper trading script (`scripts/paper_trade.py`)
- ✅ CSV trade logging (`alpaca_rsi_log.csv`)
- ✅ Brain retraining analysis (AUC 0.50-0.52, not promoted)
- ✅ Phase 1 RSI filters implemented (time-of-day, volume, volatility)
- ✅ Phase 1 backtest comparison: Sharpe -0.09 → 0.41 (turned losing → profitable)
- ✅ RSI_ENHANCEMENTS.md roadmap created

**Deliverables**:
- ✅ Brain decision documented in [DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md)
- ✅ Phase 1 filters in [algo.py](../algo.py)
- ✅ Phase 1 backtest results in [RSI_ENHANCEMENTS.md](RSI_ENHANCEMENTS.md)

---

## Week 5 — RSI Phase 2 & Deployment ✅
**Status**: Complete (Dec 2025)

- ✅ Phase 2 implementation (dynamic thresholds, trend filter, BB confirmation)
- ✅ Phase 1+2 backtest: **Sharpe 0.80** (+97% vs Phase 1), Win Rate 72.7%
- ✅ Updated [scripts/alpaca_rsi_bot.py](../scripts/alpaca_rsi_bot.py) with Phase 1+2 logic
- ✅ Created [DEPLOYMENT.md](../DEPLOYMENT.md) guide
- ✅ Deployed to Alpaca paper trading

**Deliverables**:
- ✅ Phase 2 enhancements in [algo.py](../algo.py) and [scripts/alpaca_rsi_bot.py](../scripts/alpaca_rsi_bot.py)
- ✅ Phase 2 backtest results in [RSI_ENHANCEMENTS.md](RSI_ENHANCEMENTS.md)
- ✅ Deployment guide: [DEPLOYMENT.md](../DEPLOYMENT.md)

---

## Week 6 — Paper Trading Monitoring 🔄
**Status**: In Progress (Dec 2025)

- ✅ Deployed Phase 1+2 strategy to Alpaca paper trading
- 🔄 Monitor 5-7 days for validation (target: Sharpe ≥1.0, win rate ≥70%)
- ⏳ Drift monitor (feature distribution checks)
- ⏳ Alert system (Slack/email on kill-switch triggers)
- ⏳ Daily P&L report automation

**Deliverables**:
- Paper trading logs in `alpaca_rsi_log.csv`
- Performance comparison vs backtest predictions
- Monitoring infrastructure

**Current Focus**:
- Backtest Phase 1 RSI enhancements (2020-2024 TSLA)
- Measure Sharpe improvement, win rate delta, drawdown impact
- Document results in RSI_ENHANCEMENTS.md
- Deploy best variant to paper trading

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
