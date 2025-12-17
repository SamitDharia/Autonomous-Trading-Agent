"""
Analyze alpaca_rsi_log.csv to track paper trading performance vs backtest predictions.

Usage:
    python scripts/analyze_trading_log.py
    python scripts/analyze_trading_log.py --log-file alpaca_rsi_log.csv --days 7
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import numpy as np


# Backtest benchmarks (Phase 1+2, 2020-2024 TSLA)
BACKTEST_BENCHMARKS = {
    "sharpe_ratio": 0.80,
    "win_rate": 0.727,  # 72.7%
    "profit_factor": 0.93,
    "avg_win": 10.05,
    "avg_loss": -10.85,
    "total_trades": 44,
}

ALERT_THRESHOLDS = {
    "sharpe_deviation": 0.20,  # Alert if Sharpe differs by >20%
    "win_rate_deviation": 0.05,  # Alert if win rate differs by >5%
    "min_trades": 3,  # Need at least 3 trades for meaningful stats
}


def load_log(log_path: Path) -> pd.DataFrame:
    """Load and parse trading log CSV."""
    if not log_path.exists():
        print(f"❌ Log file not found: {log_path}")
        sys.exit(1)
    
    df = pd.read_csv(log_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def filter_by_days(df: pd.DataFrame, days: Optional[int]) -> pd.DataFrame:
    """Filter log to last N days."""
    if days is None:
        return df
    
    cutoff = datetime.now() - timedelta(days=days)
    return df[df["timestamp"] >= cutoff]


def extract_trades(df: pd.DataFrame) -> pd.DataFrame:
    """Extract completed trades (enter + exit pairs)."""
    entries = df[df["action"] == "enter"].copy()
    exits = df[df["action"].isin(["exit_rsi", "exit_stop", "exit_tp"])].copy()
    
    trades = []
    for _, entry in entries.iterrows():
        # Find next exit after this entry
        later_exits = exits[exits["timestamp"] > entry["timestamp"]]
        if later_exits.empty:
            continue  # Trade still open
        
        exit_row = later_exits.iloc[0]
        
        pnl = (exit_row["price"] - entry["price"]) * entry["qty"]
        trades.append({
            "entry_time": entry["timestamp"],
            "exit_time": exit_row["timestamp"],
            "entry_price": entry["price"],
            "exit_price": exit_row["price"],
            "qty": entry["qty"],
            "pnl": pnl,
            "return_pct": (exit_row["price"] / entry["price"] - 1) * 100,
            "hold_time_min": (exit_row["timestamp"] - entry["timestamp"]).total_seconds() / 60,
            "exit_reason": exit_row["action"],
        })
    
    return pd.DataFrame(trades)


def calculate_metrics(trades: pd.DataFrame) -> Dict:
    """Calculate performance metrics from trades."""
    if trades.empty:
        return {
            "total_trades": 0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "total_pnl": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
        }
    
    wins = trades[trades["pnl"] > 0]
    losses = trades[trades["pnl"] <= 0]
    
    total_pnl = trades["pnl"].sum()
    win_rate = len(wins) / len(trades) if len(trades) > 0 else 0.0
    
    gross_profit = wins["pnl"].sum() if len(wins) > 0 else 0.0
    gross_loss = abs(losses["pnl"].sum()) if len(losses) > 0 else 1e-6
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0
    
    avg_win = wins["pnl"].mean() if len(wins) > 0 else 0.0
    avg_loss = losses["pnl"].mean() if len(losses) > 0 else 0.0
    
    # Sharpe ratio (annualized)
    if len(trades) > 1:
        returns = trades["return_pct"] / 100
        sharpe = (returns.mean() / (returns.std() + 1e-6)) * np.sqrt(252)
    else:
        sharpe = 0.0
    
    # Max drawdown
    cumulative = trades["pnl"].cumsum()
    running_max = cumulative.cummax()
    drawdown = cumulative - running_max
    max_dd = drawdown.min()
    
    return {
        "total_trades": len(trades),
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "total_pnl": total_pnl,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "sharpe_ratio": sharpe,
        "max_drawdown": max_dd,
    }


def compare_to_backtest(live_metrics: Dict) -> List[str]:
    """Compare live metrics to backtest and generate alerts."""
    alerts = []
    
    if live_metrics["total_trades"] < ALERT_THRESHOLDS["min_trades"]:
        return [f"⚠️  Only {live_metrics['total_trades']} trades - need {ALERT_THRESHOLDS['min_trades']}+ for meaningful analysis"]
    
    # Sharpe ratio deviation
    sharpe_diff = abs(live_metrics["sharpe_ratio"] - BACKTEST_BENCHMARKS["sharpe_ratio"])
    sharpe_pct_diff = sharpe_diff / BACKTEST_BENCHMARKS["sharpe_ratio"]
    if sharpe_pct_diff > ALERT_THRESHOLDS["sharpe_deviation"]:
        alerts.append(
            f"🚨 Sharpe deviation: {live_metrics['sharpe_ratio']:.2f} vs backtest {BACKTEST_BENCHMARKS['sharpe_ratio']:.2f} "
            f"({sharpe_pct_diff*100:.1f}% difference)"
        )
    
    # Win rate deviation
    win_rate_diff = abs(live_metrics["win_rate"] - BACKTEST_BENCHMARKS["win_rate"])
    if win_rate_diff > ALERT_THRESHOLDS["win_rate_deviation"]:
        alerts.append(
            f"🚨 Win rate deviation: {live_metrics['win_rate']*100:.1f}% vs backtest {BACKTEST_BENCHMARKS['win_rate']*100:.1f}% "
            f"({win_rate_diff*100:.1f}% difference)"
        )
    
    # Profit factor check
    if live_metrics["profit_factor"] < 0.7:  # Well below backtest 0.93
        alerts.append(
            f"🚨 Profit factor too low: {live_metrics['profit_factor']:.2f} vs backtest {BACKTEST_BENCHMARKS['profit_factor']:.2f}"
        )
    
    return alerts


def analyze_filter_effectiveness(df: pd.DataFrame) -> Dict:
    """Analyze how often each filter rejects trades."""
    filter_actions = [
        "skip_time_of_day",
        "skip_volatility", 
        "skip_volume",
        "skip_rsi",
        "skip_trend",
        "skip_bb",
    ]
    
    filter_counts = {}
    for action in filter_actions:
        count = len(df[df["action"] == action])
        filter_counts[action] = count
    
    total_skips = sum(filter_counts.values())
    entries = len(df[df["action"] == "enter"])
    
    return {
        "filter_counts": filter_counts,
        "total_skips": total_skips,
        "total_entries": entries,
        "selectivity": total_skips / (total_skips + entries) if (total_skips + entries) > 0 else 0.0,
    }


def print_report(metrics: Dict, filter_stats: Dict, trades: pd.DataFrame, alerts: List[str]):
    """Print formatted analysis report."""
    print("\n" + "="*70)
    print("📊 PAPER TRADING PERFORMANCE ANALYSIS")
    print("="*70)
    
    print(f"\n📅 Analysis Period: {trades['entry_time'].min():%Y-%m-%d} to {trades['exit_time'].max():%Y-%m-%d}")
    print(f"⏰ Last Updated: {datetime.now():%Y-%m-%d %H:%M:%S}")
    
    print("\n" + "-"*70)
    print("PERFORMANCE METRICS")
    print("-"*70)
    
    print(f"\n{'Metric':<25} {'Live':<15} {'Backtest':<15} {'Status'}")
    print("-"*70)
    
    # Sharpe
    sharpe_status = "✅" if abs(metrics["sharpe_ratio"] - BACKTEST_BENCHMARKS["sharpe_ratio"]) / BACKTEST_BENCHMARKS["sharpe_ratio"] <= ALERT_THRESHOLDS["sharpe_deviation"] else "⚠️"
    print(f"{'Sharpe Ratio':<25} {metrics['sharpe_ratio']:>7.2f}       {BACKTEST_BENCHMARKS['sharpe_ratio']:>7.2f}       {sharpe_status}")
    
    # Win Rate
    wr_status = "✅" if abs(metrics["win_rate"] - BACKTEST_BENCHMARKS["win_rate"]) <= ALERT_THRESHOLDS["win_rate_deviation"] else "⚠️"
    print(f"{'Win Rate':<25} {metrics['win_rate']*100:>6.1f}%       {BACKTEST_BENCHMARKS['win_rate']*100:>6.1f}%       {wr_status}")
    
    # Profit Factor
    pf_status = "✅" if metrics["profit_factor"] >= 0.7 else "⚠️"
    print(f"{'Profit Factor':<25} {metrics['profit_factor']:>7.2f}       {BACKTEST_BENCHMARKS['profit_factor']:>7.2f}       {pf_status}")
    
    # Other metrics
    print(f"{'Total Trades':<25} {metrics['total_trades']:>7}       {BACKTEST_BENCHMARKS['total_trades']:>7}       -")
    print(f"{'Total P&L':<25} ${metrics['total_pnl']:>6.2f}       -               -")
    print(f"{'Avg Win':<25} ${metrics['avg_win']:>6.2f}       ${BACKTEST_BENCHMARKS['avg_win']:>6.2f}       -")
    print(f"{'Avg Loss':<25} ${metrics['avg_loss']:>6.2f}       ${BACKTEST_BENCHMARKS['avg_loss']:>6.2f}       -")
    print(f"{'Max Drawdown':<25} ${metrics['max_drawdown']:>6.2f}       -               -")
    
    print("\n" + "-"*70)
    print("FILTER EFFECTIVENESS")
    print("-"*70)
    
    print(f"\nTotal Opportunities Evaluated: {filter_stats['total_skips'] + filter_stats['total_entries']}")
    print(f"Rejected by Filters: {filter_stats['total_skips']} ({filter_stats['selectivity']*100:.1f}%)")
    print(f"Entries Executed: {filter_stats['total_entries']} ({(1-filter_stats['selectivity'])*100:.1f}%)")
    
    print(f"\nFilter Breakdown:")
    for action, count in filter_stats["filter_counts"].items():
        pct = count / filter_stats["total_skips"] * 100 if filter_stats["total_skips"] > 0 else 0
        filter_name = action.replace("skip_", "").replace("_", " ").title()
        print(f"  {filter_name:<20} {count:>4} ({pct:>5.1f}%)")
    
    if alerts:
        print("\n" + "-"*70)
        print("⚠️  ALERTS")
        print("-"*70)
        for alert in alerts:
            print(f"\n{alert}")
    else:
        if metrics["total_trades"] >= ALERT_THRESHOLDS["min_trades"]:
            print("\n" + "-"*70)
            print("✅ ALL CHECKS PASSED - Performance aligned with backtest")
            print("-"*70)
    
    print("\n" + "="*70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Analyze Alpaca trading log")
    parser.add_argument("--log-file", default="alpaca_rsi_log.csv", help="Path to log CSV file")
    parser.add_argument("--days", type=int, default=None, help="Analyze last N days only")
    parser.add_argument("--export", action="store_true", help="Export metrics to CSV")
    args = parser.parse_args()
    
    log_path = Path(args.log_file)
    
    # Load and filter log
    print(f"📂 Loading log: {log_path}")
    df = load_log(log_path)
    
    if args.days:
        df = filter_by_days(df, args.days)
        print(f"📅 Filtered to last {args.days} days")
    
    print(f"📋 Total log entries: {len(df)}")
    
    # Extract trades
    trades = extract_trades(df)
    
    if trades.empty:
        print("\n⚠️  No completed trades found in log")
        print("   (Trades need both entry and exit to be analyzed)")
        
        # Show filter stats even if no trades
        filter_stats = analyze_filter_effectiveness(df)
        print(f"\n📊 Filter Activity:")
        print(f"   Total opportunities: {filter_stats['total_skips'] + filter_stats['total_entries']}")
        print(f"   Rejected: {filter_stats['total_skips']}")
        print(f"   Entered: {filter_stats['total_entries']}")
        sys.exit(0)
    
    print(f"✅ Found {len(trades)} completed trades")
    
    # Calculate metrics
    metrics = calculate_metrics(trades)
    filter_stats = analyze_filter_effectiveness(df)
    alerts = compare_to_backtest(metrics)
    
    # Print report
    print_report(metrics, filter_stats, trades, alerts)
    
    # Export if requested
    if args.export:
        export_path = log_path.parent / f"metrics_{datetime.now():%Y%m%d_%H%M%S}.csv"
        metrics_df = pd.DataFrame([metrics])
        metrics_df.to_csv(export_path, index=False)
        print(f"📊 Exported metrics to: {export_path}")


if __name__ == "__main__":
    main()
