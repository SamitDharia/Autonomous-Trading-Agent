# Notes

Running diary of decisions, rationale, and results. Keep entries concise and dated.

## 2025-10-13
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
