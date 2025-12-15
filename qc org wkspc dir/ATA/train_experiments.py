"""Training & experiment script mirroring docs/TRAINING.md updated workflow.
Run in QuantConnect Research (QuantBook) or locally after exporting minute data as CSV.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
import hashlib
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.inspection import permutation_importance
from sklearn.utils import resample
import matplotlib.pyplot as plt

try:
    import lightgbm as lgb
    LGB_AVAILABLE = True
except Exception:
    LGB_AVAILABLE = False

# QuantBook compatibility: if running inside QC Research, the QuantBook will be available.
USE_QUANTBOOK = False
try:
    from QuantConnect import QuantBook  # type: ignore
    qb = QuantBook()
    USE_QUANTBOOK = True
except Exception:
    qb = None

if USE_QUANTBOOK:
    sym = qb.AddEquity("TSLA", Resolution.Minute).Symbol
    hist = qb.History(sym, start=datetime(2018,1,1), end=datetime(2022,1,1), resolution=Resolution.Minute)
    df = hist.loc[sym].reset_index().rename(columns={"time":"timestamp"})
    df = df.set_index("timestamp").sort_index()
    df5 = pd.DataFrame({
        "open": df["open"].resample("5min").first(),
        "high": df["high"].resample("5min").max(),
        "low": df["low"].resample("5min").min(),
        "close": df["close"].resample("5min").last(),
        "volume": df["volume"].resample("5min").sum(),
    }).dropna()
else:
    # Expect a local CSV named data/TSLA_1min.csv with 'timestamp,open,high,low,close,volume'
    csv_path = Path("data/TSLA_1min.csv")
    if not csv_path.exists():
        raise RuntimeError("No QuantBook available and data/TSLA_1min.csv not found. Upload minute data or run in QC Research.")
    df = pd.read_csv(csv_path, parse_dates=["timestamp"]).set_index("timestamp").sort_index()
    df5 = pd.DataFrame({
        "open": df["open"].resample("5min").first(),
        "high": df["high"].resample("5min").max(),
        "low": df["low"].resample("5min").min(),
        "close": df["close"].resample("5min").last(),
        "volume": df["volume"].resample("5min").sum(),
    }).dropna()

# Indicators

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

# Extras
rsi_lag1 = rsi14.shift(1)
rsi_lag2 = rsi14.shift(2)
macd_slope_ewm = macd_line.ewm(span=5, adjust=False).mean().diff()
time_sin = np.sin(2 * np.pi * time_of_day / 24.0)
time_cos = np.cos(2 * np.pi * time_of_day / 24.0)
overnight_ret = df5["open"].pct_change()

# Features
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

# Filter
df_feat = df_feat[(df_feat["atr_pct"] <= 0.02) & (df_feat["volm_z"] > -1) & (df_feat["volm_z"] < 5)]

# Label H=12 by default
H = 12
cost_bps = 0.001
fwd = close.shift(-H)
df_feat["label"] = ( (fwd - close)/close > cost_bps ).astype(int)
df_feat = df_feat.dropna()

X = df_feat.drop(columns=["label"])
y = df_feat["label"]

# CV helper
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


def purged_time_series_cv_auc(clf, X, y, n_splits=5, embargo=12):
    """TimeSeriesSplit with a simple purge/embargo: remove training samples within `embargo` positions before test start."""
    tscv = TimeSeriesSplit(n_splits=n_splits)
    aucs = []
    for train_idx, test_idx in tscv.split(X):
        test_start = test_idx[0]
        # purge training indices that are within embargo of test start
        purged_train_idx = [i for i in train_idx if i < (test_start - embargo)]
        if len(purged_train_idx) < 10:  # fallback to original if too little
            purged_train_idx = train_idx
        Xtr, Xte = X.iloc[purged_train_idx], X.iloc[test_idx]
        ytr, yte = y.iloc[purged_train_idx], y.iloc[test_idx]
        clf.fit(Xtr, ytr)
        p = clf.predict_proba(Xte)[:, 1]
        aucs.append(roc_auc_score(yte, p))
    return float(np.mean(aucs)), aucs


def bootstrap_auc(clf, X_train, y_train, X_test, y_test, n_boot=200):
    """Bootstrap AUC on test set by resampling test indices with replacement."""
    clf.fit(X_train, y_train)
    p = clf.predict_proba(X_test)[:, 1]
    base_auc = roc_auc_score(y_test, p)
    aucs = []
    idx = np.arange(len(y_test))
    for _ in range(n_boot):
        bs_idx = resample(idx, replace=True, n_samples=len(idx))
        try:
            aucs.append(roc_auc_score(y_test.iloc[bs_idx], p[bs_idx]))
        except Exception:
            continue
    lower = np.percentile(aucs, 2.5) if aucs else np.nan
    upper = np.percentile(aucs, 97.5) if aucs else np.nan
    return base_auc, (lower, upper)

# Run experiments
USE_LGBM = LGB_AVAILABLE
rsi_feats = ["rsi", "rsi_lag1", "rsi_lag2", "rsi_slope", "bb_z"]
macd_feats = ["macd", "macd_sig", "macd_hist", "macd_slope", "macd_slope_ewm"]
trend_feats = ["ema20_rel", "ema50_rel", "ema200_rel"]

if USE_LGBM:
    def mk_lgb():
        return lgb.LGBMClassifier(n_estimators=500, learning_rate=0.05, random_state=42)
    rsi_clf = mk_lgb()
    macd_clf = mk_lgb()
    trend_clf = mk_lgb()

    rsi_mean_auc, _ = time_series_cv_auc(rsi_clf, X[rsi_feats], y)
    macd_mean_auc, _ = time_series_cv_auc(macd_clf, X[macd_feats], y)
    trend_mean_auc, _ = time_series_cv_auc(trend_clf, X[trend_feats], y)

    # Purged CV (embargo) check
    rsi_purged_auc, _ = purged_time_series_cv_auc(rsi_clf, X[rsi_feats], y, n_splits=5, embargo=12)
    macd_purged_auc, _ = purged_time_series_cv_auc(macd_clf, X[macd_feats], y, n_splits=5, embargo=12)
    trend_purged_auc, _ = purged_time_series_cv_auc(trend_clf, X[trend_feats], y, n_splits=5, embargo=12)

    split_idx = int(len(X)*0.8)
    X_tr_final, X_val_final = X.iloc[:split_idx], X.iloc[split_idx:]
    y_tr_final, y_val_final = y.iloc[:split_idx], y.iloc[split_idx:]

    rsi_clf.fit(X_tr_final[rsi_feats], y_tr_final, eval_set=[(X_val_final[rsi_feats], y_val_final)], early_stopping_rounds=50, verbose=False)
    macd_clf.fit(X_tr_final[macd_feats], y_tr_final, eval_set=[(X_val_final[macd_feats], y_val_final)], early_stopping_rounds=50, verbose=False)
    trend_clf.fit(X_tr_final[trend_feats], y_tr_final, eval_set=[(X_val_final[trend_feats], y_val_final)], early_stopping_rounds=50, verbose=False)

    rsi_p_tr = rsi_clf.predict_proba(X_tr_final[rsi_feats])[:, 1]
    macd_p_tr = macd_clf.predict_proba(X_tr_final[macd_feats])[:, 1]
    trend_p_tr = trend_clf.predict_proba(X_tr_final[trend_feats])[:, 1]
    rsi_p_va = rsi_clf.predict_proba(X_val_final[rsi_feats])[:, 1]
    macd_p_va = macd_clf.predict_proba(X_val_final[macd_feats])[:, 1]
    trend_p_va = trend_clf.predict_proba(X_val_final[trend_feats])[:, 1]
else:
    rsi_clf = LogisticRegression(max_iter=1000, C=0.5, random_state=42)
    macd_clf = LogisticRegression(max_iter=1000, C=0.5, random_state=42)
    trend_clf = LogisticRegression(max_iter=1000, C=0.5, random_state=42)

    rsi_mean_auc, _ = time_series_cv_auc(rsi_clf, X[rsi_feats], y)
    macd_mean_auc, _ = time_series_cv_auc(macd_clf, X[macd_feats], y)
    trend_mean_auc, _ = time_series_cv_auc(trend_clf, X[trend_feats], y)

    # Purged CV check
    rsi_purged_auc, _ = purged_time_series_cv_auc(rsi_clf, X[rsi_feats], y, n_splits=5, embargo=12)
    macd_purged_auc, _ = purged_time_series_cv_auc(macd_clf, X[macd_feats], y, n_splits=5, embargo=12)
    trend_purged_auc, _ = purged_time_series_cv_auc(trend_clf, X[trend_feats], y, n_splits=5, embargo=12)

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

brain_clf = LogisticRegression(max_iter=1000, C=1.0, random_state=42)
brain_clf.fit(brain_tr, y_tr_final)
brain_p_va = brain_clf.predict_proba(brain_va)[:, 1]
brain_auc = roc_auc_score(y_val_final.iloc[:len(brain_p_va)], brain_p_va)

# Bootstrap AUC CI for brain (on validation set)
brain_auc_base, brain_auc_ci = bootstrap_auc(brain_clf, brain_tr, y_tr_final, brain_va, y_val_final.iloc[:len(brain_p_va)])

print("AUCs (time-series CV):", {"RSI": float(rsi_mean_auc), "MACD": float(macd_mean_auc), "Trend": float(trend_mean_auc), "Brain_val": float(brain_auc)})

# Feature importance (permutation) on validation set
try:
    imp = permutation_importance(rsi_clf if not USE_LGBM else rsi_clf, X_val_final[rsi_feats], y_val_final, n_repeats=20, random_state=42)
    fi = sorted(zip(rsi_feats, imp.importances_mean), key=lambda x: -abs(x[1]))
    print("RSI feature importances:", fi)
except Exception as e:
    print("Permutation importance failed:", e)

# Expanded horizon/cost sweep
results = []
for H_try in (6, 12, 24, 48):
    for cost_try in (0.001, 0.002, 0.005):
        fwd_try = close.shift(-H_try)
        y_try = ( (fwd_try - close)/close > cost_try ).astype(int).dropna()
        common_idx = X.index.intersection(y_try.index)
        Xs = X.loc[common_idx]
        ys = y_try.loc[common_idx]
        prevalence = ys.mean()
        if len(ys) < 100:
            continue
        # Purged CV AUC on a simple logistic baseline for quick signal check
        auc_purged, _ = purged_time_series_cv_auc(LogisticRegression(max_iter=1000), Xs[rsi_feats], ys, n_splits=5, embargo=H_try)
        results.append({"H": H_try, "cost": cost_try, "prevalence": float(prevalence), "purged_auc": float(auc_purged)})

res_df = pd.DataFrame(results)
res_df.to_csv(Path("output") / "horizon_cost_sweep.csv", index=False)
print("Saved horizon/cost sweep to output/horizon_cost_sweep.csv")

# Save diagnostic plots: ROC curve for brain on validation
try:
    from sklearn.metrics import roc_curve
    fpr, tpr, _ = roc_curve(y_val_final.iloc[:len(brain_p_va)], brain_p_va)
    plt.figure()
    plt.plot(fpr, tpr, label=f"Brain AUC={brain_auc:.3f}")
    plt.plot([0,1],[0,1], linestyle='--', color='gray')
    plt.xlabel('FPR')
    plt.ylabel('TPR')
    plt.title('Brain ROC (validation)')
    plt.legend()
    plt.savefig(Path("output") / "brain_roc.png")
    plt.close()
    print("Saved ROC plot to output/brain_roc.png")
except Exception as e:
    print("Failed to save ROC plot:", e)
print("Purged AUCs:", {"RSI": float(rsi_purged_auc), "MACD": float(macd_purged_auc), "Trend": float(trend_purged_auc)})
print(f"Brain AUC CI (bootstrapped 95%): {brain_auc_ci}")

# Export logistic proxies if needed

def to_json(clf, feature_names):
    coef = clf.coef_[0]
    bias = float(clf.intercept_[0])
    weights = {name: float(w) for name, w in zip(feature_names, coef)}
    return {"type": "logistic", "bias": bias, "weights": weights}

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
# Export a runtime-friendly brain JSON (bot/brains/TSLA_1h/brain_latest.json)
try:
    feat_list = list(dict.fromkeys(rsi_feats + macd_feats + trend_feats))
    fh = hashlib.sha256("|".join(feat_list).encode()).hexdigest()
    runtime_brain = {
        "brain_version": "1.0",
        "symbol": "TSLA",
        "timeframe": "1h",
        "trained_utc": datetime.utcnow().isoformat() + "Z",
        "feature_list": feat_list,
        "feature_hash": fh,
        "scaler": {},
        "model": brain_json,
        "signal_definition": {"target": "next_N_bar_return", "horizon_bars": H, "long_threshold": cost_bps, "short_threshold": -cost_bps, "no_trade_band": 0.001},
        "risk_profile": {"vol_target": 0.1, "max_risk_per_trade": 0.002, "max_positions": 1, "cooldown_minutes": 60},
        "expected_stats": {"backtest_sharpe": None}
    }
    bot_brain_dir = Path(__file__).resolve().parents[2].parent / "bot" / "brains" / "TSLA_1h"
    bot_brain_dir.mkdir(parents=True, exist_ok=True)
    (bot_brain_dir / f"brain_{datetime.utcnow().strftime('%Y-%m-%dT%H-%M')}.json").write_text(json.dumps(runtime_brain, indent=2))
    (bot_brain_dir / "brain_latest.json").write_text(json.dumps(runtime_brain, indent=2))
    print("Exported runtime brain to bot/brains/TSLA_1h/")
except Exception as e:
    print("Failed to export runtime brain:", e)
