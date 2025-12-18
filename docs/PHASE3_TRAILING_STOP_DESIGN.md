# Phase 3.1: Trailing ATR Stop Design

**Status**: ✅ DEPLOYED (Dec 18, 2025 - 18:07 UTC, PID 46592)  
**Goal**: Lock in profits during strong reversals without leaving money on the table  
**Risk**: Medium (requires order management, more complexity than fixed exits)

---

## Problem Statement

**Current Exit Logic**:
- Fixed RSI >75 exit threshold
- Bracket order with static stop-loss (entry - 1*ATR) and take-profit (entry + 2*ATR)

**Limitations**:
1. **Leaves money on table**: If RSI hits 75 but continues to 85+, we exit too early
2. **Fixed stops don't adapt**: Price may move significantly but stop stays at original level
3. **No profit protection**: If price hits +3*ATR then reverses, we might still exit at +2*ATR or worse

**Solution**: Trailing stop that locks in profits as price moves in our favor

---

## Design Constraints

### Must-Haves
1. **Only trail when profitable**: Never move stop-loss down (widen risk)
2. **Preserve bracket order**: Don't break existing stop-loss/take-profit structure
3. **Zero-risk implementation**: If update fails, fallback to original bracket stops
4. **Backtest validation**: Must improve Sharpe by ≥10% vs Phase 2 baseline

### Nice-to-Haves
1. Configurable trail distance (1.5 ATR vs 2.0 ATR parameter)
2. Trail frequency control (every bar? every 0.5*ATR move?)
3. Acceleration: tighten trail distance as profit increases

---

## Alpaca API Research

### Bracket Order Structure
Current entry code:
```python
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
```

**Bracket Order Behavior**:
- Creates 3 orders: entry (market), stop-loss (stop), take-profit (limit)
- Stop-loss order has `order_id` that can be retrieved
- Once entry fills, stop-loss becomes active with its own order ID

### Order Update API

**Alpaca REST API**:
```python
# Get all open orders
orders = api.list_orders(status='open', symbols=[symbol])

# Find stop-loss order (has stop_price attribute)
stop_order = [o for o in orders if o.stop_price is not None][0]

# Update stop-loss order
api.replace_order(
    order_id=stop_order.id,
    qty=stop_order.qty,
    time_in_force='day',
    limit_price=None,  # Not a limit order
    stop_price=new_stop_price,  # New trailing stop
    client_order_id=stop_order.client_order_id,
)
```

**Important Notes**:
- `replace_order()` cancels old order and submits new one atomically
- If replacement fails, original order stays active (safe)
- Can only update unfilled orders (stop-loss is unfilled until triggered)

---

## Trailing Stop Logic

### High-Level Algorithm

```python
def maybe_update_trailing_stop(api, symbol, entry_price, current_price, atr_val):
    """
    Update stop-loss if price has moved favorably and we can lock in profit.
    
    Called every 5-min bar check (same frequency as entry logic).
    """
    # 1. Check if we have an open position
    try:
        pos = api.get_position(symbol)
        if float(pos.qty) <= 0:
            return  # No long position, nothing to trail
    except:
        return  # No position
    
    # 2. Only trail if profitable
    unrealized_pnl = current_price - entry_price
    if unrealized_pnl <= 0:
        return  # Not profitable yet, don't trail
    
    # 3. Calculate new trailing stop (price - 1.5 ATR)
    trail_distance = 1.5 * atr_val
    new_stop_price = current_price - trail_distance
    
    # 4. Get current stop-loss order
    orders = api.list_orders(status='open', symbols=[symbol])
    stop_orders = [o for o in orders if o.stop_price is not None]
    if not stop_orders:
        print("[TRAIL WARNING] No stop-loss order found")
        return
    
    stop_order = stop_orders[0]
    old_stop_price = float(stop_order.stop_price)
    
    # 5. Only move stop UP, never down
    if new_stop_price <= old_stop_price:
        return  # New stop worse than current, don't update
    
    # 6. Ensure new stop is at least breakeven
    min_acceptable_stop = entry_price - 0.01  # Allow $0.01 below entry
    if new_stop_price < min_acceptable_stop:
        new_stop_price = min_acceptable_stop  # Lock in at least breakeven
    
    # 7. Update stop-loss order
    try:
        api.replace_order(
            order_id=stop_order.id,
            qty=stop_order.qty,
            time_in_force='day',
            stop_price=round(new_stop_price, 2),
        )
        print(f"[TRAIL] Moved stop ${old_stop_price:.2f} → ${new_stop_price:.2f} "
              f"(profit secured: ${new_stop_price - entry_price:.2f})")
    except Exception as e:
        print(f"[TRAIL ERROR] Failed to update stop: {e}")
        # Original stop still active, safe to continue
```

### Integration Point

**Where to insert**: After position check in `run_once()`, before entry logic

