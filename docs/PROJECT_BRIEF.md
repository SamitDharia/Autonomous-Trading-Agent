# Project Brief

**This document is the source of truth for the trading system.** Keep it minimal, robust, and testable.

## Goal
Build a reliable, low-maintenance trading bot using RSI mean-reversion with proven filters (time-of-day, volatility, volume, trend) that captures oversold bounces while obeying strict risk limits.

**Current Approach**: Rule-based RSI strategy (Sharpe 0.80, 72.7% win rate) with fixed position sizing. Brain ensemble abandoned (AUC 0.50-0.52, no edge).

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

## Strategy (Current: RSI Mean-Reversion)
**Active Strategy**: Rule-based RSI with 8 filters (Phase 1+2+3)
- Entry: RSI(14) < dynamic threshold (20-30 based on volatility)
- Exit: RSI(14) > 75 or trailing stop (1.5 ATR)
- Filters: time-of-day, volatility z-score, volume z-score, trend (EMA200), Bollinger Bands, multi-timeframe RSI

**Archived: Brain Ensemble** (preserved in `ensemble/`, `experts/`, `models/` for future research)
- Level-1 experts: RSI, MACD, Trend (AUC 0.50-0.52 individually)
- Level-2 brain: Logistic regression meta-model (AUC 0.50-0.52)
- **Status**: Abandoned Dec 2025 - no edge over RSI baseline
- **Future**: May revisit for Growth Phase 5 ML expectancy filter (2027+)

## Decision & Sizing
**Current (RSI Phase 3)**:
- Entry: RSI < dynamic threshold AND all 8 filters pass
- Position size: Fixed 0.25% equity cap (ultra-conservative)
- Orders: Bracket orders (1.5 ATR stop-loss, 2 ATR take-profit)
- Trailing stop: 1.5 ATR trail when profitable (Phase 3.1)
- Minimum hold: 30 minutes to reduce churn

**Archived (Brain approach)**:
- Trade only if `|p - 0.5| ≥ 0.05` (minimum edge)
- Position size: Volatility-scaled (ATR-based), capped at 1% equity

## Risk (hard stops)
- Daily stop: -1% of equity → go flat, stop trading for the day
- Max concurrent positions: 1 (current), 2-3 for multi-symbol expansion (Growth Phase 1+)
- Position cap: 0.25% equity per trade (current), 2% for aggressive growth strategy
- Kill-switch: any data/model/broker error → flatten and pause

## Backtesting
- Include costs: fees + realistic spread/slippage
- Walk-forward: train on past N months, validate on next month, roll forward
- Promote strategies only if they beat baselines (do-nothing & MA crossover) after costs

## Rollout
- Backtest → Paper (1–2 weeks) → tiny Live only after stability
- One-button rollback to last good version

## Repo / Project Layout
**Current (RSI Strategy)**:
```
/docs/                        # Documentation (source of truth: PROJECT_BRIEF.md)
/scripts/
  alpaca_rsi_bot.py           # Production bot (Phase 1+2+3) - ACTIVE
  analyze_recent_trades.py    # Performance analysis
  daily_health_check.ps1      # Automated monitoring
/features/
  feature_builder.py          # Indicator & regime features (for QC backtests)
/risk/
  position_sizing.py          # ATR-based sizing (archived brain approach)
  guards.py                   # Daily stop, kill-switch checks (used in QC backtests)
/ml/
  shadow.py                   # Shadow ML logging (Phase 4, disabled by default)
algo.py                       # QuantConnect backtest algorithm (Phase 1+2 reference)
```

**Archived (Brain Ensemble)** - preserved for future research:
```
/experts/                     # Level-1 expert models (rsi_expert.py, macd_expert.py, trend_expert.py)
/ensemble/                    # Level-2 brain meta-model (brain.py)
/models/                      # Trained model JSONs (brain.json, *_expert.json)
```

On QuantConnect: Use `algo.py` for backtests only. Upload model files to QC Object Store if needed for research.

