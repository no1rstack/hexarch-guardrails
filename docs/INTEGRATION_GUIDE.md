# Hexarch Guardrails - Integration Guide

## 🎯 For Different Platforms

### 1. Python Scripts & CLI Tools

**Setup:**
```bash
pip install hexarch-guardrails
```

**Usage:**
```python
from hexarch_guardrails import Guardian

guardian = Guardian()

@guardian.check("api_budget")
def my_script():
    # Your code here
    pass

if __name__ == "__main__":
    my_script()
```

**Deploy:**
```bash
python my_script.py
```

---

### 2. Discord Bots

**Setup:**
```bash
pip install discord.py hexarch-guardrails
```

**Usage:**
```python
import discord
from hexarch_guardrails import Guardian

bot = discord.Client()
guardian = Guardian()

@bot.event
async def on_message(message):
    @guardian.check("rate_limit")
    async def respond():
        await message.channel.send("Hello!")
    
    await respond()
```

---

### 3. Web Applications (Flask)

**Setup:**
```bash
pip install flask hexarch-guardrails
```

**Usage:**
```python
from flask import Flask
from hexarch_guardrails import Guardian

app = Flask(__name__)
guardian = Guardian()

@app.route("/expensive")
@guardian.check("api_budget")
def expensive_operation():
    return {"result": "done"}

if __name__ == "__main__":
    app.run()
```

---

### 4. AWS Lambda

**Setup:**
```bash
# Include in requirements.txt
hexarch-guardrails
requests
pyyaml
```

**Usage:**
```python
from hexarch_guardrails import Guardian

guardian = Guardian()

@guardian.check("api_budget")
def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'body': 'Success'
    }
```

**Deploy:**
```bash
zip -r lambda_package.zip .
aws lambda update-function-code --function-name my-func --zip-file fileb://lambda_package.zip
```

---

### 5. GitHub Actions

**Setup in workflow:**
```yaml
name: API Budget Check
on: [pull_request]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install hexarch-guardrails
      - run: python -c "
          from hexarch_guardrails import Guardian
          guardian = Guardian()
          print(f'Policies loaded: {guardian.list_policies()}')
          "
```

---

### 6. Docker Containers

**Dockerfile:**
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]
```

**requirements.txt:**
```
hexarch-guardrails
requests
pyyaml
```

**Build & Run:**
```bash
docker build -t my-app .
docker run -p 8000:8000 my-app
```

---

### 7. Kubernetes Pods

**deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: app
        image: my-app:latest
        env:
        - name: OPA_URL
          value: "http://opa-service:8181"
        - name: HEXARCH_POLICY_FILE
          value: "/etc/hexarch/hexarch.yaml"
        volumeMounts:
        - name: policy
          mountPath: /etc/hexarch
      volumes:
      - name: policy
        configMap:
          name: hexarch-policies
```

**ConfigMap:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: hexarch-policies
data:
  hexarch.yaml: |
    policies:
      - id: "api_budget"
        rules:
          - resource: "openai"
            monthly_budget_usd: 10
```

**Deploy:**
```bash
kubectl apply -f deployment.yaml
```

---

### 8. OpenAI Integration

**Complete Example:**
```python
from hexarch_guardrails import Guardian
import openai

# Setup
guardian = Guardian()
openai.api_key = "sk-..."

# Define protected functions
@guardian.check("api_budget", context={"api": "openai", "model": "gpt-4"})
def ask_gpt4(question: str):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": question}]
    )
    return response.choices[0].message.content

@guardian.check("rate_limit", context={"service": "openai"})
def ask_gpt35(question: str):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": question}]
    )
    return response.choices[0].message.content

# Use
if __name__ == "__main__":
    answer = ask_gpt4("What is machine learning?")
    print(answer)
```

---

### 9. Anthropic Claude Integration

**Setup:**
```bash
pip install anthropic hexarch-guardrails
```

**Usage:**
```python
from hexarch_guardrails import Guardian
import anthropic

guardian = Guardian()
client = anthropic.Anthropic(api_key="sk-ant-...")

@guardian.check("api_budget", context={"api": "anthropic"})
def ask_claude(prompt: str):
    message = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

result = ask_claude("Explain quantum computing")
```

---

### 10. AWS SDK Integration

**Setup:**
```bash
pip install boto3 hexarch-guardrails
```

**Usage:**
```python
from hexarch_guardrails import Guardian
import boto3

