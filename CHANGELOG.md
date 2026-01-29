# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-29

### Added
- Initial public release of hexarch-guardrails Python SDK
- Guardian class for policy-driven decorator-based protection
- OPAClient for integration with Open Policy Agent
- PolicyLoader for YAML-based policy configuration
- Auto-discovery of hexarch.yaml policy files
- Custom exception types (PolicyViolation, OPAConnectionError, PolicyConfigError)
- Examples for OpenAI budget protection, Discord rate limiting, safe deletions
- TinyLlama integration example with custom policies
- Comprehensive test suite (30+ tests)
- MIT License (Noir Stack LLC)

### Features
- Zero-config auto-discovery of policy files
- Decorator-based protection: `@guardian.check("policy_id")`
- YAML-driven policy configuration
- Local-first operation (works offline with local OPA)
- Compatible with Python 3.8+
- Environment variable loading via python-dotenv

### Documentation
- README with quick start guide
- API reference documentation
- Policy authoring guide
- Multiple integration examples

---

[0.1.0]: https://github.com/no1rstack/hexarch-guardrails/releases/tag/v0.1.0
