# Implementation Audit (Code-and-Test Grounded)

## Objective

Establish a documentation baseline where every architectural/capability statement is tied to observable implementation.

## Audit Inputs

Code surfaces reviewed:
- SDK: `hexarch_guardrails/*`
- CLI + server: `hexarch_cli/*`
- ORM/data models: `hexarch_cli/models/*`
- Runtime config paths: `hexarch_cli/server/security.py`, `hexarch_cli/commands/serve.py`, `hexarch_cli/db.py`
- Dependencies: `pyproject.toml`
- Existing docs for consistency risk: `README.md`, `docs/API_REFERENCE.md`, `docs/INTEGRATION_GUIDE.md`

Verification run:
- `pytest tests/test_server_authorize.py tests/test_rules_engine.py tests/test_guardian.py -q`
- Result: 29 passed

## Verified Findings

1. **Policy evaluation plane exists and is callable over HTTP**
   - Evidence: `/authorize` endpoint and policy evaluation path in server code.

2. **Governance entities are persisted and queryable**
   - Evidence: SQLAlchemy models and API routes for rules/policies/entitlements/decisions.

3. **Audit trail includes chain verification mechanics**
   - Evidence: canonical payload + `prev_hash`/`entry_hash`; chain verify function and endpoint.

4. **API key lifecycle and scope enforcement are implemented**
   - Evidence: API key model, issue/revoke routes, and scope checks in enforcement module.

5. **Operational security middleware is implemented**
   - Evidence: security headers, request ID injection, and rate-limit middleware.

## Qualified Findings (Implemented with limits)

1. **Rate limiting**
   - Implemented as in-memory sliding window per process.
   - Not a distributed/shared limiter across replicas.

2. **Audit checkpoint signing**
   - Implemented via optional HMAC signing with configured key.
   - Signing is conditional, not always-on by default.

3. **OpenAPI/docs exposure**
   - Available only when explicitly enabled.

## Claims Removed or Reworded for Public Safety

The following claim styles are intentionally excluded from public docs unless external evidence is provided:
- Certification/attestation claims
- Guaranteed HA/SLO/performance absolutes
- Distributed/global enforcement guarantees not implemented in code
- Deep operational internals that increase security disclosure risk

## Outputs Produced

- Internal source document: `docs/TECHNICAL_SOURCE_DOCUMENTATION.md`
- Claim matrix: `docs/CLAIMS_VALIDATION_MATRIX.md`
- Public-safe derivation: `docs/PUBLIC_DOCUMENTATION.md`
