import pytest
from bot.src.model.brain_loader import BrainLoader, BrainLoadError
from bot.src.features.feature_spec import FEATURE_LIST_H1, compute_feature_hash
from pathlib import Path

def test_brain_loader_valid():
    path = Path(__file__).parents[3] / 'brains' / 'TSLA_1h' / 'brain_latest.json'
    bl = BrainLoader(str(path))
    assert bl.get_model() is not None

def test_feature_hash_mismatch():
    path = Path(__file__).parents[3] / 'brains' / 'TSLA_1h' / 'brain_latest.json'
    bl = BrainLoader(str(path))
    assert not bl.feature_hash_ok(FEATURE_LIST_H1)
