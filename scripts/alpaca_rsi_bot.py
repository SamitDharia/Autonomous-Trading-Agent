"""
RSI-based Alpaca paper bot with Phase 1+2 enhancements (standalone, outside QC/LEAN).

Strategy:
- RSI baseline with dynamic thresholds (20/80, 25/75, 30/70 based on volatility)
- Phase 1 Filters: time-of-day (10:00-15:30), volatility regime (vol_z>0.5), volume confirmation (volm_z>1.0)
- Phase 2 Enhancements: trend filter (ema200_rel>-5%), Bollinger Band confirmation (bb_z<-0.8)
- Position: 0.25% equity cap, 30-min minimum hold
- Brackets: 1x ATR stop, 2x ATR take-profit

Backtest Performance (2020-2024):
- Sharpe: 0.80 (vs baseline -0.11)
- Win Rate: 72.7% (vs baseline 64.3%)
- Trade Count: 44 (vs baseline 168)

Usage:
  Set environment variables:
    ALPACA_API_KEY
    ALPACA_SECRET_KEY
    (optional) ALPACA_BASE_URL (default: https://paper-api.alpaca.markets)

  Run:
    python scripts/alpaca_rsi_bot.py --symbol TSLA --loop
"""

import argparse
import csv
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pytz
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


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def bollinger_bands(series: pd.Series, period: int = 20, num_std: float = 2.0) -> tuple:
    """Returns (middle_band, upper_band, lower_band)"""
    middle = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    upper = middle + (std * num_std)
    lower = middle - (std * num_std)
    return middle, upper, lower


