# Training the experts and brain (quick path)

These steps are designed to be as simple as possible and run inside the QuantConnect Research notebook (no local setup required).

## What you’ll do
1) Open a QC Research notebook.
2) Copy/paste the code below to:
   - Pull TSLA minute data.
   - Resample to 5-minute bars.
   - Build features and labels (60-minute forward return).
   - Train tiny logistic experts (RSI, MACD, Trend) and a brain.
   - Save JSON model files to `/Content/output/`.
3) Download the JSONs and upload them to the QC Object Store.

## Notebook code (paste and run all)
```python
import json
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score

qb = QuantBook()
sym = qb.AddEquity("TSLA", Resolution.Minute).Symbol
hist = qb.History(sym, start=datetime(2019,1,1), end=datetime(2020,1,1), resolution=Resolution.Minute)

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
ema20 = close.ewm(span=20, adjust=False).mean()
ema50 = close.ewm(span=50, adjust=False).mean()
ema200 = close.ewm(span=200, adjust=False).mean()
rsi14 = rsi(close)
macd_line, macd_sig, macd_hist = macd(close)
atr14 = atr(df5)
bb_mid = close.rolling(20).mean()
bb_std = close.rolling(20).std()
bb_z = (close - bb_mid) / (2 * bb_std + 1e-9)

df_feat = pd.DataFrame({
    "rsi": rsi14,
    "macd": macd_line,
    "macd_sig": macd_sig,
    "macd_hist": macd_hist,
    "ema20": ema20,
    "ema50": ema50,
    "ema200": ema200,
    "atr": atr14,
    "atr_pct": atr14 / close,
    "bb_z": bb_z,
    "tod": df5.index.hour + df5.index.minute/60.0,
})

# Label: 60-minute (12 bars) forward return > 0?
fwd = close.shift(-12)
ret_fwd = (fwd - close) / close
df_feat["label"] = (ret_fwd > 0).astype(int)
df_feat = df_feat.dropna()

X = df_feat.drop(columns=["label"])
y = df_feat["label"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

def train_logit(features, target):
    lr = LogisticRegression(max_iter=500, random_state=42)
    lr.fit(features, target)
    return lr

# Train experts on small feature subsets
rsi_feats = X_train[["rsi", "bb_z"]]
macd_feats = X_train[["macd", "macd_sig", "macd_hist"]]
trend_feats = X_train[["ema20", "ema50", "ema200"]]

rsi_clf = train_logit(rsi_feats, y_train)
macd_clf = train_logit(macd_feats, y_train)
trend_clf = train_logit(trend_feats, y_train)

# Brain input: expert probs + regime
rsi_p = rsi_clf.predict_proba(rsi_feats)[:,1]
macd_p = macd_clf.predict_proba(macd_feats)[:,1]
trend_p = trend_clf.predict_proba(trend_feats)[:,1]
regime = X_train[["atr_pct", "tod"]]
brain_X = pd.DataFrame({"rsi": rsi_p, "macd": macd_p, "trend": trend_p, "volatility": regime["atr_pct"], "time_of_day": regime["tod"]})
brain_clf = train_logit(brain_X, y_train.loc[brain_X.index])

def to_json(clf, feature_names):
    coef = clf.coef_[0]
    bias = float(clf.intercept_[0])
    weights = {name: float(w) for name, w in zip(feature_names, coef)}
    return {"type": "logistic", "bias": bias, "weights": weights}

rsi_json = to_json(rsi_clf, ["rsi", "bb_z"])
macd_json = to_json(macd_clf, ["macd", "macd_sig", "macd_hist"])
trend_json = to_json(trend_clf, ["ema20", "ema50", "ema200"])
brain_json = to_json(brain_clf, ["experts.rsi", "experts.macd", "experts.trend", "regime.volatility", "regime.time_of_day"])

out = Path("/Content/output")
out.mkdir(parents=True, exist_ok=True)
(out / "rsi_expert.json").write_text(json.dumps(rsi_json, indent=2))
(out / "macd_expert.json").write_text(json.dumps(macd_json, indent=2))
(out / "trend_expert.json").write_text(json.dumps(trend_json, indent=2))
(out / "brain.json").write_text(json.dumps(brain_json, indent=2))

print("Saved models to /Content/output/*.json")
feat_map = {
    "RSI": ["rsi", "bb_z"],
    "MACD": ["macd", "macd_sig", "macd_hist"],
    "Trend": ["ema20", "ema50", "ema200"],
}
for name, clf_obj in [("RSI", rsi_clf), ("MACD", macd_clf), ("Trend", trend_clf)]:
    feats = feat_map[name]
    p = clf_obj.predict_proba(X_test[feats])[:,1]
    print(name, "AUC", roc_auc_score(y_test.iloc[:len(p)], p))
```

## Export and upload
1) In the QC notebook file browser (left), download the four JSONs from `/Content/output/`.
2) On your machine in `C:\Projects\Autonomous-Trading-Agent` run:
   ```powershell
   cd "qc org wkspc dir"
   lean cloud object-store set "models/rsi_expert.json" "..\\models\\rsi_expert.json"
   lean cloud object-store set "models/macd_expert.json" "..\\models\\macd_expert.json"
   lean cloud object-store set "models/trend_expert.json" "..\\models\\trend_expert.json"
   lean cloud object-store set "models/brain.json" "..\\models\\brain.json"
   ```
3) Re-run the QC web backtest (project “ATA”). With `self.use_brain = True`, it will now use your trained ensemble.
