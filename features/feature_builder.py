"""
Feature builder for indicators and simple regime features.

This module will be used by the QuantConnect algorithm to compute
and package features for experts and the ensemble brain.
"""

from typing import Dict, Any


def build_features(context: Any) -> Dict[str, float]:
    """Return a dictionary of features from QCAlgorithm indicator values.

    Parameters
    ----------
    context: Any
        A QCAlgorithm instance that provides access to indicator values
        (rsi, macd, ema20/50/200, atr, bb, Time, Portfolio).

    Returns
    -------
    Dict[str, float]
        A feature dictionary with indicator and regime features.
        Returns {} if indicators are not ready.
    """
    # Check if indicators are ready
    if not (context.rsi.IsReady and context.atr.IsReady):
        return {}

    # Get current price
    price = context.Securities[context.symbol].Price if hasattr(context, 'symbol') else 0.0
    if price <= 0:
        return {}

    # Indicator values
    rsi_val = float(context.rsi.Current.Value)
    macd_line = float(context.macd.Current.Value) if context.macd.IsReady else 0.0
    macd_signal = float(context.macd.Signal.Current.Value) if context.macd.Signal.IsReady else 0.0
    macd_hist = macd_line - macd_signal
    atr_val = float(context.atr.Current.Value)
    atr_pct = atr_val / price if price > 0 else 0.0

    # EMA (trend)
    ema20_val = float(context.ema20.Current.Value) if context.ema20.IsReady else price
    ema50_val = float(context.ema50.Current.Value) if context.ema50.IsReady else price
    ema200_val = float(context.ema200.Current.Value) if context.ema200.IsReady else price
    ema20_rel = (price / ema20_val - 1) if ema20_val > 0 else 0.0
    ema50_rel = (price / ema50_val - 1) if ema50_val > 0 else 0.0
    ema200_rel = (price / ema200_val - 1) if ema200_val > 0 else 0.0

    # Bollinger Bands
    bb_mid = float(context.bb.MiddleBand.Current.Value) if context.bb.IsReady else price
    bb_upper = float(context.bb.UpperBand.Current.Value) if context.bb.IsReady else price
    bb_lower = float(context.bb.LowerBand.Current.Value) if context.bb.IsReady else price
    bb_width = bb_upper - bb_lower
    bb_z = (price - bb_mid) / (0.5 * bb_width) if bb_width > 0 else 0.0

    # Regime features: time-of-day and realized volatility (stub for now)
    time_of_day = context.Time.hour + context.Time.minute / 60.0 if hasattr(context, 'Time') else 9.5
    time_of_day_norm = time_of_day / 24.0  # Normalize to [0, 1]

    # Build feature dictionary
    features = {
        'rsi': rsi_val,
        'macd': macd_line,
        'macd_signal': macd_signal,
        'macd_hist': macd_hist,
        'atr': atr_val,
        'atr_pct': atr_pct,
        'ema20_rel': ema20_rel,
        'ema50_rel': ema50_rel,
        'ema200_rel': ema200_rel,
        'bb_z': bb_z,
        'time_of_day': time_of_day_norm,
    }

    return features

