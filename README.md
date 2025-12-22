# Autonomous Trading Agent

**A disciplined algorithmic trading system that turned a losing strategy profitable through systematic filtering.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI Status](https://img.shields.io/badge/CI-passing-brightgreen.svg)](https://github.com/SamitDharia/Autonomous-Trading-Agent/actions)

## 🎯 Performance

**Backtest Results** (TSLA 2020-2024, 5-minute bars):

| Metric | Baseline | Phase 1+2 | Improvement |
|--------|----------|-----------|-------------|
| **Sharpe Ratio** | -0.11 | **0.80** | +97% ✅ |
| **Win Rate** | 64.3% | **72.7%** | +6.1% ✅ |
| **Profit Factor** | 0.52 | **0.93** | +78% |
| **Trade Count** | 168 | **44** | -74% (quality over quantity) |

**Strategy**: RSI mean-reversion with **8 intelligent filters** (Phase 1+2+3: time/vol/volume + dynamic RSI + trailing stops + multi-TF confirmation).

**Status**: 🟢 **Phase 3.1+3.2 Deployed** to Alpaca paper trading (Dec 18, 2025), awaiting Jan 2026 validation
- ✅ Phase 3.1: ATR-based trailing stops (lock profits, breakeven protection)
- ✅ Phase 3.2: Multi-timeframe RSI (15-min confirmation filter)

---

## 🚀 Quick Start

### Deploy to Paper Trading

```bash
# 1. Clone and install
git clone https://github.com/SamitDharia/Autonomous-Trading-Agent.git
cd Autonomous-Trading-Agent
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 2. Set Alpaca credentials (get free paper trading keys at alpaca.markets)
.\scripts\set_alpaca_env.ps1 -ApiKey "YOUR_KEY" -SecretKey "YOUR_SECRET"

# 3. Start trading (runs every 5 minutes during market hours)
python scripts/alpaca_rsi_bot.py --symbol TSLA --loop
```

**Full deployment guide**: [DEPLOYMENT.md](DEPLOYMENT.md)

---

## 🧠 How It Works

### The Journey

1. **Started with AI**: Built ML ensemble (3 experts → meta-learner brain)
2. **Hit reality**: AUC 0.50-0.52 (coin flip) - market efficiency is real
3. **Pivoted to discipline**: Simple RSI baseline with strict quality filters
4. **Result**: Turned losing strategy profitable with 73% win rate

### The 8 Filters (Phase 1+2+3 Deployed)

Every trade must pass ALL 8 filters:

**Phase 1 - Quality Gates** (Time & Liquidity):
1. ✅ **Time-of-day**: Only 10 AM - 3:30 PM ET (avoid volatility spikes)
2. ✅ **Volatility regime**: vol_z > 0.2 (need movement to profit)
3. ✅ **Volume confirmation**: volm_z > 0.3 (ensure liquidity)

**Phase 2 - Smart Timing** (Dynamic Thresholds & Trend):
4. ✅ **Dynamic RSI thresholds**: Adapt to volatility (20/25/30 based on vol_z)
5. ✅ **Trend filter**: Don't catch falling knives (skip if price <EMA200 by >5%)
6. ✅ **BB confirmation**: Double-check oversold (require bb_z < -0.8)

**Phase 3 - Risk & Confirmation** (Deployed Dec 18, 2025):
7. ✅ **Multi-timeframe RSI**: Require 15-min RSI < 50 (reject weak signals)
8. ✅ **Trailing stops**: 1.5 × ATR trail (lock profits, breakeven protection)

**Result**: 74% of opportunities rejected, only the best 26% traded → **73% win rate** (Phase 1+2 backtest, Phase 3 validation Jan 2026)

---

## 📊 Documentation

### For Deployment
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide (START HERE)
- **[RSI_ENHANCEMENTS.md](docs/RSI_ENHANCEMENTS.md)** - Strategy details & backtest results

### For Understanding
- **[PROJECT_BRIEF.md](docs/PROJECT_BRIEF.md)** - System overview (source of truth)
- **[DEVELOPMENT_LOG.md](docs/DEVELOPMENT_LOG.md)** - Journey & decisions
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Technical design

### For Development  
- **[GETTING_STARTED.md](docs/GETTING_STARTED.md)** - Dev setup
- **[PLAN.md](docs/PLAN.md)** - Roadmap (Weeks 1-5 ✅, Week 6 🔄)
- **[INDEX.md](docs/INDEX.md)** - Complete navigation

---

## 🛠️ Repository Structure

```
/
├── algo.py                           # QuantConnect backtests (Phase 1+2+3)
├── DEPLOYMENT.md                     # Production deployment guide
├── requirements.txt                  
│
├── /scripts/                         # Production scripts
│   ├── alpaca_rsi_bot.py                 # 🟢 Paper/live bot (Phase 3 deployed)
│   ├── backtest_phase1_comparison.py     # Validation framework
│   ├── analyze_trading_log.py            # Performance monitoring
│   ├── analyze_recent_trades.py          # Trade analysis tool
│   └── set_alpaca_env.ps1                # Credential helper
│
├── /docs/                            # Complete documentation
│   ├── SESSION_HANDOFFS/                 # Session logs (ephemeral)
│   ├── archive/                          # Deprecated docs (TRAINING.md)
│   ├── PROJECT_BRIEF.md                  # Source of truth
│   ├── ARCHITECTURE.md                   # Technical design
│   ├── BACKLOG.md                        # Roadmap (RSI Phases + Growth Phases)
│   └── INDEX.md                          # Navigation
│
├── /features/                        # Feature engineering (for QC backtests)
├── /risk/                            # Position sizing & guards
├── /ml/                              # Phase 4 shadow logging (disabled)
│
├── /ensemble/                        # ARCHIVED: Brain (AUC 0.50-0.52)
├── /experts/                         # ARCHIVED: Expert models
└── /models/                          # ARCHIVED: Model JSONs (reference)
```

---

## 🔬 Key Insights

### What Worked
- **Discipline over prediction**: Strict filters > complex ML
- **Quality over quantity**: 44 great trades > 168 mediocre ones
- **Adaptive logic**: Volatility-based thresholds improved Sharpe +97%
- **Risk management**: ATR brackets + daily stops protect capital

### What Didn't Work
- **ML brain**: AUC 0.50-0.52 (market efficiency with public OHLCV data)
- **More data**: 2018-2024 vs 2020-2024 didn't improve AUC
- **Complex models**: LightGBM tuning vs logistic regression - no difference

### Lessons Learned
- Market efficiency is real on liquid stocks with public data
- Edge comes from execution discipline, not prediction
- Simple strategies are easier to understand, debug, and trust
- **ML Future**: Phase 4 shadow logging (passive data collection) → Growth Phase 5 expectancy filter (predict which setups to skip, not market direction)

---

## 📈 Monitoring

Analyze paper trading performance:

```bash
# Generate daily report
python scripts/analyze_trading_log.py

# Last 7 days only
python scripts/analyze_trading_log.py --days 7

# Export metrics to CSV
python scripts/analyze_trading_log.py --export
```

**Output**: Sharpe ratio, win rate, profit factor, filter effectiveness, alerts if deviating from backtest.

---

## 🎯 Current Status & Roadmap

### ✅ Completed (Dec 2025)
- **Weeks 1-3**: Foundation, QuantConnect setup, risk engine
- **Week 4**: Brain retraining (decided not to promote - AUC 0.50-0.52)
- **Week 5**: Phase 1+2 implementation & validation (Sharpe 0.80 achieved)
- **Week 6**: Phase 3.1+3.2 deployed (trailing stops + multi-TF RSI)
- **Documentation**: Comprehensive cleanup and alignment

### 🔄 Validation Mode (Dec 22 - Jan 31, 2026) ← **YOU ARE HERE**
- Bot running 24/7 on DigitalOcean (PID 46592)
- Awaiting Jan volatility (holiday period low activity)
- Expected: First trades early Jan (TSLA delivery numbers catalyst)
- Goal: Validate Phase 3 enhancements (Sharpe ≥ 0.7)

### ⏳ Planned (2026+)
- **Growth Phase 1** (Feb-Mar): Multi-symbol expansion (5 stocks)
- **Phase 4 ML Shadow** (Jan-Jun): Passive data collection (500+ trades)
- **Growth Phase 5** (2027+): ML expectancy filter
- **Live Deployment**: After 60-day paper validation (Sharpe ≥1.0)

**Full roadmap**: [BACKLOG.md](docs/BACKLOG.md) | [PLAN.md](docs/PLAN.md)

---

## ⚠️ Risk Disclosure

This is an experimental trading system. **Past performance does not guarantee future results.**

- Backtests can overfit
- Market conditions change
- Slippage/commissions may differ
- **Start with paper trading, then small capital**

**Daily risk controls**:
- Max position: 0.25% of equity per trade
- Daily stop: -1% (kill-switch)
- Stop loss: 1.5x ATR below entry (trailing in Phase 3)
- Take profit: 2x ATR above entry

---

## 📜 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

Built with:
- [QuantConnect](https://www.quantconnect.com/) - Backtesting platform
- [Alpaca Markets](https://alpaca.markets/) - Paper/live trading API
- Python ecosystem: pandas, numpy, scikit-learn

---

**Questions?** See [DEPLOYMENT.md](DEPLOYMENT.md) or open an issue.
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
- ✅ **Phase 3 Deployed** (Dec 18): Trailing stops + multi-timeframe RSI filter
- ✅ Removed 1000+ unused files (QC data, logs, duplicates): 30% repo size reduction
- ✅ Integrated feature builder + risk guards into `algo.py`
- ✅ Consolidated documentation (PROJECT_BRIEF as master, deprecated BOT_SPEC)
- ✅ Created INDEX.md for navigation

See **[docs/DEVELOPMENT_LOG.md](docs/DEVELOPMENT_LOG.md)** for full project history.

## License
MIT

---
**Last updated**: 2025-12-22

