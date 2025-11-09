Param(
    [Parameter(Mandatory=$true)] [string]$ApiKey,
    [Parameter(Mandatory=$true)] [string]$SecretKey,
    [string]$BaseUrl = "https://paper-api.alpaca.markets"
)
$ErrorActionPreference = 'Stop'
$env:ALPACA_API_KEY = $ApiKey
$env:ALPACA_SECRET_KEY = $SecretKey
$env:ALPACA_BASE_URL = $BaseUrl
Write-Host "Set ALPACA_API_KEY/SECRET_KEY/BASE_URL in this session."

