"""
Feature builder for indicators and simple regime features.

This module will be used by the QuantConnect algorithm to compute
and package features for experts and the ensemble brain.
"""

from typing import Dict, Any


def build_features(context: Any) -> Dict[str, float]:
    """Return a dictionary of features.

    Parameters
    ----------
    context: Any
        An object that provides access to indicator values (e.g., QCAlgorithm).

    Returns
    -------
    Dict[str, float]
        A feature dictionary. Placeholder for now.
    """
    # TODO: Wire up RSI, EMA, MACD, ATR, Bollinger, and regime (vol, TOD, DOW).
    return {}

