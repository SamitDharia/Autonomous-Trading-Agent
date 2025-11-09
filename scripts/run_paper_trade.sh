#!/usr/bin/env bash
set -euo pipefail
python scripts/paper_trade.py "${@:-"--dry-run"}"

