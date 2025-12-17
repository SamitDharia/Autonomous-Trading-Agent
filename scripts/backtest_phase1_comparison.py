"""
QuantConnect backtest comparison: RSI Baseline vs Phase 1 Enhanced

This notebook should be run in QuantConnect Research to compare:
- Baseline: RSI <25 entry, >75 exit (no filters)
- Phase 1: Same + time-of-day + volume + volatility filters

Run both strategies on same data (2020-2024 TSLA), compare metrics.
"""

import pandas as pd
import numpy as np
from datetime import datetime

# Initialize QuantBook
qb = QuantBook()
sym = qb.AddEquity("TSLA", Resolution.Minute).Symbol

# Get historical data (2020-2024 for backtesting)
start_date = datetime(2020, 1, 1)
end_date = datetime(2024, 12, 31)
hist = qb.History(sym, start=start_date, end=end_date, resolution=Resolution.Minute)

# Resample to 5-minute bars
df = hist.loc[sym].reset_index().rename(columns={"time": "timestamp"})
df = df.set_index("timestamp").sort_index()
df5 = pd.DataFrame({
    "open": df["open"].resample("5min").first(),
    "high": df["high"].resample("5min").max(),
    "low": df["low"].resample("5min").min(),
    "close": df["close"].resample("5min").last(),
    "volume": df["volume"].resample("5min").sum(),
}).dropna()

print(f"Data range: {df5.index.min()} to {df5.index.max()}")
print(f"Total 5-min bars: {len(df5)}")

# Calculate indicators


def rsi(series, period=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    roll_up = up.ewm(alpha=1/period, adjust=False).mean()
    roll_down = down.ewm(alpha=1/period, adjust=False).mean() + 1e-9
    rs = roll_up / roll_down
    return 100 - (100 / (1 + rs))


def atr(df, period=14):
    hl = df["high"] - df["low"]
    hc = (df["high"] - df["close"].shift()).abs()
    lc = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, adjust=False).mean()


# Build features
close = df5["close"]
ret1 = close.pct_change()
rsi14 = rsi(close)
atr14 = atr(df5)
atr_pct = atr14 / close

# Volatility z-score (20-bar rolling vol, 100-bar normalization)
vol20 = ret1.rolling(20).std()
vol_z = (vol20 - vol20.rolling(100).mean()) / (vol20.rolling(100).std() + 1e-9)
vol_z = vol_z.fillna(0)

# Volume z-score
volm_z = (df5["volume"] - df5["volume"].rolling(20).mean()) / (df5["volume"].rolling(20).std() + 1e-9)
volm_z = volm_z.fillna(0)

# Time of day (9.5 = 9:30am)
time_of_day = df5.index.hour + df5.index.minute / 60.0

# EMA200 for trend filter
ema200 = close.ewm(span=200, adjust=False).mean()
ema200_rel = (close - ema200) / ema200

# Bollinger Bands (20-period, 2 std dev)
bb_mid = close.rolling(20).mean()
bb_std = close.rolling(20).std()
bb_z = (close - bb_mid) / (2 * bb_std + 1e-9)

# Consolidate
df_feat = pd.DataFrame({
    "close": close,
    "rsi": rsi14,
    "atr": atr14,
    "atr_pct": atr_pct,
    "vol_z": vol_z,
    "volm_z": volm_z,
    "time_of_day": time_of_day,
    "ema200_rel": ema200_rel,
    "bb_z": bb_z,
})
df_feat = df_feat.dropna()

print(f"\nFeatures ready: {len(df_feat)} bars")

# Backtest function


