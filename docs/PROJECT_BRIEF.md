# Project Brief

This document is the source of truth for the trading system. Keep it minimal, robust, and testable.

## Goal (single sentence)
Build a reliable, low‑maintenance trading bot that predicts whether the next 60 minutes will move enough (after costs) to justify a trade, sizes positions by confidence, and obeys strict risk limits.

## Rails
- Platform: QuantConnect (LEAN Cloud)
- Brokerage: Alpaca (paper first)
- Code: Python (single QC project to keep it simple)
- Storage: QC Object Store for models

## Universe & Horizon (start narrow)
- Symbols: TSLA only (Week 1–2), then expand to a small basket (e.g., AAPL, MSFT, SPY)
- Bars: 5‑minute bars
- Prediction horizon: next 60 minutes (12 bars)

## Features (inputs)
- Price/volume bars (OHLCV)
- Indicators: RSI(14), EMA(20/50/200) + slopes, MACD(12,26,9) + histogram, ATR(14), Bollinger z‑score(20,2)
- Regime: realized volatility (last 24 bars), time‑of‑day, day‑of‑week

## Models (stacked ensemble)
### Level‑1 experts (tiny, robust)
- RSI expert → probability of positive 60‑min return using RSI + z‑score + slope
- MACD expert → using MACD, signal, histogram, slope
- Trend expert → using EMA(20/50/200), crossovers, slopes
- (Add a Volatility expert later)

### Level‑2 brain (meta‑model)
- Logistic regression (initially) combining expert probabilities + 2 regime features (volatility, time‑of‑day).
- Output is final probability `p ∈ [0,1]`.

## Decision & Sizing
- Trade only if `|p − 0.5| ≥ 0.05` (minimum edge)
- Position size: volatility‑scaled (ATR‑based), capped at 1% of equity per position
- Orders: bracket (stop‑loss and take‑profit); minimum hold 15 minutes to reduce churn

## Risk (hard stops)
- Daily stop: −1% of equity → go flat, stop trading for the day
- Max concurrent positions: 1 (Week 1–2), later 3
- Kill‑switch: any data/model/broker error → flatten and pause

## Backtesting
- Include costs: fees + realistic spread/slippage
- Walk‑forward: train on past N months, validate on next month, roll forward
- Promote strategies only if they beat baselines (do‑nothing & MA crossover) after costs

## Rollout
- Backtest → Paper (1–2 weeks) → tiny Live only after stability
- One‑button rollback to last good version

## Repo / Project Layout (conceptual; QC can keep most in one file)
```
/docs/
  PROJECT_BRIEF.md
  NOTES.md                    # running diary: decisions, why, results
/features/
  feature_builder.py          # build indicator & regime features
/experts/
  rsi_expert.py               # load + predict_proba(features)
  macd_expert.py
  trend_expert.py
/ensemble/
  brain.py                    # load brain model; blend expert outputs + regime
/risk/
  position_sizing.py          # prob->size (ATR scale, caps)
  guards.py                   # daily stop, kill-switch checks
/models/
  rsi_expert.json             # saved tiny models (or .pkl)
  macd_expert.json
  trend_expert.json
  brain.pkl
/tests/
  test_features.py
  test_rsi_expert.py
  test_position_sizing.py
algo.py                       # QuantConnect main algorithm (wires it all)
```

On QuantConnect you can keep helpers inside `algo.py` to start. Upload the model files to QC Object Store and load them in `Initialize()`.

## Current status (Dec 2025)
- Skeleton algo runs end-to-end (indicators, brackets, daily stop, min hold). Brain disabled for trading (`use_brain = False`) so the RSI rule fires.
- Local/QC Web IDE backtests currently use bundled EURUSD minute data (May 2014) for fast iteration; TSLA remains the target equity once ready.
- Expert/brain JSON loaders work with QC Object Store (Byte[] fixed). Models are placeholders returning ~0.5; no real edge yet.

## Next steps to full ensemble
1) Train experts and brain offline: build features (RSI, MACD, EMAs, ATR, BB, regime), label 60-min forward returns, train/calibrate tiny models, save JSONs, upload to Object Store.
2) Enable ensemble: set `use_brain = True`, keep edge threshold (|p-0.5| >= 0.05), cap size at 1% with ATR scaling, test locally/QC.
3) Tune churn: adjust RSI/edge thresholds and size; ensure daily stop (-1%) respected; add guard for max concurrent positions (1).
4) Return to TSLA: switch back to TSLA Minute, longer date range; include realistic costs and slippage in backtests.
5) Paper trade on QC: use Alpaca Paper brokerage, tiny size, monitor a week; then consider live only after stable paper results.
