# ML Shadow-Mode Package

**Status**: Implemented, Disabled by Default  
**Purpose**: Collect training dataset for future ML research (Phase 4)  
**Risk Level**: ZERO (lazy imports, try/except wrapper, never impacts trade execution)

## Overview

This package provides optional ML integration for the Alpaca RSI bot. It operates in "shadow mode" - logging features and trade context without affecting live trading decisions.

**Design Philosophy**:
- 📊 **Log-first approach**: Collect 500+ labeled trades before training any models
- 🛡️ **Zero-risk integration**: Impossible to break trade execution (lazy imports + try/except)
- 🎯 **Market-state features only**: No bot-performance metrics (prevents overfitting)
- 🔄 **Completely reversible**: Disable via environment variable, no code changes

## Quick Start

### Enable Shadow Logging

```bash
# Set environment variable (add to ~/.bashrc or export before bot start)
export ML_SHADOW_ENABLED=true

# Restart bot
kill $(cat bot.pid)
nohup .venv/bin/python scripts/alpaca_rsi_bot.py --symbol TSLA --loop > bot.log 2>&1 &
echo $! > bot.pid

# Verify logging working (wait 5+ minutes for first trade signal)
tail ml_shadow_log.jsonl
```

### Configuration Options

```bash
# Enable/disable shadow-mode logging (default: false)
export ML_SHADOW_ENABLED=true

# Log-only mode - don't run predictions (default: true, safe for Phase 4.1)
export ML_SHADOW_LOG_ONLY=true

# Run ML predictions if model exists (default: false, for Phase 4.2+)
export ML_SHADOW_PREDICT=false

# Log file path (default: ml_shadow_log.jsonl)
export ML_SHADOW_LOG_PATH=ml_shadow_log.jsonl

# Model path for predictions (default: models/shadow_model.pkl)
export ML_SHADOW_MODEL_PATH=models/shadow_model.pkl
```

## File Structure

```
ml/
├── __init__.py          # Package marker
├── shadow.py            # shadow_log() function + config
└── README.md            # This file

# Generated files (when enabled):
ml_shadow_log.jsonl      # Training dataset (features + trade context)
ml_predictions.jsonl     # ML predictions (Phase 4.2+)
ml_shadow_errors.log     # Error log (if shadow logging fails)
```

## Log Schema

### ml_shadow_log.jsonl

One JSON object per line (JSONL format):

```json
{
  "signal_id": "trade_20251217_103045",
  "timestamp": "2025-12-17T10:30:45.123456",
  "symbol": "TSLA",
  "side": "buy",
  "entry_ref_price": 245.30,
  "qty": 12,
  "planned_tp": 247.85,
  "planned_sl": 243.75,
  "max_hold_bars": 6,
  "features": {
    "rsi": 23.4,
    "atr": 2.55,
    "vol_z": 0.82,
    "volm_z": 1.23,
    "ema200_rel": -2.3,
    "bb_z": -0.95,
    "time_of_day": 10.5
  }
}
```

### Feature Definitions

| Feature | Description | Example | Range |
|---------|-------------|---------|-------|
| `rsi` | RSI(14) value at signal time | 23.4 | 0-100 (oversold <25, overbought >75) |
| `atr` | Average True Range (volatility) | 2.55 | >0 (higher = more volatile) |
| `vol_z` | Volatility z-score (20-bar) | 0.82 | ~-3 to +3 (>0.5 = high-vol regime) |
| `volm_z` | Volume z-score (20-bar) | 1.23 | ~-3 to +3 (>1.0 = volume spike) |
| `ema200_rel` | Distance from EMA200 in % | -2.3 | ~-10 to +10 (negative = downtrend) |
| `bb_z` | Bollinger Band z-score | -0.95 | ~-2 to +2 (<-0.8 = near lower band) |
| `time_of_day` | Hour.decimal (ET timezone) | 10.5 | 10.0-15.5 (10 AM - 3:30 PM) |

**Why These Features?**:
- ✅ **Market-state only**: Independent of bot's past performance
- ✅ **Available pre-trade**: All computed before order submission
- ✅ **No leakage**: Can't "see the future" when logging
- ❌ **NO bot-performance metrics**: No recent_sharpe, recent_win_rate, equity_curve (causes overfitting)

## Usage Example

### In Trading Bot Code

```python
from datetime import datetime

# ... (calculate features, filters pass, compute qty/TP/SL)

# Shadow-mode logging (Phase 4)
try:
    from ml.shadow import is_enabled, shadow_log
    
    if is_enabled():
        ml_prediction = shadow_log(
            signal_id=f"trade_{datetime.now():%Y%m%d_%H%M%S}",
            timestamp=datetime.now(),
            symbol="TSLA",
            side="buy",
            entry_ref_price=245.30,
            qty=12,
            planned_tp=247.85,
            planned_sl=243.75,
            max_hold_bars=6,  # 30 min / 5 min bars
            features={
                "rsi": 23.4,
                "atr": 2.55,
                "vol_z": 0.82,
                "volm_z": 1.23,
                "ema200_rel": -2.3,
                "bb_z": -0.95,
                "time_of_day": 10.5,
            },
        )
        
        # If ML prediction returned (Phase 4.2+), log it but DON'T use it
        if ml_prediction:
            print(f"[ML SHADOW] {ml_prediction['ml_signal']} "
                  f"(prob={ml_prediction['ml_prob']:.4f}) - LOGGING ONLY")
except Exception as e:
    # CRITICAL: ML must never break trade execution
    print(f"[ML SHADOW WARNING] {e} - continuing with trade")

# Trade executes normally regardless of ML
api.submit_order(...)
```

