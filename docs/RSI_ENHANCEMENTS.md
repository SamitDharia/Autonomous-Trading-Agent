# RSI Baseline Strategy Enhancements

**Status**: Phase 1 in development  
**Last Updated**: 2025-12-17

## Executive Summary

The RSI baseline strategy (enter <25, exit >75, 0.25% cap, 30m hold, ATR brackets) is our champion after brain models failed to achieve meaningful AUC (0.50-0.52). This document outlines a phased approach to systematically improve the RSI baseline through regime filtering, dynamic logic, and advanced execution techniques.

**Key Finding**: RSI baseline works due to **strict risk management**, not prediction. Enhancements focus on **trade quality over quantity** - filter out low-probability setups, optimize exits, and adapt to market regimes.

---

## Current Baseline Parameters

```python
# Entry
rsi_buy_threshold = 25    # Oversold entry
rsi_sell_threshold = 75   # Overbought exit

# Position Sizing
position_size = 0.0025    # 0.25% of equity

# Risk Management
min_hold = 30 minutes     # Prevent overtrading
daily_stop = -1.0%        # Kill-switch
stop_loss = 1.0 * ATR     # Protective stop
take_profit = 2.0 * ATR   # Profit target

# Filters
None (trades all market hours, all volatility regimes)
```

**Current Performance** (from paper trading):
- Sharpe: ~1.0-1.2
- Win Rate: ~55-60%
- Max Drawdown: ~2-3%
- Trade Frequency: 2-5 trades/day

---

## Phase 1: Quick Win Filters (Week 1)

**Goal**: Eliminate low-quality trades in unfavorable conditions  
**Expected Impact**: +10-20% Sharpe, -30% losing trades  
**Implementation Time**: 1-2 hours  
**Risk**: Low (pure filters, no logic changes)

### 1.1 Time-of-Day Filter

**Rationale**: Market open (9:30-10:00) and close (3:30-4:00) have wide spreads, erratic price action, and low liquidity in 5-min bars. Mean reversion signals are noisier.

**Implementation**:
```python
time_of_day = features["time_of_day"]  # Already calculated (9.5 = 9:30am)

# Skip trading during first/last 30 minutes
if time_of_day < 10.0 or time_of_day > 15.5:
    return  # Outside core trading hours
```

**Backtest Hypothesis**:
- ✅ Fewer false entries during volatile open/close
- ✅ Better fills (tighter spreads)
- ✅ Reduced slippage costs
- ⚠️ Slightly fewer trades (~10% reduction)

---

### 1.2 Volume Confirmation Filter

**Rationale**: RSI <25 + volume spike = stronger reversal signal. High volume indicates institutional absorption or capitulation, not just noise.

**Implementation**:
```python
volm_z = features["volm_z"]  # Volume z-score (already calculated)

# Entry logic
if not invested and rsi < 25:
    if volm_z > 1.0:  # Volume > 1 std dev above 20-bar average
        # Enter position (strong signal)
    else:
        # Skip entry, volume too low (weak signal)
        return
```

**Backtest Hypothesis**:
- ✅ Higher win rate (+5-10%)
- ✅ Fewer whipsaw entries in low-volume choppy periods
- ⚠️ Moderate trade reduction (~20%)

---

### 1.3 Volatility Regime Filter

**Rationale**: Mean reversion requires volatility. In low-vol ranges (<0.5σ), price moves are small and RSI extremes are false signals (whipsaws). Only trade when volatility is above average.

**Implementation**:
```python
vol_regime = features["vol_z"]  # Volatility z-score (already calculated)

# Check at start of trade logic
if vol_regime < 0.5:  # Below average volatility
    # Skip trading, not enough movement for profitable reversions
    return
```

**Backtest Hypothesis**:
- ✅ Significantly higher Sharpe (+15-25%)
- ✅ Fewer losing trades in low-vol consolidations
- ⚠️ Moderate trade reduction (~25%)

---

### Phase 1 Implementation Checklist

- [ ] Add time-of-day filter to `_on_five_minute_bar()` in [algo.py](../algo.py)
- [ ] Add volume confirmation to entry logic
- [ ] Add volatility regime filter
- [ ] Update `self.Debug()` logs to show filter status
- [ ] Create backtest comparison: baseline vs Phase 1
- [ ] Document results in [DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md)

**Acceptance Criteria**:
- Sharpe improves by ≥10%
- Win rate improves or stays flat
- Max drawdown decreases or stays flat
- Trade count reduction <40%

---

## Phase 2: Dynamic Logic (Week 2-3)

