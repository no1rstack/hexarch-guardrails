# 📚 Hexarch Guardrails Python SDK - Complete Index

## 🚀 START HERE

**New to this project?** Read in this order:

1. **START_HERE.txt** ← Begin here (2 min read)
2. **QUICKSTART.md** ← Get started in 5 minutes
3. **examples/openai_budget.py** ← See it in action
4. **docs/API_REFERENCE.md** ← Learn the API

---

## 📖 DOCUMENTATION

### Quick Reference
- [START_HERE.txt](START_HERE.txt) - Orientation guide
- [README.md](README.md) - Package overview
- [QUICKSTART.md](QUICKSTART.md) - 5-minute tutorial

### Comprehensive Guides
- [docs/API_REFERENCE.md](docs/API_REFERENCE.md) - Complete API (500 lines)
- [docs/INTEGRATION_GUIDE.md](docs/INTEGRATION_GUIDE.md) - 12 integration patterns
- [FILE_MANIFEST.md](FILE_MANIFEST.md) - File-by-file description

### Status & Delivery
- [COMPLETION_REPORT.md](COMPLETION_REPORT.md) - Delivery summary
- [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) - What's included
- [DELIVERY_SUMMARY.md](DELIVERY_SUMMARY.md) - High-level overview

---

## 💻 CORE LIBRARY

### Main Module: `hexarch_guardrails/`

**Guardian** (Main Class)
- File: [hexarch_guardrails/guardian.py](hexarch_guardrails/guardian.py)
- What: Decorator-based policy enforcement
- Methods: `check()`, `evaluate_policy()`, `list_policies()`, `get_policy()`
- Example: `@guardian.check("api_budget")`

**OPA Client**
- File: [hexarch_guardrails/opa_client.py](hexarch_guardrails/opa_client.py)
- What: REST client for OPA server
- Methods: `check_policy()`, `get_policy()`, `publish_policy()`
- Usage: Handles all OPA communication

**Policy Loader**
- File: [hexarch_guardrails/policy_loader.py](hexarch_guardrails/policy_loader.py)
- What: YAML config management with auto-discovery
- Methods: `load()`, `find_policy_file()`, `validate()`
- Feature: Walks up directory tree to find config

**Exceptions**
- File: [hexarch_guardrails/exceptions.py](hexarch_guardrails/exceptions.py)
- Types: PolicyViolation, PolicyWarning, OPAConnectionError, PolicyConfigError, OPAPolicyError
- Usage: Proper error handling throughout

**Templates**
- File: [hexarch_guardrails/templates.py](hexarch_guardrails/templates.py)
- What: Default policy templates and config
- Usage: Reference for users

**Package Init**
- File: [hexarch_guardrails/__init__.py](hexarch_guardrails/__init__.py)
- What: Exports main classes and exceptions
- Usage: `from hexarch_guardrails import Guardian`

---

## 🎯 EXAMPLES

Real-world use cases - copy and adapt:

1. **OpenAI Budget Protection** 💰
   - File: [examples/openai_budget.py](examples/openai_budget.py)
   - Use: Prevent overspending on API calls
   - Pattern: `@guardian.check("api_budget")`

2. **Discord Rate Limiting** 🤖
   - File: [examples/discord_ratelimit.py](examples/discord_ratelimit.py)
   - Use: Prevent getting rate-limited
   - Pattern: `@guardian.check("rate_limit")`

3. **Safe File Operations** 🗑️
   - File: [examples/safe_delete.py](examples/safe_delete.py)
   - Use: Require confirmation for deletes
   - Pattern: `@guardian.check("safe_delete")`

---

## 🧪 TESTS

Run tests to verify everything works:

```bash
pytest                              # Run all
pytest --cov=hexarch_guardrails     # With coverage
pytest -v                           # Verbose
```

Test Files:
- [tests/test_guardian.py](tests/test_guardian.py) - Guardian class tests (10+)
- [tests/test_opa_client.py](tests/test_opa_client.py) - OPA client tests (12+)
- [tests/test_policy_loader.py](tests/test_policy_loader.py) - Config loader tests (10+)

---

## ⚙️ CONFIGURATION

### Policy File
- **File:** [hexarch.yaml](hexarch.yaml)
- **What:** Annotated configuration template
- **Includes:** 6 built-in policies with full explanations
- **How to use:** Copy to your project root

### Package Configuration
- **setup.py** - PyPI package configuration
  - Ready to publish: `python setup.py sdist bdist_wheel`
  - Dependencies: requests, pyyaml, python-dotenv
  
- **pytest.ini** - Test configuration
  - Auto-discovers tests in `tests/` directory
  - Runs with verbose output
  
- **.gitignore** - Standard Python ignores
  - Excludes __pycache__, .venv, dist, etc.

---

## 📊 QUICK STATS

| Category | Details |
|----------|---------|
| **Core Code** | 5 files, ~620 lines |
| **Examples** | 3 files, ~115 lines |
| **Tests** | 3 files, ~390 lines, 30+ cases |
| **Docs** | 8+ files, ~2000 lines |
| **Total** | ~3,125 lines of code + docs |
| **Status** | Production-ready ✅ |

