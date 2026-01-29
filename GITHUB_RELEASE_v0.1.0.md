# hexarch-guardrails v0.1.0 Release

**Initial public release of the hexarch guardrails OPA policy enforcement SDK.**

## What's New

### Core Features
- **6 OPA Policies**: AI governance, entitlements, compliance, quotas, cost controls, user restrictions
- **9 Provider Integrations**: OpenAI, Anthropic Claude, Mistral, Google Gemini, Groq, Cohere, xAI, Nebium, Local Models
- **Python Guardian SDK**: Simple `@guard` decorator + context manager pattern
- **Decision History**: Full audit trail with decision IDs, latency metrics, failure modes
- **Role-Based Access Control**: React AdminDecisionDashboard with auditor/admin gating
- **Operational Instrumentation**: UUID per request, latency measurement, per-provider failure modes

### Testing
- 30+ comprehensive tests covering all policies
- Policy-level validation with OPA server
- End-to-end integration examples
- Schema validation for entitlements

### Documentation
- `DECISION_GOVERNANCE_GUIDE.md`: Decision flow diagrams + concrete enforcement examples
- `NEXT_PUBLIC_SURFACE.md`: Strategic roadmap (v0.2.0 Evidence Export → v0.3.0 CLI → v1.0.0 Policy UI)
- Complete API reference and schema authoring guide
- OPA policy templates for common use cases

## Installation

### PyPI (Recommended)
```bash
pip install hexarch-guardrails
```

### From Wheel
```bash
pip install hexarch_guardrails-0.1.0-py3-none-any.whl
```

### From Source
```bash
pip install hexarch_guardrails-0.1.0.tar.gz
```

## Quick Start

```python
from hexarch.guardian import Guardian

guardian = Guardian()

@guardian.guard("openai", context={"user_id": "alice", "tier": "free"})
async def generate_response():
    return "Hello, world!"
```

## Python Support
- Python 3.8, 3.9, 3.10, 3.11
- Dependencies: requests, pyyaml, python-dotenv

## License
MIT License © Noir Stack LLC (2026)

## Links
- **Documentation**: https://github.com/no1rstack/hexarch-guardrails/blob/main/README.md
- **Policies**: https://github.com/no1rstack/hexarch-guardrails/tree/main/hexarch/policies
- **Examples**: https://github.com/no1rstack/hexarch-guardrails/tree/main/examples
- **PyPI**: https://pypi.org/project/hexarch-guardrails/

## Next Steps
- v0.2.0: Evidence Export Endpoint for compliance auditing
- v0.3.0: Admin CLI (hexarch-ctl) for policy management
- v1.0.0: Policy Authoring UI with visual builder

---
**Released**: January 29, 2026  
**Repository**: https://github.com/no1rstack/hexarch-guardrails  
**Questions?** Open an issue on GitHub
