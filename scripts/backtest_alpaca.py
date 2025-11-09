import os
import sys
from datetime import datetime, timezone
from typing import Optional

import numpy as np
import pandas as pd


def _require_env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        print(f"ERROR: Missing env var {name}")
        sys.exit(1)
    return v


def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    up = delta.clip(lower=0.0)
    down = (-delta).clip(lower=0.0)
    roll_up = up.ewm(alpha=1 / period, adjust=False).mean()
    roll_down = down.ewm(alpha=1 / period, adjust=False).mean() + 1e-12
    rs = roll_up / roll_down
    return 100 - (100 / (1 + rs))


def fetch_bars(symbol: str, start: str, end: str, timeframe: str = "Minute") -> pd.DataFrame:
    # Defer import to avoid dependency unless used
    from alpaca_trade_api.rest import REST, TimeFrame

    key = _require_env("ALPACA_API_KEY")
    secret = _require_env("ALPACA_SECRET_KEY")
    base = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    api = REST(key, secret, base_url=base)

    tf = getattr(TimeFrame, timeframe)
    # Convert to RFC3339
    def to_rfc3339(s: str) -> str:
        try:
            dt = datetime.fromisoformat(s)
        except ValueError:
            # Accept YYYYMMDD
            dt = datetime.strptime(s, "%Y%m%d")
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()

    bars = api.get_bars(symbol, tf, start=to_rfc3339(start), end=to_rfc3339(end))
    # alpaca-trade-api returns a BarSet-like list with attributes
    records = []
    for b in bars:
        # prefer unified attribute names
        ts = getattr(b, "t", None) or getattr(b, "timestamp", None)
        if isinstance(ts, (int, float)):
            idx = pd.to_datetime(ts, unit="ns", utc=True)
        else:
            idx = pd.to_datetime(ts, utc=True)
        records.append(
            {
                "timestamp": idx,
                "open": float(getattr(b, "o", getattr(b, "open", 0.0))),
                "high": float(getattr(b, "h", getattr(b, "high", 0.0))),
                "low": float(getattr(b, "l", getattr(b, "low", 0.0))),
                "close": float(getattr(b, "c", getattr(b, "close", 0.0))),
                "volume": float(getattr(b, "v", getattr(b, "volume", 0.0))),
            }
        )
    df = pd.DataFrame.from_records(records).set_index("timestamp").sort_index()
    return df


def resample_5min(df: pd.DataFrame) -> pd.DataFrame:
    o = df["open"].resample("5min").first()
    h = df["high"].resample("5min").max()
    l = df["low"].resample("5min").min()
    c = df["close"].resample("5min").last()
    v = df["volume"].resample("5min").sum()
    out = pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "volume": v}).dropna()
    return out


def run_rsi_backtest(df5: pd.DataFrame, size_pct: float = 0.005, min_hold_bars: int = 3) -> dict:
    df = df5.copy()
    df["rsi"] = _rsi(df["close"]).fillna(method="bfill")

    equity = 100_000.0
    position = 0
    last_entry_i: Optional[int] = None
    pnl = 0.0
    trades = 0
    prices = df["close"].values
    for i in range(1, len(df)):
        price = prices[i]
        prev = prices[i - 1]
        if position != 0:
            pnl += position * (price - prev)

        rsi = float(df["rsi"].iloc[i])
        if position == 0 and rsi < 30:
            qty = int((equity * size_pct) / max(price, 1e-6))
            if qty > 0:
                position = qty
                trades += 1
                last_entry_i = i
        elif position != 0 and rsi > 70 and (last_entry_i is None or i - last_entry_i >= min_hold_bars):
            position = 0
            trades += 1

    bar_ret = pd.Series(prices).pct_change().dropna().values
    sharpe = float((bar_ret.mean() / (bar_ret.std() + 1e-12)) * np.sqrt(len(bar_ret)))
    return {"net_pnl": float(pnl), "sharpe": sharpe, "trades": int(trades)}


def main():
    import argparse

    p = argparse.ArgumentParser(description="Backtest RSI rule on Alpaca historical bars")
    p.add_argument("--symbol", default="TSLA")
    p.add_argument("--start", default="2020-01-02")
    p.add_argument("--end", default="2020-01-31")
    p.add_argument("--timeframe", default="Minute", choices=["Minute"])  # we resample to 5min
    args = p.parse_args()

    df = fetch_bars(args.symbol, args.start, args.end, args.timeframe)
    if df.empty:
        print("ERROR: No bars returned. Check symbol/date range and data plan.")
        sys.exit(2)
    df5 = resample_5min(df)
    m = run_rsi_backtest(df5)
    print(
        f"BACKTEST (ALPACA DATA) DONE | SYMBOL: {args.symbol} | NET_PNL: {m['net_pnl']:.2f} | SHARPE: {m['sharpe']:.2f} | TRADES: {m['trades']}"
    )


if __name__ == "__main__":
    main()

