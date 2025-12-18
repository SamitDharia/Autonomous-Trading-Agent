# Phase 3.2: Multi-Timeframe RSI Confirmation

**Status**: ✅ DEPLOYED (Dec 18, 2025 - 18:24 UTC, PID 46592)  
**Goal**: Strengthen entry signals using 15-min RSI confirmation alongside 5-min RSI  
**Risk**: Medium (requires bar consolidation, more complexity)

---

## Problem Statement

**Current Entry Logic**:
- Single timeframe: 5-min RSI < 25 (oversold) triggers entry
- Fast-moving but noisy: 5-min bars capture quick reversals but also false signals

**Limitations**:
1. **Whipsaws**: 5-min RSI can spike to <25 briefly, then reverse (false oversold)
2. **Weak reversals**: Sometimes RSI <25 but broader trend still down (15-min RSI = 50+)
3. **No timeframe confirmation**: Missing multi-scale validation

**Solution**: Require both 5-min AND 15-min RSI to be oversold for entry

---

## Design Philosophy

### Multi-Timeframe Theory
- **Lower timeframe (5-min)**: Fast signals, entry timing
- **Higher timeframe (15-min)**: Trend confirmation, filter false signals
- **Alignment**: When both agree (both oversold), signal is stronger

**Example Scenarios**:

| 5-min RSI | 15-min RSI | Action | Rationale |
|-----------|------------|--------|-----------|
| 23 | 28 | ✅ ENTER | Both oversold, strong reversal setup |
| 23 | 45 | ❌ SKIP | Only 5-min oversold, 15-min neutral (weak signal) |
| 23 | 65 | ❌ SKIP | 5-min oversold but 15-min still uptrend (likely whipsaw) |
| 30 | 22 | ❌ SKIP | 15-min oversold but 5-min not extreme yet (wait for better entry) |

---

## Implementation Approaches

### Option A: Strict Dual Confirmation (Conservative)
**Logic**: BOTH timeframes must be oversold
```python
if rsi_5m < 25 and rsi_15m < 30:
    # Strong oversold across timeframes, enter
else:
    # Skip, signal not strong enough
```

**Pros**:
- ✅ Highest quality signals
- ✅ Fewer whipsaws
- ✅ Better win rate

**Cons**:
- ⚠️ Significantly fewer trades (maybe -40% to -60%)
- ⚠️ May miss some valid 5-min reversals
- ⚠️ 15-min RSI <30 is less common

**Recommended Thresholds**:
- 5-min RSI < 25 (current)
- 15-min RSI < 30 (looser than 5-min to avoid over-filtering)

---

### Option B: Directional Agreement (Balanced)
**Logic**: 15-min RSI must be <50 (bearish bias), 5-min <25 for entry
```python
if rsi_5m < 25 and rsi_15m < 50:
    # 5-min oversold + 15-min bearish = good reversal setup
else:
    # Skip
```

**Pros**:
- ✅ Moderate trade reduction (~20-30%)
- ✅ Filters strong uptrend whipsaws (15-min RSI >50)
- ✅ More forgiving than Option A

**Cons**:
- ⚠️ Still allows some weak signals (15-min RSI 45-50 range)

**Recommended Thresholds**:
- 5-min RSI < 25
- 15-min RSI < 50 (neutral/bearish only)

---

### Option C: Weighted Scoring (Advanced)
**Logic**: Score = (5-min oversold degree) + (15-min oversold degree), threshold = -50
```python
score_5m = (25 - rsi_5m)  # Higher score if more oversold
score_15m = (30 - rsi_15m) * 0.5  # Weight 15-min less

total_score = score_5m + score_15m

if total_score > 5:  # Tunable threshold
    # Combined signal strong enough
else:
    # Skip
```

**Pros**:
- ✅ Flexible: allows strong 5-min to compensate for weak 15-min
- ✅ Tunable via single parameter (threshold)

**Cons**:
- ⚠️ More complex, harder to explain
- ⚠️ Requires parameter tuning

---

## Recommended: Option B (Directional Agreement)

**Why Option B**:
1. **Balance**: Not too strict (Option A), not too loose (current single-TF)
2. **Clear logic**: "5-min oversold + 15-min not bullish"
3. **Moderate impact**: ~20-30% trade reduction (acceptable)
4. **Easy to backtest**: Simple boolean check

**Implementation**:
```python
# Calculate 15-min RSI (consolidate 5-min bars)
rsi_15m = calculate_rsi_15min(df_5min)

# Entry logic with multi-TF check
if rsi_5m < rsi_low:  # Dynamic threshold (20/25/30)
    if rsi_15m < 50:  # 15-min must be bearish/neutral
        # Phase 1+2 filters...
        # Enter if all pass
    else:
        msg = f"Skip: 5m RSI {rsi_5m:.1f} oversold but 15m RSI {rsi_15m:.1f} still bullish"
        append_log("skip_multi_tf", price, rsi_5m, 0, msg)
```

---

## Technical Implementation

