Param(
  [string]$Symbol = "TSLA",
  [string]$Start = "2020-01-02",
  [string]$End = "2020-01-31"
)
$ErrorActionPreference = 'Stop'
python scripts/backtest_alpaca.py --symbol $Symbol --start $Start --end $End

