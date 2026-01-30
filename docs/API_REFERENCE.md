# Hexarch Guardrails - API Reference

## Core Classes

### Guardian

Main class for initializing and managing guardrails.

#### Constructor

```python
Guardian(
    policy_file: Optional[str] = None,
    opa_url: str = "http://localhost:8181",
    enforce: bool = True
)
```

**Parameters:**
- `policy_file` (str, optional): Path to hexarch.yaml. Auto-discovers if None.
- `opa_url` (str): URL to OPA server. Default: `http://localhost:8181`
- `enforce` (bool): If True, block violations. If False, warn only. Default: `True`

**Raises:**
- `PolicyConfigError`: If policy file not found or invalid
- `OPAConnectionError`: If cannot connect to OPA

**Example:**
```python
guardian = Guardian()
# or
guardian = Guardian(policy_file="/etc/hexarch.yaml", opa_url="http://opa:8181")
```

---

#### Methods

### `check(policy_id, context=None)`

Decorator to check a policy before function execution.

```python
@guardian.check(policy_id: str, context: Optional[Dict[str, Any]] = None)
def my_function():
    pass
```

**Parameters:**
- `policy_id` (str): ID of policy to check (e.g., "api_budget")
- `context` (dict, optional): Additional context for policy evaluation

**Returns:**
- Decorator function

**Raises:**
- `PolicyViolation`: If policy denied
- `ValueError`: If policy_id doesn't exist

**Example:**
```python
@guardian.check("api_budget", context={"api": "openai"})
def expensive_call():
    import openai
    return openai.ChatCompletion.create(...)
```

---

### `evaluate_policy(policy_id, context)`

Directly evaluate a policy without running a function.

```python
decision = guardian.evaluate_policy(
    policy_id: str,
    context: Dict[str, Any]
) -> Dict[str, Any]
```

**Parameters:**
- `policy_id` (str): Policy to evaluate
- `context` (dict): Request context (function, operation, resource, user, etc.)

**Returns:**
```python
{
    "allowed": bool,           # Whether policy allows
    "reason": str,             # Why (allowed/denied)
    "action": str,             # Recommended action (allow/warn/block)
    "severity": str            # Info/warning/error
}
```

**Example:**
```python
decision = guardian.evaluate_policy(
    "api_budget",
    {"api": "openai", "tokens": 500}
)

if decision["allowed"]:
    print("✅ Allowed")
else:
    print(f"❌ Denied: {decision['reason']}")
```

---

### `guard_function(func, policy_id, context=None)`

Programmatically guard a function (non-decorator).

```python
guarded_func = guardian.guard_function(
    func: Callable,
    policy_id: str,
    context: Optional[Dict[str, Any]] = None
) -> Callable
```

**Parameters:**
- `func` (callable): Function to guard
- `policy_id` (str): Policy to enforce
- `context` (dict, optional): Additional context

**Returns:**
- Guarded function

**Example:**
```python
def original_operation():
    return "result"

guarded = guardian.guard_function(original_operation, "safe_delete")
result = guarded()
```

---

### `list_policies()`

Get list of all available policy IDs.

```python
policies = guardian.list_policies() -> List[str]
```

**Returns:**
- List of policy IDs

**Example:**
```python
policies = guardian.list_policies()
print(policies)
# Output: ['api_budget', 'rate_limit', 'safe_delete', 'access_control']
```

---

### `get_policy(policy_id)`

Get full policy definition by ID.

```python
policy = guardian.get_policy(policy_id: str) -> Dict[str, Any]
```

**Parameters:**
- `policy_id` (str): Policy ID

**Returns:**
```python
{
    "id": str,
    "description": str,
    "enabled": bool,
    "rules": List[Dict],
    ...
}
```

**Raises:**
- `ValueError`: If policy doesn't exist

**Example:**
```python
policy = guardian.get_policy("api_budget")
print(f"Policy: {policy['description']}")
print(f"Rules: {policy['rules']}")
```

---

### `guard_function(func, policy_id, context=None)`

Programmatically guard a function.

```python
guarded = guardian.guard_function(
    func: Callable,
    policy_id: str,
    context: Optional[Dict] = None
) -> Callable
```

---

## Exceptions

### PolicyViolation

Raised when policy is violated and `enforce=True`.

```python
from hexarch_guardrails import PolicyViolation

try:
    @guardian.check("safe_delete")
    def delete_file(path):
        os.remove(path)
    
    delete_file("important.txt")
except PolicyViolation as e:
    print(f"Policy violation: {e}")
```

---

### PolicyWarning

Raised when policy warning is issued.

```python
from hexarch_guardrails import PolicyWarning
```

---

### OPAConnectionError

Raised when cannot connect to OPA server.

```python
from hexarch_guardrails import OPAConnectionError

try:
    guardian = Guardian()
except OPAConnectionError as e:
    print(f"OPA connection failed: {e}")
    # Fallback to local policy evaluation
```