### Bar Consolidation (5-min → 15-min)

**Approach 1: Pandas Resample** (Simple)
```python
def consolidate_to_15min(df_5min: pd.DataFrame) -> pd.DataFrame:
    """
    Resample 5-min bars to 15-min bars.
    Requires df_5min to have DatetimeIndex.
    """
    df_15min = df_5min.resample('15T').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum',
    }).dropna()
    
    return df_15min

def calculate_rsi_15min(df_5min: pd.DataFrame) -> float:
    """Calculate current 15-min RSI from 5-min bars"""
    df_15min = consolidate_to_15min(df_5min)
    df_15min['rsi'] = rsi(df_15min['close'], period=14)
    
    if df_15min.empty or df_15min['rsi'].isna().all():
        return 50.0  # Neutral fallback
    
    return float(df_15min['rsi'].iloc[-1])
```

**Pros**:
- ✅ Simple, one-liner resample
- ✅ Handles timezone correctly
- ✅ Standard pandas method

**Cons**:
- ⚠️ Requires enough history (14 x 15-min = 210 min = 3.5 hours)
- ⚠️ May have alignment issues if 5-min bars not on 15-min boundaries

---

### Approach 2: Manual Grouping** (More Control)
```python
def consolidate_to_15min_manual(df_5min: pd.DataFrame) -> pd.DataFrame:
    """
    Manually group 5-min bars into 15-min bars.
    Groups every 3 consecutive 5-min bars.
    """
    # Ensure we have multiple of 3 bars
    n = len(df_5min)
    n_trimmed = (n // 3) * 3
    df_trimmed = df_5min.iloc[-n_trimmed:]
    
    bars_15min = []
    for i in range(0, len(df_trimmed), 3):
        chunk = df_trimmed.iloc[i:i+3]
        
        bar_15min = {
            'timestamp': chunk.index[-1],  # Use last 5-min bar's timestamp
            'open': chunk['open'].iloc[0],
            'high': chunk['high'].max(),
            'low': chunk['low'].min(),
            'close': chunk['close'].iloc[-1],
            'volume': chunk['volume'].sum(),
        }
        bars_15min.append(bar_15min)
    
    df_15min = pd.DataFrame(bars_15min).set_index('timestamp')
    return df_15min
```

**Pros**:
- ✅ Full control over grouping logic
- ✅ No alignment issues

**Cons**:
- ⚠️ More code, manual logic
- ⚠️ Must handle edge cases (non-multiple of 3 bars)

**Recommended**: Use **Approach 1 (Resample)** for simplicity.

---

## Data Requirements

**Current Setup**:
- Fetch 14 days of 5-min bars (~1000+ bars)
- Calculate RSI(14) on 5-min timeframe

**New Requirements for 15-min RSI**:
- Need RSI(14) on 15-min bars = 14 x 15 min = 210 minutes = 3.5 hours
- But need warm-up for RSI calculation = ~28 x 15 min = 7 hours
- **Fetch same 14 days**, consolidate to 15-min, calculate RSI

**No changes needed**: Current 14-day fetch provides enough data

---

## Integration Point

**File**: `scripts/alpaca_rsi_bot.py`  
**Location**: After dynamic RSI threshold calculation, before entry logic

```python
def run_once():
    # ... (fetch 5-min bars, calculate features)
    
    df = fetch_bars(api, args.symbol, days=14, feed=args.feed)
    df = calculate_features(df)  # 5-min features
    
    latest = df.iloc[-1]
    rsi_5m = float(latest["rsi"])
    # ... (other 5-min features)
    
    # Phase 3.2: Calculate 15-min RSI
    rsi_15m = calculate_rsi_15min(df)
    
    # Get dynamic thresholds
    rsi_low, rsi_high = get_dynamic_rsi_thresholds(vol_z)
    
    # ... (position check, min hold check)
    
    # Entry logic with multi-TF filter
    if rsi_5m >= rsi_low:
        msg = f"No entry: RSI {rsi_5m:.2f} >= {rsi_low:.0f}"
        append_log("skip_rsi", price, rsi_5m, 0, msg)
        return
    
    # NEW: Multi-TF filter (Phase 3.2)
    if rsi_15m >= 50.0:
        msg = f"No entry: 5m RSI {rsi_5m:.2f} oversold but 15m RSI {rsi_15m:.2f} still bullish"
        append_log("skip_multi_tf", price, rsi_5m, 0, msg)
        return
    
    # ... (continue with Phase 1+2 filters)
```

---

## Backtest Validation Plan

### Test Matrix

| Config | 5-min RSI | 15-min RSI | Expected Impact |
|--------|-----------|------------|-----------------|
| Current (Phase 2) | <25 | N/A | Baseline (Sharpe 0.80) |
| Option A | <25 | <30 | -50% trades, +20% Sharpe (high quality) |
| Option B | <25 | <50 | -25% trades, +10% Sharpe (balanced) |
| Option C (score) | Weighted | Weighted | Variable, requires tuning |

