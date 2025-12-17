# Documentation Index

## Quick Start (for new contributors)
Read in this order:
1. **[PROJECT_BRIEF.md](PROJECT_BRIEF.md)** — Goal, architecture, models, risk controls (source of truth)
2. **[DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md)** — Recent decisions, rationale, results (running diary)
3. **[PLAN.md](PLAN.md)** — 8-week roadmap with status
4. **[BACKLOG.md](BACKLOG.md)** — Known issues and enhancements

## Core Documentation

### System Design
- **[PROJECT_BRIEF.md](PROJECT_BRIEF.md)** — Trading system overview: goal, non-negotiables, features, models, risk, rollout
  - Universe: TSLA (5m bars), expand to basket later
  - Models: 3 experts (RSI, MACD, Trend) → brain (logistic regression)
  - Risk: -1% daily stop, ATR-based position sizing, bracket orders
  - Current status: RSI-only mode (brain parked until AUC improves)

### Development
- **[DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md)** — Dated entries for decisions and results
  - Latest: 2025-12-16 cleanup (1000+ files removed, algo.py integrated)
  - Workflow: QC for research/backtests, local for live/paper (Alpaca)
  
- **[PLAN.md](PLAN.md)** — 8-week roadmap
  - Weeks 1-3: ✅ Foundation, LEAN setup, risk engine
  - Weeks 4-8: 🔄 Paper trading, brain promotion, hardening

- **[BACKLOG.md](BACKLOG.md)** — Open items and enhancements
- **[BACKLOG_ISSUES.md](BACKLOG_ISSUES.md)** — Additional tracked issues

### Reference
- **[TRAINING.md](TRAINING.md)** — Model training notes (if applicable)
- **[REVIEW.md](REVIEW.md)** — Code review notes (if applicable)

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
