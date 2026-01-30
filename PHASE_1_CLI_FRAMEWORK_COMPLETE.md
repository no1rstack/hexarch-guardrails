# Hexarch Admin CLI (hexarch-ctl) - Phase 1 Complete

**Status**: ✅ Framework Complete (2026-01-29)  
**Version**: 0.3.0  
**Phase**: 1 - Core Framework  

---

## 📋 Phase 1 Summary

### What Was Built

**Core Framework Components** (9 modules, ~2000 LOC):

1. **CLI Entry Point** (`cli.py`)
   - Root Click group with global flags
   - Context management for all commands
   - Version display, help system
   - Command: `hexarch-ctl health` (verify API connectivity)

2. **Configuration System** (`config/`)
   - `schemas.py`: Pydantic models for validation
     - APIConfig (URL, token, timeout, SSL)
     - OutputConfig (format, colors, page size)
     - AuditConfig (logging, rotation)
     - PolicyConfig (caching, validation)
   - `config.py`: ConfigManager for loading configs
     - File-based (YAML)
     - Environment variables
     - CLI flag overrides
     - Directory initialization

3. **Output Formatting** (`output/`)
   - `colors.py`: ColorScheme for terminal output
     - ANSI color codes
     - Semantic colors (success, error, warning)
     - Colored message helpers
   - `formatter.py`: OutputFormatter for multiple formats
     - JSON output
     - CSV output (spreadsheet-friendly)
     - Table output (human-readable)
     - Message printing (success, error, warning, info)

4. **API Client** (`api/`)
   - `auth.py`: AuthManager for bearer token handling
   - `client.py`: HexarchAPIClient with methods
     - list_policies()
     - get_policy(name)
     - export_decisions(...filters...)
     - get_metrics(...filters...)
     - health_check()

5. **Audit Logging** (`logging/`)
   - `audit.py`: AuditLogger with rotating file handler
   - Logs to ~/.hexarch/cli.log
   - 100MB max file size, keeps 10 backups
   - Tracks command execution, API calls, errors

6. **Testing Foundation** (`tests/cli/`)
   - Framework tests for CLI, config, formatting
   - Click test runner integration
   - Configuration validation tests
   - Output format verification

---

## 🏗️ Architecture

### Directory Structure

```
hexarch-guardrails-py/
├── hexarch_cli/                    # Main CLI package
│   ├── __init__.py                 # Entry point: __version__, cli()
│   ├── __main__.py                 # python -m hexarch_cli
│   ├── cli.py                      # Root Click CLI group
│   ├── config/                     # Configuration management
│   │   ├── __init__.py
│   │   ├── schemas.py              # Pydantic models (5 config classes)
│   │   └── config.py               # ConfigManager class
│   ├── output/                     # Output formatting
│   │   ├── __init__.py
│   │   ├── colors.py               # ColorScheme for ANSI colors
│   │   └── formatter.py            # OutputFormatter (JSON/CSV/Table)
│   ├── api/                        # API client
│   │   ├── __init__.py
│   │   ├── auth.py                 # AuthManager for bearers
│   │   └── client.py               # HexarchAPIClient
│   ├── logging/                    # Audit logging
│   │   ├── __init__.py
│   │   └── audit.py                # AuditLogger with rotation
│   └── commands/                   # Command implementations (Phase 2+)
│       └── __init__.py
└── tests/cli/
    ├── test_framework.py           # Framework tests
    └── ... (Phase 2+ command tests)
```

### Configuration Hierarchy

```
CLI Flags (highest priority)
    ↓
Environment Variables
    ↓
Config File (~/.hexarch/config.yml)
    ↓
Defaults (lowest priority)
```

### Data Flow

```
hexarch-ctl [flags]
    ↓
ConfigManager (load + validate)
    ↓
HexarchContext (config, api_client, formatter, audit_logger)
    ↓
Commands (use context to fetch data, format output, log)
    ↓
Output (table/json/csv) + Audit Log Entry
```

