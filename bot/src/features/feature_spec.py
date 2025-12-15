"""Defines the canonical feature list and small helpers used by QC and runtime."""

FEATURE_LIST_H1 = [
    "rsi",
    "macd",
    "bb_z",
    "atr",
    "ema20_rel",
    "vol_z",
]


def compute_feature_hash(feature_list):
    import hashlib
    s = "|".join(feature_list)
    return hashlib.sha256(s.encode()).hexdigest()
