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
  - Deployed to Alpaca paper trading via [scripts/alpaca_rsi_bot.py](../scripts/alpaca_rsi_bot.py)
- **Brain archived**: AUC 0.50-0.52 (no edge), code preserved in `ensemble/`, `experts/`, `models/`
- **Current champion**: RSI baseline + Phase 1+2 filters (see [RSI_ENHANCEMENTS.md](docs/RSI_ENHANCEMENTS.md))
- Comprehensive deployment guide: [DEPLOYMENT.md](DEPLOYMENT.md)
- CSV logging to `alpaca_rsi_log.csv`

## Next steps (Week 6 - Monitoring)
1) **Paper trading validation** (5-7 days): Monitor Sharpe ≥1.0, win rate ≥70%, compare vs backtest predictions
2) **Infrastructure setup**: Drift monitoring (feature distribution checks), alert system (kill-switch notifications), daily P&L reports
3) **Live trading decision** (Week 7): If paper successful → live deployment OR Phase 3 implementation (trailing stops, multi-timeframe, position scaling)
3) **Paper trading certification** (Week 5-6): Deploy best-performing RSI variant to Alpaca paper for 2+ weeks. Monitor Sharpe ≥1.3, win rate ≥58%, max DD <2%.
4) **Infrastructure Week** (Week 6): Build drift monitor (KS-test weekly), alert system (Slack webhook), daily P&L reports.
5) **Brain future**: Revisit ML only if alternative data sources become available (order flow, sentiment, options). Current brain archived as reference - AUC 0.50-0.52 with public OHLCV data is expected ceiling.

---

## See Also
- **[ARCHITECTURE.md](ARCHITECTURE.md)** — System design, module dependencies, data flow
- **[GETTING_STARTED.md](GETTING_STARTED.md)** — Setup, run backtest, paper trading
- **[DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md)** — Recent decisions and results
- **[PLAN.md](PLAN.md)** — 8-week roadmap with status
- **[INDEX.md](INDEX.md)** — Documentation navigation

---

**Last updated**: 2025-12-17
