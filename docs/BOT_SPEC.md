# Autonomous TSLA Quant Bot — Spec v1.0

This document captures the single-page bot spec and the repo-level plan.

See `bot/` for a runnable skeleton and `bot/brains/TSLA_1h/brain_schema_v1.json` for the Brain JSON contract.

Key non-negotiables:
- Single symbol TSLA, single timeframe (start with 1h or 15m)
- Risk engine is authoritative; ML is an opinion
- Kill-switches: daily loss, drawdown, data quality checks

Workplan: follow the 8-week roadmap in `docs/PLAN.md`.
