# Hexarch Guardrails — Public Technical Overview

## What is implemented today

Hexarch Guardrails provides a Python SDK and a FastAPI service for policy-driven request authorization and governance workflows.

Implemented capabilities include:
- Policy evaluation endpoint that returns ALLOW/DENY outcomes
- Rules/policies/entitlements/decisions APIs for governance state management
- Audit logging for decision and mutation events
- Hash-linked audit records with verification support
- Optional signed audit checkpoints (when signing key is configured)
- API key issuance/revocation with scope-based enforcement
- Built-in request metadata controls (request IDs, security headers)
- Built-in rate limiting

## Reliability and control model

The service uses explicit failure behavior rather than silent passes:
- Authentication is required by default
- Requests without applicable policy coverage are denied by default (except controlled bootstrap mode)
- Denials and evaluation outcomes are recorded in audit logs

This design supports explainable enforcement outcomes and reproducible audit review.

## Integration flexibility

Hexarch can be used in two ways:
- Embedded in Python applications via the `Guardian` SDK decorators
- Exposed as a standalone API service via `hexarch-ctl serve api`

The platform supports SQLite for local workflows and PostgreSQL for production-oriented deployments.

## Security posture (public-safe summary)

Implemented controls in the service include:
- Bearer-token protection enabled by default
- Scope checks for API key identities (`read` / `write` / `admin`)
- API key values stored as hashes (not plain text)
- Security-focused response headers via middleware
- Optional CORS allowlisting

## Important implementation-qualified notes

To keep this public overview precise:
- Rate limiting is implemented in-process (per service instance), not as a distributed global limiter.
- Audit integrity is application-level hash chaining and verification; it is not represented here as an external immutable ledger service.
- Documentation/OpenAPI endpoints are disabled by default and can be enabled explicitly.
- High availability and scale characteristics depend on runtime deployment topology.

## What this means for teams

For engineering teams, the implemented value proposition is:
- A concrete authorization and policy-evaluation control plane
- Auditable decision trails with integrity checks
- Practical integration paths for local development and service-based deployment
- Configurable hardening defaults for auth and operational guardrails

This overview intentionally excludes internal operational mechanics and sensitive implementation details while preserving verifiable technical accuracy.
