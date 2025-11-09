import os
import sys
from dataclasses import dataclass
from typing import List, Tuple
import numpy as np
import pandas as pd

from scripts.backtest_alpaca import fetch_bars, resample_5min, _rsi


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df["high"]
    low = df["low"]
    close = df["close"].shift(1)
    tr = np.maximum(high - low, np.maximum((high - close).abs(), (low - close).abs()))
    return pd.Series(tr).ewm(alpha=1 / period, adjust=False).mean().reindex(df.index)


def simulate(df5: pd.DataFrame, entry_rsi: float, exit_rsi: float, size_pct: float, stop_k: float, tp_k: float) -> dict:
    df = df5.copy()
    df["rsi"] = _rsi(df["close"]).bfill()
    df["atr"] = atr(df).bfill()

    equity = 100_000.0
    position = 0
    last_entry_i = None
    pnl = 0.0
    trades = 0
    prices = df["close"].values
    atrv = df["atr"].values
    rsi = df["rsi"].values
    stop = None
    tp = None

    for i in range(1, len(df)):
        price = prices[i]
        prev = prices[i - 1]
        if position != 0:
            pnl += position * (price - prev)
            # Check brackets
            if stop is not None and price <= stop:
                position = 0
                trades += 1
                stop = tp = None
                continue
            if tp is not None and price >= tp:
                position = 0
                trades += 1
                stop = tp = None
                continue

        if position == 0 and rsi[i] < entry_rsi:
            qty = int((equity * size_pct) / max(price, 1e-6))
            if qty > 0:
                position = qty
                trades += 1
                last_entry_i = i
                a = max(atrv[i], 1e-6)
                stop = max(0.01, price - stop_k * a)
                tp = price + tp_k * a
        elif position != 0 and rsi[i] > exit_rsi and (last_entry_i is None or i - last_entry_i >= 3):
            position = 0
            trades += 1
            stop = tp = None

    bar_ret = pd.Series(prices).pct_change().dropna().values
    sharpe = float((bar_ret.mean() / (bar_ret.std() + 1e-12)) * np.sqrt(len(bar_ret)))
    return {"net_pnl": float(pnl), "sharpe": sharpe, "trades": int(trades)}


def main():
    import argparse
    p = argparse.ArgumentParser("Parameter sweep on Alpaca data")
    p.add_argument("--symbol", default="TSLA")
    p.add_argument("--start", default="2020-01-02")
    p.add_argument("--end", default="2020-01-31")
    args = p.parse_args()

    df = fetch_bars(args.symbol, args.start, args.end)
    if df.empty:
        print("ERROR: No data returned")
        sys.exit(2)
    df5 = resample_5min(df)

    grids = {
        "entry_rsi": [20, 25, 30],
        "exit_rsi": [70, 75, 80],
        "size_pct": [0.002, 0.003, 0.005],
        "stop_k": [1.0, 1.5],
        "tp_k": [1.5, 2.0],
    }

    results = []
    for er in grids["entry_rsi"]:
        for xr in grids["exit_rsi"]:
            for sp in grids["size_pct"]:
                for sk in grids["stop_k"]:
                    for tk in grids["tp_k"]:
                        m = simulate(df5, er, xr, sp, sk, tk)
                        results.append((m["net_pnl"], m["sharpe"], m["trades"], er, xr, sp, sk, tk))

    # sort by net_pnl then sharpe
    results.sort(key=lambda x: (x[0], x[1]), reverse=True)
    top = results[:10]
    print("TOP PARAMS (net_pnl, sharpe, trades, entry_rsi, exit_rsi, size, stop_k, tp_k):")
    for row in top:
        print(row)


if __name__ == "__main__":
    main()

