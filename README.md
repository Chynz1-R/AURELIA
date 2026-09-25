# AURELIA

**AURELIA** stands for **Adaptive Universal Reasoning Engine for Learning, Investigation, and Action**.

This repository provides an initial, local-first Python foundation for structured research workflows with:

- a bounded **research engine**,
- typed **evidence and claim tracking**,
- an explainable **safety layer**, and
- deterministic **uncertainty reporting**.

## Architecture

Source layout (`src/aurelia`):

- `models.py` — typed dataclasses for questions, plans, evidence, claims, safety decisions, assessments, uncertainty, and synthesis outputs.
- `evidence.py` — in-memory evidence store with provenance-preserving records and support/contradiction claim links.
- `research.py` — `ResearchEngine` for question validation, bounded plan creation, claim assessment, synthesis, and unresolved question tracking.
- `safety.py` — configurable `SafetyPolicy` and `SafetyLayer` that explicitly allow/flag/block risky inputs.
- `uncertainty.py` — deterministic confidence and uncertainty computation using evidence quality, agreement/conflict, and coverage.
- `cli.py` / `__main__.py` — minimal no-network demo entry point.

## Install and run locally

```bash
python -m pip install -e .
python -m aurelia "How effective is intervention X?"
```

Or via console script:

```bash
aurelia "How effective is intervention X?"
```

## Run tests

```bash
python -m pytest
```

## Safety boundaries and non-goals

AURELIA currently:

- does **not** perform autonomous real-world execution,
- does **not** perform network scraping or credential handling,
- does **not** automate medical/legal/financial decisions,
- does **not** claim to independently solve unsolved scientific problems,
- does enforce conservative, auditable safety decisions that can block synthesis.

Blocked actions are never silently executed; safety outcomes are explicit in outputs.

## Roadmap (initial)

- Persistent evidence backend adapters.
- Richer policy tuning and audit log integration.
- Stronger claim graph reasoning and citation tooling.
- Expanded uncertainty diagnostics and report export formats.
