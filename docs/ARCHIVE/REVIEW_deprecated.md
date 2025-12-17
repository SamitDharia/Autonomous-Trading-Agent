# Repository Review

## Overview
This repository contains a QuantConnect LEAN trading algorithm skeleton with supporting modules for feature construction, expert
models, an ensemble "brain", risk utilities, JSON model artifacts, and a simple local backtest harness. The structure broadly
matches the project brief, and the code is reasonably well documented, but several critical gaps block reliable execution and
testing.

## Strengths
- Clear separation between feature generation, expert models, ensemble logic, and risk helpers, which matches the documented
  architecture and makes future extensions straightforward. 【F:algo.py†L1-L195】【F:risk/position_sizing.py†L1-L22】
- Sample JSON weights and loaders are in place for each expert and the ensemble, enabling deterministic behaviour once the
  loading paths are fixed. 【F:experts/rsi_expert.py†L1-L47】【F:ensemble/brain.py†L1-L55】【F:models/brain.json†L1-L11】
- A lightweight local backtest script provides a fast sanity check on the RSI heuristic, which is valuable for iteration without
  needing the full LEAN environment. 【F:scripts/local_backtest.py†L1-L64】

## Issues & Risks
### 1. Test suite fails to import project packages
Running `pytest` from the repository root fails because Python cannot resolve the top-level packages (e.g., `experts`). The test
modules import the packages directly but never add the project root to `sys.path`, so when the tests execute from inside the
`tests/` directory the imports break. This prevents the automated test suite from running at all. 【F:tests/test_experts_brain.py†L1-L35】【adf6ac†L1-L15】

**Recommendation:** Add a `conftest.py` (or modify each test) to append the repository root to `sys.path`, or convert the
project into an installable package so the imports resolve consistently.

### 2. Risk guard for the daily stop is a no-op
`risk.guards.daily_pnl_stop_hit` always returns `False`, so any code that relies on this helper will never trigger the daily
P&L stop, violating a core risk control from the project brief. The docstring explicitly calls this out as TODO, but shipping
with a hardcoded `False` means the guard cannot be trusted. 【F:risk/guards.py†L8-L25】

**Recommendation:** Implement the actual equity drawdown check (using `algo.Portfolio.TotalPortfolioValue` and tracked start-of-
day equity) or fail loudly so callers know the guard is unimplemented.

### 3. Feature builder stub returns an empty dictionary
`features.feature_builder.build_features` currently returns `{}`. Any consumer that expects indicator or regime values will get
missing data, leading to degenerate model predictions. This is especially problematic for the experts, which expect feature
names such as `"rsi"`, `"macd_hist"`, etc. 【F:features/feature_builder.py†L1-L25】

**Recommendation:** Implement the function to read the indicators from the provided context (or raise `NotImplementedError` to
avoid silently returning empty features).

### 4. Repository includes generated artifacts
`__pycache__` directories are committed in multiple packages (`experts`, `ensemble`, `scripts`, `tests`). These should not be
version-controlled and indicate the absence of a `.gitignore` rule for Python bytecode. Keeping them in the tree leads to noisy
diffs and merge conflicts. 【84dba5†L1-L7】

**Recommendation:** Remove the cached files from version control and add standard Python ignore patterns (`__pycache__/`, `*.pyc`,
`.pytest_cache/`, etc.).

### 5. Documentation gaps
The README provides only the project title with no setup or usage guidance, which makes onboarding difficult. In addition,
the project brief references tests (e.g., `test_features.py`, `test_rsi_expert.py`) that do not exist, so expectations are out of
sync with the actual codebase. 【F:README.md†L1-L1】【F:docs/PROJECT_BRIEF.md†L59-L78】

**Recommendation:** Flesh out the README with installation, testing, and basic workflow instructions, and align the brief with the
current testing strategy.

## Suggested Next Steps
1. Fix the import path issue so the existing tests execute, then add coverage for `risk` and feature utilities.
2. Implement or explicitly guard incomplete functions (`daily_pnl_stop_hit`, `build_features`) before relying on them in the
   live algorithm.
3. Add a repository-level `.gitignore` and remove existing bytecode caches from version control.
4. Expand the README and keep `docs/PROJECT_BRIEF.md` in sync with the evolving test suite.
