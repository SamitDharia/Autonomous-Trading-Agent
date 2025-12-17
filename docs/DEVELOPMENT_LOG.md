# Development Log

Running diary of decisions, rationale, and results. Keep entries concise and dated.

---

## 2025-12-16
**Cleanup & Integration Sprint**
- Removed 1000+ unused files (QC data, old logs, duplicate code): 30% repo size reduction (3.1 GB → 2.2 GB)
- Integrated feature builder, risk guards, expert/brain ensemble into `algo.py`
- Consolidated documentation: PROJECT_BRIEF (master), DEVELOPMENT_LOG (this file), BOT_SPEC deprecated
- Status: algo.py ready for local backtest, brain parked until retraining

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
