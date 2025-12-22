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
  - Models: RSI baseline with Phase 1+2+3 enhancements - **CURRENT CHAMPION**
  - Brain: Stacked ensemble archived (AUC 0.50-0.52, not promoted)
  - Risk: -1% daily stop, 0.25% position cap, ATR brackets (1x/2x)
  - **Current status**: Phase 1+2+3 deployed to paper trading (PID 46592)
  - **Phase 3.1**: ATR-based trailing stops (1.5 ATR, only when profitable)
  - **Phase 3.2**: Multi-timeframe RSI filter (15-min RSI < 50 confirmation)
  - **Maximum Returns Path**: See BACKLOG.md for 5-phase growth roadmap (12-22% targets)

- **[DEPLOYMENT.md](../DEPLOYMENT.md)** — Local deployment guide
  - Alpaca paper trading setup
  - Credential configuration
  - Running the bot (loop mode)
  - Monitoring and troubleshooting
  - Success criteria (5-7 day evaluation)

- **[CLOUD_DEPLOYMENT.md](CLOUD_DEPLOYMENT.md)** — Cloud deployment guide (NEW)
  - DigitalOcean, AWS EC2, Google Cloud setup
  - SSH key configuration, security best practices
  - Auto-restart on reboot (cron jobs)
  - Monitoring and health checks
  - Current deployment: DigitalOcean Frankfurt droplet ($6/month)

- **[RSI_ENHANCEMENTS.md](RSI_ENHANCEMENTS.md)** — RSI strategy optimization roadmap
  - Phase 1: ✅ COMPLETE (time-of-day, volume, volatility filters)
  - Phase 2: ✅ COMPLETE (dynamic thresholds, trend filter, BB confirmation)
  - Phase 3: ✅ DEPLOYED (trailing stops, multi-timeframe RSI)
  - Phase 4: ✅ IMPLEMENTED (shadow ML logging, disabled by default)
  - Backtest results: Baseline → Phase 1 → Phase 1+2 comparison
  - Live performance: Monitoring Phase 3 enhancements

- **[PHASE3_TRAILING_STOP_DESIGN.md](PHASE3_TRAILING_STOP_DESIGN.md)** — Trailing stop design
  - ✅ DEPLOYED (Dec 18, 2025 - 18:07 UTC)
  - ATR-based trailing stop via order.replace() API
  - Only trail when profitable, 1.5 ATR distance
  - Target: +10% Sharpe improvement

- **[PHASE3_MULTI_TF_RSI_DESIGN.md](PHASE3_MULTI_TF_RSI_DESIGN.md)** — Multi-timeframe RSI design
  - ✅ DEPLOYED (Dec 18, 2025 - 18:24 UTC)
  - 15-min RSI confirmation (5m <25, 15m <50)
  - Filters whipsaws when broader trend still bullish
  - Target: +10-15% Sharpe, ~25% trade reduction

### Getting Started
- **[GETTING_STARTED.md](GETTING_STARTED.md)** — Setup guide (NEW)
  - Install dependencies
  - Configure Alpaca API keys
  - Run local backtest
  - Verify feature output
  - Run paper trading
  - Common issues & fixes

### Operations
- **[DAILY_MONITORING.md](DAILY_MONITORING.md)** — Daily monitoring guide (NEW)
  - Quick health check commands
  - Manual monitoring queries
  - Troubleshooting reference
  - Timeline expectations (holidays, validation windows)
  - Analysis tools (analyze_recent_trades.py)
  - Automated script: scripts/daily_health_check.ps1

### Development
- **[DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md)** — Dated entries for decisions and results
  - Latest: 2025-12-18 Week 6 (cloud deployment, ML infrastructure, Phase 3 planning)
  - Previous: 2025-12-17 Phase 2 validation (Sharpe 0.80, deployed to paper trading)
  - 2025-12-16 brain retraining (AUC 0.50-0.52, not promoted), Phase 1 implementation
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
  - **Maximum Returns Path**: 5-phase roadmap targeting 12-22% annual returns (2026-2027)

### Reference
- **[TRAINING.md](archive/TRAINING.md)** — Brain training code (ARCHIVED, brain ensemble abandoned)
- **[ARCHITECTURE.md](ARCHITECTURE.md)** — System architecture (current RSI baseline + legacy ensemble)

### Archive
- **[archive/](archive/)** — Deprecated documentation
  - TRAINING.md (Brain ensemble training guide - deprecated Dec 2025)
  
- **[SESSION_HANDOFFS/](SESSION_HANDOFFS/)** — Session logs (ephemeral)
  - 2025-12-19.md (Phase 3 deployment validation)
  - 2025-12-22.md (Maximum Returns Path, daily monitoring, doc cleanup)
  
- **[ARCHIVE/](ARCHIVE/)** — Historical cleanup docs
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
├── /scripts/                 # Production scripts (alpaca_rsi_bot.py, analyze_recent_trades.py)
├── /ml/                      # Shadow ML logging (Phase 4, disabled by default)
│   ├── shadow.py                   # Shadow logging functions
│   └── README.md                   # ML infrastructure documentation
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

**Last updated**: 2025-12-22
