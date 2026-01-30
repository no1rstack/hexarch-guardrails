# Changelog

All notable changes to hexarch-guardrails are documented in this file.

## [0.4.0] - 2026-01-29

### Overview

v0.4.0 introduces persistent storage, entitlement lifecycle management, and database-backed CLI operations. This release shifts hexarch-guardrails from a stateless evaluation library to a full-featured policy and decision management system with audit trails.

### Added

#### Database Persistence Layer
- SQLAlchemy ORM models for Decision, Policy, Rule, Entitlement, and AuditLog
- SQLite (default) and PostgreSQL support
- Alembic migrations for schema versioning
- Soft deletes and version tracking on all entities
- Complete audit trail with actor tracking and change history

#### Database Models
- **Rule**: Composable conditions, permissions, and constraints with priority-based evaluation
- **Policy**: Scoped (GLOBAL, ORGANIZATION, TEAM, USER, RESOURCE) policy bundles with failure modes
- **Entitlement**: User/entity grants with lifecycle management (ACTIVE, PENDING, SUSPENDED, REVOKED, EXPIRED)
- **Decision**: Authorization decisions with state machine (PENDING → APPROVED → ACTIVE)
- **AuditLog**: Complete audit trail with change tracking and actor history

#### CLI Commands
- `hexarch-ctl db upgrade [revision]`: Apply database migrations
- `hexarch-ctl db downgrade [revision]`: Revert migrations
- `hexarch-ctl db current`: Show current migration version
- `hexarch-ctl db history`: View migration history
- `hexarch-ctl rule create`: Create rules from JSON/YAML
- `hexarch-ctl rule list`: List all rules
- `hexarch-ctl rule get [id]`: Retrieve specific rule
- `hexarch-ctl rule delete [id]`: Soft or hard delete rules
- `hexarch-ctl policy db-list`: List policies from database
- `hexarch-ctl policy db-create`: Create policy with configuration
- `hexarch-ctl policy db-get [id]`: Retrieve specific policy
- `hexarch-ctl policy db-delete [id]`: Delete policy
- `hexarch-ctl entitlement db-list`: List entitlements
- `hexarch-ctl entitlement db-create`: Create entitlement
- `hexarch-ctl entitlement db-get [id]`: Retrieve entitlement
- `hexarch-ctl entitlement db-delete [id]`: Delete entitlement
- `hexarch-ctl decision db-list`: List decisions
- `hexarch-ctl decision db-create`: Create decision
- `hexarch-ctl decision db-get [id]`: Retrieve decision
- `hexarch-ctl decision db-delete [id]`: Delete decision

#### Rules Engine Enhancements
- JSON/YAML rule definition format
- 15+ operators: equals, not_equals, in, not_in, contains, gt, gte, lt, lte, between, regex, exists, starts_with, ends_with
- Composite rules with AND/OR/NOT operators
- Priority-based rule ordering
- Evaluation tracing for debugging

#### Configuration
- Database connection via `DATABASE_URL` environment variable
- Provider selection: `DATABASE_PROVIDER` (sqlite/postgresql)
- Pool and connection tuning options
- SQL debug logging via `SQL_ECHO`

### Changed

- Policy model now supports multiple scopes and failure modes
- Entitlement status now includes SUSPENDED state for temporary revocation
- CLI config commands now prompt for database configuration

### Fixed

- Duplicate index definitions in migration schema
- Self-referencing Rule relationship syntax
- Color formatting for concatenated ANSI codes
- Entitlement granted_by field now nullable for system-granted entitlements

### Dependencies Added

- `sqlalchemy>=2.0.0` - ORM and database abstraction
- `alembic>=1.13.0` - Database migration tool
- `psycopg2-binary>=2.9.0` - PostgreSQL adapter (optional for PostgreSQL support)

### Database

- Initial migration: `001_initial_schema` creates all core tables with indexes
- Supports SQLite (file-based, no setup required) and PostgreSQL (client-server)
- Forward and backward migration support via Alembic

### Testing

- Added 14 database model tests (test_models.py)
- All 16 rules engine tests passing
- 30/30 database and rules tests passing (100% pass rate for v0.4.0 functionality)

### Migration Guide

For users upgrading from v0.3.1:

1. Update to v0.4.0: `pip install hexarch-guardrails==0.4.0`
2. Initialize database: `hexarch-ctl db upgrade head`
3. (Optional) Migrate existing policies to database via CLI commands
4. Existing v0.3.1 commands (policy list, decision query) remain unchanged

### Known Limitations

- PostgreSQL support requires `psycopg2-binary` installation
- Initial migration creates new database; existing JSON policies must be manually imported
- Decision approval workflow is enforced in models but not yet in REST API

## [0.3.1] - 2025-12-15

### Added
- Policy comparison and diffing
- CSV export for decisions
- Metrics trends analysis

### Fixed
- OPA client connection pooling
- Policy validation error messages

## [0.3.0] - 2025-11-30

### Added
- Initial CLI framework
- Policy file validation
- Decision query API
- Guardian decorator for function-level protection

[0.4.0]: https://github.com/no1rstack/hexarch-guardrails/releases/tag/v0.4.0
[0.3.1]: https://github.com/no1rstack/hexarch-guardrails/releases/tag/v0.3.1
[0.3.0]: https://github.com/no1rstack/hexarch-guardrails/releases/tag/v0.3.0
