# v0.4.0 Release Summary

**What's New**: Database persistence, 5 ORM models, database-backed CLI, entitlement lifecycle management.

## What You Get

- SQLite (default) or PostgreSQL support
- 5 SQLAlchemy models: Decision, Policy, Rule, Entitlement, AuditLog
- CLI commands for database CRUD operations
- Migration management (`db upgrade`, `db downgrade`, `db current`, `db history`)
- Complete audit trails with soft deletes and versioning
- 30/30 tests passing

## Getting Started

```bash
pip install hexarch-guardrails==0.4.0
hexarch-ctl db upgrade head
```

## Upgrading from v0.3.1

1. Update: `pip install --upgrade hexarch-guardrails`
2. Initialize: `hexarch-ctl db upgrade head`
3. All v0.3.1 commands remain unchanged

## Dependencies Added

- `sqlalchemy>=2.0.0`
- `alembic>=1.13.0`
- `psycopg2-binary>=2.9.0` (optional, PostgreSQL only)

**Release Date**: 2026-01-29 | **Python**: >=3.8 | **License**: MIT
