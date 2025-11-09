import os
import sys


def require_env(name: str) -> str:
    val = os.getenv(name)
    if not val:
        print(f"ERROR: Missing required env var {name}")
        sys.exit(1)
    return val


def main() -> None:
    # Defer import to avoid installing if unused
    from alpaca_trade_api.rest import REST, TimeFrame

    key = require_env("ALPACA_API_KEY")
    secret = require_env("ALPACA_SECRET_KEY")
    base = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")

    api = REST(key, secret, base_url=base)
    acct = api.get_account()
    print(f"ALPACA PAPER OK | CASH: {acct.cash}")

    dry = ("--dry-run" in sys.argv) or (os.getenv("DRY_RUN", "1") == "1")
    if dry:
        print("DRY RUN | No orders placed")
        print("PAPER RUN OK | ORDERS QUEUED: 0")
        return

    symbol = os.getenv("SYMBOL", "TSLA")
    qty = int(os.getenv("QTY", "1"))
    bars = api.get_bars(symbol, TimeFrame.Minute, limit=5)
    last = bars[-1]
    last_price = float(getattr(last, "c", getattr(last, "close", 0.0)))
    tp = round(last_price * 1.01, 2)
    sl = round(last_price * 0.99, 2)
    o = api.submit_order(
        symbol=symbol,
        qty=qty,
        side="buy",
        type="market",
        time_in_force="day",
        order_class="bracket",
        take_profit={"limit_price": tp},
        stop_loss={"stop_price": sl},
    )
    print(f"PAPER RUN OK | ORDERS QUEUED: 1 | ORDER_ID: {o.id}")


if __name__ == "__main__":
    main()

