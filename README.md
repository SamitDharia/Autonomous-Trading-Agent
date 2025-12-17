# Autonomous Trading Agent

An autonomous trading system that uses a stacked ensemble of expert models (RSI, MACD, Trend) and a meta-learner brain to predict 60-minute forward returns and size positions with strict risk controls.

**Current Status**: RSI-only baseline mode (brain parked until retraining improves AUC vs. baseline)

## Quick Links
- **[📘 Project Brief](docs/PROJECT_BRIEF.md)** — System goals, architecture, models, risk controls
- **[📚 Documentation Index](docs/INDEX.md)** — Full docs navigation + reading guide
- **[📝 Development Log](docs/DEVELOPMENT_LOG.md)** — Recent decisions and results
- **[🗺️ Roadmap](docs/PLAN.md)** — 8-week plan (Weeks 1-3 ✅, 4-8 🔄)

## Repository Structure
```
/
├── algo.py                   # Main QuantConnect algorithm (LEAN-compatible)
├── requirements.txt          # Python dependencies
│
├── /docs/                    # Documentation
│   ├── INDEX.md              # Navigation guide (start here)
│   ├── PROJECT_BRIEF.md      # Source of truth for trading system
│   ├── DEVELOPMENT_LOG.md    # Running diary
│   └── PLAN.md               # 8-week roadmap
│
├── /experts/                 # Level-1 expert models
│   ├── rsi_expert.py         # RSI + z-score + slope → probability
│   ├── macd_expert.py        # MACD + signal + histogram → probability
│   └── trend_expert.py       # EMA(20/50/200) + crossovers → probability
│
├── /ensemble/                # Level-2 brain (meta-model)
│   └── brain.py              # Logistic regression: experts + regime → final p
│
├── /features/                # Feature engineering
│   └── feature_builder.py    # Indicators (RSI, MACD, EMAs, ATR, BB) + regime
│
├── /risk/                    # Risk management
│   ├── position_sizing.py    # Probability → size (ATR-scaled, capped)
│   └── guards.py             # Daily stop, kill-switches, indicator readiness
│
├── /models/                  # Trained model JSONs (local + QC Object Store)
│   ├── rsi_expert.json
│   ├── macd_expert.json
│   ├── trend_expert.json
│   └── brain.json
│
├── /scripts/                 # Backtests & utilities
│   ├── local_backtest.py     # Run LEAN locally
│   ├── paper_trade.py        # Alpaca paper trading
│   └── alpaca_rsi_bot.py     # Standalone Alpaca bot (RSI-only)
│
└── /tests/                   # Unit tests
    ├── test_experts_brain.py
    ├── test_local_backtest.py
    └── conftest.py
```

## Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Local Backtest
```bash
python scripts/local_backtest.py --start-date 2024-01-01 --end-date 2024-06-30 --symbol TSLA
```

### 3. Run Tests
```bash
pytest tests/ -v
```

## Key Features
✅ **Stacked Ensemble**: 3 expert models → brain meta-learner  
✅ **Risk-First**: -1% daily stop, ATR-based sizing, bracket orders  
✅ **Dual Runtime**: QuantConnect (research/backtests) + local LEAN/Alpaca (live/paper)  
✅ **Model Versioning**: JSON models in local `/models/` + QC Object Store  
✅ **Kill-Switches**: Auto-flatten on daily loss, data errors, broker issues  

## Current Workflow
- **Research/Backtests**: QuantConnect Cloud (LEAN Web IDE)
- **Live/Paper**: Local Lean CLI or standalone Alpaca script (avoid QC live fees)
- **Models**: Train in QC, export JSON, sync to local `/models/`

## Recent Changes (Dec 2025)
- ✅ Removed 1000+ unused files (QC data, logs, duplicates): 30% repo size reduction
- ✅ Integrated feature builder + risk guards into `algo.py`
- ✅ Consolidated documentation (PROJECT_BRIEF as master, deprecated BOT_SPEC)
- ✅ Created INDEX.md for navigation

See **[CLEANUP_SUMMARY.md](CLEANUP_SUMMARY.md)** for full cleanup details.

## License
MIT

---
**Last updated**: 2025-12-17

