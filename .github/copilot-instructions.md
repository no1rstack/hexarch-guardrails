---
description: "Workspace documentation alignment rules for Hexarch Guardrails. Use when editing README, START_HERE, QUICKSTART, INDEX, publication docs, package metadata references, version strings, Python support claims, product positioning, or documentation governance files."
---

# Hexarch Guardrails documentation alignment rules

## Canonical truth sources

- `pyproject.toml` is the canonical source for:
  - package version
  - Python support range
  - package metadata
- `hexarch_guardrails/__init__.py` must expose `__version__` and match `pyproject.toml`.
- If documentation conflicts with `pyproject.toml`, `pyproject.toml` is authoritative.

## How to update docs

- Prefer minimal, targeted factual corrections.
- Do not rewrite entire documents when only a few facts are stale.
- Correct only what is necessary, especially:
  - version numbers
  - Python support ranges
  - installation wording
  - example counts
  - package surface descriptions
- Re-scan after edits to confirm stale values are gone.

## Documentation classification

### Canonical current-state docs
These should reflect the current repository state and current package metadata:
- `README.md`
- `START_HERE.txt`
- `QUICKSTART.md`
- `INDEX.md`
- other current-state overview or publication docs unless explicitly versioned

### Technical reference docs
These should remain technically aligned with the implementation, but may describe specific subsystems in detail:
- `docs/PUBLIC_DOCUMENTATION.md`
- `docs/TECHNICAL_SOURCE_DOCUMENTATION.md`
- `docs/INTEGRATION_GUIDE.md`
- `docs/API_REFERENCE.md`

### Historical docs
These are versioned or snapshot documents and should not be force-updated to the current version unless explicitly requested:
- `RELEASE_NOTES.md`
- `CHANGELOG.md`
- `RELEASE_v*.md`
- older milestone, completion, or phase-summary documents that clearly describe past states

## Product positioning consistency

When aligning top-level docs, use this canonical framing unless a file is intentionally historical:

> Hexarch Guardrails is a decision enforcement and proof system delivered as an SDK, API service, and CLI.

Keep wording close to the document’s existing tone. Do not add unnecessary new marketing language.

## Counting rules

- When counting examples, use curated top-level Python example scripts in `examples/*.py`.
- Exclude `examples/__init__.py`.
- Do not silently count nested demo folders as equivalent to top-level SDK examples unless the doc explicitly refers to demos broadly.

## Drift indicators to check

Watch for:
- stale version strings
- stale Python support ranges
- outdated phrases like `when published`
- stale dependency counts
- SDK-only descriptions when the package also exposes a CLI and API service

## Validation expectations

After documentation edits:
- verify modified files are error-free
- re-scan for the specific stale phrases or values you changed
- call out any intentional historical inconsistencies you left unchanged
