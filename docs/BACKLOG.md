# Project Backlog (GitHub Issues style)

## Epics

- Epic: Runtime Hardening
  - Add kill-switches and daily health checks
  - Implement Alpaca bracket order reconciliation
  - Add alerts and telemetry (Slack/email)
  - Acceptance: system halts after configurable loss thresholds and sends notifications

- Epic: Training & Diagnostic Reliability
  - Add purged CV, bootstrap CI, permutation importance (done)
  - Automate QC Research runs and artifact publications
  - Acceptance: diagnostics scripts export `output/` artifacts and timestamped brain JSONs

- Epic: Deployment & CI
  - Automate QC cloud push and fixes for project-name issue
  - Add release pipelines and model promotion workflow
  - Acceptance: merged brain JSONs are tagged and available to runtime loader

## Tasks

- Task: Fix QC cloud push CLI project-name error
  - Steps: reproduce, adjust project config or rename before push, test push
  - Accept: `qc` push succeeds with no special-character error

- Task: Add `docs/BACKLOG.md` (this file)

- Task: Clean repo of generated artifacts
  - Remove committed `__pycache__/`, `*.pyc`, `.QuantConnect/cache/` files
  - Add `.gitignore` rules to prevent recurrence
  - Acceptance: `git status` shows no tracked bytecode files

- Task: Add PR review checklist for model promotion
  - Include tests, diagnostics pass, AUC improvements and feature-hash parity

If you'd like, I can convert each task into GitHub Issues and open them as a PR-ready batch.
