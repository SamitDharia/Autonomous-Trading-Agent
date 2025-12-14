"""
Ensemble brain blends expert probabilities with regime features.
Supports a tiny logistic model loaded from QC Object Store or local file.
Falls back to equal-weight average if not available.
"""

from typing import Any, Dict
import json
from math import exp


def _sigmoid(z: float) -> float:
    try:
        return 1.0 / (1.0 + exp(-z))
    except OverflowError:
        return 0.0 if z < 0 else 1.0


class Brain:
    def __init__(self, model: Any = None):
        # model: {"type": "logistic", "bias": float, "weights": {"experts.rsi": w, "experts.macd": w, "experts.trend": w, "regime.volatility": w, "regime.time_of_day": w}}
        self._model = model or {"type": "avg"}

    @classmethod
    def load(cls, obj_store: Any, key: str) -> "Brain":
        data = None
        if obj_store is not None:
            try:
                if obj_store.ContainsKey(key):
                    raw = obj_store.ReadBytes(key)
                    # accept both .pkl (ignored) and .json content as bytes
                    try:
                        raw_bytes = bytes(raw.ToArray()) if hasattr(raw, "ToArray") else bytes(raw)
                        data = json.loads(raw_bytes.decode("utf-8"))
                    except Exception:
                        data = None
            except Exception:
                data = None
        if data is None:
            try:
                with open(key, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = None
        return cls(data)

    def predict_proba(self, expert_probs: Dict[str, float], regime: Dict[str, float]) -> float:
        if not isinstance(self._model, dict):
            return 0.5
        if self._model.get("type") == "logistic":
            bias = float(self._model.get("bias", 0.0))
            weights: Dict[str, float] = dict(self._model.get("weights", {}))
            z = bias
            # experts
            z += float(weights.get("experts.rsi", 0.0)) * float(expert_probs.get("rsi", 0.5))
            z += float(weights.get("experts.macd", 0.0)) * float(expert_probs.get("macd", 0.5))
            z += float(weights.get("experts.trend", 0.0)) * float(expert_probs.get("trend", 0.5))
            # regime
            z += float(weights.get("regime.volatility", 0.0)) * float(regime.get("volatility", 0.0))
            z += float(weights.get("regime.time_of_day", 0.0)) * float(regime.get("time_of_day", 0.0))
            return float(_sigmoid(z))
        # default: average experts
        if not expert_probs:
            return 0.5
        return float(sum(expert_probs.values()) / len(expert_probs))