## Safety Guarantees

### 1. Lazy Imports
```python
# ml.shadow only imported if ML_SHADOW_ENABLED=true
try:
    from ml.shadow import is_enabled, shadow_log
    if is_enabled():
        # ... logging code
except:
    pass  # Module not found? Continue silently
```

**Result**: Zero overhead when disabled (default state)

### 2. Try/Except Wrapper
```python
def shadow_log(...):
    try:
        # ... log to file
    except Exception as e:
        # Log error, never raise
        with open("ml_shadow_errors.log", "a") as f:
            f.write(f"{datetime.now()} | ERROR: {e}\n")
        return None
```

**Result**: Any exception caught and logged, trade continues normally

### 3. No Decision Impact
- ML predictions (if computed) are **logged only**
- Rule-based filters are **sole decision-makers**
- Even if ML says "REJECT", trade still executes (shadow-mode)

**Result**: ML can never block profitable trades or force losing trades

## Training Dataset Preparation (Phase 4.1)

After collecting 500+ trades, join shadow logs with actual outcomes:

```python
import pandas as pd
import json

# Load shadow logs (features at decision time)
with open("ml_shadow_log.jsonl") as f:
    shadow_data = [json.loads(line) for line in f]
shadow_df = pd.DataFrame(shadow_data)

# Load actual trade outcomes
trade_df = pd.read_csv("alpaca_rsi_log.csv")
entries = trade_df[trade_df["action"] == "enter"].copy()
exits = trade_df[trade_df["action"] == "exit"].copy()

# Match entries to exits by timestamp proximity
# ... (implementation details when ready to train)

# Calculate PnL for each trade
# ... 

# Label: 1 if profitable, 0 if loss
labeled_df["label"] = (labeled_df["pnl"] > 0).astype(int)

# Save training dataset
labeled_df.to_csv("ml_training_dataset.csv", index=False)
print(f"Training dataset: {len(labeled_df)} labeled trades")
print(f"Win rate: {labeled_df['label'].mean():.1%}")
```

## Model Training (Phase 4.2, Optional)

```python
import lightgbm as lgb
from sklearn.model_selection import TimeSeriesSplit

# Load labeled dataset
df = pd.read_csv("ml_training_dataset.csv")

# Extract features
feature_cols = ["rsi", "atr", "vol_z", "volm_z", "ema200_rel", "bb_z", "time_of_day"]
X = df[feature_cols]
y = df["label"]

# Walk-forward validation
tscv = TimeSeriesSplit(n_splits=5)
for train_idx, test_idx in tscv.split(X):
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    
    model = lgb.LGBMClassifier(max_depth=3, n_estimators=100)
    model.fit(X_train, y_train)
    
    # Evaluate on out-of-sample test set
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    # ... (calculate expectancy, not just AUC)

# Save final model
import pickle
with open("models/shadow_model.pkl", "wb") as f:
    pickle.dump(model, f)
```

## Go/No-Go Decision Criteria (Phase 4.4)

After shadow-mode prediction testing (200+ trades), compare:

```python
# Load shadow predictions
with open("ml_predictions.jsonl") as f:
    preds = [json.loads(line) for line in f]
pred_df = pd.DataFrame(preds)

# Join with actual outcomes
results = pred_df.merge(outcomes_df, on="signal_id")

# Compare expectancy
ml_approved = results[results["ml_signal"] == "APPROVE"]
ml_rejected = results[results["ml_signal"] == "REJECT"]

approved_expectancy = ml_approved["pnl"].mean()
rejected_expectancy = ml_rejected["pnl"].mean()
baseline_expectancy = results["pnl"].mean()

# Go/No-Go decision
if approved_expectancy > baseline_expectancy + 2 * results["pnl"].std():
    print("✅ PROMOTE: ML improves expectancy significantly")
elif rejected_expectancy < -5.0:
    print("✅ PROMOTE: ML identifies bad trades (use as veto filter)")
else:
    print("❌ ABANDON: ML adds no value, stick with rule-based filters")
```

**Critical**: Use **expectancy** (avg PnL per trade), NOT AUC. Brain model failed at AUC 0.50 despite clean data because AUC doesn't correlate with trading profit.

## Troubleshooting

### Shadow logging not working

```bash
# Check if enabled
echo $ML_SHADOW_ENABLED  # Should show "true"

# Check for errors
cat ml_shadow_errors.log

# Check bot logs
tail bot.log | grep "ML SHADOW"
```

### Log file empty

- Wait 5+ minutes after bot start (5-min bar checks)
- Filters may be rejecting all signals (check `tail alpaca_rsi_log.csv`)
- Verify bot actually running: `ps aux | grep alpaca_rsi_bot`

### Import errors

```bash
# Verify ml package exists
ls -la ml/
# Should see: __init__.py, shadow.py, README.md

# Test import manually
.venv/bin/python -c "from ml.shadow import shadow_log; print('OK')"
```

## See Also

- [RSI_ENHANCEMENTS.md](../docs/RSI_ENHANCEMENTS.md) - Phase 4 detailed documentation
- [alpaca_rsi_bot.py](../scripts/alpaca_rsi_bot.py) - Trading bot with shadow hook
- [DEVELOPMENT_LOG.md](../docs/DEVELOPMENT_LOG.md) - Implementation history
