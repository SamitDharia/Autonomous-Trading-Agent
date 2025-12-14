"""
Position sizing utilities.

Maps model probability and volatility (ATR) to a target position size
with sensible caps. Exact mapping will be finalized in Phase 3.
"""

from typing import Optional


def size_from_prob(prob: float, atr_pct: Optional[float] = None, cap: float = 0.01) -> float:
    """Map probability to position size in [-cap, +cap].

    Placeholder linear mapping around 0.5 with optional ATR scaling.
    This will be refined alongside backtests and tests.
    """
    p = max(0.0, min(1.0, prob))
    edge = p - 0.5  # in [-0.5, 0.5]
    # Linear map: edge 0.5 -> cap; edge -0.5 -> -cap
    size = (edge / 0.5) * cap
    if atr_pct and atr_pct > 0:
        # Inversely scale by ATR percentage (higher ATR -> smaller size)
        size /= (1.0 + atr_pct)
    return max(-cap, min(cap, size))

