# hexarch-guardrails Releases

This directory contains the Python package distribution artifacts for `hexarch-guardrails`.

## Version 0.1.0

**Release Date:** January 29, 2026

### Distribution Files

- **Wheel (Binary Distribution)**
  - File: `hexarch_guardrails-0.1.0-py3-none-any.whl`
  - Size: 17.5 KB
  - Type: Universal Python 3 wheel
  - Installation: `pip install hexarch_guardrails-0.1.0-py3-none-any.whl`

- **Source Distribution (SDist)**
  - File: `hexarch_guardrails-0.1.0.tar.gz`
  - Size: 13.6 KB
  - Type: Gzip-compressed tarball
  - Installation: `pip install hexarch_guardrails-0.1.0.tar.gz`

### Contents

Both distributions include:
- Core library: `hexarch_guardrails/`
  - `guardian.py` - Main Guardian class for policy decoration
  - `opa_client.py` - OPA server communication
  - `policy_loader.py` - YAML policy configuration loader
  - `exceptions.py` - Custom exception types
  - `templates.py` - Policy templates and defaults

- Examples:
  - `examples/openai_budget.py` - Budget protection example
  - `examples/discord_ratelimit.py` - Rate limiting example
  - `examples/safe_delete.py` - Safe deletion example
  - `examples/tinyllama_guardrails.py` - TinyLlama integration

- Tests:
  - `tests/test_guardian.py` - Guardian class tests
  - `tests/test_opa_client.py` - OPA client tests
  - `tests/test_policy_loader.py` - Policy loader tests

- Documentation:
  - `README.md` - Getting started guide
  - `LICENSE` - MIT License
  - `setup.py` - Package metadata

### Python Compatibility

- Python 3.8+
- Tested on: 3.8, 3.9, 3.10, 3.11

### Dependencies

- `requests>=2.28.0` - HTTP client for OPA communication
- `pyyaml>=6.0` - YAML policy configuration parsing
- `python-dotenv>=0.21.0` - Environment variable loading

### Installation from File

```bash
# From wheel (recommended)
pip install hexarch_guardrails-0.1.0-py3-none-any.whl

# From source
pip install hexarch_guardrails-0.1.0.tar.gz
```

### Installation from PyPI

```bash
pip install hexarch-guardrails
```

### Verification

After installation, verify:

```python
from hexarch_guardrails import Guardian, PolicyViolation

# Check version
import hexarch_guardrails
print(hexarch_guardrails.__version__)  # Should print: 0.1.0

# Create instance
guardian = Guardian()
print(f"Guardian initialized: {guardian is not None}")
```

### License

MIT © Noir Stack LLC - See LICENSE file
