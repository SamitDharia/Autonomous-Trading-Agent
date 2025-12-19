# Project Backlog

**Last Updated**: 2025-12-19  
**Current Week**: Week 6-7 (Phase 3 Deployed, Holiday Monitoring Period)

## Priority Legend
- 🔴 High (Current Week)
- 🟡 Medium (Next 2-3 weeks)
- 🟢 Low (Future, not scheduled)

---

## 🔴 High Priority (Week 6 - Current)

### Week 6 Paper Trading Validation + Phase 3 Deployment
**Priority**: 🔴 High  
**Status**: Phase 3.1+3.2 Deployed, Monitoring  
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
- [x] **Day 2 Health Check** (Dec 19): Bot healthy, no trades (expected - holiday low volatility)
- [ ] **Holiday Period Monitoring** (Dec 19 - Jan 3): Bot running, zero trades expected
- [ ] **First Phase 3 Entry** (Expected: Early Jan - TSLA delivery numbers catalyst)
- [ ] **Validation Period** (Jan 6-31): Collect 5-10 Phase 3 trades during Q4 earnings volatility
- [ ] Validate skip_multi_tf and trail_update logs after first entry
- [ ] Run analyze_recent_trades.py after 5+ trades collected

**Expected Timeline** (Seasonal Volatility Analysis):
- **Dec 19-23**: Low probability trades (pre-holiday quiet period)
- **Dec 23 - Jan 3**: Very low probability (holiday period, skeleton crews)
- **Jan 6-10**: First trades likely (TSLA Q4 delivery numbers, fresh capital returns)
- **Jan 20-31**: High-volume validation period (Q4 earnings week, ±5-10% TSLA moves typical)
- **Target**: 5-15 Phase 3 trades by Feb 1, 2026

**Next Steps** (After Validation - Feb 2026):
1. **Shadow ML Decision**: Enable ML_SHADOW_ENABLED=true if Phase 3 stable (start collecting training data)
   - ML stays dormant, only logs features + outcomes
   - Zero risk to execution (try/except wrapper)
   - Target: 500+ labeled trades over 6 months
2. **Phase 3.3 Evaluation**: Assess need for additional enhancements based on Phase 3.1+3.2 results:
   - ATR acceleration (tighten trail as profit grows)
   - Partial profit-taking (scale out at milestones)
   - Time-based stops (exit stale positions)
3. **Live Trading Consideration**: If Phase 3 Sharpe ≥ 1.0, consider moving to real money

**Acceptance**:
- ✅ Bracket orders place correctly (stop-loss, take-profit)
- ✅ Entry/exit timing matches expected behavior
- ✅ No critical errors or missed signals
- ✅ Execution infrastructure fully validated (Dec 18 first trade)
- 🔄 Phase 3 validation: 5-10 clean trades (expected by Jan 31, 2026)

**Current Status** (Dec 19):
- Bot healthy: PID 46592, running 27+ hours
- Market conditions: Low volatility (vol_z < 0, volm_z < 0)
- Filter status: Correctly rejecting setups (skip_volatility, skip_volume)
- Position: Flat (orphaned position manually closed Dec 18)

**Blockers**: 
- ✅ None - waiting for market volatility to return (seasonal pattern)

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
- [x] Deploy to paper trading (running on droplet PID 46592)
- [ ] Validate trail behavior with first profitable position (waiting on Jan volatility)
- [ ] Backtest vs Phase 2 baseline after live validation (target: +10% Sharpe)

**Note**: Trailing stop code ready, awaiting first Phase 3 entry (expected Jan 6-31)

**Phase 3.2 - Multi-Timeframe RSI**:
- [x] Design document created ([PHASE3_MULTI_TF_RSI_DESIGN.md](PHASE3_MULTI_TF_RSI_DESIGN.md))
- [x] Selected approach: Option B (5m <25, 15m <50)
- [x] Implement 15-min RSI consolidation (Dec 18, 18:24 UTC)
- [x] Add multi-TF filter to entry logic
- [x] Deploy to paper trading (running on droplet PID 46592)
- [ ] Validate skip_multi_tf logs with first new entry (waiting on Jan volatility)
- [ ] Backtest vs Phase 2 baseline after collecting trades (target: +10% Sharpe)

