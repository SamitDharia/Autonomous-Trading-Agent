#!/usr/bin/env pwsh
# Daily Health Check for Autonomous Trading Bot
# Run this once per day to verify bot is healthy
# Usage: .\scripts\daily_health_check.ps1

$DROPLET_IP = "138.68.150.144"
$DROPLET_USER = "root"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Daily Bot Health Check - $(Get-Date -Format 'yyyy-MM-dd HH:mm')" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 1. Check if bot process is running
Write-Host "[1/5] Checking bot process..." -ForegroundColor Yellow
ssh ${DROPLET_USER}@${DROPLET_IP} "cd ~/Autonomous-Trading-Agent && ps aux | grep alpaca_rsi_bot | grep -v grep"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Bot is running`n" -ForegroundColor Green
} else {
    Write-Host "❌ Bot is NOT running - RESTART NEEDED!`n" -ForegroundColor Red
}

# 2. Check last 5 log entries
Write-Host "[2/5] Last 5 log entries:" -ForegroundColor Yellow
ssh ${DROPLET_USER}@${DROPLET_IP} "cd ~/Autonomous-Trading-Agent && tail -5 alpaca_rsi_log.csv"
Write-Host ""

# 3. Count today's activity
Write-Host "[3/5] Today's activity:" -ForegroundColor Yellow
$TODAY = Get-Date -Format "yyyy-MM-dd"
ssh ${DROPLET_USER}@${DROPLET_IP} "cd ~/Autonomous-Trading-Agent && grep '$TODAY' alpaca_rsi_log.csv | wc -l" | ForEach-Object {
    Write-Host "Total log entries today: $_" -ForegroundColor White
}

# 4. Check for any entries (trades or rejections)
Write-Host "`n[4/5] Looking for trades or Phase 3 activity today:" -ForegroundColor Yellow
ssh ${DROPLET_USER}@${DROPLET_IP} "cd ~/Autonomous-Trading-Agent && grep '$TODAY' alpaca_rsi_log.csv | grep -E 'entry|bracket|trail_update|exit' | tail -5"
if ($LASTEXITCODE -ne 0) {
    Write-Host "No trades today (checking filters...)" -ForegroundColor Yellow
    ssh ${DROPLET_USER}@${DROPLET_IP} "cd ~/Autonomous-Trading-Agent && grep '$TODAY' alpaca_rsi_log.csv | tail -3 | cut -d',' -f3"
}
Write-Host ""

# 5. Summary
Write-Host "[5/5] Summary:" -ForegroundColor Yellow
Write-Host "- Bot Status: Check line [1/5] above" -ForegroundColor White
Write-Host "- Expected: Zero trades until Jan 6-10 (holiday period)" -ForegroundColor White
Write-Host "- Expected: First Phase 3 trade during Jan delivery numbers or earnings" -ForegroundColor White
Write-Host "- Next check: Run this script tomorrow`n" -ForegroundColor White

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Health check complete!" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan
