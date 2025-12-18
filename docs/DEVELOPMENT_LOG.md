# Development Log

Running diary of decisions, rationale, and results. Keep entries concise and dated.

---

## 2025-12-18
**Week 6: Cloud Deployment & Phase 4 ML Infrastructure**
- **Cloud Deployment**: Bot successfully deployed to DigitalOcean droplet (Frankfurt, $6/month)
  - Created [CLOUD_DEPLOYMENT.md](CLOUD_DEPLOYMENT.md) guide (AWS, DigitalOcean, Google Cloud)
  - Fixed timezone bug: Bot was using UTC instead of US/Eastern for time_of_day filter
  - Deployed bot as background process (nohup), running 24/7 since Dec 17
- **Temporary Filter Loosening**: Reduced vol_z (0.5→0.2) and volm_z (1.0→0.3) thresholds
  - **Rationale**: Strict filters = 1 trade per 6 weeks; loosened to get 2-5 trades this week for execution validation
  - Plan: Revert to strict levels after bracket orders confirmed working
- **Phase 4 Shadow ML Logging**: Implemented zero-risk ML infrastructure
  - Created `ml/shadow.py` with lazy imports + try/except wrapper (impossible to break execution)
  - Added shadow hook in `alpaca_rsi_bot.py` (disabled by default, enable via ML_SHADOW_ENABLED env var)
  - Log-first approach: Collect 500+ labeled trades before training any models
  - Market-state features only (RSI, vol_z, volm_z, etc.) - no bot-performance metrics
  - Documented in [RSI_ENHANCEMENTS.md](RSI_ENHANCEMENTS.md) Phase 4 + [ml/README.md](../ml/README.md)
- **Phase 3 Planning**: Designed trailing stops + multi-TF RSI (no implementation yet)
  - [PHASE3_TRAILING_STOP_DESIGN.md](PHASE3_TRAILING_STOP_DESIGN.md): ATR-based trailing stops via order.replace()
  - [PHASE3_MULTI_TF_RSI_DESIGN.md](PHASE3_MULTI_TF_RSI_DESIGN.md): 15-min RSI confirmation (5m <25, 15m <50)
  - Created `scripts/analyze_recent_trades.py` for post-trade analysis
- **Status**: Bot running on droplet, waiting for first trade execution (Dec 18, 10 AM ET market open)
- **Decision**: Wait for execution validation before implementing Phase 3 enhancements

## 2025-12-17
**Phase 2 Validation & Deployment**
- Completed Phase 2 backtest (2020-2024 TSLA, 5-min bars)
  - Combined Phase 1+2: **Sharpe 0.80** (vs Phase 1: 0.41, Baseline: -0.11)
  - Win rate: **72.7%** (vs Phase 1: 66.7%, Baseline: 64.3%)
  - Trade count: 44 (vs Phase 1: 48, Baseline: 168) - quality over quantity
  - Profit factor: 0.93 (nearly breakeven on average trade basis)
- **Key insight**: Phase 2 dynamic logic (volatility-adaptive thresholds, trend filter, BB confirmation) added +97% Sharpe improvement
- Updated `scripts/alpaca_rsi_bot.py` with all Phase 1+2 enhancements
- Created comprehensive deployment guide ([DEPLOYMENT.md](../DEPLOYMENT.md))
- **Status**: Phase 1+2 strategy deployed to Alpaca paper trading, monitoring 5-7 days
- **Decision**: RSI baseline with Phase 1+2 filters is champion (brain remains disabled)

## 2025-12-16
**Cleanup & Integration Sprint**
- Removed 1000+ unused files (QC data, old logs, duplicate code): 30% repo size reduction (3.1 GB → 2.2 GB)
- Integrated feature builder, risk guards, expert/brain ensemble into `algo.py`
- Consolidated documentation: PROJECT_BRIEF (master), DEVELOPMENT_LOG (this file), BOT_SPEC deprecated
- Completed brain retraining: extended data (2018-2024), horizon optimization (H=6/12/24), LightGBM tuning
  - **Results**: AUC 0.50-0.52 across all configurations (no edge achieved)
  - **Analysis**: Market efficiency ceiling with public OHLCV data
  - **Decision**: Brain not promoted, RSI baseline remains champion
