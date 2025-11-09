import numpy as np
import pandas as pd


def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    up = delta.clip(lower=0.0)
    down = (-delta).clip(lower=0.0)
    roll_up = up.ewm(alpha=1 / period, adjust=False).mean()
    roll_down = down.ewm(alpha=1 / period, adjust=False).mean() + 1e-12
    rs = roll_up / roll_down
    return 100 - (100 / (1 + rs))


def simulate_short_run(
    seed: int = 42,
    bars: int = 78,
    price0: float = 100.0,
    vol: float = 0.003,
):
    """Run a deterministic toy RSI strategy backtest and return metrics.

    Returns dict with keys: net_pnl, sharpe, trades
    """
    rng = np.random.default_rng(seed)
    rets = rng.normal(0.0, vol, size=bars)
    prices = price0 * np.exp(np.cumsum(rets))
    idx = pd.date_range("2020-01-02 09:30", periods=bars, freq="5min")
    df = pd.DataFrame({"price": prices}, index=idx)
    df["rsi"] = _rsi(df["price"])  # warmup via EWM

    equity = 100_000.0
    size_pct = 0.005
    position = 0  # shares
    last_entry_i = None
    min_hold = 3  # bars (~15min)
    pnl = 0.0
    trades = 0

    for i in range(1, len(df)):
        price = df["price"].iloc[i]
        prev = df["price"].iloc[i - 1]
        if position != 0:
            pnl += position * (price - prev)
        rsi = df["rsi"].iloc[i]
        if position == 0 and rsi < 30:
            qty = int((equity * size_pct) / max(price, 1e-9))
            if qty > 0:
                position = qty
                trades += 1
                last_entry_i = i
        elif (
            position != 0
            and rsi > 70
            and (last_entry_i is None or i - last_entry_i >= min_hold)
        ):
            position = 0
            trades += 1

    # Simple Sharpe proxy on 5-min bars
    bar_ret = pd.Series(prices).pct_change().dropna().values
    sharpe = float((bar_ret.mean() / (bar_ret.std() + 1e-12)) * np.sqrt(len(bar_ret)))
    return {"net_pnl": float(pnl), "sharpe": sharpe, "trades": int(trades)}


if __name__ == "__main__":
    m = simulate_short_run()
    print(
        f"BACKTEST DONE | NET_PNL: {m['net_pnl']:.2f} | SHARPE: {m['sharpe']:.2f} | TRADES: {m['trades']}"
    )

