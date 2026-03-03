# Hexarch Guardrails — Technical Source Documentation (Implementation-Bound)

## Scope and Method

This document is constrained to verifiable implementation in this repository.

Validation basis used:
- Runtime/server code in `hexarch_cli.server.*`
- SDK code in `hexarch_guardrails.*`
- Data models in `hexarch_cli.models.*`
- CLI wiring in `hexarch_cli.cli` and `hexarch_cli.commands.*`
- Dependency manifest in `pyproject.toml`
- Tests executed locally:
  - `pytest tests/test_server_authorize.py tests/test_rules_engine.py tests/test_guardian.py -q`
  - Result: 29 passed

Claims in this document are either:
- **Verified**: directly visible in code/tests
- **Qualified**: implementation exists but has explicit limitations
- **Not verified**: intentionally excluded from capability statements

---

## 1) Implemented Architecture (Verified)

### 1.1 Components

- **Python SDK layer** (`hexarch_guardrails`)
  - `Guardian` decorator/programmatic guard surface
  - YAML policy loading + validation
  - OPA REST client calls
- **Admin/ops CLI layer** (`hexarch_cli`)
  - `hexarch-ctl` command root
  - Server launch command (`hexarch-ctl serve api`)
  - Policy/rule/decision/entitlement/admin command groups
- **REST API server layer** (`hexarch_cli.server.app`)
  - FastAPI app with resource endpoints and authorization endpoint
  - Middleware: request IDs, security headers, in-memory rate limiting
- **Persistence layer**
  - SQLAlchemy ORM models
  - SQLite and PostgreSQL connection support in `hexarch_cli.db`
- **Policy execution layer**
  - Rule DSL parser/evaluator in `hexarch_cli.rules_engine`
  - Policy-to-rule orchestration in model logic (`Policy.evaluate`)

### 1.2 Request/Decision Flow (Server)

Observed in `hexarch_cli.server.app` + `hexarch_cli.server.enforcement`:
1. HTTP request enters middleware stack.
2. Authentication is enforced (unless explicitly disabled by config).
3. API key scope checks run for API-key identities.
4. Applicable policies are selected (global/scope-based match).
5. Rules are evaluated; deny/allow result is produced.
6. Evaluation and many mutating actions are audit-logged.
7. API response returned with standardized status handling.

---

## 2) Capability Inventory

## 2.1 SDK: Local Guarding + OPA-backed Decisions (Verified)

Implemented behavior:
- Decorator-style guard application (`Guardian.check`)
- Programmatic guard wrapping (`Guardian.guard_function`)
- Policy listing/get by ID
- Policy file discovery and YAML validation
- OPA health check at client init
- OPA decision request to `/v1/data/guardrails/evaluate`

Key constraints:
- SDK policy decision semantics depend on external OPA response format.
- `Guardian.enforce` constructor argument is present but not used to branch behavior in `Guardian.check`.

## 2.2 REST API: Policy Governance Endpoints (Verified)

Implemented endpoints (observed in app router):
- Public utility/health: `/`, `/health`, `/echo`, `robots.txt`, `sitemap.xml`
- Policy simulation: `POST /authorize`
- CRUD-style list/create/get operations for:
  - `/rules`
  - `/policies`
  - `/entitlements`
  - `/decisions`
- Audit retrieval and verification:
  - `/audit-logs`
  - `/audit-logs/verify`
  - `/audit-logs/checkpoint`
  - persisted checkpoint endpoints under `/audit-checkpoints`
- Provider call event ingestion/listing:
  - `POST /events/provider-calls`
  - `GET /events/provider-calls`
- API key admin endpoints (feature-gated):
  - `/api-keys`
  - `/api-keys/{id}/revoke`

## 2.3 Policy Evaluation DSL (Verified)