---

### OPAPolicyError

Raised when OPA policy evaluation fails.

```python
from hexarch_guardrails import OPAPolicyError
```

---

### PolicyConfigError

Raised when policy configuration is invalid.

```python
from hexarch_guardrails import PolicyConfigError

try:
    guardian = Guardian(policy_file="invalid.yaml")
except PolicyConfigError as e:
    print(f"Config error: {e}")
```

---

## Policy Loader (Advanced)

### PolicyLoader.load(policy_file=None)

Load policy configuration from YAML.

```python
from hexarch_guardrails.policy_loader import PolicyLoader

config = PolicyLoader.load("/path/to/hexarch.yaml")
# or auto-discover:
config = PolicyLoader.load()
```

---

### PolicyLoader.find_policy_file(start_path=".")

Find policy file by walking up directory tree.

```python
found = PolicyLoader.find_policy_file("/my/project")
if found:
    print(f"Found policy at: {found}")
```

---

### PolicyLoader.validate(config)

Validate policy configuration structure.

```python
PolicyLoader.validate(config)  # Raises PolicyConfigError if invalid
```

---

## OPA Client (Advanced)

### OPAClient

Direct interface to OPA server.

```python
from hexarch_guardrails.opa_client import OPAClient

opa = OPAClient("http://localhost:8181")
decision = opa.check_policy("my_policy", {"user": "alice"})
```

#### Methods

**check_policy(policy_id, context)**
Evaluate a policy against context.

**get_policy(policy_path)**
Get policy data from OPA.

**publish_policy(policy_name, policy_content)**
Publish a policy to OPA.

---

## Context Variables

Common context variables passed to policies:

```python
{
    "function": str,           # Name of guarded function
    "policy_id": str,          # ID of policy being checked
    "user": str,               # Current user (optional)
    "resource": str,           # Resource being accessed
    "operation": str,          # Operation (create/read/update/delete)
    "api": str,                # API service name
    "timestamp": int,          # Unix timestamp
    "metadata": dict,          # Custom metadata
}
```

---

## Configuration (hexarch.yaml)

### Policy Definition

```yaml
policies:
  - id: "policy_name"
    description: "Human-readable description"
    enabled: true
    rules:
      - rule_key: rule_value
        action: "allow|warn|block"
```

### Enforcement Modes

```yaml
enforcement: "strict"  # Block all violations (default)
# or
enforcement: "warn"    # Only warn about violations
```

---

## Type Hints

Full type signature reference:

```python
from typing import Dict, Any, Optional, Callable, List

# Guardian constructor
Guardian(
    policy_file: Optional[str] = None,
    opa_url: str = "http://localhost:8181",
    enforce: bool = True
)

# check decorator
def check(
    policy_id: str,
    context: Optional[Dict[str, Any]] = None
) -> Callable

# evaluate_policy
def evaluate_policy(
    policy_id: str,
    context: Dict[str, Any]
) -> Dict[str, Any]

# list_policies
def list_policies() -> List[str]

# get_policy
def get_policy(policy_id: str) -> Dict[str, Any]
```

---

## Common Patterns

### Pattern 1: Budget-Protected API Call

```python
@guardian.check("api_budget")
def call_expensive_api():
    return api.query()
```

### Pattern 2: Rate-Limited Operation

```python
@guardian.check("rate_limit", context={"service": "discord"})
async def send_message(msg):
    await client.send(msg)
```

### Pattern 3: Safe Deletion with Confirmation

```python
@guardian.check("safe_delete")
def delete_critical_file(path):
    os.remove(path)
```

### Pattern 4: Multi-Level Protection

```python
@guardian.check("access_control")
@guardian.check("api_budget")
@guardian.check("rate_limit")
def protected_operation():
    pass
```

---

## Error Handling Best Practices

```python
from hexarch_guardrails import Guardian, PolicyViolation, OPAConnectionError

guardian = Guardian()

try:
    @guardian.check("policy_id")
    def my_func():
        pass
    
    my_func()

except PolicyViolation as e:
    # Policy denied - handle appropriately
    logger.warning(f"Policy violation: {e}")
    # Fallback behavior or user notification

except OPAConnectionError as e:
    # OPA unavailable - degrade gracefully
    logger.error(f"Policy engine unavailable: {e}")
    # Fallback to default behavior or queue for later

except Exception as e:
    # Unexpected error
    logger.error(f"Unexpected error: {e}")
    raise
```

---

## Performance Considerations

- Guardian decorators have minimal overhead (~1-2ms per check)
- OPA policies are cached by default
- Network latency to OPA is primary bottleneck
- Consider local OPA for low-latency checks

---

## Version Compatibility

- Python 3.8+
- Requires: requests, pyyaml, python-dotenv
- Tested on: Python 3.8, 3.9, 3.10, 3.11

