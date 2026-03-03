# Good First Issues for Hexarch Guardrails

Labels to use: `good first issue`, `documentation`, `enhancement`, `help wanted`

---

## 📚 Documentation Issues

### Issue #1: Add Examples for Flask Integration
**Labels**: `good first issue`, `documentation`, `examples`

**Description**:
Create a Flask integration example similar to our FastAPI and Django templates. Should include:
- Basic Flask app with protected routes
- `hexarch.yaml` policy configuration
- README with setup instructions
- Sample tests

**Files to create**:
- `templates/flask/README.md`
- `templates/flask/app.py`
- `templates/flask/hexarch.yaml`

**Resources**:
- See existing templates: `templates/fastapi/` and `templates/django/`
- Flask docs: https://flask.palletsprojects.com/

**Estimated time**: 2-3 hours

**Good for beginners** because: Clear structure to follow from existing templates, minimal Python complexity.

---

### Issue #2: Improve CLI Help Messages
**Labels**: `good first issue`, `documentation`, `cli`

**Description**:
Enhance the help text for `hexarch-ctl` commands to be more beginner-friendly. Currently some commands have minimal help text.

**Tasks**:
1. Add examples to command help (e.g., `hexarch-ctl policy list --help` should show example output)
2. Add "See also" references between related commands
3. Include common troubleshooting tips in command descriptions

**Files to edit**:
- `hexarch_cli/commands/policy.py`
- `hexarch_cli/commands/serve.py`

**Example improvement**:
```python
# Before
@click.command()
def list():
    """List all policies"""

# After
@click.command()
def list():
    """
    List all policies from connected OPA server.
    
    Examples:
        hexarch-ctl policy list
        hexarch-ctl policy list --format json
    
    See also: hexarch-ctl policy export
    """
```

**Estimated time**: 1-2 hours

**Good for beginners** because: Small, focused changes; no complex logic required.

---

### Issue #3: Add Type Hints to Public APIs
**Labels**: `good first issue`, `enhancement`, `type-safety`

**Description**:
Add type hints to the public Guardian API to improve IDE autocomplete and type checking.

**Files to edit**:
- `hexarch_guardrails/guardian.py` (main Guardian class)
- `hexarch_guardrails/policy_loader.py`

**Tasks**:
1. Add parameter and return type hints
2. Add docstring with types (Google style)
3. Ensure mypy passes with `--strict` flag

**Example**:
```python
# Before
def check(self, policy_id):
    """Check policy"""

# After
def check(self, policy_id: str) -> Callable:
    """
    Decorator to check policy before function execution.
    
    Args:
        policy_id: The ID of the policy to check
        
    Returns:
        Decorated function with policy enforcement
        
    Raises:
        PolicyViolationError: If policy check fails
    """
```

**Estimated time**: 2-3 hours

**Good for beginners** because: Straightforward task with clear acceptance criteria; learn best practices.

---

## 🧪 Testing Issues

### Issue #4: Add Integration Test for Django Template
**Labels**: `good first issue`, `testing`, `django`

**Description**:
Create automated tests for the Django integration template in `templates/django/`.

**Tasks**:
1. Create `templates/django/tests/` directory
2. Add tests for:
   - View decorator behavior
   - Celery task protection
   - Middleware functionality
3. Use pytest-django
4. Add CI workflow to run these tests

**Files to create**:
- `templates/django/tests/test_views.py`
- `templates/django/tests/test_decorators.py`
- `templates/django/tests/conftest.py`

**Resources**:
- pytest-django: https://pytest-django.readthedocs.io/
- See existing tests in `tests/` directory

**Estimated time**: 3-4 hours

**Good for beginners** because: Clear scope; existing test patterns to follow.

---

### Issue #5: Add Unit Tests for Rate Limiter Edge Cases
**Labels**: `good first issue`, `testing`, `bug-prevention`

**Description**:
Add tests for rate limiter edge cases that aren't currently covered:
1. Time boundary transitions (e.g., minute rollover)
2. Concurrent access from multiple threads
3. Large burst followed by sustained rate