`RuleEvaluator` supports:
- Combinators: `all`, `any`, `not`
- Wrappers: `allow`, `deny`
- Field operators: `equals`, `not_equals`, `in`, `not_in`, `contains`, `not_contains`, `gt`, `gte`, `lt`, `lte`, `starts_with`, `ends_with`, `regex`, `between`, `exists`
- Dotted path extraction with list indexing (e.g., `user.roles[0]`)

## 2.4 Audit Integrity Mechanism (Verified, Qualified)

Implemented:
- Audit entries contain canonical payload, `prev_hash`, and `entry_hash` (SHA-256)
- Chain verification endpoint checks hash continuity and payload digest
- Optional signed checkpoints using HMAC SHA-256 when key env vars are configured

Qualification:
- This is an application-level tamper-evident chain, not an external immutable ledger.

## 2.5 Authentication and Authorization (Verified, Qualified)

Implemented:
- Bearer token required by default
- Static token path via env-configured server token
- DB-backed API key support (hashed storage, revocation, last-used update)
- Scope enforcement (`read`, `write`, `admin`) for API key identities

Qualification:
- Identity model currently relies on normalized headers + token paths in enforcement module.
- No first-party OAuth/JWT issuer verification module is present in this repo.

## 2.6 Rate Limiting and Security Headers (Verified, Qualified)

Implemented:
- In-memory sliding-window limiter in middleware
- Security headers middleware sets browser hardening headers
- Request ID propagation middleware

Qualification:
- Rate limiter is single-process memory based; not distributed/shared across replicas.
- Effective limits are process-local.

## 2.7 Storage/Database (Verified)

Implemented:
- SQLAlchemy ORM models and session manager
- SQLite default and PostgreSQL configuration paths
- Init/create-all and drop-all DB lifecycle methods

Qualification:
- Concrete HA/replication behavior depends on external DB deployment and is not implemented in app code.

---

## 3) Operational Constraints and Failure Modes (Verified)

- If auth is required and no server token configured, protected access returns 503 (`Server auth not configured`).
- API key admin endpoints are hidden unless explicitly enabled.
- With no applicable policies, requests are denied unless bootstrap allow mode is active for limited setup paths.
- Rate limiting can be disabled by configuration; when enabled, limiter acts per process instance.
- OPA availability is required for SDK paths that call OPA client methods.

---

## 4) Test-Backed Evidence Summary

Executed test modules verify:
- Auth enforcement and denial paths
- Bootstrap policy creation behavior
- `/authorize` decision behavior
- Audit log chain fields and verification endpoint behavior
- API key issuance and revocation constraints
- API key scope denial logging
- Rule evaluation operators and composition
- Guardian/OPA client integration behavior under mocked OPA responses

Executed command result:
- `29 passed` for focused suite listed in Scope and Method.

---

## 5) Items Explicitly Not Claimed

The following are not asserted as implemented capabilities in this technical source because they are not directly proven in this repository alone:
- Multi-region/high-availability guarantees
- Distributed/global rate limiting
- Formal compliance certification status
- Deterministic latency/throughput SLO guarantees
- End-to-end zero-downtime migration guarantees

---

## 6) Evidence Pointers (Code Locations)

Primary files used for verification:
- `hexarch_guardrails/guardian.py`
- `hexarch_guardrails/opa_client.py`
- `hexarch_guardrails/policy_loader.py`
- `hexarch_cli/server/app.py`
- `hexarch_cli/server/enforcement.py`
- `hexarch_cli/server/security.py`
- `hexarch_cli/server/middleware.py`
- `hexarch_cli/rules_engine.py`
- `hexarch_cli/models/audit.py`
- `hexarch_cli/models/policy.py`
- `hexarch_cli/models/rule.py`
- `hexarch_cli/models/api_key.py`
- `hexarch_cli/db.py`
- `tests/test_server_authorize.py`
- `tests/test_rules_engine.py`
- `tests/test_guardian.py`
- `tests/test_opa_client.py`
- `pyproject.toml`
