# Project Backlog

**Last Updated**: 2025-12-18  
**Current Week**: Week 6 (Paper Trading Validation + Cloud Deployment)

## Priority Legend
- 🔴 High (Current Week)
- 🟡 Medium (Next 2-3 weeks)
- 🟢 Low (Future, not scheduled)

---

## 🔴 High Priority (Week 6 - Current)

### Week 6 Paper Trading Validation + Phase 3 Deployment
**Priority**: 🔴 High  
**Status**: Complete (Phase 3.1+3.2 Deployed)  
**Owner**: User

**Goal**: Validate Phase 1+2 execution works correctly in live environment, deploy Phase 3 enhancements.

**Tasks**:
- [x] Deploy bot to DigitalOcean droplet (138.68.150.144)
- [x] Fix timezone bug (UTC → US/Eastern for time_of_day filter)
- [x] Loosen filters temporarily (vol_z 0.5→0.2, volm_z 1.0→0.3) for faster validation
- [x] Verify bot running 24/7 (process 44394)
- [x] **First trade execution** (Dec 18, 15:54 UTC - 5 TSLA @ $484.74)
- [x] Monitor bracket orders (stop-loss, take-profit) execute correctly
- [x] Discovered churning issue with ultra-loose filters (vol_z > 0.0)
- [x] Restored production filters (vol_z > 0.2, volm_z > 0.3)
- [x] Make go/no-go decision for Phase 3 implementation (GO - execution validated)
- [x] **Phase 3.1 Deployed**: ATR-based trailing stops (18:07 UTC, PID 46125)
- [x] **Phase 3.2 Deployed**: Multi-timeframe RSI confirmation (18:24 UTC, PID 46592)
- [ ] Collect 3-5 clean trades with Phase 3.1+3.2 for analysis
- [ ] Run analyze_recent_trades.py to check Phase 3 performance

**Acceptance**:
- ✅ Bracket orders place correctly (stop-loss, take-profit)
- ✅ Entry/exit timing matches expected behavior
- ✅ No critical errors or missed signals
- 🔄 At least 3 clean trades executed (1 complete, churning trades excluded)

**Blockers**: 
- None - execution infrastructure fully validated

**Next Steps**:
1. Check dashboard at 3 PM Ireland (10 AM ET): https://app.alpaca.markets/paper/dashboard
2. If successful → Implement Phase 3.1 (trailing stops)
3. If errors → Debug bracket orders, delay Phase 3

---

### Phase 3 Planning (Ready to Implement After Validation)
**Priority**: 🔴 High  
**Status**: Design Complete, Implementation Waiting  
**Owner**: User

**Goal**: Enhance Phase 1+2 strategy with advanced techniques (trailing stops, multi-TF RSI).

**Phase 3.1 - Trailing ATR Stop**:
- [x] Design document created ([PHASE3_TRAILING_STOP_DESIGN.md](PHASE3_TRAILING_STOP_DESIGN.md))
- [x] Researched Alpaca order.replace() API
- [x] Implement trailing stop logic in alpaca_rsi_bot.py (Dec 18, 17:47 UTC)
- [x] Deploy to paper trading (running on droplet PID 44977)
- [ ] Validate trail behavior with first profitable position
- [ ] Backtest vs Phase 2 baseline after live validation (target: +10% Sharpe)

**Phase 3.2 - Multi-Timeframe RSI**:
- [x] Design document created ([PHASE3_MULTI_TF_RSI_DESIGN.md](PHASE3_MULTI_TF_RSI_DESIGN.md))
- [x] Selected approach: Option B (5m <25, 15m <50)
- [ ] Implement 15-min RSI consolidation
- [ ] Add multi-TF filter to entry logic
- [ ] Backtest vs Phase 2 baseline (target: +10% Sharpe)
- [ ] Deploy to paper trading if validated

**Acceptance**:
- Trailing stops: Sharpe improves ≥10% vs Phase 2 (target: 0.88+)
- Multi-TF RSI: Win rate improves +3-5%, trade reduction <40%
- Combined Phase 3: Sharpe ≥1.0

**Dependencies**: Week 6 execution validation must complete first

---

## 🟡 Medium Priority (Weeks 7-8)

### Phase 4 Shadow ML Logging (Infrastructure Ready)
**Priority**: 🟡 Medium  
**Status**: Implemented, Disabled by Default  
**Owner**: User

**Goal**: Collect training dataset for future ML research (optional).

**Tasks**:
- [x] Implement ml/shadow.py with zero-risk logging
- [x] Add shadow hook in alpaca_rsi_bot.py (try/except wrapper)
- [x] Document in RSI_ENHANCEMENTS.md + ml/README.md
- [ ] Enable ML_SHADOW_ENABLED=true after Week 6 validation
- [ ] Collect 500+ trades over 6 months
- [ ] Analyze: Does ML improve expectancy vs rule-based filters?
- [ ] Go/No-Go decision based on out-of-sample expectancy (not AUC)

**Acceptance**:
- JSONL log contains 500+ trades with features + outcomes
- If ML expectancy > baseline + 2σ → Train model and promote
- If no improvement → Abandon ML, stick with rules

**Blockers**: Need 6 months of live trading data first

---

### Analysis & Monitoring Tools
**Priority**: 🟡 Medium  
**Status**: Partially Complete  
**Owner**: User

**Tasks**:
- [x] Created analyze_recent_trades.py (win rate, Sharpe, PnL analysis)
- [ ] Add drift monitoring (feature distribution shifts)
- [ ] Weekly performance reports (automated)
- [ ] Slack/email alerts for daily loss >-1%
- [ ] Dashboard: real-time PnL, open positions, filter stats

**Acceptance**:
- analyze_recent_trades.py shows accurate metrics vs backtest
- Drift alerts trigger if feature distributions shift >20%
- Weekly reports sent automatically

**Blockers**: None

---

## 🟢 Low Priority (Future, Not Scheduled)
**Priority**: 🟡 Medium (Week 6)  
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