## Current status (Dec 2025)
- **Phase 1+2+3 Deployed** (2025-12-18):
  - Backtest Results (2020-2024 TSLA): **Sharpe 0.80**, Win Rate 72.7%, Profit Factor 0.93
  - Phase 2 added +97% Sharpe improvement over Phase 1 (+0.39 absolute)
  - All 8 filters implemented:
    - Phase 1: time-of-day, volatility, volume
    - Phase 2: dynamic RSI, trend filter, BB confirmation
    - Phase 3: multi-timeframe RSI (15-min confirmation)
  - Phase 3 enhancements: ATR-based trailing stops (1.5x ATR trail)
  - Deployed to DigitalOcean cloud (Frankfurt, $6/month) running 24/7
  - Bot running via [scripts/alpaca_rsi_bot.py](../scripts/alpaca_rsi_bot.py) (PID 46592)
- **Brain archived**: AUC 0.50-0.52 (no edge), code preserved in `ensemble/`, `experts/`, `models/`
- **Current champion**: RSI baseline + Phase 1+2+3 (see [RSI_ENHANCEMENTS.md](RSI_ENHANCEMENTS.md))
- **Validation status**: Phase 3 deployed, awaiting market volatility (expected Jan 2026)
- **Phase 4 infrastructure**: ML shadow logging (ml/shadow.py), disabled by default, zero-risk data collection
- Comprehensive deployment guides: [DEPLOYMENT.md](../DEPLOYMENT.md) (local), [CLOUD_DEPLOYMENT.md](CLOUD_DEPLOYMENT.md) (cloud)
- CSV logging to `alpaca_rsi_log.csv`

## Next steps (Week 7+ - Phase 3 Validation)
1) **✅ Week 6 Complete**: First trade executed (Dec 18, 15:54 UTC), bracket orders validated, filters restored (vol_z 0.2, volm_z 0.3)
2) **✅ Phase 3.1+3.2 Deployed** (Dec 18, 18:24 UTC):
   - Phase 3.1: ATR-based trailing stops (1.5x ATR trail, breakeven protection)
   - Phase 3.2: Multi-timeframe RSI (require 15-min RSI < 50 for entry)
   - Both enhancements live on droplet (PID 46592)
3) **🔄 Holiday Period** (Dec 19 - Jan 3): Low volatility expected, zero trades likely
4) **Validation Period** (Jan 6-31, 2026): Collect 5-15 Phase 3 trades during TSLA catalysts:
   - Early Jan: Q4 delivery numbers
   - Late Jan: Q4 earnings (high volatility week)
5) **Performance analysis**: Run analyze_recent_trades.py after 5+ trades collected
6) **60-day certification** (Q1 2026): Paper run with Sharpe ≥1.0, max drawdown <2% before live deployment
7) **Brain future**: Enable shadow ML logging after Phase 3 validation (collect 500+ trades over 6 months)

## Maximum Returns Path (Long-term Vision)
**Target**: 12-22% annual returns through aggressive scaling (see [BACKLOG.md](BACKLOG.md#-maximum-returns-path-aggressive-growth-strategy))

**Phased approach** (2026-2027):
- **Growth Phase 1** (Feb-Mar 2026): Multi-symbol expansion (5 stocks) → 2-4% annual return
- **Growth Phase 2** (Mar-Apr 2026): 2% position sizing → 8-12% annual return
- **Growth Phase 3** (May-Jun 2026): Loosen filters (high risk) → 12-16% annual return
- **Growth Phase 4** (Aug-Nov 2026): Add momentum strategy → 16-20% annual return
- **Growth Phase 5** (2027): ML expectancy filter → 18-22% annual return

**Capital requirements**: $5K minimum (realistic), $10K+ recommended

**Probability of success**: Conservative case (Growth Phases 1-2 only) = 70% confidence for 8-12% returns

**Note**: This is separate from core RSI Enhancement Phases (1-4). Maximum Returns Path begins AFTER RSI Phase 3 validation (Jan 2026+).

Full details including risk management, validation gates, correlation risk, and capital scaling projections are documented in BACKLOG.md

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

**Last updated**: 2025-12-22
