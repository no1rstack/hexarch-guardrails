# v0.1.0 Release

**Released:** January 29, 2026

This is the initial public release of **hexarch-guardrails**, a lightweight policy-driven API protection library for Python.

## 🎯 What's Included

**Core Library:**
- `Guardian` - Main decorator class for policy-based function protection
- `OPAClient` - Integration with Open Policy Agent for policy evaluation
- `PolicyLoader` - YAML-based policy configuration loading
- Custom exceptions for clear error handling

**Examples:**
- OpenAI API budget protection
- Discord rate limiting
- Safe file deletion patterns
- TinyLlama integration with custom policies

**Tests:**
- 30+ unit tests covering all core functionality
- Integration tests for example scenarios

## 📦 Distribution

### Installation from PyPI (Recommended)

```bash
pip install hexarch-guardrails
```

### Download Artifacts

- **Wheel (Binary):** `hexarch_guardrails-0.1.0-py3-none-any.whl` (17 KB)
- **Source Distribution:** `hexarch_guardrails-0.1.0.tar.gz` (14 KB)

Or install locally:

```bash
pip install hexarch_guardrails-0.1.0-py3-none-any.whl
# or
pip install hexarch_guardrails-0.1.0.tar.gz
```

## ✅ Quick Verification

After installation:

```python
from hexarch_guardrails import Guardian, PolicyViolation

# Check version
import hexarch_guardrails
print(hexarch_guardrails.__version__)  # 0.1.0

# Initialize with auto-discovery
guardian = Guardian()

# Use decorator-based protection
@guardian.check("api_budget")
def protected_api_call():
    return "OK"

result = protected_api_call()
```

## 📋 Python Support

- Python 3.8+
- Tested on: 3.8, 3.9, 3.10, 3.11

## 📚 Documentation

- [README](./README.md) - Getting started
- [CHANGELOG](./CHANGELOG.md) - Version history
- [Examples](./examples/) - Integration patterns

## 📄 License

MIT © Noir Stack LLC

See [LICENSE](./LICENSE) for full details.

## 🔗 Links

- **PyPI:** https://pypi.org/project/hexarch-guardrails/
- **GitHub:** https://github.com/no1rstack/hexarch-guardrails
- **Documentation:** https://github.com/no1rstack/hexarch-guardrails#readme

## 🚀 What's Next

- Future releases will add:
  - Additional policy templates
  - Performance optimizations
  - Extended OPA integration features
  - CLI tooling for policy management

---

**This is production-ready release for the Python SDK only.**

The Hexarch platform itself remains proprietary. This package is MIT-licensed for broad compatibility with open-source and commercial environments.