def backtest_rsi(df, phase1_filters=False, phase2_enhancements=False, initial_capital=100000.0):
    """
    Backtest RSI strategy with optional Phase 1 filters and Phase 2 enhancements.
    
    Phase 1: Time-of-day, volatility regime, volume confirmation filters
    Phase 2: Dynamic RSI thresholds, trend filter (EMA200), Bollinger Band confirmation
    
    Returns DataFrame with trade log and performance metrics.
    """
    capital = initial_capital
    position = 0  # shares held
    entry_price = 0
    entry_time = None
    trades = []
    equity_curve = []
    
    # Track daily P&L for daily stop
    start_of_day_equity = capital
    current_day = None
    
    # Parameters
    rsi_buy = 25
    rsi_sell = 75
    position_size_pct = 0.0025  # 0.25%
    min_hold_minutes = 30
    daily_stop_pct = -0.01  # -1%
    commission_bps = 0.5  # 0.5 bps per trade
    slippage_bps = 2.0  # 2 bps slippage
    
    for idx, row in df.iterrows():
        # Daily reset for daily stop
        if current_day is None or idx.date() != current_day:
            current_day = idx.date()
            start_of_day_equity = capital + (position * row.close if position > 0 else 0)
        
        # Calculate current equity
        current_equity = capital + (position * row.close if position > 0 else 0)
        
        # Daily stop check
        daily_pnl_pct = (current_equity - start_of_day_equity) / start_of_day_equity
        if daily_pnl_pct <= daily_stop_pct:
            if position > 0:
                # Exit position
                exit_price = row.close * (1 - slippage_bps / 10000)
                exit_value = position * exit_price
                commission = exit_value * (commission_bps / 10000)
                capital += exit_value - commission
                
                pnl = (exit_price - entry_price) * position - commission
                hold_minutes = (idx - entry_time).total_seconds() / 60 if entry_time else 0
                
                trades.append({
                    'entry_time': entry_time,
                    'exit_time': idx,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'shares': position,
                    'pnl': pnl,
                    'hold_minutes': hold_minutes,
                    'exit_reason': 'daily_stop'
                })
                
                position = 0
                entry_price = 0
                entry_time = None
            # Skip trading for rest of day
            equity_curve.append({'time': idx, 'equity': current_equity})
            continue
        
        # Phase 1 Filters (if enabled)
        if phase1_filters:
            # 1. Time-of-day filter: 10:00-15:30 only
            if row.time_of_day < 10.0 or row.time_of_day > 15.5:
                equity_curve.append({'time': idx, 'equity': current_equity})
                continue
            
            # 2. Volatility regime filter: vol_z > 0.5
            if row.vol_z < 0.5:
                equity_curve.append({'time': idx, 'equity': current_equity})
                continue
        
        # Phase 2 Enhancements (if enabled)
        if phase2_enhancements:
            # 2.1 Dynamic RSI thresholds based on volatility
            if row.vol_z > 1.0:  # High volatility
                rsi_buy = 30
                rsi_sell = 70
            elif row.vol_z < -0.5:  # Low volatility
                rsi_buy = 20
                rsi_sell = 80
            else:  # Normal volatility
                rsi_buy = 25
                rsi_sell = 75
        else:
            # Fixed thresholds
            rsi_buy = 25
            rsi_sell = 75
        
        # Exit logic
        if position > 0 and row.rsi > rsi_sell:
            # Check minimum hold
            if entry_time and (idx - entry_time).total_seconds() / 60 >= min_hold_minutes:
                exit_price = row.close * (1 - slippage_bps / 10000)
                exit_value = position * exit_price
                commission = exit_value * (commission_bps / 10000)
                capital += exit_value - commission
                
                pnl = (exit_price - entry_price) * position - commission
                hold_minutes = (idx - entry_time).total_seconds() / 60
                
                trades.append({
                    'entry_time': entry_time,
                    'exit_time': idx,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'shares': position,
                    'pnl': pnl,
                    'hold_minutes': hold_minutes,
                    'exit_reason': 'rsi_exit'
                })
                
                position = 0
                entry_price = 0
                entry_time = None
        
        # Entry logic
        if position == 0 and row.rsi < rsi_buy:
            # Phase 1 Filter 3: Volume confirmation (if enabled)
            if phase1_filters and row.volm_z < 1.0:
                equity_curve.append({'time': idx, 'equity': current_equity})
                continue
            
            # Phase 2 Filter 2: Trend filter (if enabled)
            if phase2_enhancements and row.ema200_rel < -0.05:
                equity_curve.append({'time': idx, 'equity': current_equity})
                continue
            
            # Phase 2 Filter 3: Bollinger Band confirmation (if enabled)
            if phase2_enhancements and row.bb_z > -0.8:
                equity_curve.append({'time': idx, 'equity': current_equity})
                continue
            
            # Enter position
            target_value = current_equity * position_size_pct
            entry_price = row.close * (1 + slippage_bps / 10000)
            position = int(target_value / entry_price)
            
            if position > 0:
                entry_value = position * entry_price
                commission = entry_value * (commission_bps / 10000)
                capital -= entry_value + commission
                entry_time = idx
        
        equity_curve.append({'time': idx, 'equity': current_equity})
    
    # Close any remaining position at end
    if position > 0:
        final_row = df.iloc[-1]
        exit_price = final_row.close * (1 - slippage_bps / 10000)
        exit_value = position * exit_price
        commission = exit_value * (commission_bps / 10000)
        capital += exit_value - commission
        
        pnl = (exit_price - entry_price) * position - commission
        hold_minutes = (df.index[-1] - entry_time).total_seconds() / 60 if entry_time else 0
        
        trades.append({
            'entry_time': entry_time,
            'exit_time': df.index[-1],
            'entry_price': entry_price,
            'exit_price': exit_price,
            'shares': position,
            'pnl': pnl,
            'hold_minutes': hold_minutes,
            'exit_reason': 'end_of_test'
        })
    
    # Convert to DataFrames
    trades_df = pd.DataFrame(trades)
    equity_df = pd.DataFrame(equity_curve)
    
    # Calculate metrics
    if len(trades_df) > 0:
        total_pnl = trades_df['pnl'].sum()
        win_rate = (trades_df['pnl'] > 0).mean()
        avg_win = trades_df[trades_df['pnl'] > 0]['pnl'].mean() if (trades_df['pnl'] > 0).any() else 0
        avg_loss = trades_df[trades_df['pnl'] < 0]['pnl'].mean() if (trades_df['pnl'] < 0).any() else 0
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
        
        # Equity curve metrics
        equity_df['returns'] = equity_df['equity'].pct_change()
        sharpe = (equity_df['returns'].mean() / equity_df['returns'].std()) * np.sqrt(252 * 78) if equity_df['returns'].std() > 0 else 0  # 78 5-min bars/day
        max_dd = ((equity_df['equity'].cummax() - equity_df['equity']) / equity_df['equity'].cummax()).max()
        
        metrics = {
            'total_pnl': total_pnl,
            'total_return_pct': (total_pnl / initial_capital) * 100,
            'trade_count': len(trades_df),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'sharpe': sharpe,
            'max_drawdown': max_dd,
            'final_equity': equity_df['equity'].iloc[-1]
        }
    else:
        metrics = {
            'total_pnl': 0,
            'total_return_pct': 0,
            'trade_count': 0,
            'win_rate': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'profit_factor': 0,
            'sharpe': 0,
            'max_drawdown': 0,
            'final_equity': initial_capital
        }
    
    return trades_df, equity_df, metrics


