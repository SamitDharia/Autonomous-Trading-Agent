# Documentation Index

## Quick Start (for new contributors)
Read in this order:
1. **[PROJECT_BRIEF.md](PROJECT_BRIEF.md)** — Goal, architecture, models, risk controls (source of truth)
2. **[GETTING_STARTED.md](GETTING_STARTED.md)** — Setup, run backtest, verify output, paper trading
3. **[ARCHITECTURE.md](ARCHITECTURE.md)** — Module dependencies, data flow, testing strategy
4. **[DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md)** — Recent decisions, rationale, results
5. **[PLAN.md](PLAN.md)** — 8-week roadmap with status (Weeks 1-3 ✅, Week 4 🔄)
6. **[BACKLOG.md](BACKLOG.md)** — Known issues, enhancements, priorities

## Core Documentation

### System Design
- **[PROJECT_BRIEF.md](PROJECT_BRIEF.md)** — Trading system overview
  - Goal: Predict 60-min forward returns, size by confidence, enforce risk limits
  - Universe: TSLA (5m bars), expand to basket later
  - Models: 3 experts (RSI, MACD, Trend) → brain (logistic regression)
  - Risk: -1% daily stop, ATR-based position sizing, bracket orders
  - Current status: RSI-only mode (brain parked until AUC improves)

- **[ARCHITECTURE.md](ARCHITECTURE.md)** — System architecture (NEW)
  - Module structure and dependencies
  - Data flow: bars → features → experts → brain → size → order
  - Model storage (local + QC Object Store)
  - Testing strategy
  - Dual runtime (QC vs. local)

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
  - Latest: 2025-12-17 documentation consolidation
  - Previous: 2025-12-16 cleanup (1000+ files removed, algo.py integrated)
  - Workflow: QC for research/backtests, local for live/paper (Alpaca)
  
- **[PLAN.md](PLAN.md)** — 8-week roadmap (ENHANCED)
  - Week 1-3: ✅ Foundation, LEAN setup, risk engine
  - Week 4: 🔄 Paper canary mode (current focus)
  - Week 5-6: ⏳ Brain promotion system
  - Week 7-8: ⏳ Robustness hardening

- **[BACKLOG.md](BACKLOG.md)** — Open items and enhancements (CONSOLIDATED)
  - 🔴 High: Brain retraining, drift monitor, alert system
  - 🟡 Medium: Walk-forward pipeline, multi-symbol, analytics
  - 🟢 Low: Regime filters, RL sizing, trade journal

### Reference
- **[TRAINING.md](TRAINING.md)** — Model training notes (QC Research notebook)
- **[REVIEW.md](REVIEW.md)** — Repository review and known issues

### Archive
- **[ARCHIVE/](ARCHIVE/)** — Deprecated/historical docs
  - BOT_SPEC_deprecated.md
  - CLEANUP_2025-12.md
  - README_BOT_SPEC_deprecated.md
  - BACKLOG_ISSUES_deprecated.md

## Repository Structure
```
/
├── algo.py                   # Main QuantConnect algorithm
├── requirements.txt          # Python dependencies
├── /docs/                    # All documentation (you are here)
├── /experts/                 # Level-1 expert models (RSI, MACD, Trend)
├── /ensemble/                # Level-2 brain (meta-model)
├── /features/                # Feature builder (indicators + regime)
├── /risk/                    # Position sizing, guards, kill-switches
├── /models/                  # Trained model JSONs (local + QC Object Store)
├── /scripts/                 # Backtests, paper trading, utilities
├── /tests/                   # Unit tests for all modules
└── /brains/                  # Brain model storage (versioned)
```

## Module Dependencies
```
algo.py
  ├─→ features.feature_builder.build_features()
  ├─→ risk.guards.{daily_pnl_stop_hit, indicators_ready}
  ├─→ experts.{rsi,macd,trend}_expert.predict_proba()
  ├─→ ensemble.brain.predict_proba()
  └─→ risk.position_sizing.size_from_prob()
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