**Note**: Multi-TF filter not yet reached (early filters rejecting due to low vol/volume)

**Phase 3.3 - Additional Enhancements** (Optional):
- [ ] Design ATR acceleration (tighten trail as profit increases)
- [ ] Design partial profit-taking (scale out at +1ATR, +2ATR, +3ATR)
- [ ] Design time-based stops (exit if no profit after 2 hours)
- [ ] Evaluate need based on Phase 3.1+3.2 performance

**Acceptance**:
- Trailing stops: Sharpe improves ≥10% vs Phase 2 (target: 0.88+)
- Multi-TF RSI: Win rate improves +3-5%, trade reduction <40%
- Combined Phase 3: Sharpe ≥1.0

**Dependencies**: ✅ Week 6 execution validation complete. Now waiting on market volatility (Jan 2026)

**Filter Decision**: Keeping current filters (vol_z > 0.2, volm_z > 0.3) - loosened from backtest but still selective. Analysis shows holiday period (Dec 19 - Jan 3) has historically low TSLA volatility. Expecting trades to resume in early January with delivery numbers catalyst, and high-volume validation during Q4 earnings (late Jan).

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

## 🚀 Maximum Returns Path (Aggressive Growth Strategy)

**Target**: 12-22% annual returns (realistic with risk controls)  
**Risk Tolerance**: Moderate-High  
**Timeline**: 6-12 months implementation  
**Capital Requirement**: $5K minimum (realistic), $10K+ recommended

**Capital Reality Check**:
- $2K account: Phase 1 only (0.5-1% sizing) - commissions eat profits
- $5K account: Can handle Phase 2 (2% sizing = $100/trade)
- $10K+ account: Full strategy (all phases, proper diversification)

### Strategy Overview

Current baseline (Phase 3): ~0.5-1% annual return with ultra-conservative approach (single symbol, 0.25% sizing). **Note**: Deployed filters (vol_z > 0.2, volm_z > 0.3) are already 2-3x looser than backtest (0.5/1.0), yielding estimated ~20 trades/year (vs 9 in backtest). This section outlines the path to 12-22% returns by scaling trade frequency, diversification, and position sizing.

### Implementation Roadmap

#### **Phase 1: Multi-Symbol Expansion** (Week 1-3)
**Goal**: 3-4x trade opportunities through diversification

**Actions**:
- Add 4 more liquid symbols: AAPL, MSFT, NVDA, SPY
- Same Phase 3 strategy (RSI mean-reversion + 8 filters)
- **Correlation monitoring**: Calculate 30-day rolling correlation between pairs
- Stagger entries: Max 2 positions if correlation < 0.75, else max 1 position

**Code Changes**:
```python
# In alpaca_rsi_bot.py:
SYMBOLS = ["TSLA", "AAPL", "MSFT", "NVDA", "SPY"]  # Was: symbol = "TSLA"
MAX_CONCURRENT_POSITIONS = 2  # Dynamic based on correlation
CORRELATION_THRESHOLD = 0.75  # If avg > 0.75, reduce to 1 position
```

**Expected Impact**:
- Trade frequency: 20/year → 60-80/year (3-4x, accounting for correlation)
- Annual return: 0.5-1% → 2-4%
- Risk: Low (but note: tech stocks are 0.7-0.9 correlated in crashes)

**Backtest Required**: 
- Validate each symbol individually on 2020-2024 data (require Sharpe > 0.5)
- Test correlation matrix during COVID crash, 2022 correction
- Verify max drawdown < 5% with 2 concurrent positions

**Validation Gate**: If any symbol Sharpe < 0.5 or correlation crisis causes >8% drawdown, exclude that symbol

---

#### **Phase 2: Aggressive Position Sizing** (Week 3-5)
**Goal**: 6-8x returns per trade through larger positions

**Actions**:
- Increase from 0.25% → 2% per trade (8x sizing)
- Maintain strict risk controls (1.5 ATR stop-loss, daily -3% kill-switch)
- With 5 symbols, max exposure = 10% (2% × 5 positions, but max 2 concurrent)
- **Conservative ramp**: Start with 1% sizing for 20 trades, then 2% if validated

