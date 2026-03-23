---
description: "Run a documentation alignment audit and fix workflow for Hexarch Guardrails. Use when asked to align docs, fix documentation drift, update version strings, standardize product positioning, validate package metadata references, add documentation conventions, or create CI checks for doc/version consistency."
---

# Documentation alignment workflow

Use this prompt when the goal is to audit and align repository documentation with the current package state.

## Objective

Make documentation structurally consistent without rewriting documents unnecessarily.

## Canonical truth sources

1. Read `pyproject.toml`.
2. Extract:
   - current package version
   - Python support range
   - package metadata as needed
3. Read `hexarch_guardrails/__init__.py`.
4. Ensure `__version__` matches `pyproject.toml`.
5. If they differ, fix `__init__.py` first.

## Repository scan

Scan for documentation drift across high-priority files first:
- `README.md`
- `START_HERE.txt`
- `QUICKSTART.md`
- `INDEX.md`
- `PUBLICATION_SUMMARY.md`
- `docs/*.md`

Look for:
- version strings
- Python support ranges
- outdated phrases such as `when published`
- incorrect example counts
- incorrect dependency claims
- SDK-only positioning where the package also includes CLI/API service functionality

Before editing, produce a concise list of mismatches you intend to correct.

## Editing rules

- Use minimal edits.
- Do not rewrite entire documents when factual corrections are enough.
- Only correct incorrect facts or stale wording.
- Reconcile current-state docs to the current package metadata.
- Do not normalize historical/versioned release documents to the current version unless explicitly asked.

## Product positioning rule

For top-level current-state docs, align to this definition:

> Hexarch Guardrails is a decision enforcement and proof system delivered as an SDK, API service, and CLI.

Keep wording close to each document’s existing tone. Avoid introducing extra marketing copy.

## Documentation classification

If needed, create or update `docs/DOCUMENTATION_CONVENTIONS.md` with:

1. Canonical current-state docs
2. Technical reference docs
3. Historical docs

Also include:

> If documentation conflicts with `pyproject.toml`, `pyproject.toml` is authoritative.

## Validator rule

If asked to add automated drift prevention:
- create `scripts/validate_docs.py`
- parse `pyproject.toml`
- validate only current-state docs by default, or explicitly ignore historical files
- fail on mismatched current-state version references
- do not fail on intentional historical release/version documents

If CI is requested, add a GitHub Actions step to run the validator.

## Final pass

After edits:
1. re-scan the changed files
2. confirm stale values are gone
3. report:
   - files modified
   - issues fixed
   - intentional historical inconsistencies left unchanged
