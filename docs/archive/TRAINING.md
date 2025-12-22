⚠️ **DEPRECATED - December 2025**

This document describes the brain ensemble approach, which has been **abandoned** as of December 2025.
- **Reason**: Brain AUC remained at 0.50-0.52 (no better than random) across all tuning attempts
- **Current Champion**: RSI baseline (no ML) with Sharpe 0.80, win rate 72.7%
- **Archived**: For historical reference only
- **Active Documentation**: See docs/PROJECT_BRIEF.md and docs/BACKLOG.md for current approach

---

# Training the experts and brain (QC Research notebook)

Use QuantConnect only for research/retraining; keep live/paper local. This notebook flow lets you retrain and then copy the JSONs into your local `models/` folder.

## Quick steps (repeatable)
1) In QC, open the ATA project → add/open `research.ipynb`.
2) Paste and run the code below (run all cells). It:
   - Pulls TSLA minute data (2018-2024, 6 years for better regime coverage).
   - Resamples to 5-minute bars.
   - Builds richer features/labels (cost-aware 60-minute forward return, includes lags + cyclical time).
   - Trains LightGBM experts (RSI, MACD, Trend) with improved hyperparameters, exports logistic proxies.
   - Saves JSONs to `output/` and prints them so you can copy/paste into local files.
   - **Auto-checks promotion criteria: AUC ≥ 0.55 and brain > max(experts)**.
3) Download from `output/` or copy the printed JSON blobs into your local `models/` files.
4) Backtest locally or in QC with `use_brain=True` (edge gate ≥ 0.15, cap 0.20%, long-only). Promote only if it beats RSI after costs.

Note: `train_experiments.py` additionally writes a runtime-ready brain to `bot/brains/TSLA_1h/brain_latest.json` and timestamps copies (see `bot/brains/TSLA_1h/brain_schema_v1.json`). The runtime loader (`bot/src/model/brain_loader.py`) validates the brain schema and checks feature hash parity.

## Notebook code (paste and run)

