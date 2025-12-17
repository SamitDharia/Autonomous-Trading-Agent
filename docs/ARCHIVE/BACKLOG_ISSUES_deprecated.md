# Prepared GitHub Issues (from docs/BACKLOG.md)

These are the issue titles and bodies parsed from `docs/BACKLOG.md`. You can use them to create issues manually, or run `scripts/create_github_issues.ps1` to create them automatically once your PAT is available in `$env:GITHUB_TOKEN`.

---

## Epic: Runtime Hardening

Title: Epic: Runtime Hardening

Body:
- Add kill-switches and daily health checks
- Implement Alpaca bracket order reconciliation
- Add alerts and telemetry (Slack/email)

Acceptance: system halts after configurable loss thresholds and sends notifications

Labels: epic, backlog

---

## Epic: Training & Diagnostic Reliability

Title: Epic: Training & Diagnostic Reliability

Body:
- Add purged CV, bootstrap CI, permutation importance (done)
- Automate QC Research runs and artifact publications

Acceptance: diagnostics scripts export `output/` artifacts and timestamped brain JSONs

Labels: epic, backlog

---

## Epic: Deployment & CI

Title: Epic: Deployment & CI

Body:
- Automate QC cloud push and fixes for project-name issue
- Add release pipelines and model promotion workflow

Acceptance: merged brain JSONs are tagged and available to runtime loader

Labels: epic, backlog

---

## Task: Fix QC cloud push CLI project-name error

Title: Task: Fix QC cloud push CLI project-name error

Body:
Steps: reproduce, adjust project config or rename before push, test push

Acceptance: `qc` push succeeds with no special-character error

Labels: task, backlog

---

## Task: Add `docs/BACKLOG.md`

Title: Task: Add docs/BACKLOG.md

Body:
Add project backlog (GitHub Issues style) to `docs/BACKLOG.md`

Labels: task, backlog

---

## Task: Clean repo of generated artifacts

Title: Task: Clean repo of generated artifacts

Body:
- Remove committed `__pycache__/`, `*.pyc`, `.QuantConnect/cache/` files
- Add `.gitignore` rules to prevent recurrence

Acceptance: `git status` shows no tracked bytecode files

Labels: task, backlog

---

## Task: Add PR review checklist for model promotion

Title: Task: Add PR review checklist for model promotion

Body:
Include tests, diagnostics pass, AUC improvements and feature-hash parity

Labels: task, backlog