**Goal**: Adapt strategy to market conditions  
**Expected Impact**: +5-15% Sharpe, better regime adaptation  
**Implementation Time**: 2-4 hours  
**Risk**: Moderate (introduces complexity, needs tuning)

### 2.1 Dynamic RSI Thresholds

**Rationale**: Fixed 25/75 thresholds work for normal volatility. In high-vol regimes, loosen (more trades). In low-vol, tighten (higher conviction).

**Implementation**:
```python
vol_regime = features["vol_z"]

# Adaptive thresholds
if vol_regime > 1.0:  # High volatility
    rsi_buy = 30   # Loosen threshold (price moves faster)
    rsi_sell = 70
elif vol_regime < -0.5:  # Low volatility
    rsi_buy = 20   # Tighten (only extreme signals)
    rsi_sell = 80
else:  # Normal volatility
    rsi_buy = 25
    rsi_sell = 75

if not invested and rsi < rsi_buy:
    # Enter with adaptive threshold
```

**Backtest Hypothesis**:
- ✅ More trades in volatile periods (higher opportunity)
- ✅ Fewer whipsaws in calm markets
- ⚠️ Requires parameter tuning per symbol

---

### 2.2 Trend Filter

**Rationale**: Don't fight strong trends. If price is >5% below EMA200 (strong downtrend), RSI <25 might not bounce - could be start of crash.

**Implementation**:
```python
ema200_rel = features["ema200_rel"]  # (close - ema200) / ema200

if not invested and rsi < 25:
    if ema200_rel < -0.05:  # Price > 5% below EMA200
        # Strong downtrend, skip long entry
        return
    # Enter position (uptrend or neutral)
```

**Backtest Hypothesis**:
- ✅ Fewer large drawdowns during crashes
- ✅ Protects capital in persistent trends
- ⚠️ May miss some valid reversals

---

### 2.3 Bollinger Band Confirmation

**Rationale**: RSI <25 + price touching lower BB = double confirmation of oversold condition.

**Implementation**:
```python
bb_z = features["bb_z"]  # (price - BB_mid) / (2 * BB_std)

if not invested and rsi < 25:
    if bb_z < -0.8:  # Price near lower Bollinger Band
        # Strong oversold, enter
    else:
        # RSI extreme but price not at BB (weaker signal)
        return
```

**Backtest Hypothesis**:
- ✅ Higher win rate (+3-5%)
- ✅ Better entry timing
- ⚠️ Fewer trades (~15% reduction)

---

### Phase 2 Implementation Checklist

- [ ] Implement dynamic RSI thresholds
- [ ] Add trend filter (EMA200 relative position)
- [ ] Add Bollinger Band confirmation
- [ ] Backtest each enhancement individually (A/B test)
- [ ] Combine best-performing filters
- [ ] Document parameter sensitivity analysis

---

## Phase 3: Advanced Techniques (Week 4+)

**Goal**: Optimize exits, add multi-timeframe, enable scaling  
**Expected Impact**: +10-20% profit per trade  
**Implementation Time**: 4-8 hours  
**Risk**: High (requires careful testing, position management complexity)

### 3.1 Trailing ATR Stop

**Rationale**: Fixed RSI >75 exit might leave money on the table. Trail stop locks in profits during strong reversals.

**Implementation**:
```python
# On each 5-min bar, if invested:
if invested and self._stop_ticket is not None:
    current_price = bar.Close
    entry_price = self.Portfolio[self.symbol].AveragePrice
    atr_value = float(self.atr.Current.Value)
    
    # Only trail if profitable
    if current_price > entry_price:
        new_stop = current_price - 1.5 * atr_value
        old_stop = self._stop_ticket.Get(OrderField.StopPrice)
        
        # Only move stop up, never down
        if new_stop > old_stop:
            self._stop_ticket.Update(UpdateOrderFields() {StopPrice = new_stop})
```

**Backtest Hypothesis**:
- ✅ Higher profit per trade (+10-20%)
- ✅ Locks in gains during strong moves
- ⚠️ May exit too early on volatile bounces

---

### 3.2 Multi-Timeframe RSI Confirmation

**Rationale**: If both 5-min and 15-min RSI are oversold, signal is stronger (not just short-term noise).

**Implementation**:
```python
# In Initialize():
self.rsi_15m = RelativeStrengthIndex(14, MovingAverageType.Wilders)
consolidator_15m = self.Consolidate(self.symbol, timedelta(minutes=15), lambda bar: None)
self.RegisterIndicator(self.symbol, self.rsi_15m, consolidator_15m)

# In trade logic:
if not invested and rsi < 25:
    if self.rsi_15m.Current.Value < 30:  # 15-min also oversold
        # Strong multi-timeframe entry signal
    else:
        # 5-min noise, skip
        return
```