Note: I added `qc org wkspc dir/ATA/train_experiments.py` which mirrors this notebook and is runnable in QuantConnect Research (or locally after exporting minute data to `data/TSLA_1min.csv`). You can open that file in the QC Code Editor and run it directly, or paste this cell into `research.ipynb`.
```python
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import TimeSeriesSplit
import lightgbm as lgb

qb = QuantBook()
sym = qb.AddEquity("TSLA", Resolution.Minute).Symbol
# Extended to 2024 for more regimes and better generalization
hist = qb.History(sym, start=datetime(2018,1,1), end=datetime(2024,1,1), resolution=Resolution.Minute)

# Resample to 5-minute
df = hist.loc[sym].reset_index().rename(columns={"time":"timestamp"})
df = df.set_index("timestamp").sort_index()
df5 = pd.DataFrame({
    "open": df["open"].resample("5min").first(),
    "high": df["high"].resample("5min").max(),
    "low": df["low"].resample("5min").min(),
    "close": df["close"].resample("5min").last(),
    "volume": df["volume"].resample("5min").sum(),
}).dropna()

# Base indicators & helpers

def rsi(series, period=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    roll_up = up.ewm(alpha=1/period, adjust=False).mean()
    roll_down = down.ewm(alpha=1/period, adjust=False).mean() + 1e-9
    rs = roll_up / roll_down
    return 100 - (100 / (1 + rs))

def macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    line = ema_fast - ema_slow
    sig = line.ewm(span=signal, adjust=False).mean()
    hist = line - sig
    return line, sig, hist

def atr(df, period=14):
    hl = df["high"] - df["low"]
    hc = (df["high"] - df["close"].shift()).abs()
    lc = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, adjust=False).mean()

close = df5["close"]
ret1 = close.pct_change()
ema20 = close.ewm(span=20, adjust=False).mean()
ema50 = close.ewm(span=50, adjust=False).mean()
ema200 = close.ewm(span=200, adjust=False).mean()
rsi14 = rsi(close)
rsi_slope = rsi14.diff()
macd_line, macd_sig, macd_hist = macd(close)
macd_slope = macd_line.diff()
atr14 = atr(df5)
atr_pct = atr14 / close
bb_mid = close.rolling(20).mean()
bb_std = close.rolling(20).std()
bb_z = (close - bb_mid) / (2 * bb_std + 1e-9)
vol20 = ret1.rolling(20).std()
vol_z = (vol20 - vol20.rolling(100).mean()) / (vol20.rolling(100).std() + 1e-9)
vol_z = vol_z.fillna(0)
volm_z = (df5["volume"] - df5["volume"].rolling(20).mean()) / (df5["volume"].rolling(20).std() + 1e-9)
volm_z = volm_z.fillna(0)
time_of_day = df5.index.hour + df5.index.minute/60.0

# Add small, high-signal extras: lagged features and cyclical time encoding
rsi_lag1 = rsi14.shift(1)
rsi_lag2 = rsi14.shift(2)
macd_slope_ewm = macd_line.ewm(span=5, adjust=False).mean().diff()
time_sin = np.sin(2 * np.pi * time_of_day / 24.0)
time_cos = np.cos(2 * np.pi * time_of_day / 24.0)
overnight_ret = df5["open"].pct_change()  # crude proxy; keep for experiments

# Consolidate features
df_feat = pd.DataFrame({
    "rsi": rsi14,
    "rsi_lag1": rsi_lag1,
    "rsi_lag2": rsi_lag2,
    "rsi_slope": rsi_slope,
    "macd": macd_line,
    "macd_sig": macd_sig,
    "macd_hist": macd_hist,
    "macd_slope": macd_slope,
    "macd_slope_ewm": macd_slope_ewm,
    "ema20": ema20,
    "ema50": ema50,
    "ema200": ema200,
    "ema20_rel": close/ema20 - 1,
    "ema50_rel": close/ema50 - 1,
    "ema200_rel": close/ema200 - 1,
    "atr": atr14,
    "atr_pct": atr_pct,
    "bb_z": bb_z,
    "ret1": ret1,
    "vol20": vol20,
    "vol_z": vol_z,
    "volm_z": volm_z,
    "time_of_day": time_of_day,
    "time_sin": time_sin,
    "time_cos": time_cos,
    "overnight_ret": overnight_ret,
})

# Filters: drop very noisy/illiquid bars
df_feat = df_feat[(df_feat["atr_pct"] <= 0.02) & (df_feat["volm_z"] > -1) & (df_feat["volm_z"] < 5)]

# Label: forward horizon (configurable) > cost threshold
# Using 2-hour horizon (24 * 5-min bars) based on sweep results showing H=24 → AUC 0.5275
H = 24
cost_bps = 0.001  # 10 bps
fwd = close.shift(-H)
ret_fwd = (fwd - close) / close

# Drop rows with NaNs after adding lags
df_feat["label"] = (ret_fwd > cost_bps).astype(int)
df_feat = df_feat.dropna()

# Time-series CV helper

def time_series_cv_auc(clf, X, y, n_splits=5):
    tscv = TimeSeriesSplit(n_splits=n_splits)
    aucs = []
    for train_idx, test_idx in tscv.split(X):
        Xtr, Xte = X.iloc[train_idx], X.iloc[test_idx]
        ytr, yte = y.iloc[train_idx], y.iloc[test_idx]
        clf.fit(Xtr, ytr)
        p = clf.predict_proba(Xte)[:, 1]
        aucs.append(roc_auc_score(yte, p))
    return float(np.mean(aucs)), aucs

# Quick experiment choice: Logistic for deployment; LightGBM for testing
USE_LGBM = True

# Feature subsets for tiny experts
rsi_feats = ["rsi", "rsi_lag1", "rsi_lag2", "rsi_slope", "bb_z"]
macd_feats = ["macd", "macd_sig", "macd_hist", "macd_slope", "macd_slope_ewm"]
trend_feats = ["ema20_rel", "ema50_rel", "ema200_rel"]

X = df_feat.drop(columns=["label"])
y = df_feat["label"]

# Diagnostics: print class balance
print(f"Dataset size: {len(y)} samples")
print(f"Class balance: {y.sum()} positives ({y.mean()*100:.2f}%), {len(y)-y.sum()} negatives ({(1-y.mean())*100:.2f}%)")
print(f"Date range: {df_feat.index.min()} to {df_feat.index.max()}")

# Build and evaluate experts with time-series CV
if USE_LGBM:
    def mk_lgb():
        # Increased trees + lower learning rate for better generalization
        return lgb.LGBMClassifier(n_estimators=800, learning_rate=0.03, max_depth=4, 
                                  min_child_samples=50, subsample=0.8, colsample_bytree=0.8,
                                  random_state=42)

    rsi_clf = mk_lgb()
    macd_clf = mk_lgb()
    trend_clf = mk_lgb()

    rsi_mean_auc, rsi_fold_aucs = time_series_cv_auc(rsi_clf, X[rsi_feats], y)
    macd_mean_auc, macd_fold_aucs = time_series_cv_auc(macd_clf, X[macd_feats], y)
    trend_mean_auc, trend_fold_aucs = time_series_cv_auc(trend_clf, X[trend_feats], y)

    # Fit on full training portion (80%) to produce expert probabilities for brain training
    split_idx = int(len(X) * 0.8)
    X_tr_final, X_val_final = X.iloc[:split_idx], X.iloc[split_idx:]
    y_tr_final, y_val_final = y.iloc[:split_idx], y.iloc[split_idx:]

    rsi_clf.fit(X_tr_final[rsi_feats], y_tr_final, eval_set=[(X_val_final[rsi_feats], y_val_final)], callbacks=[lgb.early_stopping(50), lgb.log_evaluation(0)])
    macd_clf.fit(X_tr_final[macd_feats], y_tr_final, eval_set=[(X_val_final[macd_feats], y_val_final)], callbacks=[lgb.early_stopping(50), lgb.log_evaluation(0)])
    trend_clf.fit(X_tr_final[trend_feats], y_tr_final, eval_set=[(X_val_final[trend_feats], y_val_final)], callbacks=[lgb.early_stopping(50), lgb.log_evaluation(0)])

    # Expert probs for brain
    rsi_p_tr = rsi_clf.predict_proba(X_tr_final[rsi_feats])[:, 1]
    macd_p_tr = macd_clf.predict_proba(X_tr_final[macd_feats])[:, 1]
    trend_p_tr = trend_clf.predict_proba(X_tr_final[trend_feats])[:, 1]
    rsi_p_va = rsi_clf.predict_proba(X_val_final[rsi_feats])[:, 1]
    macd_p_va = macd_clf.predict_proba(X_val_final[macd_feats])[:, 1]
    trend_p_va = trend_clf.predict_proba(X_val_final[trend_feats])[:, 1]

else:
    # Keep logistic path for reproducibility and JSON export
    rsi_clf = LogisticRegression(max_iter=1000, C=0.5, random_state=42)
    macd_clf = LogisticRegression(max_iter=1000, C=0.5, random_state=42)
    trend_clf = LogisticRegression(max_iter=1000, C=0.5, random_state=42)

    rsi_mean_auc, _ = time_series_cv_auc(rsi_clf, X[rsi_feats], y)
    macd_mean_auc, _ = time_series_cv_auc(macd_clf, X[macd_feats], y)
    trend_mean_auc, _ = time_series_cv_auc(trend_clf, X[trend_feats], y)

    split_idx = int(len(X) * 0.8)
    X_tr_final, X_val_final = X.iloc[:split_idx], X.iloc[split_idx:]
    y_tr_final, y_val_final = y.iloc[:split_idx], y.iloc[split_idx:]

    rsi_clf.fit(X_tr_final[rsi_feats], y_tr_final)
    macd_clf.fit(X_tr_final[macd_feats], y_tr_final)
    trend_clf.fit(X_tr_final[trend_feats], y_tr_final)

    rsi_p_tr = rsi_clf.predict_proba(X_tr_final[rsi_feats])[:, 1]
    macd_p_tr = macd_clf.predict_proba(X_tr_final[macd_feats])[:, 1]
    trend_p_tr = trend_clf.predict_proba(X_tr_final[trend_feats])[:, 1]
    rsi_p_va = rsi_clf.predict_proba(X_val_final[rsi_feats])[:, 1]
    macd_p_va = macd_clf.predict_proba(X_val_final[macd_feats])[:, 1]
    trend_p_va = trend_clf.predict_proba(X_val_final[trend_feats])[:, 1]

# Brain input dataset
regime_tr = X_tr_final[["atr_pct", "time_of_day"]]
brain_tr = pd.DataFrame({
    "rsi": rsi_p_tr,
    "macd": macd_p_tr,
    "trend": trend_p_tr,
    "volatility": regime_tr["atr_pct"],
    "time_of_day": regime_tr["time_of_day"],
})

regime_va = X_val_final[["atr_pct", "time_of_day"]]
brain_va = pd.DataFrame({
    "rsi": rsi_p_va,
    "macd": macd_p_va,
    "trend": trend_p_va,
    "volatility": regime_va["atr_pct"],
    "time_of_day": regime_va["time_of_day"],
})

# Fit a simple logistic brain on expert probs (time-series validated above)
brain_clf = LogisticRegression(max_iter=1000, C=1.0, random_state=42)
brain_clf.fit(brain_tr, y_tr_final)
brain_p_va = brain_clf.predict_proba(brain_va)[:, 1]
brain_auc = roc_auc_score(y_val_final.iloc[:len(brain_p_va)], brain_p_va)

print("AUCs (time-series CV):", {"RSI": float(rsi_mean_auc), "MACD": float(macd_mean_auc), "Trend": float(trend_mean_auc), "Brain_val": float(brain_auc)})

# Save logistic JSONs for deployment (convert only if logistic classifiers were used for experts/brain)
def to_json(clf, feature_names):
    # Only works for linear models (logistic)
    coef = clf.coef_[0]
    bias = float(clf.intercept_[0])
    weights = {name: float(w) for name, w in zip(feature_names, coef)}
    return {"type": "logistic", "bias": bias, "weights": weights}

# If experts are LGBM, we keep them for research but re-fit small logistic proxies for export
if USE_LGBM:
    export_rsi = LogisticRegression(max_iter=1000, C=0.5, random_state=42).fit(X_tr_final[rsi_feats], y_tr_final)
    export_macd = LogisticRegression(max_iter=1000, C=0.5, random_state=42).fit(X_tr_final[macd_feats], y_tr_final)
    export_trend = LogisticRegression(max_iter=1000, C=0.5, random_state=42).fit(X_tr_final[trend_feats], y_tr_final)
    export_brain = LogisticRegression(max_iter=1000, C=1.0, random_state=42).fit(brain_tr, y_tr_final)
else:
    export_rsi, export_macd, export_trend, export_brain = rsi_clf, macd_clf, trend_clf, brain_clf

rsi_json = to_json(export_rsi, rsi_feats)
macd_json = to_json(export_macd, macd_feats)
trend_json = to_json(export_trend, trend_feats)
brain_json = to_json(export_brain, ["experts.rsi", "experts.macd", "experts.trend", "regime.volatility", "regime.time_of_day"])

out = Path("output")
out.mkdir(parents=True, exist_ok=True)
(out / "rsi_expert.json").write_text(json.dumps(rsi_json, indent=2))
(out / "macd_expert.json").write_text(json.dumps(macd_json, indent=2))
(out / "trend_expert.json").write_text(json.dumps(trend_json, indent=2))
(out / "brain.json").write_text(json.dumps(brain_json, indent=2))

print("Saved models to output/*.json")
print("\n" + "="*60)
print("TRAINING RESULTS SUMMARY")
print("="*60)
print(f"Data: {df_feat.index.min()} to {df_feat.index.max()} ({len(y)} samples)")
print(f"Label balance: {y.mean()*100:.2f}% positive (60-min fwd > {cost_bps*10000:.0f} bps)")
print(f"\nAUCs (time-series CV, 5 folds):")
print(f"  RSI Expert:   {rsi_mean_auc:.4f}")
print(f"  MACD Expert:  {macd_mean_auc:.4f}")
print(f"  Trend Expert: {trend_mean_auc:.4f}")
print(f"  Brain (val):  {brain_auc:.4f}")
print(f"\n🎯 PROMOTION CRITERIA CHECK:")
print(f"  ✓ AUC >= 0.55? {'✅ YES' if brain_auc >= 0.55 else '❌ NO'} (Brain: {brain_auc:.4f})")
print(f"  ✓ Brain > max(experts)? {'✅ YES' if brain_auc > max(rsi_mean_auc, macd_mean_auc, trend_mean_auc) else '❌ NO'}")
print(f"\n📋 NEXT STEPS:")
if brain_auc >= 0.55:
    print("  1. Download JSONs from output/ to local models/")
    print("  2. Backtest in algo.py with use_brain=True, edge >= 0.15")
    print("  3. Verify beats RSI baseline after costs")
    print("  4. Upload to QC Object Store if promoted")
else:
    print("  ⚠️  Brain AUC too low - keep RSI baseline as champion")
    print("  1. Try extended date range or feature engineering")
    print("  2. Check horizon sweep results below for optimal H/cost")
    print("  3. Re-train with best parameters")
print("="*60 + "\n")

# Optional quick sweep over horizons and cost thresholds
for H_try in (6, 12, 24):
    for cost_try in (0.001, 0.002, 0.005):
        fwd_try = close.shift(-H_try)
        y_try = ( (fwd_try - close)/close > cost_try ).astype(int).dropna()
        common_idx = X.index.intersection(y_try.index)
        Xs = X.loc[common_idx]
        ys = y_try.loc[common_idx]
        # simple single-split evaluation
        split_idx = int(len(Xs)*0.8)
        clf_tmp = LogisticRegression(max_iter=1000, random_state=42)
        clf_tmp.fit(Xs.iloc[:split_idx][rsi_feats], ys.iloc[:split_idx])
        p_tmp = clf_tmp.predict_proba(Xs.iloc[split_idx:][rsi_feats])[:,1]
        auc_tmp = roc_auc_score(ys.iloc[split_idx:], p_tmp)
        print(f"H={H_try}, cost={cost_try:.4f}, RSI proxy AUC={auc_tmp:.4f}")

# Print JSONs so you can copy/paste into local models/
for fname, blob in [
    ("rsi_expert.json", rsi_json),
    ("macd_expert.json", macd_json),
    ("trend_expert.json", trend_json),
    ("brain.json", brain_json),
]:
    print(f"\n=== {fname} ===\n{json.dumps(blob, indent=2)}\n")
```
