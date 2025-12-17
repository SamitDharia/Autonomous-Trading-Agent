# Project Brief

**This document is the source of truth for the trading system.** Keep it minimal, robust, and testable.

## Goal
Build a reliable, low-maintenance trading bot that predicts whether the next 60 minutes will move enough (after costs) to justify a trade, sizes positions by confidence, and obeys strict risk limits.

## Key Non-Negotiables
- **Single symbol TSLA** (start), then expand to small basket (AAPL, MSFT, SPY)
- **Single timeframe**: 5-minute bars (prediction horizon: 60 minutes)
- **Risk engine is authoritative; ML is an opinion**
- **Kill-switches**: daily loss (-1%), data quality checks, broker errors → flatten and pause
- **QC for research/backtests only; live/paper runs locally** (avoid QC live fees)

## Rails
- Platform: QuantConnect (LEAN Cloud) for backtests/research only; local Lean/standalone for live/paper to avoid QC live fees
- Brokerage: Alpaca (paper first)
- Code: Python (single QC project to keep it simple)
- Storage: QC Object Store for model backups; local `models/` for live runs

## Universe & Horizon (start narrow)
- Symbols: TSLA only (Week 1–2), then expand to a small basket (e.g., AAPL, MSFT, SPY)
- Bars: 5-minute bars
- Prediction horizon: next 60 minutes (12 bars)

## Features (inputs)
- Price/volume bars (OHLCV)
- Indicators: RSI(14), EMA(20/50/200) + slopes, MACD(12,26,9) + histogram, ATR(14), Bollinger z-score(20,2)
- Regime: realized volatility (last 24 bars), time-of-day, day-of-week

## Models (stacked ensemble)
### Level-1 experts (tiny, robust)
- RSI expert → probability of positive 60-min return using RSI + z-score + slope
- MACD expert → using MACD, signal, histogram, slope
- Trend expert → using EMA(20/50/200), crossovers, slopes
- (Add a Volatility expert later)

### Level-2 brain (meta-model)
- Logistic regression (initially) combining expert probabilities + 2 regime features (volatility, time-of-day).
- Output is final probability `p ∈ [0,1]`.

## Decision & Sizing
- Trade only if `|p - 0.5| ≥ 0.05` (minimum edge)
- Position size: volatility-scaled (ATR-based), capped at 1% of equity per position
- Orders: bracket (stop-loss and take-profit); minimum hold 15 minutes to reduce churn

## Risk (hard stops)
- Daily stop: -1% of equity → go flat, stop trading for the day
- Max concurrent positions: 1 (Week 1–2), later 3
- Kill-switch: any data/model/broker error → flatten and pause

## Backtesting
- Include costs: fees + realistic spread/slippage
- Walk-forward: train on past N months, validate on next month, roll forward
- Promote strategies only if they beat baselines (do-nothing & MA crossover) after costs

## Rollout
- Backtest → Paper (1–2 weeks) → tiny Live only after stability
- One-button rollback to last good version

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
- Expert/brain JSON loaders work with QC Object Store (Byte[] fixed). Quick TSLA models have low AUC; brain is parked. RSI-only is the current champion (enter RSI<25, exit RSI>75, cap 0.25%, 30m hold).
- Live/paper is run locally via `scripts/alpaca_rsi_bot.py` (5m bars, RSI 25/75, ATR brackets 1x/2x, cap 0.25%, 30m hold). CSV logging to `alpaca_rsi_log.csv`.
- QC backtests with brain ON (latest models, edge 0.05–0.20, cap 0.0015–0.0020) have lost money/flat; AUC remains ~0.50–0.52. Brain not promoted.

## Next steps to full ensemble
1) Retrain experts and brain on longer TSLA history (e.g., 2018–2020+): build features/labels (60-min forward, include costs), train/calibrate models, save JSONs, upload to Object Store, and sync to local `models/`.
2) Re-enable ensemble: `use_brain = True`, strict edge gate (start with |p-0.5| >= 0.20+), cap 0.15–0.25%, long-only unless edge improves.
3) Compare against RSI champion; promote brain only if it beats RSI after costs.
4) Keep QC for research/backtests; run live/paper locally (Lean CLI or standalone Alpaca script) to avoid QC live fees.

---

## See Also
- **[ARCHITECTURE.md](ARCHITECTURE.md)** — System design, module dependencies, data flow
- **[GETTING_STARTED.md](GETTING_STARTED.md)** — Setup, run backtest, paper trading
- **[DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md)** — Recent decisions and results
- **[PLAN.md](PLAN.md)** — 8-week roadmap with status
- **[INDEX.md](INDEX.md)** — Documentation navigation

---

**Last updated**: 2025-12-17
