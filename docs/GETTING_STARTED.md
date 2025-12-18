# Getting Started

**Quick Start**: For immediate deployment, see [DEPLOYMENT.md](../DEPLOYMENT.md)  
**This guide**: Development setup and project overview

---

## Current Strategy

**Champion**: RSI Baseline with Phase 1+2+3 Enhancements  
**Status**: Deployed to Alpaca paper trading (2025-12-18, PID 46592)  
**Performance**: Phase 1+2 Sharpe 0.80, Win Rate 72.7% (2020-2024 backtest)  
**Phase 3**: Trailing stops + multi-timeframe RSI (monitoring in progress)

**Note**: The original stacked ensemble (brain + experts) achieved AUC 0.50-0.52 and was **not promoted**. Code is preserved in `ensemble/` and `experts/` directories but is **not used** in production.

---

## Prerequisites

- **Python 3.10+** (tested with 3.11)
- **Git** (to clone repository)
- **Alpaca Account** (for paper/live trading) — [Sign up here](https://alpaca.markets/)
- **QuantConnect Account** (optional, for research/backtests) — [Sign up here](https://www.quantconnect.com/)

---

## 1. Clone & Install

### Clone Repository
```bash
git clone https://github.com/SamitDharia/Autonomous-Trading-Agent.git
cd Autonomous-Trading-Agent
```

### Create Virtual Environment
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

**Key packages**:
- `pandas`, `numpy` — Data processing
- `alpaca-trade-api` — Alpaca API client
- `pytest` — Testing framework

---

## 2. Paper Trading Deployment

**For complete deployment instructions**, see **[DEPLOYMENT.md](../DEPLOYMENT.md)**

Quick summary:
1. Get Alpaca API keys (paper trading)
2. Set environment variables
3. Run: `python scripts/alpaca_rsi_bot.py --symbol TSLA --loop`

The bot implements all Phase 1+2 filters automatically.

---

## 3. Development Setup (Optional)

### Configure Alpaca API Keys (Development)
1. Log in to [Alpaca](https://app.alpaca.markets/)
2. Navigate to **Paper Trading** → **API Keys**
3. Generate new API key pair (save securely)

### Set Environment Variables

**Windows (PowerShell)**:
```powershell
$env:ALPACA_API_KEY = "your_api_key_here"
$env:ALPACA_SECRET_KEY = "your_secret_key_here"
$env:ALPACA_BASE_URL = "https://paper-api.alpaca.markets"
```

**Linux/Mac (Bash)**:
```bash
export ALPACA_API_KEY="your_api_key_here"
export ALPACA_SECRET_KEY="your_secret_key_here"
export ALPACA_BASE_URL="https://paper-api.alpaca.markets"
```

**Persistent Setup** (add to `.env` file):
```bash
# Create .env file (ignored by git)
echo "ALPACA_API_KEY=your_key" >> .env
echo "ALPACA_SECRET_KEY=your_secret" >> .env
echo "ALPACA_BASE_URL=https://paper-api.alpaca.markets" >> .env
```

Then load with `python-dotenv` (already in `requirements.txt`).

---

## 3. Verify Installation

### Run Tests
```bash
pytest tests/ -v
```

**Expected output**:
```
tests/test_experts_brain.py::test_rsi_expert_loads PASSED
tests/test_experts_brain.py::test_brain_loads PASSED
tests/test_local_backtest.py::test_feature_builder PASSED
======================== 3 passed in 2.5s ========================
```

### Check Model Files
```bash
ls models/
```

**Expected files**:
- `rsi_expert.json`
- `macd_expert.json`
- `trend_expert.json`
- `brain.json`

If missing, download from [releases](https://github.com/SamitDharia/Autonomous-Trading-Agent/releases) or train new models (see [TRAINING.md](TRAINING.md)).

---

## 4. Run Local Backtest

Test the algorithm on historical data without live trading.

### Basic Backtest (RSI-only mode)
```bash
python scripts/local_backtest.py \
  --start-date 2024-01-01 \
  --end-date 2024-06-30 \
  --symbol TSLA
```

**What happens**:
1. Loads TSLA 1-minute data from Alpaca (via API)
2. Consolidates to 5-minute bars
3. Computes indicators (RSI, MACD, EMA, ATR, BB)
4. Runs RSI baseline strategy (enter RSI<25, exit RSI>75)
5. Prints trade log + final P&L

**Expected output**:
```
[2024-01-05 09:35] ENTRY: TSLA @ $245.32, RSI=23.4, size=$500
[2024-01-05 11:20] EXIT: TSLA @ $248.15, RSI=76.2, P&L=+$11.32
...
Final P&L: +$324.50 (3.25%)
Sharpe: 1.42
Max Drawdown: -2.1%
```

### Advanced Backtest (with brain ensemble)
```bash
python scripts/local_backtest.py \
  --start-date 2024-01-01 \
  --end-date 2024-06-30 \
  --symbol TSLA \
  --use-brain \
  --edge-threshold 0.10 \
  --position-cap 0.0020
```

**Parameters**:
- `--use-brain`: Enable expert ensemble + brain (default: RSI-only)
- `--edge-threshold`: Minimum edge required (|p - 0.5|, default 0.05)
- `--position-cap`: Max position size as % of equity (default 0.0020 = 0.20%)

---

## 5. Verify Feature Output

Check that features are being computed correctly.

### Inspect First Bar
Add debug logging to `algo.py` (line ~95):
```python
features = build_features(self)
if features:
    self.Debug(f"Features: {features}")  # Add this line
```

Run backtest and check logs:
```
Features: {
  'rsi': 45.3,
  'rsi_slope': 0.02,
  'ema_fast_slow_diff': 0.015,
  'macd': 0.34,
  'macd_signal': 0.28,
  'atr_pct': 0.023,
  'time_of_day': 10.5,
  ...
}
```

### Verify Expert Predictions
Add expert logging (line ~102):
```python
expert_probs = {
    "rsi": float(self.rsi_expert.predict_proba(features)),
    "macd": float(self.macd_expert.predict_proba(features)),
    "trend": float(self.trend_expert.predict_proba(features)),
}
self.Debug(f"Experts: {expert_probs}")  # Add this line
```

Expected output:
```
Experts: {'rsi': 0.52, 'macd': 0.48, 'trend': 0.55}
```

**Healthy ranges**: All probabilities should be in [0.3, 0.7] range (not stuck at 0.5).

---

## 6. Run Paper Trading (Alpaca)

Test the algorithm with live market data (no real money).

### Start Paper Trading Bot
```bash
python scripts/paper_trade.py
```

**What happens**:
1. Connects to Alpaca paper trading account
2. Subscribes to TSLA real-time bars (5-minute aggregation)
3. Computes indicators on each bar
4. Runs RSI baseline strategy (or brain if enabled)
5. Logs trades to `alpaca_rsi_log.csv`

**Expected console output**:
```
[2025-12-17 09:35:00] Connected to Alpaca (paper mode)
[2025-12-17 09:35:00] Current portfolio: $100,000.00
[2025-12-17 09:40:00] Bar: TSLA @ $245.32, RSI=23.4
[2025-12-17 09:40:00] ENTRY: BUY 20 TSLA @ $245.32 (RSI<25)
[2025-12-17 09:40:00] Bracket orders: STOP=$244.00, TP=$247.64
...
```

### Monitor Trade Log
```bash
tail -f alpaca_rsi_log.csv
```

**CSV format**:
```csv
timestamp,symbol,action,price,qty,rsi,reason
2025-12-17 09:40:00,TSLA,BUY,245.32,20,23.4,RSI<25
2025-12-17 11:20:00,TSLA,SELL,248.15,20,76.2,RSI>75
```

### Stop Bot
Press `Ctrl+C` to gracefully shutdown.

---

## 7. Common Issues & Fixes

### Issue: `ModuleNotFoundError: No module named 'experts'`
**Cause**: Python can't find project modules.

**Fix**: Run from repository root:
```bash
cd Autonomous-Trading-Agent
python scripts/local_backtest.py
```

Or add to `PYTHONPATH`:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

---

### Issue: `FileNotFoundError: models/rsi_expert.json`
**Cause**: Model files missing or in wrong location.

**Fix**: Verify files exist:
```bash
ls models/*.json
```

If missing, download from [releases](https://github.com/SamitDharia/Autonomous-Trading-Agent/releases).

---

### Issue: Backtest returns empty P&L
**Cause**: Indicators not ready, or edge threshold too strict.

**Fix 1** - Check indicator warm-up:
```python
# In algo.py, verify warm-up period
self.SetWarmUp(timedelta(days=30))  # Increase if needed
```

**Fix 2** - Loosen edge threshold:
```bash
python scripts/local_backtest.py --edge-threshold 0.02  # Lower from 0.05
```

**Fix 3** - Check RSI bands:
```python
# In algo.py, verify RSI thresholds
if rsi < 25:  # Entry (lowered from 30)
if rsi > 75:  # Exit (raised from 70)
```

---

### Issue: Alpaca API authentication fails
**Cause**: Invalid API keys or environment variables not set.

**Fix**: Verify keys are set correctly:
```bash
echo $ALPACA_API_KEY      # Should print your key
echo $ALPACA_SECRET_KEY   # Should print your secret
```

Test connection:
```python
from alpaca.trading.client import TradingClient

client = TradingClient(
    api_key=os.getenv("ALPACA_API_KEY"),
    secret_key=os.getenv("ALPACA_SECRET_KEY"),
    paper=True
)
account = client.get_account()
print(f"Account: {account.equity}")
```

---

### Issue: Daily P&L stop not triggering
**Cause**: Guard function tracking state incorrectly.

**Fix**: Verify daily stop logic in `risk/guards.py`:
```python
def daily_pnl_stop_hit(algo, threshold=-0.01):
    # Check implementation matches expected behavior
    current_pnl = (algo.Portfolio.TotalPortfolioValue - algo._start_of_day_equity) / algo._start_of_day_equity
    return current_pnl <= threshold
```

Add debug logging:
```python
self.Debug(f"Daily P&L: {current_pnl:.4f}, Threshold: {threshold}")
```

---

## 8. Next Steps

### For Development
1. ✅ Read [ARCHITECTURE.md](ARCHITECTURE.md) to understand system design
2. ✅ Read [PROJECT_BRIEF.md](PROJECT_BRIEF.md) for goals and risk controls
3. ✅ Explore [DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md) for recent decisions

### For Model Training
1. Sign up for [QuantConnect](https://www.quantconnect.com/)
2. Follow [TRAINING.md](TRAINING.md) to retrain experts + brain
3. Export JSONs and sync to local `/models/`

### For Production
1. Run paper trading for 1-2 weeks (monitor `alpaca_rsi_log.csv`)
2. Verify daily P&L stop triggers correctly (test with small capital)
3. Compare paper results vs. backtest (should be within 10% due to slippage)
4. Only switch to live after stable paper performance

---

## Quick Reference

### File Locations
- **Algorithm**: `algo.py`
- **Models**: `models/*.json`
- **Scripts**: `scripts/{local_backtest.py, paper_trade.py}`
- **Tests**: `tests/test_*.py`
- **Logs**: `alpaca_rsi_log.csv` (paper trading output)

### Common Commands
```bash
# Run tests
pytest tests/ -v

# Local backtest (RSI-only)
python scripts/local_backtest.py --start-date 2024-01-01 --end-date 2024-06-30

# Paper trading
python scripts/paper_trade.py

# Check git status
git status
git log --oneline -10
```

---

---

## See Also
- **[ARCHITECTURE.md](ARCHITECTURE.md)** — System design and module dependencies
- **[PROJECT_BRIEF.md](PROJECT_BRIEF.md)** — Goals, risk controls, models
- **[DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md)** — Recent decisions
- **[TRAINING.md](TRAINING.md)** — Retrain models in QuantConnect
- **[INDEX.md](INDEX.md)** — Documentation navigation

## Support

- **Documentation**: [docs/INDEX.md](INDEX.md)
- **Issues**: [GitHub Issues](https://github.com/SamitDharia/Autonomous-Trading-Agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/SamitDharia/Autonomous-Trading-Agent/discussions)

---

**Last updated**: 2025-12-17
