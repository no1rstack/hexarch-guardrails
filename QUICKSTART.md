# Hexarch Guardrails - Python SDK Quickstart

## 🚀 Installation

```bash
# Install from PyPI
pip install hexarch-guardrails

# Or install from source
pip install -e .
```

## ⚡ 5-Minute Start

### Step 1: Create a Policy File

Copy `hexarch.yaml` to your project root:

```bash
cp hexarch.yaml your-project/
```

Or create a minimal one:

```yaml
# hexarch.yaml
policies:
  - id: "api_budget"
    rules:
      - resource: "openai"
                monthly_budget: 10
```

### Step 2: Use in Your Code

```python
from hexarch_guardrails import Guardian

# Initialize (auto-discovers hexarch.yaml)
guardian = Guardian()

# ⚠️ Requires a running OPA server (see "Running OPA Locally" below)

# Protect your expensive API calls
@guardian.check("api_budget")
def call_openai(prompt: str):
    import openai
    return openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

# Use it - guardrails check budget first!
response = call_openai("Hello GPT-4!")
```

### Step 3: Run Your Script

```bash
python your_script.py
```

If OPA is not running yet, start it first:

```bash
docker run -p 8181:8181 openpolicyagent/opa:latest run --server
```

That's it! 🎉

---

## 📚 Common Use Cases

### 1️⃣ Protect OpenAI Budget

```python
from hexarch_guardrails import Guardian

guardian = Guardian()

@guardian.check("api_budget", context={"api": "openai"})
def expensive_analysis(data: str):
    import openai
    return openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": f"Analyze: {data}"}]
    )

# Will warn/block if budget exceeded
result = expensive_analysis("Large dataset...")
```

### 2️⃣ Rate-Limit Discord Bot

```python
from hexarch_guardrails import Guardian

guardian = Guardian()

@guardian.check("rate_limit")
async def send_discord_message(channel, message):
    await channel.send(message)

# Enforces your configured rate limits before sending
await send_discord_message(channel, "Hello!")
```

### 3️⃣ Protect File Operations

```python
from hexarch_guardrails import Guardian
import os

guardian = Guardian()

@guardian.check("safe_delete")
def delete_important_file(path: str):
    os.remove(path)

# Will block unless confirmation logic is implemented by the application
delete_important_file("important_data.csv")
```

### 4️⃣ AWS/Cloud Operations

```python
from hexarch_guardrails import Guardian
import boto3

guardian = Guardian()

@guardian.check("api_budget", context={"service": "aws"})
def expensive_computation():
    # Start a large EC2 job
    ec2 = boto3.resource('ec2')
    instances = ec2.create_instances(ImageId='ami-123', MinCount=10, MaxCount=10)
    return instances

# Protected by budget guardrails
instances = expensive_computation()
```

---

## 🎯 Available Policies

### `api_budget`
Prevents overspending on API calls

**Checks:**
- Monthly budget per API service
- Alerts at percentage thresholds
- Blocks expensive calls when near limit

**Example:**
```python
@guardian.check("api_budget", context={"api": "openai"})
def call_api():
    pass
```

### `rate_limit`
Prevents API rate limiting and abuse

**Checks:**
- Requests per minute
- Requests per hour
- Service-specific limits

**Example:**
```python
@guardian.check("rate_limit")
def api_call():
    pass
```

### `safe_delete`
Requires confirmation for destructive ops

**Checks:**
- File deletions
- Database operations
- Directory removal

**Example:**
```python
@guardian.check("safe_delete")
def delete_file(path):
    os.remove(path)
```

### `access_control`
Restricts who can perform operations

**Checks:**
- User permissions
- Admin-only operations
- Data access rules

**Example:**
```python
@guardian.check("access_control", context={"operation": "admin"})
def admin_operation():
    pass
```

### `time_based`
Prevents operations at certain times

**Checks:**
- Hour-based restrictions
- Day-based restrictions
- Context-aware timing

**Example:**
```python
@guardian.check("time_based")
def deploy_to_production():
    pass
```

---

## ⚙️ Configuration

### Policy File Location

Guardian auto-discovers policy files in this order:
1. `hexarch.yaml` (in current directory)
2. `hexarch.yml`
3. `.hexarch.yaml`
4. `.hexarch.yml`
5. Parent directories (walks up tree)

### Manual Configuration

```python
# Specify policy file explicitly
guardian = Guardian(policy_file="/path/to/hexarch.yaml")

# Custom OPA URL
guardian = Guardian(opa_url="http://custom-opa:8181")

# Warn mode (don't block)
guardian = Guardian(enforce=False)
```

---

## 🔧 Advanced Usage

### Programmatic Guarding

Instead of decorators, guard functions programmatically:

```python
guardian = Guardian()

def risky_operation():
    return "done"

# Guard it
guarded = guardian.guard_function(
    risky_operation,
    policy_id="safe_delete"
)

# Use it
result = guarded()
```

### Direct Policy Evaluation

```python
# Evaluate policy without running a function
decision = guardian.evaluate_policy(
    "api_budget",
    context={"api": "openai", "tokens": 1000}
)

if decision["allowed"]:
    print("✅ Operation allowed")
else:
    print(f"❌ {decision['reason']}")
```

### List Available Policies

```python
policies = guardian.list_policies()
print(f"Available policies: {policies}")
# Example output (depends on your hexarch.yaml):
# Available policies: ['api_budget', 'rate_limit', 'safe_delete', 'access_control', 'time_based']
```

### Get Policy Details

```python
policy = guardian.get_policy("api_budget")
print(f"Policy: {policy['description']}")
print(f"Rules: {len(policy['rules'])} rules")
```

---

## 🚨 Error Handling

```python
from hexarch_guardrails import Guardian, PolicyViolation

guardian = Guardian()

@guardian.check("safe_delete")
def delete_file(path):
    import os
    os.remove(path)

try:
    delete_file("important.txt")
except PolicyViolation as e:
    print(f"❌ Cannot delete: {e}")
    # Log the violation, alert user, etc.
except Exception as e:
    print(f"Unexpected error: {e}")
```

---

## 📊 Logging

Enable logging to track policy decisions:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

guardian = Guardian()
```

---

## 🐳 Running OPA Locally

Guardrails needs OPA running to evaluate policies.

### Docker (Easiest)

```bash
docker run -p 8181:8181 openpolicyagent/opa:latest run --server
```

### Manual Installation

```bash
# macOS
brew install opa

# Then run
opa run --server
```

---

## 🧪 Testing

Run the test suite:

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# With coverage
pytest --cov=hexarch_guardrails
```

---

## 📖 Examples

See `examples/` directory for complete examples:
- `openai_budget.py` - Budget protection for OpenAI
- `discord_ratelimit.py` - Discord bot rate limiting
- `safe_delete.py` - Safe file operations

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repo
2. Create a feature branch
3. Add tests
4. Submit a PR

---

## 📄 License

MIT License - see LICENSE file

---

## 💬 Support

- GitHub Issues: Report bugs
- Discussions: Ask questions
- Email: dev@hexarch.io

---

## 🎓 Next Steps

1. **Read the [Policy Authoring Guide](./docs/POLICY_GUIDE.md)** to create custom policies
2. **Check the [API Reference](./docs/API_REFERENCE.md)** for full API docs
3. **Explore [examples](./examples/)** for your use case
4. **Join our community** and share what you build!

Happy guarding! 🛡️
