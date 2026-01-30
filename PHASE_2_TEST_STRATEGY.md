# Phase 2 CLI Test Strategy

**Status**: ✅ VERIFIED  
**Date**: 2026-01-29  
**Test Results**: 20/20 passing (100%)

---

## Executive Summary

This document explains the testing approach used for Hexarch CLI v0.3.0 (Admin CLI), specifically addressing the transition from a stubbed test environment to a real CLI operating against live infrastructure.

### Key Problem Solved

The CLI evolved from a design into an operational tool that:
- Makes real HTTP API calls
- Returns meaningful error codes
- Logs all operations
- Handles network failures gracefully

Tests had to evolve similarly. They changed from:
- **❌ Old approach**: Assume mocked API works, accept any exit code
- **✅ New approach**: Mock API properly, assert exact behavior

---

## Testing Philosophy

### Design Principles

1. **Tests mock infrastructure, not behavior**
   - Mock the API client (infrastructure)
   - Don't mock the formatter (business logic)
   - The CLI should work exactly the same with real vs mocked API

2. **Tests verify realistic failure scenarios**
   - API error → exit code 1, error message
   - Missing file → exit code 2 (Click's default)
   - No policies → success with "no policies" message

3. **Tests are independent of backend running state**
   - No tests require `http://localhost:8080` to be running
   - All external dependencies are mocked
   - Tests pass in CI/CD environments

### Test Isolation

Each test:
- Creates its own mock API client
- Patches `HexarchAPIClient` and `ConfigManager` 
- Uses the CliRunner's `isolated_filesystem()` for file operations
- Cleans up after itself automatically

---

## Implementation: How We Test Policy Commands

### Setup: Fixtures

```python
@pytest.fixture
def cli_runner():
    """Get Click CLI test runner."""
    return CliRunner()

@pytest.fixture
def mock_api_client():
    """Mock API client that doesn't hit network."""
    client = Mock()
    client.list_policies.return_value = []
    client.get_policy.return_value = {...}
    return client

@pytest.fixture
def test_config():
    """Configuration for test environment."""
    return HexarchConfig(
        api=APIConfig(url="http://localhost:8080", token="test-token"),
        output=OutputConfig(format="table", colors=False),
        audit=AuditConfig(log_file=None),
        policy=PolicyConfig(cache_ttl=3600)
    )
```

### Test Pattern: Policy List with Success

```python
def test_policy_list_with_policies(self, cli_runner, mock_api_client, test_config):
    """Test policy list with policies."""
    
    # Arrange: Set up mock return value
    mock_api_client.list_policies.return_value = [
        {"name": "ai_governance", "status": "active", ...},
        {"name": "entitlements", "status": "active", ...}
    ]
    
    # Act: Patch infrastructure and invoke CLI
    with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
        with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
            mock_cm_instance = Mock()
            mock_cm_instance.get_config.return_value = test_config
            mock_cm.return_value = mock_cm_instance
            
            result = cli_runner.invoke(cli, ["policy", "list"])
    
    # Assert: Verify behavior
    assert result.exit_code == 0
    assert "ai_governance" in result.output
    assert "entitlements" in result.output
```

### Test Pattern: API Error

```python
def test_policy_list_api_error(self, cli_runner, mock_api_client, test_config):
    """Test policy list with API error."""
    
    # Arrange: Simulate API failure
    mock_api_client.list_policies.side_effect = Exception("Connection refused")
    
    # Act: Invoke CLI with error condition
    with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
        with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
            mock_cm.return_value.get_config.return_value = test_config
            result = cli_runner.invoke(cli, ["policy", "list"])
    
    # Assert: Verify graceful failure
    assert result.exit_code == 1  # Runtime error
    assert "Failed to fetch policies" in result.output
```

### Test Pattern: Argument Error

```python
def test_policy_validate_missing_file(self, cli_runner):
    """Test validating a missing file."""
    result = cli_runner.invoke(cli, ["policy", "validate", "nonexistent.rego"])
    
    # Click exits with 2 for argument errors
    assert result.exit_code == 2
```

### Test Pattern: File Operations (Isolated Filesystem)

```python
def test_policy_validate_valid(self, cli_runner):
    """Test validating a valid policy."""
    with cli_runner.isolated_filesystem():
        # Create a valid policy file in temp directory
        with open("test.rego", "w") as f:
            f.write("package test\n\nallow :- true")
        
        result = cli_runner.invoke(cli, ["policy", "validate", "test.rego"])
        
        # Should validate successfully
        assert result.exit_code == 0
        assert "valid" in result.output.lower()
```

---

## Exit Code Semantics

| Exit Code | Meaning | Example |
|-----------|---------|---------|
| 0 | Success | `hexarch-ctl policy list` returns policies |
| 1 | Runtime error | API connection fails, validation fails |
| 2 | Usage/argument error | Missing required argument, file not found (Click's default) |

---

## What Gets Mocked vs. What Doesn't

### ✅ We MOCK:

- `HexarchAPIClient` - No network calls
- `ConfigManager` - No filesystem lookups
- `AuditLogger` - No file writes

### ❌ We DON'T mock:

- `OutputFormatter` - Tests verify actual formatting
- `click` framework - Tests interact with real Click behavior
- `HexarchContext` - Tests verify real context passing
- File I/O in `validate` command - Tests use `isolated_filesystem()`

### Rationale

We mock infrastructure (API, config, logging) but test the actual CLI behavior. This ensures:
- If formatting breaks, tests fail ✓
- If Click integration breaks, tests fail ✓
- If context passing breaks, tests fail ✓
- But we don't depend on external services ✓

---

## Test Coverage

### Policy Commands (13 tests)

#### `policy list` (4 tests)
- ✅ No policies → success message
- ✅ With policies → correct output
- ✅ API error → failure with message
- ✅ JSON format → correct formatting

#### `policy export` (3 tests)
- ✅ Single policy → exports content
- ✅ All policies → JSON format
- ✅ API error → graceful failure

#### `policy validate` (3 tests)
- ✅ Valid policy → success
- ✅ Invalid policy (no package) → failure
- ✅ Missing file → exit code 2

#### `policy diff` (1 test)
- ✅ Show current version → success

#### Integration (2 tests)
- ✅ Command group registered
- ✅ Help text displays correctly

### Framework Tests (7 tests)

- ✅ CLI version command
- ✅ CLI help command
- ✅ Config defaults
- ✅ Output formatter (JSON, CSV, table)
- ✅ Success message formatting

---

## Running the Tests

### Run all CLI tests
```bash
pytest tests/cli/ -v
```

### Run only policy command tests
```bash
pytest tests/cli/test_policy_commands.py -v
```

### Run single test
```bash
pytest tests/cli/test_policy_commands.py::TestPolicyList::test_policy_list_with_policies -xvs
```

### Run with coverage
```bash
pytest tests/cli/ --cov=hexarch_cli --cov-report=html
```

---

## Key Insights

### Problem 1: Context Passing

**Original issue**: `AttributeError: 'NoneType' object has no attribute 'formatter'`

**Root cause**: Click's root group initializes context, but wasn't being passed to subcommand groups.

**Solution**: Add guards at start of each command:
```python
if not click_ctx.obj:
    click.echo("Error: CLI context not initialized", err=True)
    sys.exit(1)

ctx: HexarchContext = click_ctx.obj
formatter = ctx.formatter  # Now guaranteed to work
```

### Problem 2: Test Expectations

**Original issue**: Tests failed with "Connection failed: http://localhost:8080"

**Root cause**: Tests assumed mocked API but CLI was making real calls. Tests were wrong, not the CLI.

**Solution**: Properly mock `HexarchAPIClient` in test setup so CLI never makes real HTTP calls.

### Problem 3: Exit Code Semantics

**Original issue**: Test expected exit code 1 for missing file, got 2

**Root cause**: Click's default behavior for argument errors is exit code 2

**Solution**: Accept Click's conventions. Don't override unless there's a reason.

---

## Best Practices Established

1. **Always mock external dependencies** but not your own code
2. **Use fixtures for reusable test setup**
3. **Patch at the import site** (`hexarch_cli.cli.HexarchAPIClient` not `hexarch_cli.api.HexarchAPIClient`)
4. **Use `isolated_filesystem()`** for file I/O tests
5. **Test error paths** - API failures, missing files, invalid input
6. **Assert output** - Not just exit codes, but what the user sees
7. **Test the happy path** - Normal operation with valid input

---

## Continuation

This test strategy applies to all future CLI commands:

### Phase 3: Decision Commands
- Mock `api_client.query_decisions()`
- Mock `api_client.get_decision_stats()`
- Test filtering and pagination

### Phase 4: Metrics & Config Commands
- Mock `api_client.get_metrics()`
- Mock `api_client.validate_config()`
- Test configuration file I/O

### Phase 5+: Additional Commands
- Follow the same mocking patterns
- Fixture reuse across test suites
- Maintain 100% test pass rate

---

## Summary

✅ **20/20 tests passing**
✅ **100% test pass rate**
✅ **0 flaky tests**
✅ **No external dependencies required**
✅ **Repeatable on any machine**

The CLI is now tested at a production standard. Tests can run in CI/CD, on developer machines, and in isolated environments without requiring any running backend services.

**Phase 2 is complete and verified.**
