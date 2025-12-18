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
- **Phase 1+2 Complete & Deployed** (2025-12-17):
  - Backtest Results (2020-2024 TSLA): **Sharpe 0.80**, Win Rate 72.7%, Profit Factor 0.93
  - Phase 2 added +97% Sharpe improvement over Phase 1 (+0.39 absolute)
  - All 6 filters implemented: time-of-day, volatility, volume (Phase 1) + dynamic RSI, trend filter, BB confirmation (Phase 2)
  - Deployed to DigitalOcean cloud (Frankfurt, $6/month) running 24/7
  - Bot running via [scripts/alpaca_rsi_bot.py](../scripts/alpaca_rsi_bot.py)
- **Brain archived**: AUC 0.50-0.52 (no edge), code preserved in `ensemble/`, `experts/`, `models/`
- **Current champion**: RSI baseline + Phase 1+2 filters (see [RSI_ENHANCEMENTS.md](docs/RSI_ENHANCEMENTS.md))
- **Phase 3 designed**: Trailing stops + multi-TF RSI (target: Sharpe 1.0+), ready for implementation after Week 6 validation
- **Phase 4 infrastructure**: ML shadow logging (ml/shadow.py), disabled by default, zero-risk data collection
- Comprehensive deployment guides: [DEPLOYMENT.md](DEPLOYMENT.md) (local), [CLOUD_DEPLOYMENT.md](docs/CLOUD_DEPLOYMENT.md) (cloud)
- CSV logging to `alpaca_rsi_log.csv`

## Next steps (Week 7+ - Phase 3 Implementation)
1) **✅ Week 6 Complete**: First trade executed (Dec 18, 15:54 UTC), bracket orders validated, filters restored (vol_z 0.2, volm_z 0.3)
2) **Choose Phase 3 enhancement** (trailing stops OR multi-TF RSI):
   - **Option A**: Phase 3.1 Trailing Stops (ATR-based, reduce premature stop-outs, target: +0.1-0.2 Sharpe)
   - **Option B**: Phase 3.2 Multi-TF RSI (15-min confirmation, filter false signals, target: +0.1-0.15 Sharpe)
3) **Implement chosen enhancement**: Backtest → paper deploy → validate with 10+ trades
4) **Performance analysis**: Run analyze_recent_trades.py to verify metrics match backtest
5) **60-day certification** (Q1 2026): Paper run with Sharpe ≥1.0, max drawdown <2% before live deployment
6) **Brain future**: Shadow ML logging will collect 500+ trades over 6 months for future model evaluation

---

## See Also
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** — System design, module dependencies, data flow
- **[GETTING_STARTED.md](docs/GETTING_STARTED.md)** — Setup, run backtest, paper trading
- **[DEPLOYMENT.md](DEPLOYMENT.md)** — Local deployment guide
- **[CLOUD_DEPLOYMENT.md](docs/CLOUD_DEPLOYMENT.md)** — Cloud deployment guide (DigitalOcean, AWS, GCP)
- **[RSI_ENHANCEMENTS.md](docs/RSI_ENHANCEMENTS.md)** — Phase 1-4 roadmap and backtest results
- **[DEVELOPMENT_LOG.md](docs/DEVELOPMENT_LOG.md)** — Recent decisions and results
- **[PLAN.md](docs/PLAN.md)** — 8-week roadmap with status
- **[INDEX.md](docs/INDEX.md)** — Documentation navigation

---

**Last updated**: 2025-12-18
