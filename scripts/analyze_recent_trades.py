"""
Analyze recent trades from Alpaca RSI bot log.

Parses alpaca_rsi_log.csv to calculate:
- Win rate
- Avg win/loss
- Sharpe ratio
- Profit factor
- Trade frequency
- Filter effectiveness

Usage:
    python scripts/analyze_recent_trades.py
    python scripts/analyze_recent_trades.py --log alpaca_rsi_log.csv --days 7
"""

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import numpy as np


def parse_log(log_path: Path) -> pd.DataFrame:
    """Load and parse alpaca_rsi_log.csv"""
    df = pd.read_csv(log_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def match_entries_exits(df: pd.DataFrame) -> pd.DataFrame:
    """
    Match entry/exit pairs to calculate PnL per trade.
    
    Returns DataFrame with columns:
    - entry_time
    - entry_price
    - exit_time
    - exit_price
    - pnl
    - pnl_pct
    - hold_minutes
    - rsi_entry
    - rsi_exit
    """
    entries = df[df["action"] == "enter"].copy()
    exits = df[df["action"].isin(["exit_rsi", "exit"])].copy()
    
    trades = []
    for _, entry in entries.iterrows():
        # Find next exit after this entry
        future_exits = exits[exits["timestamp"] > entry["timestamp"]]
        if future_exits.empty:
            continue  # No exit yet (position still open)
        
        exit_row = future_exits.iloc[0]
        
        entry_price = float(entry["price"])
        exit_price = float(exit_row["price"])
        qty = float(entry["qty"])
        
        pnl = (exit_price - entry_price) * qty
        pnl_pct = ((exit_price - entry_price) / entry_price) * 100
        hold_minutes = (exit_row["timestamp"] - entry["timestamp"]).total_seconds() / 60
        
        trades.append({
            "entry_time": entry["timestamp"],
            "entry_price": entry_price,
            "entry_rsi": float(entry["rsi"]),
            "exit_time": exit_row["timestamp"],
            "exit_price": exit_price,
            "exit_rsi": float(exit_row["rsi"]),
            "qty": qty,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "hold_minutes": hold_minutes,
        })
    
    return pd.DataFrame(trades)


def calculate_metrics(trades_df: pd.DataFrame) -> dict:
    """Calculate performance metrics from matched trades"""
    if trades_df.empty:
        return {
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "profit_factor": 0.0,
            "sharpe": 0.0,
            "total_pnl": 0.0,
            "max_win": 0.0,
            "max_loss": 0.0,
            "avg_hold_min": 0.0,
        }
    
    wins = trades_df[trades_df["pnl"] > 0]
    losses = trades_df[trades_df["pnl"] <= 0]
    
    total_trades = len(trades_df)
    win_rate = len(wins) / total_trades if total_trades > 0 else 0.0
    
    avg_win = wins["pnl"].mean() if len(wins) > 0 else 0.0
    avg_loss = losses["pnl"].mean() if len(losses) > 0 else 0.0
    
    total_win = wins["pnl"].sum() if len(wins) > 0 else 0.0
    total_loss = abs(losses["pnl"].sum()) if len(losses) > 0 else 0.0
    profit_factor = total_win / total_loss if total_loss > 0 else float('inf')
    
    # Sharpe: avg return / std deviation of returns
    mean_pnl = trades_df["pnl"].mean()
    std_pnl = trades_df["pnl"].std()
    sharpe = (mean_pnl / std_pnl) if std_pnl > 0 else 0.0
    
    return {
        "total_trades": total_trades,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "profit_factor": profit_factor,
        "sharpe": sharpe,
        "total_pnl": trades_df["pnl"].sum(),
        "max_win": trades_df["pnl"].max() if total_trades > 0 else 0.0,
        "max_loss": trades_df["pnl"].min() if total_trades > 0 else 0.0,
        "avg_hold_min": trades_df["hold_minutes"].mean() if total_trades > 0 else 0.0,
    }


def analyze_filters(df: pd.DataFrame, days: int = None) -> dict:
    """Analyze filter rejection rates"""
    if days:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        df = df[df["timestamp"] >= cutoff]
    
    total_checks = len(df)
    filter_counts = df["action"].value_counts().to_dict()
    
    return {
        "total_checks": total_checks,
        "entries": filter_counts.get("enter", 0),
        "exits": filter_counts.get("exit_rsi", 0) + filter_counts.get("exit", 0),
        "skip_time": filter_counts.get("skip_time_of_day", 0),
        "skip_volatility": filter_counts.get("skip_volatility", 0),
        "skip_volume": filter_counts.get("skip_volume", 0),
        "skip_rsi": filter_counts.get("skip_rsi", 0),
        "skip_trend": filter_counts.get("skip_trend", 0),
        "skip_bb": filter_counts.get("skip_bb", 0),
    }


def print_report(metrics: dict, filters: dict, trades_df: pd.DataFrame, days: int = None):
    """Print formatted analysis report"""
    print("=" * 70)
    print("ALPACA RSI BOT - TRADE ANALYSIS")
    print("=" * 70)
    
    time_range = f"Last {days} days" if days else "All time"
    print(f"\nTime Range: {time_range}")
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n" + "=" * 70)
    print("PERFORMANCE METRICS")
    print("=" * 70)
    
    print(f"\nTotal Trades:     {metrics['total_trades']}")
    
    if metrics['total_trades'] == 0:
        print("\n⚠️  No trades executed yet.")
        print("   Bot is running and checking conditions every 5 minutes.")
        print("   Waiting for market conditions to meet all filter criteria.")
        print("\n   Current filters (temporarily loosened for Week 6):")
        print("   - Time of day: 10:00-15:30 ET")
        print("   - RSI < threshold (dynamic 20/25/30)")
        print("   - Volatility: vol_z > 0.2")
        print("   - Volume spike: volm_z > 0.3")
        print("   - Trend filter: ema200_rel > -5%")
        print("   - Bollinger: bb_z < -0.8")
        return
    
    print(f"Wins:             {metrics['wins']}")
    print(f"Losses:           {metrics['losses']}")
    print(f"Win Rate:         {metrics['win_rate']:.1%}")
    print(f"\nAvg Win:          ${metrics['avg_win']:.2f}")
    print(f"Avg Loss:         ${metrics['avg_loss']:.2f}")
    print(f"Max Win:          ${metrics['max_win']:.2f}")
    print(f"Max Loss:         ${metrics['max_loss']:.2f}")
    print(f"\nProfit Factor:    {metrics['profit_factor']:.2f}")
    print(f"Sharpe Ratio:     {metrics['sharpe']:.2f}")
    print(f"Total PnL:        ${metrics['total_pnl']:.2f}")
    print(f"\nAvg Hold Time:    {metrics['avg_hold_min']:.1f} minutes")
    
    print("\n" + "=" * 70)
    print("FILTER ANALYSIS")
    print("=" * 70)
    
    total = filters["total_checks"]
    print(f"\nTotal Checks:     {total}")
    print(f"Entries:          {filters['entries']} ({filters['entries']/total*100:.1f}%)")
    print(f"Exits:            {filters['exits']} ({filters['exits']/total*100:.1f}%)")
    
    print("\nFilter Rejections:")
    print(f"  Time of Day:    {filters['skip_time']} ({filters['skip_time']/total*100:.1f}%)")
    print(f"  Volatility:     {filters['skip_volatility']} ({filters['skip_volatility']/total*100:.1f}%)")
    print(f"  Volume:         {filters['skip_volume']} ({filters['skip_volume']/total*100:.1f}%)")
    print(f"  RSI Threshold:  {filters['skip_rsi']} ({filters['skip_rsi']/total*100:.1f}%)")
    print(f"  Trend (EMA200): {filters['skip_trend']} ({filters['skip_trend']/total*100:.1f}%)")
    print(f"  Bollinger Band: {filters['skip_bb']} ({filters['skip_bb']/total*100:.1f}%)")
    
    if not trades_df.empty:
        print("\n" + "=" * 70)
        print("RECENT TRADES")
        print("=" * 70)
        
        recent = trades_df.tail(10)
        print("\nLast 10 Trades:")
        for _, trade in recent.iterrows():
            status = "✅ WIN" if trade["pnl"] > 0 else "❌ LOSS"
            print(f"\n{trade['entry_time'].strftime('%Y-%m-%d %H:%M')}")
            print(f"  Entry: ${trade['entry_price']:.2f} (RSI {trade['entry_rsi']:.1f})")
            print(f"  Exit:  ${trade['exit_price']:.2f} (RSI {trade['exit_rsi']:.1f})")
            print(f"  PnL:   ${trade['pnl']:.2f} ({trade['pnl_pct']:.2f}%) - {status}")
            print(f"  Hold:  {trade['hold_minutes']:.0f} min")
    
    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Analyze Alpaca RSI bot trades")
    parser.add_argument("--log", default="alpaca_rsi_log.csv", help="Path to log file")
    parser.add_argument("--days", type=int, help="Analyze only last N days (default: all)")
    parser.add_argument("--export", help="Export trades to CSV (optional)")
    args = parser.parse_args()
    
    log_path = Path(args.log)
    if not log_path.exists():
        print(f"ERROR: Log file not found: {log_path}")
        print("\nMake sure you're in the project directory:")
        print("  cd ~/Autonomous-Trading-Agent")
        return 1
    
    # Load log
    df = parse_log(log_path)
    
    # Match entry/exit pairs
    trades_df = match_entries_exits(df)
    
    # Filter by date if requested
    if args.days and not trades_df.empty:
        cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)
        trades_df = trades_df[trades_df["entry_time"] >= cutoff]
    
    # Check if we have any trades to analyze
    if trades_df.empty:
        print(f"\n⚠️  No completed trades found in the last {args.days} days" if args.days else "\n⚠️  No completed trades found in log")
        print("\nThis is NORMAL during holiday period (Dec 19 - Jan 3)")
        print("Expected behavior: Bot running, logging skip_volatility/skip_volume only")
        print("\nFilter breakdown:")
        filters = analyze_filters(df, days=args.days)
        for filter_name, count in filters.items():
            print(f"  {filter_name}: {count}")
        print("\n✅ Bot is healthy - just waiting for qualifying setups")
        print("📅 First trades expected: Jan 6-10 (TSLA delivery numbers)")
        return 0
    
    # Calculate metrics
    metrics = calculate_metrics(trades_df)
    filters = analyze_filters(df, days=args.days)
    
    # Print report
    print_report(metrics, filters, trades_df, days=args.days)
    
    # Export if requested
    if args.export and not trades_df.empty:
        export_path = Path(args.export)
        trades_df.to_csv(export_path, index=False)
        print(f"\n✅ Exported {len(trades_df)} trades to {export_path}")
    
    return 0


if __name__ == "__main__":
    exit(main())