guardian = Guardian()
ec2 = boto3.resource('ec2')

@guardian.check("api_budget", context={"service": "aws", "operation": "ec2"})
def launch_instances():
    instances = ec2.create_instances(
        ImageId='ami-0c55b159cbfafe1f0',
        MinCount=1,
        MaxCount=1
    )
    return instances

@guardian.check("safe_delete")
def terminate_instances(instance_ids):
    ec2.instances.filter(InstanceIds=instance_ids).terminate()

if __name__ == "__main__":
    instances = launch_instances()
    print(f"Launched: {instances[0].id}")
    # terminate_instances([instances[0].id])  # Requires confirmation
```

---

### 11. Hugging Face Transformers

**Setup:**
```bash
pip install transformers torch hexarch-guardrails
```

**Usage:**
```python
from hexarch_guardrails import Guardian
from transformers import pipeline

guardian = Guardian()

@guardian.check("rate_limit")
def generate_text(prompt: str):
    generator = pipeline('text-generation', model='gpt2')
    result = generator(prompt, max_length=50)
    return result[0]['generated_text']

if __name__ == "__main__":
    text = generate_text("Once upon a time")
    print(text)
```

---

### 12. LangChain Integration

**Setup:**
```bash
pip install langchain hexarch-guardrails
```

**Usage:**
```python
from hexarch_guardrails import Guardian
from langchain.llms import OpenAI
from langchain.agents import initialize_agent, Tool

guardian = Guardian()

@guardian.check("api_budget", context={"api": "openai"})
def run_agent(query: str):
    llm = OpenAI(temperature=0)
    agent = initialize_agent(
        tools=[],
        llm=llm,
        agent="zero-shot-react-description"
    )
    return agent.run(query)

if __name__ == "__main__":
    result = run_agent("What is the capital of France?")
    print(result)
```

---

## 🔧 OPA Setup for All Platforms

### Local Development
```bash
# macOS
brew install opa
opa run --server

# Linux
docker run -p 8181:8181 openpolicyagent/opa:latest run --server

# Windows
choco install opa
opa run --server
```

### Production Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: opa
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: opa
        image: openpolicyagent/opa:latest
        ports:
        - containerPort: 8181
        command: ["opa", "run", "--server"]
```

---

## 📊 Environment Variables

```bash
# OPA URL (default: http://localhost:8181)
export OPA_URL="http://opa-server:8181"

# Policy file location (default: auto-discover)
export HEXARCH_POLICY_FILE="/etc/hexarch/hexarch.yaml"

# Enable debug logging
export HEXARCH_DEBUG="true"

# Enforcement mode (default: strict)
export HEXARCH_ENFORCEMENT="warn"
```

**Usage in code:**
```python
import os
from hexarch_guardrails import Guardian

guardian = Guardian(
    policy_file=os.getenv("HEXARCH_POLICY_FILE"),
    opa_url=os.getenv("OPA_URL", "http://localhost:8181")
)
```

---

## 🚀 Quick Integration Template

Copy this to get started:

```python
"""
my_app.py - Guardrails-protected application
"""
import os
from hexarch_guardrails import Guardian, PolicyViolation

# Initialize
guardian = Guardian(
    policy_file=os.getenv("HEXARCH_POLICY_FILE"),
    opa_url=os.getenv("OPA_URL", "http://localhost:8181")
)

# Define protected operations
@guardian.check("api_budget")
def expensive_operation():
    print("Running expensive operation...")
    return {"status": "success"}

@guardian.check("safe_delete")
def delete_something(resource_id):
    print(f"Deleting {resource_id}...")
    return True

# Error handling
def main():
    try:
        result = expensive_operation()
        print(f"✅ Success: {result}")
    except PolicyViolation as e:
        print(f"❌ Blocked: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
```

---

## ✅ Integration Checklist

- [ ] Install: `pip install hexarch-guardrails`
- [ ] Add: `hexarch.yaml` to project root
- [ ] Import: `from hexarch_guardrails import Guardian`
- [ ] Initialize: `guardian = Guardian()`
- [ ] Protect: `@guardian.check("policy_id")`
- [ ] Test: Run with OPA server
- [ ] Deploy: Include in requirements.txt/Dockerfile
- [ ] Monitor: Check logs for policy violations

