Param(
  [string]$ProjectName = "ATA"
)
$ErrorActionPreference = 'Stop'
Push-Location "qc org wkspc dir"
try {
  # Ensure latest files are pushed then start a backtest
  lean cloud push $ProjectName | Out-Null
  lean cloud backtest $ProjectName
  Write-Host "Submitted cloud backtest for project '$ProjectName'." -ForegroundColor Green
  Write-Host "List recent backtests:" -ForegroundColor Cyan
  lean cloud backtest list
}
finally {
  Pop-Location
}