```python
def run_once():
    # ... (fetch data, calculate features)
    
    # Current position?
    pos_qty = 0.0
    entry_price = None
    try:
        pos = api.get_position(args.symbol)
        pos_qty = float(pos.qty)
        entry_price = float(pos.avg_entry_price)
    except:
        pos_qty = 0.0
    
    if pos_qty > 0:
        # PHASE 3: Update trailing stop if profitable
        maybe_update_trailing_stop(
            api=api,
            symbol=args.symbol,
            entry_price=entry_price,
            current_price=price,
            atr_val=atr_val,
        )
        
        # Existing exit logic (RSI > threshold)
        if rsi_val > rsi_high:
            api.close_position(args.symbol)
            # ...
```

---

## Parameters to Test

### Trail Distance
- **1.0 ATR**: Tight trail, locks in profit quickly but may exit early on volatility
- **1.5 ATR**: Balanced (recommended starting point)
- **2.0 ATR**: Loose trail, allows more breathing room but less profit protection

### Trail Frequency
- **Every bar (5 min)**: Most responsive, max profit protection
- **Every 0.5 ATR move**: Reduces API calls, less noise
- **Only when profit > 1 ATR**: Conservative, waits for significant profit first

### Breakeven Lock
- **Immediate**: Move stop to breakeven as soon as profitable
- **After +0.5 ATR**: Wait for some profit cushion before locking breakeven
- **After +1.0 ATR**: Conservative, only lock in after substantial profit

---

## Backtest Validation Plan

### Test Setup
1. Fork `alpaca_rsi_bot.py` → `alpaca_rsi_bot_phase3.py`
2. Add trailing stop logic
3. Run backtest on 2020-2024 TSLA data
4. Compare to Phase 2 baseline (Sharpe 0.80, Win Rate 72.7%)

### Success Criteria
- ✅ Sharpe improves by ≥10% (target: 0.88+)
- ✅ Avg win increases (capturing more of strong moves)
- ✅ Max drawdown unchanged or improved
- ✅ Win rate stays ≥70% (don't sacrifice quality)

### Failure Modes to Watch
- ⚠️ **Overtrailing**: Stops too tight, get shaken out on normal volatility
- ⚠️ **API errors**: Replace order failures cause missed exits
- ⚠️ **Backtest optimism**: Works in backtest, fails live (forward-test required)

---

## Risk Mitigation

### 1. API Failure Handling
```python
try:
    api.replace_order(...)
except Exception as e:
    # Log error but don't crash
    append_log("trail_error", price, rsi_val, qty, str(e))
    # Original stop-loss still active, position protected
```

### 2. Sanity Checks
```python
# Never move stop above current price (instant trigger)
if new_stop_price >= current_price:
    raise ValueError("Invalid stop: above current price")

# Never widen stop (move down)
if new_stop_price < old_stop_price:
    return  # Silently skip, don't update
```

### 3. Logging
Log every trail attempt for post-trade analysis:
```csv
timestamp,symbol,action,price,rsi,qty,note
2025-12-18 10:35:00,TSLA,trail_skip,245.30,65.2,12,new_stop $243.50 <= old_stop $244.00
2025-12-18 10:40:00,TSLA,trail_update,247.85,68.4,12,stop $244.00 → $246.10 (+$2.10)
```

---

## Alternative Approaches Considered

### Option A: Percentage-Based Trail
- Trail at fixed % below current price (e.g., 2%)
- **Rejected**: Doesn't adapt to volatility (2% on TSLA may be too tight/loose)

### Option B: EMA-Based Trail
- Set stop at EMA(20) or EMA(50)
- **Rejected**: EMA lags, may not lock in fast-moving profits

### Option C: Parabolic SAR
- Use SAR indicator as dynamic stop
- **Rejected**: Too complex for Phase 3, save for Phase 4+

**Winner**: ATR-based trail (adapts to volatility, simple to implement)

---

## Implementation Checklist (Do After Execution Validation)

- [ ] Create `scripts/alpaca_rsi_bot_phase3.py` (fork of Phase 2 bot)
- [ ] Implement `maybe_update_trailing_stop()` function
- [ ] Add integration point in `run_once()` position check
- [ ] Add trail logging to `alpaca_rsi_log.csv`
- [ ] Test manually with paper trading (1 trade)
- [ ] Backtest Phase 3 vs Phase 2 (2020-2024)
- [ ] Document results in RSI_ENHANCEMENTS.md
- [ ] If validated, merge to main bot and deploy to droplet

---

## Next Steps

1. **Wait for first trade execution** (Dec 18, 3 PM Ireland)
2. **If successful**: Implement Phase 3 trailing stops
3. **If failed**: Debug bracket orders first, Phase 3 waits

**Target Timeline**:
- **Dec 18**: Validate execution works
- **Dec 19**: Implement trailing stops (if execution OK)
- **Dec 20-21**: Backtest + paper test Phase 3
- **Dec 22**: Deploy Phase 3 to droplet if validated

---

## See Also

- [RSI_ENHANCEMENTS.md](RSI_ENHANCEMENTS.md) - Phase 3 overview
- [alpaca_rsi_bot.py](../scripts/alpaca_rsi_bot.py) - Current Phase 2 bot
- Alpaca API Docs: https://alpaca.markets/docs/api-references/trading-api/orders/