**Backtest Hypothesis**:
- ✅ Significantly higher win rate (+5-10%)
- ✅ Fewer false entries
- ⚠️ Fewer trades (~20-30% reduction)

---

### 3.3 Position Scaling (Pyramiding)

**Rationale**: If RSI drops to 15 after initial entry at 25, signal is even stronger. Add to position (max 1.5x initial size).

**Implementation**:
```python
if invested and rsi < 15:  # Extreme oversold while already long
    current_value = abs(self.Portfolio[self.symbol].HoldingsValue)
    max_target = self.Portfolio.TotalPortfolioValue * 0.0025 * 1.5  # 1.5x max
    
    if current_value < max_target:
        additional_qty = int((max_target - current_value) / bar.Close)
        if additional_qty > 0:
            self.MarketOrder(self.symbol, additional_qty, tag="Scale-in RSI<15")
            # Adjust stop to breakeven on total position
```

**Backtest Hypothesis**:
- ✅ Bigger winners on strong reversals
- ⚠️ Higher risk (larger position size)
- ⚠️ Requires careful stop management

---

### 3.4 VIX Regime Filter

**Rationale**: Mean reversion needs market volatility. If VIX <15, markets are calm (fewer opportunities). Only trade when VIX >18.

**Implementation**:
```python
# In Initialize():
self.vix = self.AddData(CBOE, "VIX", Resolution.Daily).Symbol

# In trade logic:
vix_value = self.Securities[self.vix].Price
if vix_value < 18:  # Low volatility regime
    # Skip trading, market too calm
    return
```

**Backtest Hypothesis**:
- ✅ Fewer trades, higher Sharpe (only favorable regimes)
- ✅ Better risk-adjusted returns
- ⚠️ Requires VIX data subscription

---

### Phase 3 Implementation Checklist

- [ ] Implement trailing ATR stop
- [ ] Add 15-min RSI confirmation
- [ ] Build position scaling logic
- [ ] Add VIX regime filter (if data available)
- [ ] Comprehensive backtest: all phases combined
- [ ] Forward test in paper trading for 2+ weeks

---

## Testing Framework

### Backtest Metrics

Track for each phase:
```
Sharpe Ratio         (target: ≥1.5)
Win Rate %           (target: ≥60%)
Profit Factor        (target: ≥1.8)
Max Drawdown %       (target: ≤3%)
Avg Win / Avg Loss   (target: ≥1.5)
Trade Count          (baseline: 2-5/day)
```

### A/B Test Protocol

For each enhancement:
1. **Baseline**: Run 2020-2024 backtest with current code
2. **Enhanced**: Run same period with single enhancement
3. **Compare**: Document delta in metrics table
4. **Decision**: Keep if Sharpe +10% OR win rate +5% AND drawdown unchanged

### Parameter Sensitivity

Test key thresholds:
- Time-of-day: 9:45-10:00 vs 10:00-10:15 (entry cutoff)
- Volume: volm_z > 0.5 vs 1.0 vs 1.5
- Volatility: vol_z > 0.3 vs 0.5 vs 0.7
- Dynamic RSI: [20,80] vs [25,75] vs [30,70]

---

## Rollout Plan

**Week 1**: Phase 1 implementation + backtest  
**Week 2**: Deploy Phase 1 to paper trading, monitor 5 days  
**Week 3**: Phase 2 implementation + backtest  
**Week 4**: Combined Phase 1+2 paper testing  
**Week 5+**: Phase 3 research (if needed)

**Success Criteria for Production**:
- Paper trading Sharpe ≥1.3 for 10+ days
- Win rate ≥58%
- Max daily drawdown <2%
- No critical bugs or missed exits

---

## Risk Warnings

**Over-Optimization**: Too many filters = curve-fitting. Limit to 3-4 filters max.  
**Look-Ahead Bias**: Ensure all features are available in real-time (no future data).  
**Regime Change**: Backtest includes 2020-2024 (COVID, inflation, rate hikes). May not work in all futures.  
**Transaction Costs**: Slippage + commission must be included in backtests (10 bps TSLA).

---

## See Also

- [DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md) - Implementation results
- [algo.py](../algo.py) - Current strategy code
- [PLAN.md](PLAN.md) - 8-week roadmap (Week 4 in progress)
- [BACKLOG.md](BACKLOG.md) - Future enhancements and infrastructure

---

**Next Action**: Implement Phase 1 filters in [algo.py](../algo.py)
