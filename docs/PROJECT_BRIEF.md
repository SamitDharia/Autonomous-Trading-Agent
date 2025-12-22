# Project Brief

**This document is the source of truth for the trading system.** Keep it minimal, robust, and testable.

## Goal
Build a reliable, low-maintenance trading bot using RSI mean-reversion with proven filters (time-of-day, volatility, volume, trend) that captures oversold bounces while obeying strict risk limits.

**Current Approach**: Rule-based RSI strategy (Sharpe 0.80, 72.7% win rate) with fixed position sizing. Brain ensemble abandoned (AUC 0.50-0.52, no edge).

## Key Non-Negotiables
- **Single symbol TSLA** (current deployment), expand to 5-symbol basket in Growth Phase 1 (2026)
- **Single timeframe**: 5-minute bars (RSI strategy), 15-min confirmation (Phase 3.2)
- **Rule-based strategy is primary; ML is optional future filter** (Phase 4 shadow logging, Growth Phase 5 expectancy filter)
- **Risk engine is authoritative**: -1% daily stop, 0.25% position cap (current), bracket orders mandatory
- **Kill-switches**: daily loss (-1%), data quality checks, broker errors → flatten and pause
- **QC for research/backtests only; live/paper runs locally via Alpaca** (avoid QC live fees)

## Rails
- **Platform**: QuantConnect for backtests/research only; production runs locally via Alpaca API (no QC live fees)
- **Brokerage**: Alpaca paper trading (current deployment on DigitalOcean droplet)
- **Code**: Python 3.x (scripts/alpaca_rsi_bot.py for production, algo.py for QC backtests)
- **Storage**: Local CSV logging (alpaca_rsi_log.csv), future: JSONL for ML shadow data (ml/shadow.py)
- **Deployment**: DigitalOcean Frankfurt droplet ($6/month), 24/7 uptime, SSH access

## Universe & Horizon
**Current (RSI Phase 3)**:
- Symbol: TSLA only (deployed Dec 18, 2025)
- Bars: 5-minute primary, 15-minute confirmation (Phase 3.2 multi-TF)
- Hold time: Typically 30-60 minutes (median from backtest)

**Future (Growth Phase 1+)**:
- Symbols: Expand to 5-stock basket (TSLA, AAPL, MSFT, NVDA, SPY) with correlation monitoring
- Bars: Same 5-min/15-min approach
- Max concurrent: 2 positions if correlation < 0.75, else 1

## Features (inputs)
- Price/volume bars (OHLCV)
- Indicators: RSI(14), EMA(20/50/200) + slopes, MACD(12,26,9) + histogram, ATR(14), Bollinger z-score(20,2)
- Regime: realized volatility (last 24 bars), time-of-day, day-of-week

## Strategy (Current: RSI Mean-Reversion)
**Active Strategy**: Rule-based RSI with 8 filters (Phase 1+2+3)
- Entry: RSI(14) < dynamic threshold (20-30 based on volatility)
- Exit: RSI(14) > 75 or trailing stop (1.5 ATR)
- Filters: time-of-day, volatility z-score, volume z-score, trend (EMA200), Bollinger Bands, multi-timeframe RSI

**Phase 4 (Infrastructure Ready)**: Shadow ML Logging
- **Purpose**: Collect training data for future ML filter (Growth Phase 5)
- **Status**: Code implemented (ml/shadow.py), disabled by default (ML_SHADOW_ENABLED=false)
- **Approach**: Zero-risk passive logging - ML observes but never influences trades
- **Timeline**: Enable after Phase 3 validation (Jan 2026+), collect 500+ trades over 6 months
- **Future use**: Train expectancy model to filter low-quality setups (Growth Phase 5, 2027+)

**Archived: Brain Ensemble** (preserved in `ensemble/`, `experts/`, `models/` for reference)
- Level-1 experts: RSI, MACD, Trend (AUC 0.50-0.52 individually)
- Level-2 brain: Logistic regression meta-model (AUC 0.50-0.52)
- **Status**: Abandoned Dec 2025 - no edge over RSI baseline
- **Lesson**: Prediction accuracy (AUC) ≠ profitability. Rule-based filters (Sharpe 0.80) beat ML ensemble (AUC 0.50)

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
**Current approach (RSI strategy)**:
- Platform: QuantConnect (2020-2024 TSLA, 5-min bars)
- Costs: 0.5 bps commission + 2 bps slippage (realistic Alpaca modeling)
- Baseline comparison: RSI raw (Sharpe -0.11) vs Phase 1 (0.41) vs Phase 1+2 (0.80)
- Promote only if: Sharpe improvement ≥10% AND win rate ≥65%

**Future (ML approach)**:
- Walk-forward validation: Train on 6 months, test on next month, roll forward
- Out-of-sample requirement: ML expectancy must beat rule-based baseline + 0.3 Sharpe
- Data: Use shadow logs (500+ labeled trades minimum)

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
7) **Phase 4 ML Shadow Logging**: Enable after Phase 3 validation (Jan 2026+)
   - Set ML_SHADOW_ENABLED=true in production bot
   - Zero risk: ML logs features/outcomes but never influences trading
   - Collect 500+ trades over 6 months (estimated 50-100 trades by Jul 2026)
   - Goal: Train expectancy model for Growth Phase 5 filter (predict which setups to skip)

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