**Success Criteria** (vs Phase 2 baseline):
- ✅ Sharpe improves by ≥10% (target: 0.88+)
- ✅ Win rate improves or stays ≥70%
- ✅ Trade reduction <40% (enough opportunities)
- ✅ Max drawdown unchanged or better

**If Option B Fails**: Try Option A (stricter) or abandon multi-TF

---

## Exit Logic (Future Enhancement)

**Current**: Exit on 5-min RSI >75 (overbought)

**Multi-TF Exit Option**:
```python
# Exit if EITHER timeframe overbought
if rsi_5m > 75 or rsi_15m > 70:
    api.close_position(symbol)
```

**Rationale**: 15-min overbought = broader reversal likely, exit even if 5-min not extreme yet

**Note**: Test this separately after entry multi-TF validated

---

## Risk Considerations

### 1. Over-Filtering
- **Risk**: Too strict multi-TF filter → very few trades
- **Mitigation**: Start with Option B (looser), tighten if needed

### 2. Data Alignment
- **Risk**: 5-min bars not aligned on 15-min boundaries → consolidation errors
- **Mitigation**: Use pandas resample (handles alignment automatically)

### 3. Insufficient History
- **Risk**: Not enough 15-min bars for RSI(14) calculation
- **Mitigation**: Check df_15min length ≥28 before calculating RSI, fallback to neutral (50) if insufficient

### 4. Performance Overhead
- **Risk**: Consolidating 5-min → 15-min every check adds computation
- **Mitigation**: Negligible (pandas resample is fast), already fetching 1000+ bars

---

## Implementation Checklist (Do After Execution Validation)

- [ ] Add `consolidate_to_15min()` function to alpaca_rsi_bot.py
- [ ] Add `calculate_rsi_15min()` function
- [ ] Insert multi-TF check in entry logic (after RSI threshold check)
- [ ] Add "skip_multi_tf" logging action
- [ ] Test manually: verify 15-min RSI calculation correct
- [ ] Backtest Option B vs Phase 2 (2020-2024)
- [ ] If validated, backtest Option A for comparison
- [ ] Document results in RSI_ENHANCEMENTS.md
- [ ] Deploy to droplet if Sharpe improves ≥10%

---

## Alternative Timeframes Considered

### 30-min RSI
- **Pros**: Even stronger trend confirmation
- **Cons**: Too slow, may miss fast reversals, fewer alignment opportunities

### 1-hour RSI
- **Pros**: Major trend filter
- **Cons**: Very slow, likely over-filters (< 10 trades/year)

### 3-min + 5-min
- **Pros**: Faster signals
- **Cons**: Both noisy, minimal filtering benefit

**Winner**: 15-min RSI (3x consolidation of 5-min, good balance)

---

## Code Snippet: Full Implementation

```python
def consolidate_to_15min(df_5min: pd.DataFrame) -> pd.DataFrame:
    """Resample 5-min bars to 15-min bars"""
    return df_5min.resample('15T').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum',
    }).dropna()


def calculate_rsi_15min(df_5min: pd.DataFrame, min_bars: int = 28) -> float:
    """
    Calculate 15-min RSI from 5-min bars.
    Returns neutral (50.0) if insufficient data.
    """
    try:
        df_15min = consolidate_to_15min(df_5min)
        
        if len(df_15min) < min_bars:
            print(f"[WARNING] Insufficient 15-min bars ({len(df_15min)} < {min_bars}), using neutral RSI")
            return 50.0
        
        df_15min['rsi'] = rsi(df_15min['close'], period=14)
        
        if df_15min['rsi'].isna().all():
            return 50.0
        
        return float(df_15min['rsi'].iloc[-1])
    
    except Exception as e:
        print(f"[ERROR] Failed to calculate 15-min RSI: {e}, using neutral")
        return 50.0
```

---

## Expected Results (Hypothesis)

**Option B** (5m <25, 15m <50):
- Trade reduction: ~25%
- Sharpe improvement: +10-15%
- Win rate improvement: +3-5%
- Avg win: unchanged
- Avg loss: -20% (better entries = smaller stops triggered)

**If successful**: Combine with Phase 3.1 (trailing stops) for maximum Sharpe

---

## Next Steps

1. **Wait for first trade execution** (Dec 18, 3 PM Ireland)
2. **If successful**: Implement trailing stops (Phase 3.1) first
3. **Then**: Add multi-TF RSI (Phase 3.2)
4. **Test both combined**: Trailing stops + multi-TF RSI
5. **Target**: Sharpe 1.0+ (vs current 0.80)

---

## See Also

- [RSI_ENHANCEMENTS.md](RSI_ENHANCEMENTS.md) - Phase 3 overview
- [PHASE3_TRAILING_STOP_DESIGN.md](PHASE3_TRAILING_STOP_DESIGN.md) - Phase 3.1 design
- [alpaca_rsi_bot.py](../scripts/alpaca_rsi_bot.py) - Current Phase 2 bot