- Created RSI enhancement roadmap (Phase 1-3) in [RSI_ENHANCEMENTS.md](RSI_ENHANCEMENTS.md)
- Implemented Phase 1 filters (time-of-day, volatility, volume)
- Phase 1 backtest: Sharpe -0.09 → 0.41 (turned losing strategy profitable)
- Implemented Phase 2 enhancements (dynamic thresholds, trend filter, BB confirmation)
- Status: algo.py ready for deployment with Phase 1+2, brain archived

## 2025-12-15
**Workflow & Alpaca Setup**
- Initialized repository structure and created the Project Brief.

## 2025-11-09
- Wired expert/brain JSON loaders; enabled brain in algo.
- Verified local backtest and paper dry-run with Alpaca keys.
- Added sample model weights and passing tests (2).

## 2025-12-14
- Enabled RSI dummy rule path (`use_brain = False`) to force trades for local/QC backtests.
- Switched local/QC backtest asset to EURUSD (May 2014) to use bundled data.
- Fixed Object Store Byte[] decoding in expert/brain loaders for QC cloud/Web IDE.
- Ran QC Web IDE backtest successfully; small PnL, lots of trades due to simple RSI thresholds.
- Trained quick TSLA models (low AUC); decided to park them and keep RSI-only as champion.
- Tightened brain path (edge 0.20, cap 0.15%, long-only), then turned brain off; RSI baseline uses bands 25/75, cap 0.25%, 30m hold.
- Backtests now mostly flat/slightly down; plan to retrain models next week.

## 2025-12-15
- Chose workflow: QC for research/backtests/retraining only; live/paper runs locally (Lean CLI or standalone). Avoid QC live fees.
- Standalone Alpaca bot (`scripts/alpaca_rsi_bot.py`) live path: RSI 25/75, 5m bars, cap 0.25%, 30m hold, ATR brackets 1x stop / 2x TP, CSV logging enabled.
- Models (RSI/MACD/Trend/Brain) stored locally and in QC Object Store; brain remains off until retrained with better AUC vs RSI baseline.
- Next retrain plan: use QC notebook to build 2018–2020+ TSLA set, include costs, train experts/brain, export JSONs, sync to local `models/`, then evaluate brain vs RSI before enabling.

## 2025-12-14 (eve) – brain test runs
- Trained updated models (2018–2022, cost-aware label, filters) but AUCs stayed ~0.50–0.52. JSONs updated in `models/`.
- QC backtests with brain ON, edge 0.05–0.20 and cap 0.0015–0.0020 all lost money/flat; no clear edge. RSI baseline remains stronger.
- Current QC code: brain ON, edge gate 0.05, cap 0.0020 (for testing). If blank backtest, loosen edge; if too many losing trades, tighten or set `use_brain=False` to revert to RSI baseline.

## 2025-12-17
**Brain Retraining: Final Results & Decision**
- Completed comprehensive brain retraining with extended data (2018-2024, 6 years)
- Improved hyperparameters: LightGBM 800 trees, lr=0.03, regularization
- Tested multiple configurations (H=6/12/24, 3 cost thresholds, extended date range)
- **Results**: All configurations yielded AUC ~0.50-0.52 (coin-flip performance)
  - H=12: RSI 0.5029, MACD 0.5049, Trend 0.5089, Brain 0.5094
  - H=24: RSI 0.5029, MACD 0.5049, Trend 0.5089, Brain 0.5077
  - Horizon sweep showed marginal improvements (H=24 0.5275) but this was single-split overfitting; time-series CV revealed true performance ~0.50
- **Analysis**: Public technical indicators on liquid stocks (TSLA) are heavily arbitraged. AUC 0.50-0.52 is the expected ceiling with OHLCV-derived features. Real edge requires alternative data (order flow, sentiment, options) or microstructure features.
- **Decision**: Keep RSI baseline as champion (`use_brain=False`). Brain shows no predictive edge over simple mean-reversion at extremes.
- **Rationale**: RSI baseline works due to strict risk management (ATR brackets, 30m hold, daily stop, 0.25% cap), not prediction. Focus shifts to infrastructure (drift monitor, alerts) and RSI strategy enhancements.
- Models archived in `models/*.json` for reference; brain path remains in code but disabled by default.

---

## See Also
- **[PROJECT_BRIEF.md](PROJECT_BRIEF.md)** — System goals and current status
- **[PLAN.md](PLAN.md)** — 8-week roadmap (Week 4 in progress)
- **[BACKLOG.md](BACKLOG.md)** — Open items and priorities
- **[INDEX.md](INDEX.md)** — Documentation navigation

---

**Last updated**: 2025-12-18
