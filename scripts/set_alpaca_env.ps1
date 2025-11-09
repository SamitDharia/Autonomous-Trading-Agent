Param(
    [string]$ApiKey = "<PKUGWKLAZ7BI4WWKURNELSUEN4>",
    [string]$SecretKey = "<GhE8PXttnEdYvqSnaserDZZHdnkGZ126zdrDTW6vKtRv>",
    [string]$BaseUrl = "https://paper-api.alpaca.markets"
)
$ErrorActionPreference = 'Stop'
$env:ALPACA_API_KEY = $ApiKey
$env:ALPACA_SECRET_KEY = $SecretKey
$env:ALPACA_BASE_URL = $BaseUrl
Write-Host "Set ALPACA_API_KEY/SECRET_KEY/BASE_URL in this session."

