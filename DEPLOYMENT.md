# Alpaca Paper Trading Deployment Guide

**Strategy**: RSI Baseline with Phase 1+2 Enhancements  
**Status**: Ready for Paper Trading  
**Last Updated**: 2025-12-17

## Backtest Performance (2020-2024)

- **Sharpe Ratio**: 0.80 (vs baseline -0.11)
- **Win Rate**: 72.7% (vs baseline 64.3%)
- **Trade Count**: 44 (vs baseline 168)
- **Profit Factor**: 0.93

---

## Prerequisites

1. **Alpaca Account**: Sign up at https://alpaca.markets (free paper trading)
2. **API Keys**: Get paper trading API key and secret from Alpaca dashboard
3. **Python Environment**: Ensure virtual environment is activated

---

## Step 1: Set Up Alpaca Credentials

### Option A: PowerShell Script (Recommended)

```powershell
# In PowerShell terminal
.\scripts\set_alpaca_env.ps1 -ApiKey "YOUR_API_KEY" -SecretKey "YOUR_SECRET_KEY" -BaseUrl "https://paper-api.alpaca.markets"
```

### Option B: Manual Environment Variables

```powershell
# Set for current session
$env:ALPACA_API_KEY = "YOUR_API_KEY"
$env:ALPACA_SECRET_KEY = "YOUR_SECRET_KEY"
$env:ALPACA_BASE_URL = "https://paper-api.alpaca.markets"
```

### Option C: Create .env file (Not Recommended - security risk)

```bash
# Create .env file in project root (add to .gitignore!)
ALPACA_API_KEY=YOUR_API_KEY
ALPACA_SECRET_KEY=YOUR_SECRET_KEY
ALPACA_BASE_URL=https://paper-api.alpaca.markets
```

---

## Step 2: Install Dependencies

```powershell
# Activate virtual environment if not already active
.\.venv\Scripts\Activate.ps1

# Install Alpaca API
pip install alpaca-trade-api
```

---

## Step 3: Test Connection (Dry Run)

```powershell
# Test without placing orders
python scripts/alpaca_rsi_bot.py --symbol TSLA

# Expected output:
# - Account equity displayed
# - Feature calculations (RSI, vol_z, volm_z, ema200_rel, bb_z)
# - Filter status (pass/skip reasons)
# - No actual trades placed
```

---

## Step 4: Deploy to Paper Trading

### Single Run (Test Once)

```powershell
python scripts/alpaca_rsi_bot.py --symbol TSLA
```

### Continuous Loop (Production Mode)

```powershell
# Run every 5 minutes (recommended for 5-min bars)
python scripts/alpaca_rsi_bot.py --symbol TSLA --loop --sleep-min 5
```

**Keep this terminal running!** Press `Ctrl+C` to stop.

---

## Strategy Parameters

The bot implements **all Phase 1+2 filters automatically**:

### Phase 1 Filters
- ✅ **Time-of-day**: Only trade 10:00 AM - 3:30 PM ET
- ✅ **Volatility regime**: Only trade when vol_z > 0.5
- ✅ **Volume confirmation**: Only trade when volm_z > 1.0

### Phase 2 Enhancements
- ✅ **Dynamic RSI thresholds**:
  - High volatility (vol_z > 1.0): RSI 30/70
  - Normal volatility: RSI 25/75
  - Low volatility (vol_z < -0.5): RSI 20/80
- ✅ **Trend filter**: Skip entry if price < EMA200 by >5%
- ✅ **Bollinger Band confirmation**: Only enter if bb_z < -0.8 (double oversold)

### Risk Management
- **Position size**: 0.25% of equity per trade
- **Min hold time**: 30 minutes
- **Stop loss**: 1x ATR below entry
- **Take profit**: 2x ATR above entry

---

## Monitoring

### Log File

The bot creates `alpaca_rsi_log.csv` with every decision:

