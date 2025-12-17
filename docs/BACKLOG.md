# Project Backlog

## Priority Legend
- 🔴 High (Week 4-5)
- 🟡 Medium (Week 6-7)
- 🟢 Low (Week 8+)

---

## 🔴 High Priority

### RSI Baseline Phase 1 Backtest (Current Focus)
**Priority**: 🔴 High  
**Status**: In Progress  
**Owner**: TBD

**Goal**: Backtest Phase 1 RSI enhancements vs baseline to validate +10-20% Sharpe improvement hypothesis.

**Tasks**:
- [x] Implement Phase 1 filters (time-of-day, volume, volatility)
- [ ] Create backtest comparison script (baseline vs Phase 1)
- [ ] Run 2020-2024 TSLA backtest in QuantConnect
- [ ] Measure metrics: Sharpe, win rate, max DD, trade count
- [ ] Document results in RSI_ENHANCEMENTS.md
- [ ] Deploy best variant to paper trading

**Acceptance**:
- Sharpe improves by ≥10% OR win rate +5%
- Max drawdown unchanged or decreased
- Trade count reduction <40%

**Blockers**: None

---

### Brain Retraining (COMPLETED - NOT PROMOTED)
**Priority**: 🔴 High → ✅ Complete  
**Status**: Complete (Dec 17, 2025)  
**Owner**: TBD

**Result**: Tested multiple configurations (H=6/12/24, 2018-2024 data, LightGBM hyperparameter tuning). All yielded AUC 0.50-0.52 (coin-flip). **Decision: Brain not promoted. RSI baseline remains champion.** Public OHLCV features on liquid stocks have limited predictive power. Models archived in `models/*.json` for reference. See DEVELOPMENT_LOG.md for full analysis.

**Lessons Learned**:
- Financial markets are adversarial - basic technical indicators on public data unlikely to achieve strong edge
- AUC 0.50-0.52 is expected ceiling with OHLCV-derived features
- Real edge requires alternative data (order flow, sentiment, options) or microstructure features
- RSI baseline works due to strict risk management (ATR brackets, daily stop), not prediction

---

### Drift Monitor
**Priority**: 🔴 High  
**Status**: Not Started  
**Owner**: TBD

**Goal**: Detect feature distribution shifts in live data vs. training data.

**Tasks**:
- [ ] Track feature statistics (mean, std) for each expert
- [ ] Compute Kolmogorov-Smirnov test weekly
- [ ] Alert if any feature drifts beyond 2-sigma threshold
- [ ] Log drift metrics to CSV for analysis

**Acceptance**:
- Alert triggered if RSI distribution shifts ≥20%
- Weekly drift report emailed/logged

**Blockers**: None

---

### Alert System (Slack/Email)
**Priority**: 🔴 High  
**Status**: Not Started  
**Owner**: TBD

**Goal**: Send notifications on kill-switch triggers, daily stop hits, or drift alerts.

**Tasks**:
- [ ] Integrate Slack webhook for critical alerts
- [ ] Send email on daily P&L stop (-1%)
- [ ] Send email on 60-day certification completion
- [ ] Log all alerts to CSV

**Acceptance**:
- Slack message sent within 1 minute of daily stop trigger
- Email includes trade log summary + P&L

**Blockers**: None

---

## 🟡 Medium Priority

### Walk-Forward Validation Pipeline
**Priority**: 🟡 Medium  
**Status**: Not Started  
**Owner**: TBD

**Goal**: Automate rolling 3-month train/test cycles to validate brain robustness.

**Tasks**:
- [ ] Script to partition data into rolling windows
- [ ] Train brain on each window
- [ ] Backtest on next month (out-of-sample)
- [ ] Aggregate metrics (Sharpe, max DD, win rate)
- [ ] Fail if any window underperforms baseline

**Acceptance**:
- Brain validated on ≥12 rolling windows (1 year)
- All windows beat RSI baseline (Sharpe ≥0.8)

**Blockers**: High-priority brain retraining must complete first

---

### Multi-Symbol Support
**Priority**: 🟡 Medium  
**Status**: Not Started  
**Owner**: TBD

**Goal**: Expand from TSLA-only to small basket (AAPL, MSFT, SPY).

**Tasks**:
- [ ] Generalize feature builder to accept symbol parameter
- [ ] Train expert models for each symbol (3 x 3 = 9 models)
- [ ] Portfolio optimization (allocate capital across symbols)
- [ ] Risk controls: max 3 concurrent positions

**Acceptance**:
- Algo runs on 4 symbols simultaneously
- Position sizing respects portfolio-level caps
- Backtest shows diversification benefit (lower DD)

**Blockers**: Single-symbol brain must be stable first

---

### Performance Analytics Dashboard
**Priority**: 🟡 Medium  
**Status**: Not Started  
**Owner**: TBD

