"""
Shadow-mode ML logging for training dataset collection.

Usage:
    from ml.shadow import shadow_log
    
    shadow_log(
        signal_id="trade_20251217_103045",
        timestamp=datetime.now(),
        symbol="TSLA",
        side="buy",
        entry_ref_price=245.30,
        qty=12,
        planned_tp=247.85,
        planned_sl=243.75,
        max_hold_bars=36,  # 30 min / 5 min bars
        features={
            "rsi": 23.4,
            "atr": 2.55,
            "vol_z": 0.82,
            "volm_z": 1.23,
            "ema200_rel": -2.3,
            "bb_z": -0.95,
            "time_of_day": 10.5,
        }
    )

Config (environment variables):
    ML_SHADOW_ENABLED: "true" to enable shadow logging (default: false)
    ML_SHADOW_LOG_ONLY: "true" to only log, skip prediction (default: true)
    ML_SHADOW_PREDICT: "true" to run ML prediction if model exists (default: false)
    ML_SHADOW_LOG_PATH: path to log file (default: ml_shadow_log.jsonl)
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


def _get_config(key: str, default: str) -> str:
    """Get config value from environment."""
    return os.getenv(key, default)


def is_enabled() -> bool:
    """Check if shadow-mode logging is enabled."""
    return _get_config("ML_SHADOW_ENABLED", "false").lower() in ("true", "1", "yes")


def shadow_log(
    signal_id: str,
    timestamp: datetime,
    symbol: str,
    side: str,
    entry_ref_price: float,
    qty: int,
    planned_tp: float,
    planned_sl: float,
    max_hold_bars: int,
    features: Dict[str, float],
) -> Optional[Dict[str, Any]]:
    """
    Log trade signal + features for ML training dataset collection.
    
    This function:
    1. Writes one JSON row to ml_shadow_log.jsonl (training dataset)
    2. Optionally runs ML prediction if ML_SHADOW_PREDICT=true and model exists
    3. Returns prediction dict if computed, else None
    4. Never raises exceptions (wrapped in try/except to protect trade execution)
    
    Args:
        signal_id: Unique identifier for this signal (e.g., "trade_20251217_103045")
        timestamp: When the signal was generated
        symbol: Trading symbol (e.g., "TSLA")
        side: "buy" or "sell"
        entry_ref_price: Expected entry price (current market price)
        qty: Planned position size
        planned_tp: Take-profit target price
        planned_sl: Stop-loss price
        max_hold_bars: Maximum hold time in bars (e.g., 36 bars = 30 min / 5 min)
        features: Feature snapshot at decision time (market-state only)
            Expected keys: rsi, atr, vol_z, volm_z, ema200_rel, bb_z, time_of_day
    
    Returns:
        Optional dict with ML prediction if computed:
        {
            "ml_prob": 0.6234,  # P(profitable)
            "ml_signal": "APPROVE",  # "APPROVE" or "REJECT"
            "ml_model_version": "v1.0"
        }
        Returns None if prediction not enabled or model not available.
    """
    if not is_enabled():
        return None
    
    try:
        # Build log entry
        log_entry = {
            "signal_id": signal_id,
            "timestamp": timestamp.isoformat(),
            "symbol": symbol,
            "side": side,
            "entry_ref_price": round(entry_ref_price, 2),
            "qty": qty,
            "planned_tp": round(planned_tp, 2),
            "planned_sl": round(planned_sl, 2),
            "max_hold_bars": max_hold_bars,
            "features": features,
        }
        
        # Append to JSONL file (one JSON object per line)
        log_path = Path(_get_config("ML_SHADOW_LOG_PATH", "ml_shadow_log.jsonl"))
        with open(log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        # Optional: run ML prediction if enabled and model exists
        prediction = None
        if _get_config("ML_SHADOW_PREDICT", "false").lower() in ("true", "1", "yes"):
            prediction = _run_prediction(features)
            if prediction:
                # Log prediction alongside features
                with open(log_path.parent / "ml_predictions.jsonl", "a") as f:
                    pred_entry = {
                        "signal_id": signal_id,
                        "timestamp": timestamp.isoformat(),
                        **prediction,
                    }
                    f.write(json.dumps(pred_entry) + "\n")
        
        return prediction
    
    except Exception as e:
        # CRITICAL: Never let ML logging break trade execution
        # Log error and continue silently
        try:
            error_log = Path("ml_shadow_errors.log")
            with open(error_log, "a") as f:
                f.write(f"{datetime.now().isoformat()} | ERROR: {e}\n")
        except:
            pass  # Even error logging failed - give up silently
        
        return None


def _run_prediction(features: Dict[str, float]) -> Optional[Dict[str, Any]]:
    """
    Run ML prediction if model exists.
    
    This is a placeholder for Phase 4.2+ when a trained model is available.
    For now, returns None (log-only mode).
    
    Args:
        features: Feature dict with keys: rsi, atr, vol_z, volm_z, ema200_rel, bb_z, time_of_day
    
    Returns:
        Optional dict with prediction results, or None if no model available
    """
    # Check if model file exists
    model_path = Path(_get_config("ML_SHADOW_MODEL_PATH", "models/shadow_model.pkl"))
    if not model_path.exists():
        return None
    
    # Placeholder for future implementation
    # TODO: Load model, extract features in correct order, call predict_proba()
    # For now, return None to indicate model not ready
    return None
    
    # Future implementation (Phase 4.2+):
    # import pickle
    # with open(model_path, "rb") as f:
    #     model = pickle.load(f)
    # 
    # # Extract features in model's expected order
    # X = [features.get(k, 0.0) for k in model.feature_names_]
    # prob = model.predict_proba([X])[0][1]  # P(profitable)
    # 
    # return {
    #     "ml_prob": round(prob, 4),
    #     "ml_signal": "APPROVE" if prob > 0.55 else "REJECT",
    #     "ml_model_version": model.version,
    # }
