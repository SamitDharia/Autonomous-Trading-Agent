import sys
from pathlib import Path

# Ensure project root on path for imports when pytest changes CWD
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.local_backtest import simulate_short_run


def test_simulate_short_run_returns_metrics():
    m = simulate_short_run()
    assert isinstance(m["net_pnl"], float)
    assert isinstance(m["sharpe"], float)
    assert isinstance(m["trades"], int)
