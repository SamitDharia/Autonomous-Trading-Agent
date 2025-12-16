"""
Risk guards: daily stop, kill-switch, readiness checks.
"""

from typing import Any, Optional
from datetime import date


def daily_pnl_stop_hit(algo: Any, threshold: float = -0.01) -> bool:
    """Return True if daily P&L <= threshold (e.g., -1%).

    Parameters
    ----------
    algo : Any
        A QCAlgorithm instance with Portfolio and Time attributes.
    threshold : float
        Daily loss threshold (e.g., -0.01 for -1%). Negative values represent losses.

    Returns
    -------
    bool
        True if cumulative daily P&L <= threshold, False otherwise.
    """
    # Check if we have required attributes
    if not hasattr(algo, 'Portfolio') or not hasattr(algo, 'Time'):
        return False

    # Track start-of-day equity if not already done
    if not hasattr(algo, '_start_of_day_equity'):
        algo._start_of_day_equity = algo.Portfolio.TotalPortfolioValue
        algo._current_day = algo.Time.date()
        return False

    # Reset at new day
    if algo.Time.date() > algo._current_day:
        algo._start_of_day_equity = algo.Portfolio.TotalPortfolioValue
        algo._current_day = algo.Time.date()
        return False

    # Compute daily P&L as a fraction of starting equity
    current_equity = algo.Portfolio.TotalPortfolioValue
    daily_pnl_pct = (current_equity - algo._start_of_day_equity) / algo._start_of_day_equity if algo._start_of_day_equity > 0 else 0.0

    return daily_pnl_pct <= threshold


def indicators_ready(*indicators: Any) -> bool:
    """Return True if all indicators are ready."""
    return all(getattr(ind, "IsReady", False) if hasattr(ind, "IsReady") else bool(ind) for ind in indicators)


def kill_switch(error_flag: bool) -> bool:
    """Return True if a critical error has been detected."""
    return bool(error_flag)

