# Release Notes: hexarch-guardrails 0.3.0

**Release Date**: January 29, 2026  
**Status**: ✅ Ready for Production

---

## Overview

Version 0.3.0 introduces comprehensive CLI functionality for managing Hexarch guardrails, including decision query/export capabilities, provider metrics analysis, and configuration management. This release includes critical audit trail improvements and removes unsupported features.

---

## New Features

### Decision Commands (Phase 3)
Complete decision log management with three new commands:

- **`hexarch-ctl decision query`** - Query recent decisions with filtering
  - Filter by date range (`--from`, `--to`)
  - Filter by provider, user ID, or decision (ALLOW/DENY)
  - Support for JSON, table, and CSV output formats
  - Configurable result limits (1-1000)

- **`hexarch-ctl decision export`** - Export decision history (NEW: unlimited pagination)
  - Export to JSON or CSV formats
  - Filter by date range and multiple criteria
  - **Full dataset support**: No longer capped at 1,000 records
  - Automatic pagination through all available data
  - Output to file or stdout

- **`hexarch-ctl decision stats`** - Analyze decision statistics
  - Filter by date range
  - Group by provider, decision, user, or hourly buckets
  - JSON output with aggregated statistics

### Metrics Commands (Phase 4)
Provider performance monitoring with three commands:

- **`hexarch-ctl metrics show`** - Display provider metrics
  - Real-time metrics for all configured providers
  - Table, JSON, or CSV output formats
  - Time-window filtering (1h, 6h, 1d, 7d, 30d)

- **`hexarch-ctl metrics export`** - Export metrics for analysis
  - Export to JSON or CSV formats
  - File output with directory creation
  - Filter by time window

- **`hexarch-ctl metrics trends`** - Analyze provider trends
  - Show performance trends over time
  - Configurable time window and grouping
  - JSON output with trend analysis

### Config Commands (Phase 4/5)
Configuration management with three commands:

- **`hexarch-ctl config init`** - Interactive configuration setup
  - Create or update config file
  - Prompt for API URL, token, audit settings
  - Store in user's home directory

- **`hexarch-ctl config set`** - Update individual config values
  - Change any configuration parameter
  - Preserve other settings
  - Immediate validation

- **`hexarch-ctl config validate`** - Test configuration
  - Verify API connectivity
  - Validate token and permissions
  - Check configuration file syntax

### Full Command Structure
```
hexarch-ctl
├── policy          [list, export, validate, diff]
├── decision        [query, export, stats]
├── metrics         [show, export, trends]
├── config          [init, set, validate]
└── health          [health check]
```

---

## Bug Fixes

### Audit Logging Gap Fixed
**Issue**: Commands returned early without logging when no data was found, breaking audit trails.

**Fix**: Added `ctx.audit_logger.log_command()` calls before all early returns in:
- `decision query` - Logs "No matching data" when zero results
- `decision export` - Logs "No matching data" when zero results
- `decision stats` - Logs "No matching data" when stats unavailable

**Impact**: Complete audit accountability for every command invocation, including zero-result queries.

### Export Pagination Implemented
**Issue**: `decision export` was hard-capped at 1,000 records with no pagination mechanism.

**Fix**: Implemented pagination loop that:
- Fetches up to 1,000 records per API call
- Automatically follows pagination offsets
- Stops when fewer than 1,000 results are received
- Supports arbitrary dataset sizes

**Impact**: Users can now export complete decision history, not just first page.

### Unsupported Parquet Format Removed
**Issue**: `--format parquet` was advertised but never worked. Always failed with "requires pyarrow dependency" error.

**Fix**: 
- Removed `parquet` from supported format options
- Removed unreachable error handling code
- Now only `json` and `csv` formats are available

**Impact**: No misleading options. CLI only exposes fully implemented features.

---

## Technical Improvements

### Version Alignment
- CLI version: 0.3.0
- SDK version: 0.3.0
- Package version: 0.3.0
- All aligned for consistent distribution

### Dependency Updates
Added CLI-specific dependencies:
- `click>=8.1.0` - CLI framework
- `pydantic>=2.0` - Configuration validation
- `tabulate>=0.9.0` - Table formatting
- `colorama>=0.4.6` - Colored output
- `python-dotenv>=0.21.0` - Environment variables

### Entry Point Configuration
- Console script: `hexarch-ctl` (available after install)
- Supports global command invocation: `$ hexarch-ctl --help`
- Configured in both `setup.py` and `pyproject.toml`

### Development Status
- Upgraded from "3 - Alpha" to "4 - Beta"
- Production-ready code with comprehensive testing
- 81 passing tests (100% pass rate, 1.51s execution)

---

## Testing & Quality Assurance

