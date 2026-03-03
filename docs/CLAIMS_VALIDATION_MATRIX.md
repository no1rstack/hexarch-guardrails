# Claims Validation Matrix

Purpose: map externally consumable claims to observable implementation evidence.

Legend:
- Verified: directly supported by code/tests in this repo
- Qualified: supported with specific limitations
- Rejected: not supportable as written

| Claim Candidate | Status | Evidence Basis | Qualification / Required Wording |
|---|---|---|---|
| Policy-based authorization decisions are exposed via API | Verified | `hexarch_cli/server/app.py` (`POST /authorize`), `hexarch_cli/server/enforcement.py` | Describe as ALLOW/DENY evaluation endpoint |
| Rules and policies are persisted and queryable | Verified | `hexarch_cli/models/*`, server CRUD routes | Keep language at API-level CRUD capability |
| Audit events are tamper-evident | Qualified | `hexarch_cli/models/audit.py` hash-chain fields + verify logic | Say application-level hash chain; avoid implying external immutable ledger |
| Checkpoints can be signed | Qualified | `AuditService.sign_checkpoint` with HMAC env key | Mark as optional and key-config dependent |
| API key lifecycle controls exist (issue/revoke/scope) | Verified | `hexarch_cli/models/api_key.py`, `/api-keys` routes, `enforcement.py` scope checks | Note admin endpoints are feature-gated |
| Security headers are automatically added | Verified | `hexarch_cli/server/middleware.py` | Applies to server responses via middleware |
| Rate limiting is built in | Qualified | `SlidingWindowRateLimiter` + middleware | Clarify in-memory, single-process, per-instance |
| SDK supports decorator guardrails | Verified | `hexarch_guardrails/guardian.py` | Requires policy config and OPA connectivity for OPA-backed checks |
| Works with SQLite and PostgreSQL | Verified | `hexarch_cli/db.py` URL/provider handling | Production characteristics depend on deployment topology |
| OpenAPI/docs are available | Qualified | `is_docs_enabled()` + FastAPI docs toggles | Disabled by default; enabled by explicit config |
| Enterprise-grade distributed enforcement | Rejected | No distributed coordination module observed | Do not claim |
| Guaranteed high availability/fault tolerance | Rejected | Repo has no HA orchestrator logic guarantees | Phrase as deployment-dependent |
| Compliance certification achieved | Rejected | No cert artifacts or attestation implementation in repo | Do not claim certification |
| Zero performance overhead | Rejected | No benchmarked zero-overhead proof in repo | Do not claim |