---

## 🚀 Quick Start

### Installation (Dev Mode)

```bash
cd hexarch-guardrails-py

# Install with CLI extras
pip install -e ".[cli]"

# Or install all (including dev)
pip install -e ".[cli,dev]"
```

### Initialize Configuration

```bash
# Interactive setup (creates ~/.hexarch/config.yml)
hexarch-ctl config init

# Or use environment variables
export HEXARCH_API_URL=https://api.hexarch.io
export HEXARCH_API_TOKEN=sk_test_...
```

### Test CLI is Working

```bash
# Check API connectivity
hexarch-ctl health

# Should output: ✓ API is healthy: http://localhost:8080
```

### Run Framework Tests

```bash
# Install pytest
pip install pytest pytest-cov

# Run tests
pytest tests/cli/test_framework.py -v

# Coverage report
pytest tests/cli/test_framework.py --cov=hexarch_cli
```

---

## 💡 Usage Examples

### Command-Line Flags

```bash
# Use custom API URL
hexarch-ctl --api-url https://prod.hexarch.io health

# Use custom config file
hexarch-ctl --config /etc/hexarch/prod.yml policy list

# Output as JSON
hexarch-ctl --format json policy list

# Verbose logging
hexarch-ctl --verbose policy list
```

### Configuration File

**~/.hexarch/config.yml:**
```yaml
version: "0.3"
api:
  url: "https://api.hexarch.io"
  token: "${HEXARCH_API_TOKEN}"  # Use env var for secrets
  timeout_seconds: 30
  verify_ssl: true
output:
  format: "table"
  colors: true
  page_size: 100
audit:
  enabled: true
  log_path: "~/.hexarch/cli.log"
  log_level: "info"
  max_size_mb: 100
  backup_count: 10
policies:
  cache_ttl_minutes: 5
  validation_strict: false
```

### Environment Variables

```bash
# API configuration
export HEXARCH_API_URL=https://api.hexarch.io
export HEXARCH_API_TOKEN=sk_test_xyz

# Output format
export HEXARCH_FORMAT=json

# Audit logging
export HEXARCH_AUDIT_LOG=/var/log/hexarch/cli.log
```

---

## 📦 Dependencies Added

**Core Framework** (required):
- `click>=8.1.0` - CLI framework
- `pydantic>=2.0` - Configuration validation
- `tabulate>=0.9.0` - Table formatting
- `colorama>=0.4.6` - Cross-platform colors

**Existing** (unchanged):
- `requests>=2.28.0` - HTTP client
- `pyyaml>=6.0` - YAML parsing
- `python-dotenv>=0.21.0` - .env support

**Dev** (for testing):
- `pytest>=7.0` - Testing framework

---

## 🔌 API Client Methods

All methods in `HexarchAPIClient` are ready for Phase 2 commands:

```python
# Policy operations
list_policies() -> List[Dict]
get_policy(name: str) -> Dict

# Decision operations
export_decisions(
    date_from=None,
    date_to=None,
    provider=None,
    user_id=None,
    decision=None,
    page=1,
    page_size=100
) -> Dict

# Metrics operations
get_metrics(
    date_from=None,
    date_to=None,
    time_window=None
) -> Dict

# Health check
health_check() -> bool
```

---

## 📝 Configuration Classes

All configuration is validated via Pydantic:

