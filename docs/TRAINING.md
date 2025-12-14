# Training the experts and brain (QC Research notebook)

Use QuantConnect only for research/retraining; keep live/paper local. This notebook flow lets you retrain and then copy the JSONs into your local `models/` folder.

## Quick steps (repeatable)
1) In QC, open the ATA project → add/open `research.ipynb`.
2) Paste and run the code below (run all cells). It:
   - Pulls TSLA minute data.
   - Resamples to 5-minute bars.
   - Builds richer features/labels (cost-aware 60-minute forward return).
   - Trains tiny logistic experts (RSI, MACD, Trend) with simple C search, and the brain.
   - Saves JSONs to `output/` and prints them so you can copy/paste into local files.
3) Download from `output/` or copy the printed JSON blobs into your local `models/` files.
4) Backtest locally or in QC with `use_brain=True` (edge gate ≥ 0.20, cap 0.15–0.25%, long-only). Promote only if it beats RSI after costs.

## Notebook code (paste and run)
```python
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

qb = QuantBook()
sym = qb.AddEquity("TSLA", Resolution.Minute).Symbol
# extend history for more regimes
hist = qb.History(sym, start=datetime(2018,1,1), end=datetime(2022,1,1), resolution=Resolution.Minute)

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

df_feat = pd.DataFrame({
    "rsi": rsi14,
    "rsi_slope": rsi_slope,
    "macd": macd_line,
    "macd_sig": macd_sig,
    "macd_hist": macd_hist,
    "macd_slope": macd_slope,
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
})

# Filters: drop very noisy/illiquid bars
df_feat = df_feat[(df_feat["atr_pct"] <= 0.02) & (df_feat["volm_z"] > -1) & (df_feat["volm_z"] < 5)]

# Label: 60-minute forward net return > cost threshold (tougher)
fwd = close.shift(-12)
ret_fwd = (fwd - close) / close
cost_bps = 0.001  # 10 bps to approximate costs/slippage
df_feat["label"] = (ret_fwd > cost_bps).astype(int)
df_feat = df_feat.dropna()

X = df_feat.drop(columns=["label"])
y = df_feat["label"]

# time-based split
split_idx = int(len(X)*0.8)
X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]

def best_logit(Xtr, ytr, Xvl, yvl, Cs=(0.05,0.1,0.5,1.0)):
    best = None
    best_auc = -1
    for c in Cs:
        lr = LogisticRegression(max_iter=500, random_state=42, C=c, penalty="l2")
        lr.fit(Xtr, ytr)
        p = lr.predict_proba(Xvl)[:,1]
        auc = roc_auc_score(yvl.iloc[:len(p)], p)
        if auc > best_auc:
            best_auc = auc
            best = lr
    return best, best_auc

# Train experts on small feature subsets
rsi_feats = ["rsi", "rsi_slope", "bb_z"]
macd_feats = ["macd", "macd_sig", "macd_hist", "macd_slope"]
trend_feats = ["ema20_rel", "ema50_rel", "ema200_rel"]

rsi_clf, rsi_auc = best_logit(X_train[rsi_feats], y_train, X_val[rsi_feats], y_val)
macd_clf, macd_auc = best_logit(X_train[macd_feats], y_train, X_val[macd_feats], y_val)
trend_clf, trend_auc = best_logit(X_train[trend_feats], y_train, X_val[trend_feats], y_val)

# Brain input: expert probs + regime
rsi_p_tr = rsi_clf.predict_proba(X_train[rsi_feats])[:,1]
macd_p_tr = macd_clf.predict_proba(X_train[macd_feats])[:,1]
trend_p_tr = trend_clf.predict_proba(X_train[trend_feats])[:,1]
regime_tr = X_train[["atr_pct", "time_of_day"]]
brain_tr = pd.DataFrame({
    "rsi": rsi_p_tr,
    "macd": macd_p_tr,
    "trend": trend_p_tr,
    "volatility": regime_tr["atr_pct"],
    "time_of_day": regime_tr["time_of_day"],
})

rsi_p_va = rsi_clf.predict_proba(X_val[rsi_feats])[:,1]
macd_p_va = macd_clf.predict_proba(X_val[macd_feats])[:,1]
trend_p_va = trend_clf.predict_proba(X_val[trend_feats])[:,1]
regime_va = X_val[["atr_pct", "time_of_day"]]
brain_va = pd.DataFrame({
    "rsi": rsi_p_va,
    "macd": macd_p_va,
    "trend": trend_p_va,
    "volatility": regime_va["atr_pct"],
    "time_of_day": regime_va["time_of_day"],
})

brain_clf, brain_auc = best_logit(brain_tr, y_train.loc[brain_tr.index], brain_va, y_val.loc[brain_va.index])

def to_json(clf, feature_names):
    coef = clf.coef_[0]
    bias = float(clf.intercept_[0])
    weights = {name: float(w) for name, w in zip(feature_names, coef)}
    return {"type": "logistic", "bias": bias, "weights": weights}

rsi_json = to_json(rsi_clf, rsi_feats)
macd_json = to_json(macd_clf, macd_feats)
trend_json = to_json(trend_clf, trend_feats)
brain_json = to_json(brain_clf, ["experts.rsi", "experts.macd", "experts.trend", "regime.volatility", "regime.time_of_day"])

out = Path("output")
out.mkdir(parents=True, exist_ok=True)
(out / "rsi_expert.json").write_text(json.dumps(rsi_json, indent=2))
(out / "macd_expert.json").write_text(json.dumps(macd_json, indent=2))
(out / "trend_expert.json").write_text(json.dumps(trend_json, indent=2))
(out / "brain.json").write_text(json.dumps(brain_json, indent=2))

print("Saved models to output/*.json")
print("AUCs (val):", {"RSI": rsi_auc, "MACD": macd_auc, "Trend": trend_auc, "Brain_val_proxy": brain_auc})

# Print JSONs to copy/paste if you prefer not to download
for fname, blob in [
    ("rsi_expert.json", rsi_json),
    ("macd_expert.json", macd_json),
    ("trend_expert.json", trend_json),
    ("brain.json", brain_json),
]:
    print(f"\n=== {fname} ===\n{json.dumps(blob, indent=2)}\n")
```
