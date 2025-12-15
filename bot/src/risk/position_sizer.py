def qty_by_atr(equity, risk_per_trade, atr, stop_atr_mult=1.5, min_qty=1, max_notional=None):
    stop_dist = max(1e-6, stop_atr_mult * atr)
    risk_dollars = equity * risk_per_trade
    qty = int(risk_dollars / stop_dist)
    if max_notional is not None:
        qty = min(qty, int(max_notional // stop_dist))
    return max(min_qty, qty)