### Test Coverage
```
✅ CLI Framework Tests         7 tests
✅ Policy Commands Tests      13 tests
✅ Decision Commands Tests    27 tests (including audit & pagination)
✅ Metrics Commands Tests     27 tests
✅ Config Commands Tests       7 tests
─────────────────────────────────────
   Total Tests Passing      81/81 (100%)
   Execution Time          1.51 seconds
```

### Distribution Artifacts
- Wheel: `hexarch_guardrails-0.3.0-py3-none-any.whl` (33 KB)
- Source: `hexarch_guardrails-0.3.0.tar.gz` (31 KB)
- Both verified with test installation in clean virtual environment

### Smoke Tests Passed
- ✅ `hexarch-ctl --version` → "version 0.3.0"
- ✅ `hexarch-ctl --help` → All 5 command groups listed
- ✅ `hexarch-ctl decision --help` → All 3 subcommands available
- ✅ `hexarch-ctl metrics --help` → All 3 subcommands available
- ✅ `hexarch-ctl config --help` → All 3 subcommands available
- ✅ `hexarch-ctl policy --help` → All 4 subcommands available

---

## Breaking Changes

⚠️ **None** - This release is fully backward compatible.

- Existing SDK code unaffected
- Policy commands unchanged
- Health check unchanged
- All APIs remain stable

---

## Migration Notes

### If upgrading from 0.1.0 or 0.2.0

No migration needed. All existing functionality continues to work:
```bash
# Existing code continues to work unchanged
from hexarch_guardrails import Guardian

guardian = Guardian(policy_loader)
result = guardian.evaluate(entitlement)
```

### If using parquet export
The `--format parquet` option has been removed. Use `--format json` or `--format csv` instead:

**Before** (no longer works):
```bash
hexarch-ctl decision export --format parquet -o decisions.parquet
```

**After** (use JSON instead):
```bash
hexarch-ctl decision export --format json -o decisions.json
```

---

## Installation

### From PyPI (when published)
```bash
pip install hexarch-guardrails==0.3.0
hexarch-ctl --version
```

### From Local Distribution
```bash
pip install dist/hexarch_guardrails-0.3.0-py3-none-any.whl
hexarch-ctl --version
```

### From Source
```bash
pip install hexarch_guardrails-0.3.0.tar.gz
hexarch-ctl --version
```

### Requirements
- Python 3.8+ (tested on 3.8, 3.9, 3.10, 3.11, 3.12)
- pip for dependency management
- Active API server connection (for decision/metrics/policy commands)

---

## Known Limitations

1. **Parquet Export Not Available** - Use JSON or CSV formats instead
2. **API Dependency** - Decision, metrics, and policy commands require active backend API
3. **Config Storage** - Configuration stored in user's home directory (`~/.hexarch/config.yaml`)
4. **Authentication** - Requires valid API token for authenticated endpoints
5. **Pagination Offset-Based** - Uses offset-based pagination (not cursor-based)

---

## Deprecations

None in this release.

---

## Future Roadmap

Potential enhancements for 0.4.0+:
- [ ] Parquet export support (with pyarrow optional dependency)
- [ ] Progress bars for large exports
- [ ] Batch audit logging for large datasets
- [ ] Cursor-based pagination support
- [ ] Configuration profiles (dev, staging, prod)
- [ ] Output templating for custom formats
- [ ] Shell completion scripts (bash, zsh, fish)

---

## Security Notes

- Store API tokens securely in environment variables or config file
- Config files contain sensitive credentials - restrict file permissions
- Audit logs contain decision details - review retention policies
- Use HTTPS for all API connections

---

## Support & Documentation

- **Getting Started**: See `REFACTORING_QUICK_START.md`
- **API Reference**: See `API_REFERENCE.md`
- **Architecture**: See `TECHNICAL_ARCHITECTURE.md`
- **Audit Report**: See `AUDIT_FINDINGS_FIXES.md`

---

## Contributors

This release represents Phase 3-5 of the Hexarch CLI implementation, including:
- Decision command suite (Phase 3)
- Metrics command suite (Phase 4)
- Configuration management (Phase 4/5)
- Audit logging improvements
- Pagination support
- Distribution packaging

---

## Checksums

Verify download integrity:
```
hexarch_guardrails-0.3.0-py3-none-any.whl
  Size: 33098 bytes
  Date: 2026-01-29 07:38 UTC

hexarch_guardrails-0.3.0.tar.gz
  Size: 31539 bytes
  Date: 2026-01-29 07:38 UTC
```

---

## Questions?

For issues, feedback, or feature requests, please file an issue in the repository.

**Status**: ✅ Production Ready | **Version**: 0.3.0 | **Release Date**: January 29, 2026
