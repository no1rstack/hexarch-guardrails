# v0.1.0 Release

**Released:** January 29, 2026

🎉 **Initial Public Release of hexarch-guardrails**

A lightweight, policy-driven API protection library for students, solo developers, and enterprises.

## What's New

### Core Features
- ✅ **Guardian class** - Decorator-based policy enforcement
- ✅ **OPA integration** - Open Policy Agent for policy evaluation
- ✅ **Zero-config setup** - Auto-discovers hexarch.yaml policy files
- ✅ **YAML-driven policies** - Define rules without code changes
- ✅ **Local-first operation** - Works offline with local OPA
- ✅ **Python 3.8+** - Broad compatibility

### Policies Included
- `api_budget` - Protect against API cost overruns
- `rate_limit` - Prevent API abuse with request throttling
- `safe_delete` - Require confirmation for destructive operations
- `access_control` - Role-based enforcement
- `quality_control` - Parameter validation
- `feature_flags` - Feature availability control

### Examples
- OpenAI budget protection
- Discord rate limiting
- Safe file deletion patterns
- TinyLlama integration

### Testing
- 30+ unit tests
- Integration tests for all examples
- Full test coverage of core components

## Installation

### From PyPI (Recommended)
```bash
pip install hexarch-guardrails
```

### From Distribution
```bash
# Wheel (faster installation)
pip install hexarch_guardrails-0.1.0-py3-none-any.whl

# Source distribution
pip install hexarch_guardrails-0.1.0.tar.gz
```

## Quick Start

```python
from hexarch_guardrails import Guardian

# Initialize (auto-discovers hexarch.yaml)
guardian = Guardian()

# Protect API calls with decorators
@guardian.check("api_budget")
def expensive_operation():
    return openai.ChatCompletion.create(model="gpt-4", ...)

# Use it
result = expensive_operation()
```

## Documentation

- [README](https://github.com/no1rstack/hexarch-guardrails#readme)
- [CHANGELOG](https://github.com/no1rstack/hexarch-guardrails/blob/main/CHANGELOG.md)
- [API Reference](https://github.com/no1rstack/hexarch-guardrails#api-reference)
- [Examples](https://github.com/no1rstack/hexarch-guardrails/tree/main/examples)

## Package Contents

- **Wheel**: `hexarch_guardrails-0.1.0-py3-none-any.whl` (17 KB)
- **Source**: `hexarch_guardrails-0.1.0.tar.gz` (13 KB)

Both include:
- Core library (`hexarch_guardrails/`)
- 4 working examples
- 30+ unit tests
- Full documentation

## Python Support

- Python 3.8
- Python 3.9
- Python 3.10
- Python 3.11

## License

MIT © Noir Stack LLC

See [LICENSE](https://github.com/no1rstack/hexarch-guardrails/blob/main/LICENSE)

## Links

- **PyPI**: https://pypi.org/project/hexarch-guardrails/
- **GitHub**: https://github.com/no1rstack/hexarch-guardrails
- **Bug Reports**: https://github.com/no1rstack/hexarch-guardrails/issues

---

**This package contains the Python SDK only.** The Hexarch platform itself remains proprietary. This MIT-licensed library enables broad distribution and integration while protecting platform IP.
