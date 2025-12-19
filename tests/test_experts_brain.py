import json
from pathlib import Path
import pytest

# Imports moved inside test to avoid import errors when skipped
# from experts.rsi_expert import RSIExpert
# from experts.macd_expert import MACDExpert
# from experts.trend_expert import TrendExpert
# from ensemble.brain import Brain


@pytest.mark.skip(reason="Brain/ensemble architecture deprecated - focusing on RSI-only strategy (Phase 1-3)")
def test_expert_and_brain_probs_in_unit_interval():
    # Ensure model files exist
    for f in ["models/rsi_expert.json", "models/macd_expert.json", "models/trend_expert.json", "models/brain.json"]:
        assert Path(f).exists(), f"Missing {f}"

    rsi = RSIExpert.load(None, "models/rsi_expert.json")
    macd = MACDExpert.load(None, "models/macd_expert.json")
    trend = TrendExpert.load(None, "models/trend_expert.json")
    brain = Brain.load(None, "models/brain.json")

    features = {
        "rsi": 28.0,
        "macd_hist": -0.05,
        "bb_z": -1.2,
        "ema20": 250.0,
        "ema200": 240.0,
    }
    rp = rsi.predict_proba(features)
    mp = macd.predict_proba(features)
    tp = trend.predict_proba(features)
    assert 0.0 <= rp <= 1.0
    assert 0.0 <= mp <= 1.0
    assert 0.0 <= tp <= 1.0
    p = brain.predict_proba({"rsi": rp, "macd": mp, "trend": tp}, {"volatility": 0.02, "time_of_day": 10.5})
    assert 0.0 <= p <= 1.0