**Files to edit**:
- `tests/test_rate_limiter.py` (create if doesn't exist)

**Existing tests to reference**:
- `tests/test_guardian.py`
- `tests/test_server_authorize.py`

**Estimated time**: 2-3 hours

**Good for beginners** because: Testing is isolated; provides hands-on experience with core functionality.

---

## 🔧 Enhancement Issues

### Issue #6: Add JSON Output Format to CLI Commands
**Labels**: `good first issue`, `enhancement`, `cli`

**Description**:
Add `--format json` flag to CLI commands that currently only output human-readable text.

**Commands to enhance**:
- `hexarch-ctl policy list`
- `hexarch-ctl serve status` (if implemented)

**Implementation guidance**:
```python
import click
import json

@click.command()
@click.option('--format', type=click.Choice(['text', 'json']), default='text')
def list(format):
    policies = get_policies()
    
    if format == 'json':
        click.echo(json.dumps(policies, indent=2))
    else:
        # Existing human-readable output
        for policy in policies:
            click.echo(f"- {policy['id']}")
```

**Files to edit**:
- `hexarch_cli/commands/policy.py`

**Estimated time**: 1-2 hours

**Good for beginners** because: Small, self-contained feature; clear specification.

---

### Issue #7: Add Retry Logic with Exponential Backoff
**Labels**: `good first issue`, `enhancement`, `reliability`

**Description**:
Add configurable retry logic for transient OPA connection failures.

**Current behavior**:
- OPA client fails immediately on connection error

**Desired behavior**:
- Retry up to 3 times with exponential backoff
- Configurable via `hexarch.yaml`:
  ```yaml
  opa:
    url: http://localhost:8181
    retry:
      max_attempts: 3
      backoff_factor: 2
  ```

**Files to edit**:
- `hexarch_guardrails/opa_client.py`
- `hexarch_guardrails/policy_loader.py` (to load retry config)

**Resources**:
- Python `tenacity` library for retry logic
- Or implement simple exponential backoff manually

**Estimated time**: 2-3 hours

**Good for beginners** because: Well-defined feature; opportunity to learn about reliability patterns.

---

## 🎨 Design Issues

### Issue #8: Design ASCII Art Banner for CLI
**Labels**: `good first issue`, `design`, `cli`, `fun`

**Description**:
Create an ASCII art banner that displays when running `hexarch-ctl` commands or starting the server.

**Requirements**:
- Should include "Hexarch Guardrails" or "HEXARCH" text
- Keep it compact (max 10 lines)
- Include version number placeholder
- Use only ASCII characters (no fancy Unicode)

**Example style**:
```
╦ ╦┌─┐─┐ ┬┌─┐┬─┐┌─┐┬ ┬
╠═╣├┤ ┌┴┬┘├─┤├┬┘│  ├─┤
╩ ╩└─┘┴ └─┴ ┴┴└─└─┘┴ ┴
Guardrails v0.4.1
```

**Files to edit**:
- `hexarch_cli/output/banner.py` (create new file)
- `hexarch_cli/commands/serve.py` (to display banner on startup)

**Estimated time**: 30 minutes - 1 hour

**Good for beginners** because: Fun, creative task; no complex code; instant visual feedback.

---

## 🐛 Bug Fix Issues

### Issue #9: Fix Typo in Error Message
**Labels**: `good first issue`, `bug`, `typo`

**Description**:
Fix typo in error message when policy file is not found.

**Current message**:
```
Error: Could not find policy file 'hexarch.yaml'. Plese ensure it exists.
```

**Should be**:
```
Error: Could not find policy file 'hexarch.yaml'. Please ensure it exists.
```

**File to edit**:
- `hexarch_guardrails/policy_loader.py` (search for "Plese")

**Estimated time**: 5 minutes

**Good for beginners** because: Perfect first PR; learn the contribution workflow.

---

### Issue #10: Handle Missing OPA Gracefully
**Labels**: `good first issue`, `bug`, `error-handling`

**Description**:
Currently, if OPA is not running, the guardian throws an ugly stack trace. Instead, it should show a helpful error message.

**Current behavior**:
```
Traceback (most recent call last):
  File "app.py", line 10, in <module>
    guardian = Guardian()
  ...
ConnectionRefusedError: [Errno 61] Connection refused
```

**Desired behavior**:
```
❌ Error: Cannot connect to OPA server at http://localhost:8181

💡 Troubleshooting:
   1. Ensure OPA is running: docker run -p 8181:8181 openpolicyagent/opa run
   2. Check your hexarch.yaml 'opa.url' configuration
   3. Or set HEXARCH_OPA_URL environment variable

See: https://github.com/no1rstack/hexarch-guardrails#opa-setup
```

**Files to edit**:
- `hexarch_guardrails/opa_client.py`
- Add custom exception: `hexarch_guardrails/exceptions.py`

**Estimated time**: 1-2 hours

**Good for beginners** because: Improves user experience; learn error handling best practices.

---

## How to Claim an Issue

1. Comment on the issue: "I'd like to work on this!"
2. Wait for maintainer confirmation
3. Fork the repo and create a branch
4. Make your changes and open a PR
5. Reference the issue in your PR description

## Resources for Contributors

- **Contributing Guide**: [CONTRIBUTING.md](../CONTRIBUTING.md)
- **Development Setup**: [docs/DEVELOPMENT.md](../docs/DEVELOPMENT.md)
- **Code Style**: We use `black` for formatting, `flake8` for linting
- **Testing**: Run `pytest` before submitting PR

## Need Help?

- Ask questions in the issue comments
- Join discussions in GitHub Discussions
- Tag @no1rstack for maintainer help

---

**Adding these issues to GitHub**:

```bash
# Install GitHub CLI if not already installed
# Then run:
gh issue create --title "Add Examples for Flask Integration" \
  --body-file good_first_issues.md \
  --label "good first issue,documentation,examples"

# Repeat for each issue above
```
