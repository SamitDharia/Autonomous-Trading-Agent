#!/usr/bin/env python3
"""
Quick health check script for DigitalOcean droplet bot.

Usage:
    python scripts/check_bot_status.py
    
    # Or with custom SSH host
    python scripts/check_bot_status.py --host root@138.68.150.144

This script:
- Checks if bot process is running (PID from bot.pid)
- Shows last 10 log entries
- Displays trade count
- Shows current time on server vs local
"""

import argparse
import subprocess
import sys
from datetime import datetime


def run_ssh_command(host: str, command: str) -> tuple[bool, str]:
    """Run SSH command and return (success, output)."""
    try:
        result = subprocess.run(
            ["ssh", host, command],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0, result.stdout.strip()
    except subprocess.TimeoutExpired:
        return False, "SSH command timed out"
    except FileNotFoundError:
        return False, "SSH not found. Install OpenSSH client."
    except Exception as e:
        return False, f"Error: {e}"


def check_bot_status(host: str = "root@138.68.150.144"):
    """Check bot health on remote server."""
    print(f"🔍 Checking bot status on {host}...\n")
    
    # Check 1: Server time
    success, output = run_ssh_command(host, "date")
    if success:
        print(f"📅 Server Time: {output}")
        print(f"📅 Local Time:  {datetime.now().strftime('%a %b %d %H:%M:%S %Z %Y')}\n")
    else:
        print(f"❌ Failed to connect: {output}\n")
        return
    
    # Check 2: Bot process running?
    success, pid_content = run_ssh_command(
        host, 
        "cd ~/Autonomous-Trading-Agent && cat bot.pid 2>/dev/null"
    )
    
    if success and pid_content:
        print(f"📌 Bot PID: {pid_content}")
        
        # Verify process actually running
        success, ps_output = run_ssh_command(host, f"ps -p {pid_content} -o pid,etime,cmd --no-headers")
        if success and ps_output:
            print(f"✅ Process Running: {ps_output}")
        else:
            print(f"❌ Process NOT running (PID {pid_content} not found)")
    else:
        print("❌ bot.pid file not found or empty\n")
    
    print()
    
    # Check 3: Recent log entries
    success, log_output = run_ssh_command(
        host,
        "cd ~/Autonomous-Trading-Agent && tail -n 10 alpaca_rsi_log.csv 2>/dev/null"
    )
    
    if success and log_output:
        print("📋 Last 10 Log Entries:")
        print(log_output)
    else:
        print("❌ No log entries found (alpaca_rsi_log.csv)\n")
    
    print()
    
    # Check 4: Trade count
    success, trade_count = run_ssh_command(
        host,
        "cd ~/Autonomous-Trading-Agent && grep -E 'enter|exit' alpaca_rsi_log.csv 2>/dev/null | wc -l"
    )
    
    if success:
        count = int(trade_count.strip()) if trade_count.strip().isdigit() else 0
        print(f"📊 Total Trades (enter/exit signals): {count}")
        
        if count == 0:
            print("   ℹ️  No trades executed yet. Waiting for market conditions.\n")
    else:
        print("❌ Could not count trades\n")
    
    # Check 5: Disk space
    success, df_output = run_ssh_command(
        host,
        "df -h / | tail -1 | awk '{print $5 \" used\"}'"
    )
    
    if success:
        print(f"💾 Disk Usage: {df_output}\n")
    
    print("✅ Health check complete!")


def main():
    parser = argparse.ArgumentParser(description="Check trading bot status on cloud server")
    parser.add_argument(
        "--host",
        default="root@138.68.150.144",
        help="SSH host (default: root@138.68.150.144)"
    )
    
    args = parser.parse_args()
    
    try:
        check_bot_status(args.host)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    main()
