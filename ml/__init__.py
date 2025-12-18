"""
ML shadow-mode logging and prediction module.

This package provides optional ML integration that:
1. Logs features + trade context for future model training (Phase 4.1)
2. Optionally runs predictions if a trained model exists (Phase 4.2+)

Never impacts live trading - all operations wrapped in try/except.
"""

__version__ = "0.1.0"
