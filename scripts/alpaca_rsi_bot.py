"""
Simple RSI-based Alpaca paper bot (standalone, outside QC/LEAN).

- Uses 5-minute bars from Alpaca.
- Enters long if RSI(14) < rsi_low.
- Exits/avoids entries if RSI > rsi_high or position exists and min-hold not met.
- Sizes at a fraction of equity (cap), default 0.25%.
- Places bracket orders with stop ~1x ATR(14) and take-profit ~2x ATR(14).

Usage:
  Set environment variables:
    ALPACA_API_KEY
    ALPACA_SECRET_KEY
    (optional) ALPACA_BASE_URL (default: https://paper-api.alpaca.markets)

  Run:
    python scripts/alpaca_rsi_bot.py --symbol TSLA
"""

import argparse
import csv
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from alpaca_trade_api.rest import REST, TimeFrame, TimeFrameUnit


def require_env(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise RuntimeError(f"Missing required env var {name}")
    return val


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    up = delta.clip(lower=0)
    down = (-delta).clip(lower=0)
    roll_up = up.ewm(alpha=1 / period, adjust=False).mean()
    roll_down = down.ewm(alpha=1 / period, adjust=False).mean() + 1e-12
    rs = roll_up / roll_down
    return 100 - (100 / (1 + rs))


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    hl = df["high"] - df["low"]
    hc = (df["high"] - df["close"].shift()).abs()
    lc = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def fetch_bars(api: REST, symbol: str, days: int = 14, feed: str = "iex") -> pd.DataFrame:
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    bars = api.get_bars(
        symbol,
        TimeFrame(5, TimeFrameUnit.Minute),
        start=start.isoformat(),
        end=end.isoformat(),
        adjustment="raw",
        limit=1000,
        feed=feed,
    )
    if not bars:
        raise RuntimeError("No bars returned")
    records = []
    for b in bars:
        ts = getattr(b, "t", None) or getattr(b, "timestamp", None)
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


def latest_filled_order_time(api: REST, symbol: str) -> datetime | None:
    since = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    orders = api.list_orders(status="all", after=since, symbols=[symbol])
    filled = [o for o in orders if getattr(o, "filled_at", None)]
    if not filled:
        return None
    latest = max(pd.to_datetime(o.filled_at, utc=True) for o in filled)
    return latest


def main() -> None:
    p = argparse.ArgumentParser(description="Standalone Alpaca RSI paper bot")
    p.add_argument("--symbol", default="TSLA")
    p.add_argument("--rsi-low", type=float, default=25.0)
    p.add_argument("--rsi-high", type=float, default=75.0)
    p.add_argument("--cap", type=float, default=0.0025, help="max fraction of equity per trade")
    p.add_argument("--min-hold-min", type=int, default=30, help="minimum hold time in minutes")
    p.add_argument("--sleep-min", type=int, default=5, help="loop interval minutes (if --loop set)")
    p.add_argument("--feed", default="iex", help="data feed (iex for free paper keys)")
    p.add_argument("--loop", action="store_true", help="keep running every sleep-min")
    p.add_argument("--log-file", default="alpaca_rsi_log.csv", help="CSV log file path")
    args = p.parse_args()

    key = require_env("ALPACA_API_KEY")
    secret = require_env("ALPACA_SECRET_KEY")
    base = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")

    api = REST(key, secret, base_url=base)

    log_path = Path(args.log_file)

    def append_log(action: str, price: float, rsi_val: float, qty: float, note: str = "") -> None:
        is_new = not log_path.exists()
        with log_path.open("a", newline="") as f:
            writer = csv.writer(f)
            if is_new:
                writer.writerow(
                    [
                        "timestamp",
                        "symbol",
                        "action",
                        "price",
                        "rsi",
                        "qty",
                        "note",
                    ]
                )
            writer.writerow(
                [
                    datetime.now(timezone.utc).isoformat(),
                    args.symbol,
                    action,
                    f"{price:.4f}",
                    f"{rsi_val:.2f}",
                    qty,
                    note,
                ]
            )

    def run_once() -> None:
        acct = api.get_account()
        equity = float(acct.equity)

        df = fetch_bars(api, args.symbol, days=14, feed=args.feed)
        df["rsi"] = rsi(df["close"])
        df["atr"] = atr(df)
        df = df.dropna()
        if df.empty:
            raise RuntimeError("Not enough data after indicators")

        latest = df.iloc[-1]
        price = float(latest["close"])
        rsi_val = float(latest["rsi"])
        atr_val = float(latest["atr"])

        # Enforce min hold by checking last filled order time
        last_fill = latest_filled_order_time(api, args.symbol)
        now = datetime.now(timezone.utc)
        if last_fill and (now - last_fill) < timedelta(minutes=args.min_hold_min):
            msg = f"Skipping: min hold not met (last fill {last_fill})"
            print(msg)
            append_log("skip_min_hold", price, rsi_val, 0, msg)
            return

        # Current position?
        pos_qty = 0.0
        try:
            pos = api.get_position(args.symbol)
            pos_qty = float(pos.qty)
        except Exception:
            pos_qty = 0.0

        if pos_qty != 0:
            # If already long and RSI > exit threshold, flatten
            if pos_qty > 0 and rsi_val > args.rsi_high:
                api.close_position(args.symbol)
                msg = f"Exit: RSI {rsi_val:.2f} > {args.rsi_high}"
                print(msg)
                append_log("exit_rsi", price, rsi_val, pos_qty, msg)
            else:
                msg = f"Holding position {pos_qty}, RSI {rsi_val:.2f}"
                print(msg)
                append_log("holding", price, rsi_val, pos_qty, msg)
            return

        # Flat: consider entry
        if rsi_val >= args.rsi_low:
            msg = f"No entry: RSI {rsi_val:.2f} >= {args.rsi_low}"
            print(msg)
            append_log("no_entry", price, rsi_val, 0, msg)
            return

        notional = equity * args.cap
        qty = int(notional / max(price, 1e-6))
        if qty <= 0:
            msg = "No entry: qty computed as 0"
            print(msg)
            append_log("no_entry_qty0", price, rsi_val, qty, msg)
            return

        stop_price = max(0.01, price - atr_val)
        tp_price = price + 2 * atr_val

        o = api.submit_order(
            symbol=args.symbol,
            qty=qty,
            side="buy",
            type="market",
            time_in_force="day",
            order_class="bracket",
            take_profit={"limit_price": round(tp_price, 2)},
            stop_loss={"stop_price": round(stop_price, 2)},
        )
        msg = (
            f"Entered {qty} {args.symbol} @ ~{price:.2f} | RSI {rsi_val:.2f} | "
            f"TP {tp_price:.2f} | SL {stop_price:.2f} | ORDER {o.id}"
        )
        print(msg)
        append_log("enter", price, rsi_val, qty, msg)

    while True:
        try:
            run_once()
        except Exception as e:
            err_msg = f"ERROR: {e}"
            print(err_msg)
            append_log("error", 0.0, 0.0, 0, err_msg)
        if not args.loop:
            break
        time.sleep(max(60, args.sleep_min * 60))


if __name__ == "__main__":
    main()