**APIConfig**:
- `url`: Backend API URL (default: http://localhost:8080)
- `token`: Bearer token
- `timeout_seconds`: Request timeout (default: 30)
- `verify_ssl`: SSL verification (default: True)

**OutputConfig**:
- `format`: json|table|csv (default: table)
- `colors`: Colored output (default: True)
- `page_size`: Records per page (default: 100)

**AuditConfig**:
- `enabled`: Enable logging (default: True)
- `log_path`: Log file path (default: ~/.hexarch/cli.log)
- `log_level`: debug|info|warn|error (default: info)
- `max_size_mb`: Max log file size (default: 100)
- `backup_count`: Backup files to keep (default: 10)

**PolicyConfig**:
- `cache_ttl_minutes`: Cache timeout (default: 5)
- `validation_strict`: Strict validation (default: False)

---

## 🧪 Test Coverage

**Current Framework Tests** (~200 lines):
- ✅ CLI version display
- ✅ CLI help text
- ✅ Config default values
- ✅ JSON output formatting
- ✅ CSV output formatting
- ✅ Table output formatting
- ✅ Success message printing

**Test Command**:
```bash
pytest tests/cli/test_framework.py -v
```

**Coverage Target for Full CLI**: 85%+

---

## 📋 Next Steps (Phase 2-5)

### Phase 2: Policy Commands (Days 3-4)
- [ ] `policy list` - List all policies
- [ ] `policy export` - Export single or all policies
- [ ] `policy validate` - Validate policy syntax
- [ ] `policy diff` - Compare policy versions

### Phase 3: Decision Commands (Days 5-6)
- [ ] `decision query` - Query with filters
- [ ] `decision export` - Export to CSV/JSON
- [ ] `decision stats` - Aggregated statistics

### Phase 4: Metrics & Config (Day 7)
- [ ] `metrics show` - Display provider metrics
- [ ] `metrics export` - Export metrics
- [ ] `config init` - Interactive setup
- [ ] `config set` - Update settings
- [ ] `config validate` - Verify configuration

### Phase 5: Testing & Release (Days 8-9)
- [ ] Integration tests for all commands
- [ ] Shell completion (bash, zsh)
- [ ] Man page generation
- [ ] Release notes
- [ ] Commit & tag v0.3.0-backend

---

## 🎯 Success Criteria for Phase 1

✅ **Framework**: Click-based CLI with context management  
✅ **Configuration**: Pydantic-validated config from file/env/flags  
✅ **Output**: JSON, CSV, table formatters with colors  
✅ **API Client**: Ready for policy, decision, metrics endpoints  
✅ **Audit Logging**: Rotating file logger to ~/.hexarch/cli.log  
✅ **Testing**: Framework tests with pytest  
✅ **Dependencies**: Added to pyproject.toml with CLI extras  
✅ **Docs**: README with quick start and architecture  

---

## 🔍 Code Quality

- **LOC**: ~2000 (framework only, no commands yet)
- **Modules**: 9 packages with clear separation of concerns
- **Type Hints**: Full type annotations throughout
- **Error Handling**: Graceful error messages with suggestions
- **Configuration**: Validated via Pydantic with defaults
- **Logging**: Audit trail to ~/.hexarch/cli.log
- **Testing**: pytest-ready with Click test runner

---

## 📞 Troubleshooting

### API Connection Issues

```bash
# Check connectivity
hexarch-ctl health

# Debug with verbose
hexarch-ctl --verbose health

# Test token
export HEXARCH_API_TOKEN=sk_test_xyz
hexarch-ctl --api-url https://api.hexarch.io health
```

### Configuration Issues

```bash
# Validate config
hexarch-ctl config validate

# Check config file
cat ~/.hexarch/config.yml

# Use environment variables instead
export HEXARCH_API_URL=https://api.hexarch.io
export HEXARCH_API_TOKEN=sk_test_xyz
```

### Output Format Issues

```bash
# Force JSON output
hexarch-ctl --format json health

# Disable colors
export HEXARCH_OUTPUT_COLORS=false
```

---

## 📄 Document References

- [ADMIN_CLI_DESIGN.md](../ADMIN_CLI_DESIGN.md) - Full design spec
- [README.md](../README.md) - Main project documentation
- Click Docs: https://click.palletsprojects.com/
- Pydantic Docs: https://docs.pydantic.dev/

---

**Phase 1 Completed**: 2026-01-29  
**Framework Ready**: Yes ✅  
**Ready for Phase 2**: Yes ✅  
**Estimated Phase 2 Start**: 2026-01-30 (Policy Commands)
