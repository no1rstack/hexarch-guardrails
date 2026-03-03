# FastAPI + Hexarch Guardrails Integration

Complete example of protecting FastAPI endpoints with policy-driven guardrails.

## Quick Start

```bash
pip install fastapi uvicorn hexarch-guardrails
```

## File Structure

```
my-fastapi-app/
├── hexarch.yaml          # Policy definitions
├── main.py              # FastAPI app with guardrails
└── requirements.txt
```

## hexarch.yaml

```yaml
policies:
  # Protect AI endpoints from excessive usage
  - id: "ai_rate_limit"
    description: "Rate limit for AI completions"
    rules:
      - resource: "openai"
        requests_per_minute: 60
        requests_per_hour: 1000
        action: "block"

  # Budget protection
  - id: "ai_budget"
    description: "Monthly AI spending cap"
    rules:
      - resource: "openai"
        monthly_budget: 500
        action: "warn_at_80%"

  # General API rate limiting
  - id: "api_rate_limit"
    description: "Protect all public endpoints"
    rules:
      - resource: "public_api"
        requests_per_minute: 100
        action: "block"

  # Expensive operations
  - id: "admin_operations"
    description: "Require confirmation for destructive ops"
    rules:
      - operation: "delete"
        action: "require_confirmation"
      - operation: "bulk_update"
        action: "require_confirmation"
```

## main.py

```python
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from hexarch_guardrails import Guardian
import openai
from typing import Optional

app = FastAPI(title="AI-Powered API with Guardrails")

# Initialize guardian
guardian = Guardian()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request models
class CompletionRequest(BaseModel):
    prompt: str
    max_tokens: int = 100
    temperature: float = 0.7


class BulkUpdateRequest(BaseModel):
    user_ids: list[int]
    confirmed: bool = False


# Protected OpenAI completion endpoint
@app.post("/api/v1/completions")
@guardian.check("ai_rate_limit")
@guardian.check("ai_budget")
async def create_completion(request: CompletionRequest):
    """
    Generate AI completion with rate limiting and budget protection.
    
    Policies applied:
    - ai_rate_limit: Max 60 req/min, 1000 req/hour
    - ai_budget: Warn at 80% of $500 monthly budget
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": request.prompt}],
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        return {
            "completion": response.choices[0].message.content,
            "tokens_used": response.usage.total_tokens
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Protected public endpoint with rate limiting
@app.get("/api/v1/data/{item_id}")
@guardian.check("api_rate_limit")
async def get_data(item_id: int):
    """
    Public endpoint with rate limiting.
    
    Policy: Max 100 requests per minute per instance.
    """
    # Your data fetching logic here
    return {
        "item_id": item_id,
        "data": "Sample data",
        "protected": True
    }


# Protected destructive operation
@app.post("/api/v1/users/bulk-update")
@guardian.check("admin_operations")
async def bulk_update_users(
    request: BulkUpdateRequest,
    admin_key: Optional[str] = Header(None)
):
    """
    Bulk update users - requires explicit confirmation.
    
    Policy: Requires confirmation flag to prevent accidental mass updates.
    """
    if not admin_key or admin_key != "your-admin-key":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if not request.confirmed:
        raise HTTPException(
            status_code=400,
            detail="Bulk operations require explicit confirmation. Set 'confirmed: true'"
        )
    
    # Your bulk update logic here
    return {
        "status": "success",
        "updated_count": len(request.user_ids),
        "message": f"Updated {len(request.user_ids)} users"
    }


# Health check (unprotected)
@app.get("/health")
async def health():
    """Health check endpoint - not rate limited"""
    return {"status": "healthy", "guardrails": "active"}


# Guardian status endpoint
@app.get("/api/v1/guardian/status")
async def guardian_status():
    """
    Check guardian policy status and current limits.
    """
    return {
        "active_policies": ["ai_rate_limit", "ai_budget", "api_rate_limit", "admin_operations"],
        "rate_limits": {
            "ai_completions": "60/min, 1000/hour",
            "public_api": "100/min"
        },
        "budget": {
            "monthly_limit": 500,
            "warn_threshold": 400
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## requirements.txt

```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
hexarch-guardrails>=0.4.1
openai>=1.0.0
pydantic>=2.0.0
```

## Run the API

```bash
# Install dependencies
pip install -r requirements.txt

# Set OpenAI API key
export OPENAI_API_KEY="your-key-here"

# Run server
python main.py
```

Server starts at: `http://localhost:8000`

## Test the Guardrails

### 1. Test rate limiting

```bash
# This will work for the first 60 requests/minute
for i in {1..65}; do
  curl -X POST http://localhost:8000/api/v1/completions \
    -H "Content-Type: application/json" \
    -d '{"prompt": "Hello", "max_tokens": 10}'
  sleep 0.5
done

# Requests 61-65 should be blocked with 429 status
```

### 2. Test budget protection

```bash
# Monitor budget warnings in server logs
curl -X POST http://localhost:8000/api/v1/completions \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Generate a long article...", "max_tokens": 2000}'
```

### 3. Test confirmation requirement

```bash
# This will fail - no confirmation
curl -X POST http://localhost:8000/api/v1/users/bulk-update \
  -H "Content-Type: application/json" \
  -H "admin-key: your-admin-key" \
  -d '{"user_ids": [1,2,3], "confirmed": false}'

# This will succeed
curl -X POST http://localhost:8000/api/v1/users/bulk-update \
  -H "Content-Type: application/json" \
  -H "admin-key: your-admin-key" \
  -d '{"user_ids": [1,2,3], "confirmed": true}'
```

## Interactive API Docs

FastAPI provides interactive docs at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

You can test all protected endpoints interactively and see guardian policies in action!

## Production Considerations

### 1. Distributed Rate Limiting

For multi-instance deployments, consider adding Redis-backed rate limiting:

```python
from hexarch_guardrails import Guardian
from redis import Redis

guardian = Guardian(
    rate_limiter_backend=Redis(host='localhost', port=6379)
)
```

### 2. Budget Tracking

Implement actual cost tracking by intercepting OpenAI responses:

```python
@guardian.check("ai_budget")
async def create_completion(request: CompletionRequest):
    response = openai.ChatCompletion.create(...)
    
    # Track actual costs
    cost = calculate_cost(response.usage)
    guardian.track_usage("openai", cost)
    
    return response
```

### 3. Monitoring

Add logging for policy violations:

```python
import logging

logger = logging.getLogger(__name__)

@app.exception_handler(PolicyViolationException)
async def policy_violation_handler(request, exc):
    logger.warning(f"Policy violation: {exc.policy_id} - {exc.reason}")
    raise HTTPException(status_code=429, detail=exc.reason)
```

## Next Steps

- Add authentication with FastAPI OAuth2
- Implement distributed rate limiting with Redis
- Add Prometheus metrics for policy violations
- Set up alerting for budget thresholds

## Links

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Hexarch Guardrails](https://github.com/no1rstack/hexarch-guardrails)
- [OpenAI API](https://platform.openai.com/docs)
