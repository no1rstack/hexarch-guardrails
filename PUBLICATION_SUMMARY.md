# Hexarch Guardrails - Publication Summary

**Date:** March 22, 2026  
**Status:** ✅ Published and actively versioned

> Source of truth for current package metadata is `pyproject.toml`, `setup.py`, `hexarch_guardrails/__init__.py`, and `CHANGELOG.md`.

---

## Distribution Channels

### 1. PyPI (Primary - LIVE ✅)
- **Package:** https://pypi.org/project/hexarch-guardrails/
- **Installation:** `pip install hexarch-guardrails`
- **Current package version:** 0.4.1
- **License:** MIT
- **Status:** Public distribution channel

### 2. GitHub Repository (LIVE ✅)
- **URL:** https://github.com/no1rstack/hexarch-guardrails
- **Branch:** main (default)
- **Status:** Public, all files committed
- **Releases:** Versioned via tags and release notes in the repository

### 3. GitHub Packages (Configured ✅)
- **Status:** Ready for publication
- **Workflow:** Automated via GitHub Actions
- **Trigger:** Tag push (v*) triggers build and upload

---

## Files Published to GitHub

### Documentation
- ✅ README.md - Getting started guide
- ✅ LICENSE - MIT License (Noir Stack LLC)
- ✅ CHANGELOG.md - Version history
- ✅ RELEASE_NOTES.md / release-specific notes - Release documentation
- ✅ docs/ - API, integration, validation, and technical documentation

### Configuration
- ✅ pyproject.toml - Modern Python packaging metadata
- ✅ setup.py - setuptools configuration
- ✅ .gitignore - Python project standards

### Automation
- ✅ workflows/publish.yml - GitHub Actions for PyPI publishing and releases

### Source Code
- ✅ hexarch_guardrails/ (library package)
- ✅ examples/ (4 working examples)
- ✅ tests/ (30+ unit tests)

---

## Package Metadata

```
Name: hexarch-guardrails
Version: 0.4.1
License: MIT © Noir Stack LLC
Author: Noir Stack (hira@noirstack.com)
Home: https://www.noirstack.com/
Repository: https://github.com/no1rstack/hexarch-guardrails
Python: 3.8, 3.9, 3.10, 3.11, 3.12
Status: Beta (production-ready package)
```

---

## Distribution Artifacts

### Wheel (Binary Distribution)
- File pattern: `hexarch_guardrails-<version>-py3-none-any.whl`
- Type: Universal Python 3 wheel
- Location: PyPI / GitHub release assets when attached

### Source Distribution
- File pattern: `hexarch_guardrails-<version>.tar.gz`
- Type: Source distribution
- Location: PyPI / GitHub release assets when attached

Both distributions include:
- Core library
- CLI and server modules
- Examples and demos
- Tests
- Documentation

---

## Creating the GitHub Release

### Automated (via Git tag) - Recommended
```bash
# In the repository root
git tag v0.4.1
git push origin v0.4.1

# GitHub Actions triggers automatically:
# 1. Build package (python -m build)
# 2. Upload to PyPI (twine upload)
# 3. Create GitHub Release with assets
```

For future releases, replace `v0.4.1` with the next package version and update `CHANGELOG.md` / release notes first.

---

## Installation Methods

### From PyPI (Recommended - LIVE NOW)
```bash
pip install hexarch-guardrails
```

### From GitHub Releases
```bash
# Download wheel from GitHub Release page
pip install hexarch_guardrails-<version>-py3-none-any.whl

# Or source distribution
pip install hexarch_guardrails-<version>.tar.gz
```

### From Source (Development)
```bash
git clone https://github.com/no1rstack/hexarch-guardrails.git
cd hexarch-guardrails
pip install -e .
```

---

## Verification

### Check Installation
```bash
python -c "from hexarch_guardrails import Guardian; print(Guardian.__doc__)"
```

### Check Version
```bash
python -c "import hexarch_guardrails; print(hexarch_guardrails.__version__)"
# Output: 0.4.1
```

### Run Tests
```bash
pytest tests/
# All 30+ tests pass
```

---

## Release Planning

- Use `CHANGELOG.md` as the public change log
- Use `RELEASE_NOTES.md` and versioned release notes for release-specific detail
- Validate README install and demo paths before tagging
- Confirm package version alignment across `pyproject.toml`, `setup.py`, and `hexarch_guardrails/__init__.py`

---

## Support & Links

- **Documentation:** https://github.com/no1rstack/hexarch-guardrails#readme
- **Bug Reports:** https://github.com/no1rstack/hexarch-guardrails/issues
- **PyPI Package:** https://pypi.org/project/hexarch-guardrails/
- **License:** MIT (see LICENSE file)

---

## Summary

✅ **Package published to PyPI**  
✅ **Source code in public GitHub repository**  
✅ **Release documentation prepared**  
✅ **Automated publishing workflow configured**  
✅ **Current package metadata aligned to 0.4.1**  

**Status: Ready for public distribution and ongoing releases**

Installation: `pip install hexarch-guardrails`
