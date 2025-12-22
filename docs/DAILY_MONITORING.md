# Daily Monitoring Queries

Quick reference for checking your bot health. Run these daily during December holiday period and January validation.

## Quick Health Check (Windows PowerShell)

```powershell
# Automated daily check (recommended):
.\scripts\daily_health_check.ps1

# Manual queries below if you prefer:
```

## Manual Queries

### 0. Sync Latest Logs to Local (First Step)
```bash
scp root@138.68.150.144:/root/Autonomous-Trading-Agent/alpaca_rsi_log.csv alpaca_rsi_log.csv
```
**Why**: Your local log file gets stale. Always sync first before analyzing locally.  
**When**: Before running analyze_recent_trades.py or checking local logs

---

### 1. Bot Process Status
```bash
ssh root@138.68.150.144 "cd ~/Autonomous-Trading-Agent && ps aux | grep alpaca_rsi_bot | grep -v grep"
```
**Expected**: Should show PID 46592 or similar (bot running)  
**Action if empty**: Bot crashed, needs restart (see DEPLOYMENT.md)

---

### 2. Last 10 Log Entries
```bash
ssh root@138.68.150.144 "cd ~/Autonomous-Trading-Agent && tail -10 alpaca_rsi_log.csv"
```
**Expected Dec 19 - Jan 3**: `skip_volatility` or `skip_volume` (low holiday volatility)  
**Expected Jan 6+**: Mix of `skip_*` and possibly `entry`, `bracket`, `trail_update`

---

### 3. Today's Activity Summary
```bash
# Count total entries today:
ssh root@138.68.150.144 "cd ~/Autonomous-Trading-Agent && grep '2025-12-19' alpaca_rsi_log.csv | wc -l"

# Replace date with current date (YYYY-MM-DD format)
```
**Expected**: 100-200 entries per day (bot runs every 5 min, logs every check)

---

### 4. Check for Trades or Phase 3 Activity
```bash
ssh root@138.68.150.144 "cd ~/Autonomous-Trading-Agent && grep '2025-12-19' alpaca_rsi_log.csv | grep -E 'entry|bracket|trail_update|exit|skip_multi_tf' | tail -20"

# Replace date with current date
```

**What to look for**:
- `entry` + `bracket`: New position opened with Phase 3 brackets ✅
- `trail_update`: Trailing stop adjusted (profitable position) ✅
- `skip_multi_tf`: Multi-TF RSI rejected entry (Phase 3.2 working) ✅
- `exit`: Position closed (profit or stop hit) ✅
- **Nothing**: No qualifying setups today (expected during holidays)

---

### 5. Current Position Status
```bash
ssh root@138.68.150.144 "cd ~/Autonomous-Trading-Agent && tail -1 alpaca_rsi_log.csv"
```
**Expected**: Last entry shows current status  
**If holding**: Line will show position qty > 0  
**If flat**: Position qty = 0

---

### 6. Filter Rejection Breakdown (Weekly Check)
```bash
# See which filters are rejecting most:
ssh root@138.68.150.144 "cd ~/Autonomous-Trading-Agent && tail -500 alpaca_rsi_log.csv | cut -d',' -f3 | sort | uniq -c | sort -rn"
```

**Expected Dec 19 - Jan 3**:
```
150 skip_volatility
100 skip_volume
 50 skip_time_of_day
  0 skip_multi_tf  (not reached yet)
  0 entry
```

**Expected Jan 6+** (when volatility returns):
```
100 skip_volume
 50 skip_volatility
 20 skip_multi_tf  (Phase 3.2 filter working!)
 10 entry
  5 trail_update
```

---

## Troubleshooting

### Bot Not Running
```bash
# Check for errors:
ssh root@138.68.150.144 "cd ~/Autonomous-Trading-Agent && tail -20 bot.log"

# Restart bot:
ssh root@138.68.150.144 "cd ~/Autonomous-Trading-Agent && pkill -f alpaca_rsi_bot.py && nohup .venv/bin/python scripts/alpaca_rsi_bot.py --symbol TSLA --loop --sleep-min 5 > bot.log 2>&1 & echo \$! > bot.pid"
```

### No Logs Since Yesterday
```bash
# Check last log timestamp:
ssh root@138.68.150.144 "cd ~/Autonomous-Trading-Agent && tail -1 alpaca_rsi_log.csv | cut -d',' -f1"

# If older than 1 hour, bot might be stuck
```

---

## What to Expect (Timeline)

| Date Range | Expected Behavior | Action |
|------------|-------------------|--------|
| **Dec 19-23** | skip_volatility/skip_volume only | ✅ Normal - just monitor |
| **Dec 24 - Jan 3** | skip_time_of_day (markets closed/half days) | ✅ Normal - enjoy holidays |
| **Jan 6-10** | First entry possible (delivery numbers) | 🔍 **Check daily!** |
| **Jan 20-31** | Multiple entries (earnings week) | 🔍 **Check 2x daily!** |

---

## Analysis Commands (After 5+ Trades)

```bash
# 1. Download latest logs (ALWAYS DO THIS FIRST):
scp root@138.68.150.144:/root/Autonomous-Trading-Agent/alpaca_rsi_log.csv alpaca_rsi_log.csv

# 2. Run local analysis:
python scripts/analyze_recent_trades.py --days 30

# 3. Check Phase 3 activity counts:
grep 'trail_update\|skip_multi_tf' alpaca_rsi_log.csv | wc -l
```

**Important**: The log file on the droplet is continuously updated, but your local copy is stale. Always sync logs before analysis.

---

## Quick Reference Card

**Daily (30 seconds)**:
```bash
.\scripts\daily_health_check.ps1
```

**Weekly (5 minutes)**:
```bash
# Sync logs first
scp root@138.68.150.144:/root/Autonomous-Trading-Agent/alpaca_rsi_log.csv alpaca_rsi_log.csv

# Check filter breakdown locally or remotely
ssh root@138.68.150.144 "cd ~/Autonomous-Trading-Agent && tail -500 alpaca_rsi_log.csv | cut -d',' -f3 | sort | uniq -c"
```

**After First Trade (analysis)**:
```bash
# Sync logs first
scp root@138.68.150.144:/root/Autonomous-Trading-Agent/alpaca_rsi_log.csv alpaca_rsi_log.csv

# Analyze locally
python scripts/analyze_recent_trades.py --days 7
```

---

**Last Updated**: 2025-12-22