**Goal**: Visualize trade performance, P&L curves, and risk metrics.

**Tasks**:
- [ ] Parse `alpaca_rsi_log.csv` into Pandas DataFrame
- [ ] Plot cumulative P&L, drawdown, Sharpe over time
- [ ] Trade heatmap (entry/exit RSI vs. return)
- [ ] Export HTML report

**Acceptance**:
- Dashboard auto-generated weekly from CSV logs
- Sharpe, Sortino, max DD visible at a glance

**Blockers**: None

---

## 🟢 Low Priority (Future Enhancements)

### Regime Filters
**Priority**: 🟢 Low  
**Status**: Not Started

**Goal**: Reduce position sizes during high-volatility regimes.

**Tasks**:
- [ ] Compute VIX-like metric (rolling 20-day ATR)
- [ ] Scale position size by inverse volatility
- [ ] Backtest regime-aware sizing vs. fixed sizing

---

### RL-Based Position Sizing
**Priority**: 🟢 Low  
**Status**: Not Started

**Goal**: Use reinforcement learning to optimize position sizing vs. fixed ATR-based.

**Tasks**:
- [ ] Define RL environment (state: features, action: size, reward: Sharpe)
- [ ] Train PPO/DDPG agent on historical data
- [ ] Compare RL sizing vs. ATR baseline

---

### Trade Journal
**Priority**: 🟢 Low  
**Status**: Not Started

**Goal**: Detailed logging of every trade with entry/exit reasons, P&L, slippage.

**Tasks**:
- [ ] Expand CSV to include: slippage, commission, hold time
- [ ] Add post-trade analysis (did stop/TP trigger? or time decay?)

---

## Epic: Runtime Hardening

**Priority**: 🔴 High  
**Status**: Partially Complete (Week 3 ✅)

**Remaining Tasks**:
- ✅ Daily P&L stop
- ✅ Kill-switch on data/broker errors
- ✅ Bracket order reconciliation
- 🔄 Alerts and telemetry (Slack/email) — In Progress
- ⏳ Drift monitor — Not Started

**Acceptance**:
- System halts after -1% daily loss
- Slack alert sent within 1 minute
- No manual intervention required for recovery

---

## Epic: Training & Diagnostic Reliability

**Priority**: 🟡 Medium  
**Status**: Partially Complete

**Remaining Tasks**:
- ✅ Purged CV, bootstrap CI, permutation importance
- ⏳ Automate QC Research runs — Not Started
- ⏳ Artifact publications (timestamped brain JSONs) — Not Started

**Acceptance**:
- Diagnostic scripts export `output/` artifacts
- Brain JSONs tagged with timestamp + AUC

---

## Epic: Deployment & CI

**Priority**: 🟢 Low  
**Status**: Not Started

**Tasks**:
- [ ] Automate QC cloud push (fix project-name error)
- [ ] Add GitHub Actions CI (run tests on PR)
- [ ] Model promotion workflow (approve brain if AUC ≥0.55)
- [ ] Release pipelines (tag + publish brain JSONs)

**Acceptance**:
- `qc` push succeeds with no special-character error
- Brain JSONs tagged and available to runtime loader
- GitHub Actions runs tests automatically on PR

---

## Fixed Issues (Archive)

### ✅ Clean repo of generated artifacts (Dec 2025)
- Removed `__pycache__/`, `*.pyc`, generated logs
- Added `.gitignore` rules
- 30% repo size reduction (3.1 GB → 2.2 GB)

### ✅ Fix QC Object Store Byte[] decoding (Dec 2025)
- Updated expert/brain loaders to handle QC Byte[] encoding
- Verified in QC Web IDE backtest

### ✅ Add `docs/BACKLOG.md` (Dec 2025)
- Created this file
- Migrated issues from `BACKLOG_ISSUES.md`

---

## GitHub Issues (To Create)

These backlog items should be converted to GitHub Issues:

1. **Brain Retraining** (#1) — 🔴 High
2. **Drift Monitor** (#2) — 🔴 High
3. **Alert System** (#3) — 🔴 High
4. **Walk-Forward Pipeline** (#4) — 🟡 Medium
5. **Multi-Symbol Support** (#5) — 🟡 Medium
6. **Performance Dashboard** (#6) — 🟡 Medium

Use `scripts/create_github_issues.ps1` to batch-create from this file.

---

## See Also
- **[PLAN.md](PLAN.md)** — 8-week roadmap (high-level milestones)
- **[PROJECT_BRIEF.md](PROJECT_BRIEF.md)** — System goals and current status
- **[DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md)** — Recent decisions
- **[INDEX.md](INDEX.md)** — Documentation navigation

---

**Last updated**: 2025-12-17  
**Next review**: Weekly (Fridays)