# Run all backtests
print("\n" + "="*60)
print("RUNNING BASELINE RSI BACKTEST")
print("="*60)
trades_baseline, equity_baseline, metrics_baseline = backtest_rsi(df_feat, phase1_filters=False, phase2_enhancements=False)

print("\n" + "="*60)
print("RUNNING PHASE 1 BACKTEST")
print("="*60)
trades_phase1, equity_phase1, metrics_phase1 = backtest_rsi(df_feat, phase1_filters=True, phase2_enhancements=False)

print("\n" + "="*60)
print("RUNNING PHASE 1+2 COMBINED BACKTEST")
print("="*60)
trades_phase12, equity_phase12, metrics_phase12 = backtest_rsi(df_feat, phase1_filters=True, phase2_enhancements=True)

# Compare results
print("\n" + "="*60)
print("BACKTEST COMPARISON RESULTS")
print("="*60)
print(f"\n{'Metric':<25} {'Baseline':>15} {'Phase 1':>15} {'Phase 1+2':>15}")
print("-" * 78)

for key in metrics_baseline.keys():
    baseline_val = metrics_baseline[key]
    phase1_val = metrics_phase1[key]
    phase12_val = metrics_phase12[key]
    
    if key in ['total_return_pct', 'win_rate', 'max_drawdown']:
        print(f"{key:<25} {baseline_val:>14.2f}% {phase1_val:>14.2f}% {phase12_val:>14.2f}%")
    elif key in ['sharpe', 'profit_factor']:
        print(f"{key:<25} {baseline_val:>15.2f} {phase1_val:>15.2f} {phase12_val:>15.2f}")
    elif key == 'trade_count':
        print(f"{key:<25} {baseline_val:>15.0f} {phase1_val:>15.0f} {phase12_val:>15.0f}")
    else:
        print(f"{key:<25} ${baseline_val:>14,.2f} ${phase1_val:>14,.2f} ${phase12_val:>14,.2f}")

# Detailed trade analysis
print("\n" + "="*60)
print("TRADE ANALYSIS")
print("="*60)

if len(trades_baseline) > 0:
    print(f"\nBaseline - First 5 trades:")
    print(trades_baseline.head())
    print(f"\nBaseline - Win/Loss breakdown:")
    print(trades_baseline.groupby(trades_baseline['pnl'] > 0)['pnl'].agg(['count', 'mean', 'sum']))