```csv
timestamp,symbol,action,price,rsi,qty,note
2025-12-17T14:30:00Z,TSLA,skip_volume,250.50,23.45,0,No entry: insufficient volume (volm_z=0.82)
2025-12-17T14:35:00Z,TSLA,enter,248.20,22.10,10,✅ ENTERED 10 TSLA @ ~248.20 | ...
```

### Console Output

Each iteration logs:
- Current price, RSI, and all filter values
- **Skip reasons** (if any filter fails)
- **Entry confirmation** (if all filters pass)
- **Exit confirmation** (when RSI > threshold)

### Alpaca Dashboard

Monitor live at: https://app.alpaca.markets/paper/dashboard
- Positions
- Order history
- P&L tracking

---

## Expected Behavior (First Week)

Based on backtest (2020-2024, 5-min bars):

| Metric | Expected Range |
|--------|---------------|
| **Trades/Week** | 0-2 trades (very selective) |
| **Win Rate** | 70-75% |
| **Avg Win** | ~$10 per share |
| **Avg Loss** | ~$10-11 per share |
| **Sharpe (weekly)** | Varies (need 5-7 days minimum) |

**Note**: Phase 1+2 filters are VERY selective. Expect many days with **no trades** - this is normal and expected.

---

## Troubleshooting

### "Missing required env var ALPACA_API_KEY"

**Solution**: Re-run credential setup (Step 1)

### "No bars returned"

**Causes**:
- Market closed (check trading hours)
- Symbol invalid
- API rate limit (free tier: 200 requests/min)

**Solution**: 
```powershell
# Test with different feed
python scripts/alpaca_rsi_bot.py --symbol TSLA --feed sip
```

### "Not enough data after feature calculation"

**Cause**: Need ~200+ bars for EMA200

**Solution**: Wait 15-20 minutes on first run for data collection

### Bot enters too frequently

**Check**: Are filters actually applied?
- Look for filter skip messages in logs
- Verify vol_z > 0.5, volm_z > 1.0, etc.

**Debug**:
```powershell
# Add verbose logging
python scripts/alpaca_rsi_bot.py --symbol TSLA --loop 2>&1 | Tee-Object -FilePath debug.log
```

---

## Success Criteria (5-7 Day Evaluation)

After 5-7 days of paper trading, evaluate:

| Metric | Target | Action if Below |
|--------|--------|----------------|
| **Sharpe Ratio** | ≥ 1.0 | Tune filters or revert to Phase 1 only |
| **Win Rate** | ≥ 70% | Check for slippage/execution issues |
| **Profit Factor** | ≥ 0.9 | Verify costs match backtest (0.5 bps + 2 bps) |
| **Max Drawdown** | < 2% | Investigate regime change or overfitting |

---

## Next Steps

### If Paper Trading Successful (meets criteria above):
1. **Option A**: Deploy to live trading with small capital
2. **Option B**: Implement Phase 3 enhancements first
3. **Option C**: Run 2-3 more weeks for confidence

### If Paper Trading Underperforms:
1. Check logs for filter effectiveness
2. Compare slippage vs backtest assumptions
3. Consider parameter tuning or Phase 1-only reversion

---

## Emergency Stop

To stop the bot immediately:

1. Press `Ctrl+C` in the terminal
2. Log into Alpaca dashboard
3. Close any open positions manually
4. Cancel pending orders

---

## Support

- **Backtest Code**: See [scripts/backtest_phase1_comparison.py](scripts/backtest_phase1_comparison.py)
- **Strategy Details**: See [docs/RSI_ENHANCEMENTS.md](docs/RSI_ENHANCEMENTS.md)
- **Development Log**: See [docs/DEVELOPMENT_LOG.md](docs/DEVELOPMENT_LOG.md)

**Questions?** Review logs and filter logic in [scripts/alpaca_rsi_bot.py](scripts/alpaca_rsi_bot.py)
