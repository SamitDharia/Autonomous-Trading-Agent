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
- **Brain retraining completed**: Tested multiple configurations (H=6/12/24, 2018-2024 data, LightGBM 800 trees). Result: AUC 0.50-0.52 (coin-flip). **Decision: Keep RSI baseline as champion** - brain has no predictive edge over simple mean-reversion.
- **RSI baseline Phase 1 enhancements in progress**: Implemented time-of-day filter (10:00-15:30), volume confirmation (volm_z > 1.0), volatility regime (vol_z > 0.5). Next: backtest comparison (2020-2024 TSLA) to measure impact.
- Skeleton algo runs end-to-end (indicators, brackets, daily stop, min hold). Brain path remains in code but disabled (`use_brain = False`).
- Live/paper is run locally via `scripts/alpaca_rsi_bot.py` (5m bars, RSI 25/75, ATR brackets 1x/2x, cap 0.25%, 30m hold). CSV logging to `alpaca_rsi_log.csv`.
- Models archived in `models/*.json` for reference. Focus shifted from ML prediction to RSI strategy optimization.

## Next steps (RSI optimization focus)
1) **Phase 1 backtest comparison** (Week 4): Run 2020-2024 TSLA backtest comparing baseline RSI vs. Phase 1 enhanced (time/volume/volatility filters). Target: +10-20% Sharpe improvement.
2) **Phase 2 implementation** (Week 5): Add dynamic RSI thresholds (volatility-adaptive), trend filter (EMA200), Bollinger Band confirmation. Backtest each enhancement individually.
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