---

## 🎯 COMMON TASKS

### Want to...
- **Get started?** → Read [QUICKSTART.md](QUICKSTART.md)
- **Understand the API?** → Read [docs/API_REFERENCE.md](docs/API_REFERENCE.md)
- **See examples?** → Check [examples/](examples/)
- **Integrate with my tech?** → Read [docs/INTEGRATION_GUIDE.md](docs/INTEGRATION_GUIDE.md)
- **Understand the code?** → Read [hexarch_guardrails/guardian.py](hexarch_guardrails/guardian.py)
- **Deploy to production?** → See [setup.py](setup.py)
- **Run tests?** → Run `pytest`
- **Know what's included?** → Read [FILE_MANIFEST.md](FILE_MANIFEST.md)

---

## 🔑 KEY CONCEPTS

### The Guardian Class
```python
from hexarch_guardrails import Guardian

guardian = Guardian()  # Auto-discovers hexarch.yaml

@guardian.check("policy_id")
def protected_function():
    pass
```

### Available Policies
1. **api_budget** - Prevent API overspending
2. **rate_limit** - Prevent rate limiting
3. **safe_delete** - Require confirmation for deletes
4. **access_control** - Permission-based control
5. **time_based** - Time-restricted operations
6. **feature_flags** - Feature availability

### How It Works
1. Decorator intercepts function call
2. Queries OPA with policy and context
3. OPA returns decision (allow/block/warn)
4. Executes function or raises exception

---

## 🚀 DEPLOYMENT OPTIONS

### As Python Package
```bash
pip install hexarch-guardrails
```

### To PyPI
```bash
python setup.py sdist bdist_wheel
twine upload dist/*
```

### In Docker
```dockerfile
FROM python:3.10-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

### In Kubernetes
Reference [docs/INTEGRATION_GUIDE.md](docs/INTEGRATION_GUIDE.md) for full K8s example

---

## 📞 HELP & SUPPORT

### Stuck? Try:
1. Read [QUICKSTART.md](QUICKSTART.md) for basics
2. Check [docs/API_REFERENCE.md](docs/API_REFERENCE.md) for API
3. Look at [examples/](examples/) for your use case
4. Review [docs/INTEGRATION_GUIDE.md](docs/INTEGRATION_GUIDE.md) for patterns
5. Read source code comments
6. Run tests to verify setup

---

## 🎓 LEARNING PATH

### Beginner (30 min)
1. Read START_HERE.txt (2 min)
2. Read QUICKSTART.md (5 min)
3. Copy and run examples (10 min)
4. Try on your own code (10 min)

### Intermediate (1-2 hours)
1. Read API_REFERENCE.md (30 min)
2. Study guardian.py source (30 min)
3. Write custom policies (30 min)

### Advanced (2-4 hours)
1. Study OPA integration (1 hour)
2. Customize policies (1 hour)
3. Build extensions (1-2 hours)

---

## 📁 FILE TREE

```
hexarch-guardrails-py/
├── Core Library
│   ├── hexarch_guardrails/guardian.py        ⭐ Main class
│   ├── hexarch_guardrails/opa_client.py      🔗 OPA integration
│   ├── hexarch_guardrails/policy_loader.py   📋 Config loading
│   ├── hexarch_guardrails/exceptions.py      ❌ Error types
│   └── hexarch_guardrails/templates.py       📝 Defaults
├── Examples
│   ├── examples/openai_budget.py             💰
│   ├── examples/discord_ratelimit.py         🤖
│   └── examples/safe_delete.py               🗑️
├── Tests
│   ├── tests/test_guardian.py                ✅
│   ├── tests/test_opa_client.py              ✅
│   └── tests/test_policy_loader.py           ✅
├── Documentation
│   ├── START_HERE.txt                        🎯 Start here
│   ├── QUICKSTART.md                         🚀
│   ├── README.md                             📖
│   ├── docs/API_REFERENCE.md                 📚
│   ├── docs/INTEGRATION_GUIDE.md             🔧
│   ├── FILE_MANIFEST.md                      📋
│   ├── COMPLETION_REPORT.md                  📊
│   └── IMPLEMENTATION_STATUS.md              ✅
└── Configuration
    ├── hexarch.yaml                          ⚙️
    ├── setup.py                              📦
    ├── pytest.ini                            🧪
    └── .gitignore                            🚫
```

---

## ✅ VERIFICATION

To verify everything is working:

```bash
# Install
pip install -e .

# Run tests
pytest

# Try example
python examples/openai_budget.py

# Check code loads
python -c "from hexarch_guardrails import Guardian; print('✅ Works!')"
```

All should pass ✅

---

## 🎉 READY TO GO

Everything is:
- ✅ Implemented
- ✅ Tested
- ✅ Documented
- ✅ Production-ready

**Start with:** [START_HERE.txt](START_HERE.txt)

**Location:** `c:\Users\noir\.vscode\projects\Hexarch\hexarch-guardrails-py\`