**Code Changes**:
```python
position_size = 0.02  # 2% per trade (vs 0.25% current)
daily_stop = -0.03    # -3% kill-switch (vs -1% current)
max_total_exposure = 0.10  # Never exceed 10% total
```

**Expected Impact**:
- Annual return: 2-4% → 8-12% (with multi-symbol + 2% sizing)
- Max drawdown: 1-2% → 6-10% (acceptable for growth account)
- Risk: Moderate-High (8x larger losses when wrong, but 1.5 ATR stops limit damage)

**Stress Test Required**: 
- Backtest on 2020 COVID crash (Feb-Mar): Verify max drawdown < 12%
- Backtest on 2022 Fed tightening: Verify monthly drawdown < 8%
- Paper trade 1 month with 2% sizing: Collect 15-25 trades

**Validation Gate**: 
- If paper trading max drawdown > 10% → reduce to 1% sizing
- If daily loss ever hits -3% → halt trading, analyze issue

---

#### **Phase 3: Loosen Filters for Higher Frequency** (Week 6-10)
**Goal**: 1.5-2x more trades through relaxed entry criteria

**Current Reality**:
- Deployed filters: vol_z > 0.2, volm_z > 0.3 (already 2-3x looser than backtest 0.5/1.0)
- Estimated current frequency: ~20 trades/year (vs 9 in backtest with strict filters)
- Further loosening is HIGH RISK - backtest showed baseline (no filters) was **losing money**

**Actions**:
- Test multiple filter configurations in backtest:
  - **Option A** (Conservative): vol_z > 0.15, volm_z > 0.25 (slight loosen)
  - **Option B** (Moderate): vol_z > 0.1, volm_z > 0.2  
  - **Option C** (Aggressive): vol_z > 0.05, volm_z > 0.15
- **CRITICAL**: Historical data shows baseline (no vol/volume filters) had:
  - Win rate: 64% (vs 73% with filters)
  - Sharpe: -0.11 (NEGATIVE - lost money)
- Choose configuration with highest Sharpe ratio **AND** win rate ≥ 65%

**Code Changes**:
```python
# Test in backtest, then deploy winner:
VOL_THRESHOLD = 0.1    # vs 0.2 current (conservative loosen)
VOLM_THRESHOLD = 0.2   # vs 0.3 current
```

**Expected Impact**:
- Trade frequency: 60-80/year → 100-120/year (with 5 symbols)
- Win rate: 70-73% → 66-70% (acceptable if Sharpe holds)
- Annual return: 8-12% → 12-16%
- Risk: HIGH (approaching losing territory - need careful validation)

**Validation Gate** (STRICT):
- Paper trade 2 months, collect 40-60 trades minimum
- Require: Win rate ≥ 66% AND Sharpe ≥ 0.65 AND Profit Factor ≥ 1.3
- **If any metric fails**: DO NOT deploy, revert to Phase 2 filters
- **Alternative**: Selective loosening (relax volm_z only, keep vol_z at 0.2)

---

#### **Phase 4: Add Momentum Strategy** (Month 3-5)
**Goal**: Diversify signal types (mean-reversion + momentum)

**Rationale**: RSI mean-reversion only captures one market pattern. Add breakout/trend-following for stronger directional moves.

**New Entry Patterns** (each requires separate design/backtest):
1. **Bollinger Band Breakouts**: Price breaks above upper BB with volume surge
2. **MACD Momentum**: MACD crosses above signal + histogram expanding
3. **Gap-Fill Setups**: Stock gaps down >2%, first bounce on volume

**Code Structure**:
```python
# Dual strategy approach:
if rsi_mean_reversion_signal():
    enter_long_rsi()  # Current Phase 3 logic
elif momentum_breakout_signal():
    enter_long_momentum()  # New logic with different exit rules
```

**Expected Impact**:
- Trade frequency: 100-120/year → 150-200/year (combined strategies)
- Annual return: 12-16% → 16-20%
- Risk: High (momentum trades have lower win rate ~55-60%, need 3:1 R/R)

