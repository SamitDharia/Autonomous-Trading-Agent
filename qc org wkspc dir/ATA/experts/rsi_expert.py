"""
RSI expert model interface.

Loads a tiny logistic model from either QC Object Store or local file.
Falls back to neutral 0.5 if unavailable.
"""

from typing import Any, Dict
import json
from math import exp


def _sigmoid(z: float) -> float:
    try:
        return 1.0 / (1.0 + exp(-z))
    except OverflowError:
        return 0.0 if z < 0 else 1.0


class RSIExpert:
    def __init__(self, model: Any = None):
        self._model = model or {"type": "logistic", "bias": 0.0, "weights": {}}

    @classmethod
    def load(cls, obj_store: Any, key: str) -> "RSIExpert":
        """Load the expert model from QC Object Store or local path.

        key example: 'models/rsi_expert.json'
        """
        data = None
        # Try QC Object Store first
        if obj_store is not None:
            try:
                if obj_store.ContainsKey(key):
                    raw = obj_store.ReadBytes(key)
                    # QC returns a .NET Byte[]; convert robustly to Python bytes
                    try:
                        raw_bytes = bytes(raw.ToArray()) if hasattr(raw, "ToArray") else bytes(raw)
                        data = json.loads(raw_bytes.decode("utf-8"))
                    except Exception:
                        data = None
            except Exception:
                data = None
        # Fallback to local file
        if data is None:
            try:
                with open(key, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = None
        return cls(data)

    def predict_proba(self, features: Dict[str, float]) -> float:
        if not isinstance(self._model, dict) or self._model.get("type") != "logistic":
            return 0.5
        bias = float(self._model.get("bias", 0.0))
        weights: Dict[str, float] = dict(self._model.get("weights", {}))
        z = bias
        for name, w in weights.items():
            z += float(w) * float(features.get(name, 0.0))
        return float(_sigmoid(z))
