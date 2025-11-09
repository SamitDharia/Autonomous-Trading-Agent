"""
Risk guards: daily stop, kill-switch, readiness checks.
"""

from typing import Any


def daily_pnl_stop_hit(algo: Any, threshold: float = -0.01) -> bool:
    """Return True if daily P&L <= threshold (e.g., -1%).

    Note: In QC, you would compute today's net profit relative to equity
    or use available statistics; this is a placeholder signature.
    """
    # TODO: Implement using QC algorithm performance metrics.
    return False


def indicators_ready(*indicators: Any) -> bool:
    """Return True if all indicators are ready."""
    return all(getattr(ind, "IsReady", False) if hasattr(ind, "IsReady") else bool(ind) for ind in indicators)


def kill_switch(error_flag: bool) -> bool:
    """Return True if a critical error has been detected."""
    return bool(error_flag)

