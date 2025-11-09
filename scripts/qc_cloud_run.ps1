Param(
  [Parameter(Mandatory=$true)] [string]$UserId,
  [Parameter(Mandatory=$true)] [string]$ApiToken,
  [string]$ProjectName = "ATA"
)
$ErrorActionPreference = 'Stop'

# Use env vars so 'lean login' can authenticate non-interactively
$env:QC_USER_ID = "$UserId"
$env:QC_API_TOKEN = "$ApiToken"

Write-Host "Logging in to QuantConnect Lean CLI..." -ForegroundColor Cyan
lean login

Push-Location "qc org wkspc dir"
try {
  Write-Host "Pushing project '$ProjectName' to QC Cloud..." -ForegroundColor Cyan
  lean cloud push $ProjectName | Out-Null

  Write-Host "Submitting cloud backtest for '$ProjectName'..." -ForegroundColor Cyan
  lean cloud backtest $ProjectName

  Write-Host "Recent backtests (use Backtest ID with 'lean cloud backtest show <ID>'):" -ForegroundColor Yellow
  lean cloud backtest list
}
finally {
  Pop-Location
}