if len(trades_phase1) > 0:
    print(f"\nPhase 1 - First 5 trades:")

if len(trades_phase12) > 0:
    print(f"\nPhase 1+2 - First 5 trades:")
    print(trades_phase12.head())
    print(f"\nPhase 1+2 - Win/Loss breakdown:")
    print(trades_phase12.groupby(trades_phase12['pnl'] > 0)['pnl'].agg(['count', 'mean', 'sum']))
if len(trades_phase1) > 0:
    print(f"\nPhase 1 - First 5 trades:")
    print(trades_phase1.head())
    print(f"\nPhase 1 - Win/Loss breakdown:")
    print(trades_phase1.groupby(trades_phase1['pnl'] > 0)['pnl'].agg(['count', 'mean', 'sum']))

if len(trades_phase12) > 0:
    print(f"\nPhase 1+2 - First 5 trades:")
    print(trades_phase12.head())
    print(f"\nPhase 1+2 - Win/Loss breakdown:")
    print(trades_phase12.groupby(trades_phase12['pnl'] > 0)['pnl'].agg(['count', 'mean', 'sum']))

# Verdict
print("\n" + "="*60)
print("VERDICT")
print("="*60)

# Phase 1 vs Baseline
sharpe_p1_abs = metrics_phase1['sharpe'] - metrics_baseline['sharpe']
win_rate_p1_delta = metrics_phase1['win_rate'] - metrics_baseline['win_rate']

print(f"\n** PHASE 1 vs BASELINE **")
print(f"Sharpe: {metrics_baseline['sharpe']:.2f} → {metrics_phase1['sharpe']:.2f} ({sharpe_p1_abs:+.2f} absolute)")
print(f"Win rate: {metrics_baseline['win_rate']:.1%} → {metrics_phase1['win_rate']:.1%} ({win_rate_p1_delta:+.1%})")
print(f"Trade count: {metrics_baseline['trade_count']} → {metrics_phase1['trade_count']} ({((metrics_phase1['trade_count'] - metrics_baseline['trade_count']) / metrics_baseline['trade_count'] * 100):+.1f}%)")

# Phase 1+2 vs Phase 1
sharpe_p12_abs = metrics_phase12['sharpe'] - metrics_phase1['sharpe']
sharpe_p12_pct = ((metrics_phase12['sharpe'] - metrics_phase1['sharpe']) / abs(metrics_phase1['sharpe']) * 100) if metrics_phase1['sharpe'] != 0 else 0
win_rate_p12_delta = metrics_phase12['win_rate'] - metrics_phase1['win_rate']

print(f"\n** PHASE 1+2 vs PHASE 1 **")
print(f"Sharpe: {metrics_phase1['sharpe']:.2f} → {metrics_phase12['sharpe']:.2f} ({sharpe_p12_abs:+.2f} absolute, {sharpe_p12_pct:+.1f}%)")
print(f"Win rate: {metrics_phase1['win_rate']:.1%} → {metrics_phase12['win_rate']:.1%} ({win_rate_p12_delta:+.1%})")
print(f"Trade count: {metrics_phase1['trade_count']} → {metrics_phase12['trade_count']} ({((metrics_phase12['trade_count'] - metrics_phase1['trade_count']) / metrics_phase1['trade_count'] * 100) if metrics_phase1['trade_count'] > 0 else 0:+.1f}%)")

# Decisions
print(f"\n** DECISIONS **")
if sharpe_p1_abs >= 0.5 or (metrics_phase1['sharpe'] > 0 and metrics_baseline['sharpe'] < 0):
    print("✅ PHASE 1 PROMOTED: Turned losing strategy profitable (Sharpe negative → positive)")
else:
    print("❌ PHASE 1 NOT PROMOTED: Insufficient improvement")

if sharpe_p12_pct >= 10 or win_rate_p12_delta >= 0.05:
    print("✅ PHASE 2 ADDS VALUE: Sharpe +10% OR win rate +5% over Phase 1")
    print("   → Deploy Phase 1+2 combined to paper trading")
elif metrics_phase12['sharpe'] > metrics_phase1['sharpe']:
    print("⚠️  PHASE 2 MARGINAL: Improvement <10%, consider deploying Phase 1 only")
else:
    print("❌ PHASE 2 DEGRADES: Stick with Phase 1 only")

print("\n" + "="*60)
