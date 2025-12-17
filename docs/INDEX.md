# Documentation Index

## Quick Start (for new contributors)
Read in this order:
1. **[DEPLOYMENT.md](../DEPLOYMENT.md)** — Production deployment guide (START HERE for paper/live trading)
2. **[PROJECT_BRIEF.md](PROJECT_BRIEF.md)** — Goal, architecture, current status (source of truth)
3. **[RSI_ENHANCEMENTS.md](RSI_ENHANCEMENTS.md)** — Phase 1+2 strategy details and backtest results
4. **[GETTING_STARTED.md](GETTING_STARTED.md)** — Development setup
5. **[DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md)** — Recent decisions, rationale, results
6. **[PLAN.md](PLAN.md)** — 8-week roadmap (Weeks 1-5 ✅, Week 6 🔄)

## Core Documentation

### System Design
- **[PROJECT_BRIEF.md](PROJECT_BRIEF.md)** — Trading system overview
  - Goal: Predict 60-min forward returns, size by confidence, enforce risk limits
  - Universe: TSLA (5m bars), expand to basket later
  - Models: RSI baseline with Phase 1+2 filters (6 filters total) - **CURRENT CHAMPION**
  - Brain: Stacked ensemble archived (AUC 0.50-0.52, not promoted)
  - Risk: -1% daily stop, 0.25% position cap, ATR brackets (1x/2x)
  - **Current status**: Phase 1+2 deployed to paper trading (Sharpe 0.80, Win Rate 72.7%)

- **[DEPLOYMENT.md](../DEPLOYMENT.md)** — Production deployment guide (NEW)
  - Alpaca paper trading setup
  - Credential configuration
  - Running the bot (loop mode)
  - Monitoring and troubleshooting
  - Success criteria (5-7 day evaluation)

- **[RSI_ENHANCEMENTS.md](RSI_ENHANCEMENTS.md)** — RSI strategy optimization roadmap
  - Phase 1: ✅ COMPLETE (time-of-day, volume, volatility filters)
  - Phase 2: ✅ COMPLETE (dynamic thresholds, trend filter, BB confirmation)
  - Phase 3: ⏳ PLANNED (trailing stops, multi-timeframe, position scaling)
  - Backtest results: Baseline → Phase 1 → Phase 1+2 comparison

### Getting Started
- **[GETTING_STARTED.md](GETTING_STARTED.md)** — Setup guide (NEW)
  - Install dependencies
  - Configure Alpaca API keys
  - Run local backtest
  - Verify feature output
  - Run paper trading
  - Common issues & fixes

### Development
- **[DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md)** — Dated entries for decisions and results
  - Latest: 2025-12-17 Phase 2 validation (Sharpe 0.80, deployed to paper trading)
  - Previous: 2025-12-16 brain retraining (AUC 0.50-0.52, not promoted), Phase 1 implementation
  - Workflow: QC for research/backtests, local Alpaca for live/paper
  
- **[PLAN.md](PLAN.md)** — 8-week roadmap
  - Weeks 1-3: ✅ Foundation, LEAN setup, risk engine
  - Weeks 4-5: ✅ RSI Phase 1+2 implementation and validation
  - Week 6: 🔄 Paper trading monitoring (current focus)
  - Weeks 7-8: ⏳ Live trading or Phase 3 enhancements

- **[BACKLOG.md](BACKLOG.md)** — Open items and enhancements
  - 🔴 High: Paper trading monitoring (Week 6 focus)
  - 🟡 Medium: Drift monitor, alert system, analytics
  - 🟢 Low: Phase 3 enhancements, multi-symbol, regime filters

### Reference
- **[TRAINING.md](TRAINING.md)** — Brain training code (archived, H=24 configuration)
- **[ARCHITECTURE.md](ARCHITECTURE.md)** — System architecture (current RSI baseline + legacy ensemble)

### Archive
- **[ARCHIVE/](ARCHIVE/)** — Deprecated/historical docs
  - REVIEW_deprecated.md (pre-cleanup repository audit)
  - BOT_SPEC_deprecated.md
  - CLEANUP_2025-12.md
  - README_BOT_SPEC_deprecated.md
  - BACKLOG_ISSUES_deprecated.md

## Repository Structure
```
/
├── algo.py                   # QuantConnect algorithm (Phase 1+2)
├── DEPLOYMENT.md             # Production deployment guide
├── requirements.txt          # Python dependencies
├── /docs/                    # All documentation (you are here)
├── /scripts/                 # Production scripts (3 files)
│   ├── alpaca_rsi_bot.py           # Paper/live trading bot
│   ├── backtest_phase1_comparison.py  # Validation framework
│   └── set_alpaca_env.ps1          # Credential helper
├── /features/                # Feature builder (indicators + regime)
├── /risk/                    # Position sizing, guards, kill-switches
├── /experts/                 # ARCHIVED: Level-1 expert models
├── /ensemble/                # ARCHIVED: Level-2 brain (meta-model)
├── /models/                  # ARCHIVED: Trained model JSONs (reference only)
└── /tests/                   # Unit tests
```

## Module Dependencies (Current)
```
alpaca_rsi_bot.py
  ├─→ calculate_features() [RSI, vol_z, volm_z, ema200_rel, bb_z]
  ├─→ get_dynamic_rsi_thresholds(vol_z) [Phase 2]
  ├─→ Phase 1 filters: time_of_day, vol_z, volm_z
  ├─→ Phase 2 filters: trend (ema200_rel), BB (bb_z)
  └─→ Alpaca REST API (bracket orders, position management)

algo.py (QuantConnect)
  ├─→ features.feature_builder.build_features()
  ├─→ risk.guards.{daily_pnl_stop_hit, indicators_ready}
  ├─→ Phase 1+2 logic (inline)
  └─→ QC broker API (SetHoldings, MarketOrder, StopMarketOrder)
```

## Common Tasks

### Run Local Backtest
```bash
python scripts/local_backtest.py --start-date 2024-01-01 --end-date 2024-06-30 --symbol TSLA
```

### Run Paper Trading (Alpaca)
```bash
# Set environment variables
export ALPACA_API_KEY="your_key"
export ALPACA_SECRET_KEY="your_secret"
export ALPACA_BASE_URL="https://paper-api.alpaca.markets"

# Run bot
python scripts/paper_trade.py
```

### Run Tests
```bash
pytest tests/ -v
```

## See Also
- **[README.md](../README.md)** — Top-level repo overview
- **[CLEANUP_SUMMARY.md](../CLEANUP_SUMMARY.md)** — Dec 2025 cleanup details (1000+ files removed)

---

**Last updated**: 2025-12-17