**Development Requirements**:
- Design 3 momentum patterns (2 weeks)
- Backtest each on 2020-2024 data (2 weeks)
- Combine strategies, test correlation (1 week)
- Paper validate 50+ momentum trades (6-8 weeks)
- **Total time**: 10-13 weeks minimum

**Validation Gate**:
- Each momentum pattern must achieve Sharpe > 0.4 standalone
- Combined strategy Sharpe > Phase 3 Sharpe + 0.2
- Max drawdown < 12%

---

#### **Phase 5: ML Expectancy Model** (Month 4-9)
**Goal**: Improve win rate through trade quality filtering

**Actions**:
1. Enable ML_SHADOW_ENABLED=true (start logging)
2. Collect 500+ labeled trades (6 months at 150 trades/year)
3. Train LightGBM model to predict trade expectancy (not just direction)
4. Add ML confidence gate: Only take trades with ML expectancy > $5 per $100 risked
5. A/B test: Baseline vs ML-filtered (compare Sharpe, win rate, profit factor)

**Code Integration**:
```python
if ml_enabled and ml_expectancy(features) < 5.0:
    return  # Skip low-expectancy setup
# Proceed with entry
```

**Expected Impact**:
- Win rate: 65-68% → 75-80% (filter out bottom 30% of trades)
- Trade frequency: 200/year → 140/year (quality over quantity)
- Annual return: 20-25% → 25-30%
- Risk: Moderate (ML overfitting risk, need robust validation)

**Success Criteria**: ML out-of-sample Sharpe > Baseline Sharpe + 0.3 (significant improvement)

---

### Expected Returns Summary

| Phase | Implementation | Symbols | Position Size | Trades/Year | Win Rate | Annual Return | Risk Level |
|-------|----------------|---------|---------------|-------------|----------|---------------|------------|
| **Current** | Complete | 1 | 0.25% | 20 (est) | 70-73% | 0.5-1% | Low |
| **Phase 1** | Week 1-3 | 5 | 0.25% | 60-80 | 68-72% | 2-4% | Low |
| **Phase 2** | Week 3-5 | 5 | 2% | 60-80 | 68-72% | 8-12% | Moderate |
| **Phase 3** | Week 6-10 | 5 | 2% | 100-120 | 66-70% | 12-16% | Mod-High |
| **Phase 4** | Month 3-5 | 5 | 2% | 150-200 | 60-65% | 16-20% | High |
| **Phase 5** | Month 6-12 | 5 | 2% | 120-160 | 70-75% | 18-22% | Moderate |

### Capital Scaling (Realistic Projections)

**With $2,000 starting capital** (NOT RECOMMENDED - commissions eat profits):
- Current: $10-20/year
- After Phase 1: $40-80/year (2-4%) - commission drag significant
- Phase 2+: NOT VIABLE ($40/trade too small for bracket orders)

**With $5,000 starting capital** (MINIMUM for growth strategy):
- Current: $25-50/year
- After Phase 1: $100-200/year (2-4%)
- After Phase 2: $400-600/year (8-12%)
- After Phase 3: $600-800/year (12-16%)
- After Phase 4+5: $900-1,100/year (18-22%)

**With $10,000 starting capital** (RECOMMENDED):
- After Phase 1: $200-400/year
- After Phase 2: $800-1,200/year (8-12%)
- After Phase 3: $1,200-1,600/year (12-16%)
- After Phase 4+5: $1,800-2,200/year (18-22%)

**With $50,000 starting capital** (serious trading):
- After Phase 2: $4,000-6,000/year
- After Phase 3: $6,000-8,000/year
- After Phase 4+5: $9,000-11,000/year

**Reality Check**: These assume:
- All phases validate successfully (50-60% chance based on backtest difficulty)
- No major market regime changes
- Strict discipline on risk management
- Correlation stays manageable

### Risk Management Rules

**Position Sizing**:
- Max 2% per trade (never exceed)
- Max 10% total exposure (5 symbols × 2%)
- Daily kill-switch: -3% equity

**Stop-Loss Protection**:
- All trades use 1.5 ATR trailing stops (Phase 3.1)
- No naked positions (bracket orders mandatory)
- Emergency manual override if bot fails