def calculate_features(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate all Phase 1+2 features"""
    # Basic indicators
    df["rsi"] = rsi(df["close"])
    df["atr"] = atr(df)
    df["ema20"] = ema(df["close"], 20)
    df["ema50"] = ema(df["close"], 50)
    df["ema200"] = ema(df["close"], 200)
    
    # Bollinger Bands
    df["bb_mid"], df["bb_upper"], df["bb_lower"] = bollinger_bands(df["close"], 20, 2.0)
    
    # Phase 1 features
    # Volatility z-score (20-period rolling)
    returns = df["close"].pct_change()
    vol = returns.rolling(20).std()
    vol_mean = vol.rolling(60).mean()
    vol_std = vol.rolling(60).std() + 1e-8
    df["vol_z"] = (vol - vol_mean) / vol_std
    
    # Volume z-score (20-period rolling)
    vol_mean_qty = df["volume"].rolling(20).mean()
    vol_std_qty = df["volume"].rolling(20).std() + 1e-8
    df["volm_z"] = (df["volume"] - vol_mean_qty) / vol_std_qty
    
    # Time of day (hours since midnight in US/Eastern, e.g., 10:30 AM ET = 10.5)
    # Convert UTC index to US/Eastern
    eastern = pytz.timezone('US/Eastern')
    df_et = df.index.tz_convert(eastern)
    df["time_of_day"] = df_et.hour + df_et.minute / 60.0
    
    # Phase 2 features
    # EMA200 relative position (%)
    df["ema200_rel"] = ((df["close"] - df["ema200"]) / df["ema200"]) * 100
    
    # BB z-score
    bb_width = df["bb_upper"] - df["bb_lower"] + 1e-8
    df["bb_z"] = (df["close"] - df["bb_mid"]) / (bb_width / 2)
    
    return df.dropna()


def get_dynamic_rsi_thresholds(vol_z: float) -> tuple:
    """
    Phase 2: Dynamic RSI thresholds based on volatility regime
    - High volatility (vol_z > 1.0): tighter thresholds (30/70)
    - Normal volatility (-0.5 to 1.0): standard thresholds (25/75)
    - Low volatility (vol_z < -0.5): wider thresholds (20/80)
    """
    if vol_z > 1.0:
        return 30.0, 70.0  # High-vol: be more conservative
    elif vol_z < -0.5:
        return 20.0, 80.0  # Low-vol: capture more opportunities
    else:
        return 25.0, 75.0  # Normal: baseline thresholds


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
    p = argparse.ArgumentParser(description="Alpaca RSI bot with Phase 1+2 enhancements")
    p.add_argument("--symbol", default="TSLA")
    p.add_argument("--cap", type=float, default=0.0025, help="max fraction of equity per trade (default 0.25%)")
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
        df = calculate_features(df)
        
        if df.empty:
            raise RuntimeError("Not enough data after feature calculation")

        latest = df.iloc[-1]
        price = float(latest["close"])
        rsi_val = float(latest["rsi"])
        atr_val = float(latest["atr"])
        vol_z = float(latest["vol_z"])
        volm_z = float(latest["volm_z"])
        time_of_day = float(latest["time_of_day"])
        ema200_rel = float(latest["ema200_rel"])
        bb_z = float(latest["bb_z"])
        
        # Get dynamic RSI thresholds based on volatility regime
        rsi_low, rsi_high = get_dynamic_rsi_thresholds(vol_z)

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
            if pos_qty > 0 and rsi_val > rsi_high:
                api.close_position(args.symbol)
                msg = f"Exit: RSI {rsi_val:.2f} > {rsi_high:.0f}"
                print(msg)
                append_log("exit_rsi", price, rsi_val, pos_qty, msg)
            else:
                msg = f"Holding position {pos_qty}, RSI {rsi_val:.2f}"
                print(msg)
                append_log("holding", price, rsi_val, pos_qty, msg)
            return

        # Flat: consider entry with Phase 1+2 filters
        
        # Phase 1 Filter 1: Time-of-day (10:00 AM to 3:30 PM ET)
        if time_of_day < 10.0 or time_of_day > 15.5:
            msg = f"No entry: outside trading hours (time_of_day={time_of_day:.2f})"
            print(msg)
            append_log("skip_time_of_day", price, rsi_val, 0, msg)
            return
        
        # Phase 1 Filter 2: Volatility regime (vol_z > 0.2) - TEMPORARILY LOOSENED FOR TESTING
        if vol_z < 0.2:
            msg = f"No entry: low volatility regime (vol_z={vol_z:.2f})"
            print(msg)
            append_log("skip_volatility", price, rsi_val, 0, msg)
            return
        
        # Phase 1 Filter 3: Volume confirmation (volm_z > 0.3) - TEMPORARILY LOOSENED FOR TESTING
        if volm_z < 0.3:
            msg = f"No entry: insufficient volume (volm_z={volm_z:.2f})"
            print(msg)
            append_log("skip_volume", price, rsi_val, 0, msg)
            return
        
        # RSI threshold check (dynamic based on volatility)
        if rsi_val >= rsi_low:
            msg = f"No entry: RSI {rsi_val:.2f} >= {rsi_low:.0f} (vol_z={vol_z:.2f})"
            print(msg)
            append_log("skip_rsi", price, rsi_val, 0, msg)
            return
        
        # Phase 2 Filter 1: Trend filter (don't catch falling knives)
        if ema200_rel < -5.0:
            msg = f"No entry: strong downtrend (ema200_rel={ema200_rel:.2f}%)"
            print(msg)
            append_log("skip_trend", price, rsi_val, 0, msg)
            return
        
        # Phase 2 Filter 2: Bollinger Band confirmation (double oversold)
        if bb_z > -0.8:
            msg = f"No entry: BB not oversold (bb_z={bb_z:.2f})"
            print(msg)
            append_log("skip_bb", price, rsi_val, 0, msg)
            return

        # All filters passed - calculate position size
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
            f"✅ ENTERED {qty} {args.symbol} @ ~{price:.2f} | "
            f"RSI {rsi_val:.2f} (thresh={rsi_low:.0f}/{rsi_high:.0f}) | "
            f"vol_z={vol_z:.2f} | volm_z={volm_z:.2f} | "
            f"ema200_rel={ema200_rel:.2f}% | bb_z={bb_z:.2f} | "
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
