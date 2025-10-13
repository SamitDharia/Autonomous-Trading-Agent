"""
MACD expert model interface.
"""

from typing import Any, Dict


class MACDExpert:
    def __init__(self, model: Any = None):
        self._model = model

    @classmethod
    def load(cls, obj_store: Any, key: str) -> "MACDExpert":
        # TODO: Implement actual load from QC Object Store.
        model = None
        return cls(model)

    def predict_proba(self, features: Dict[str, float]) -> float:
        # TODO: Use the calibrated model once available.
        return 0.5