**Drawdown Limits**:
- Daily: -3% → shut down for day
- Weekly: -6% → reduce position sizing to 1%
- Monthly: -10% → revert to Phase 1 (multi-symbol only, 0.25% sizing)

**Validation Gates**:
- Phase 1→2: Verify 20+ trades, Sharpe ≥ 0.8
- Phase 2→3: Verify 30+ trades, win rate ≥ 65%
- Phase 3→4: Verify 50+ trades, max drawdown < 8%
- Phase 4→5: Verify 100+ trades, ML out-of-sample Sharpe > baseline + 0.3

### Quick Start (Next 2 Weeks)

**To maximize returns immediately**:

1. **Day 1-2**: Multi-symbol implementation
   - Backtest AAPL, MSFT, NVDA, SPY on 2020-2024 (verify Sharpe > 0.5 each)
   - Update alpaca_rsi_bot.py with symbol loop
   - Deploy to paper trading

2. **Day 3-7**: Collect 5-10 multi-symbol trades
   - Verify bracket orders work correctly across all symbols
   - Check correlation (max 2 concurrent positions)
   
3. **Day 8**: Go/No-Go for Phase 2
   - If multi-symbol Sharpe ≥ 0.8 → increase to 2% sizing
   - If Sharpe < 0.6 → investigate, keep 0.25% sizing

4. **Day 9-14**: Test 2% sizing in paper
   - Monitor drawdown closely (should be < 3%)
   - Collect 10-15 trades

5. **Day 15+**: If stable, begin Phase 3 filter testing

### Long-Term Target (12 Months)

**Conservative Case** (Phases 1-2 only) - 70% probability:
- Annual return: 8-12%
- Max drawdown: 5-8%
- Win rate: 68-72%
- **With $10K**: $800-1,200/year
- **Risk**: Low-Moderate (proven strategy, just scaled up)

**Moderate Case** (Phases 1-3) - 40% probability:
- Annual return: 12-16%
- Max drawdown: 8-12%
- Win rate: 66-70%
- **With $10K**: $1,200-1,600/year
- **Risk**: Moderate-High (filter loosening is unproven, could backfire)

**Aggressive Case** (Phases 1-5, all successful) - 20% probability:
- Annual return: 18-22%
- Max drawdown: 12-18%
- Win rate: 70-75% (with ML)
- **With $10K**: $1,800-2,200/year
- **Risk**: High (momentum + ML both unproven, 6+ month development)

**Most Likely Outcome** (pragmatic estimate):
- Phases 1-2 succeed: 8-12% annual return
- Phase 3 fails validation: Stick with Phase 2
- Phases 4-5 never attempted: Too time-intensive
- **Realistic 12-month result**: $800-1,200/year on $10K (8-12%)

### Failure Modes & Fallback

**If Phase 2 fails** (2% sizing → excessive drawdown):
- Fallback: 1% sizing (50% reduction)
- Expected return: 5-6% (still 5x better than current)

**If Phase 3 fails** (looser filters → win rate collapse):
- Fallback: Keep strict filters (vol_z > 0.2, volm_z > 0.3)
- Expected return: 10-12% (Phase 1+2 only)

**If Phase 4 fails** (momentum strategy loses money):
- Abandon momentum, stick with mean-reversion only
- Expected return: 15-20% (Phase 1-3)

**If Phase 5 fails** (ML no improvement):
- Already documented in BACKLOG (abandon ML research)
- Expected return: 20-25% (Phase 1-4)

**Nuclear Option**: If cumulative drawdown > 20%, revert to Phase 1 baseline (single symbol, 0.25% sizing, strict filters). Rebuild confidence with 50+ profitable trades before retrying.

---

## See Also
- **[PLAN.md](PLAN.md)** — 8-week roadmap (high-level milestones)
- **[PROJECT_BRIEF.md](PROJECT_BRIEF.md)** — System goals and current status
- **[DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md)** — Recent decisions
- **[INDEX.md](INDEX.md)** — Documentation navigation
- **[RSI_ENHANCEMENTS.md](RSI_ENHANCEMENTS.md)** — Strategy improvement details

---

**Last updated**: 2025-12-19  
**Next review**: Weekly (Fridays)
