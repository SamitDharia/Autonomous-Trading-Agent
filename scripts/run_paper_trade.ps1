Param(
    [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
if ($DryRun) {
    python scripts/paper_trade.py --dry-run
} else {
    python scripts/paper_trade.py
}

