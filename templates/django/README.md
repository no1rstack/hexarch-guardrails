# Django + Hexarch Guardrails Integration

Protect Django views and background tasks with policy-driven guardrails.

## Quick Start

```bash
pip install django celery hexarch-guardrails
```

## Project Structure

```
myproject/
├── myproject/
│   ├── settings.py
│   └── celery.py
├── myapp/
│   ├── views.py
│   ├── tasks.py
│   └── decorators.py
├── hexarch.yaml
└── manage.py
```

## hexarch.yaml

```yaml
policies:
  # AI API protection
  - id: "openai_protection"
    description: "Rate limit and budget for AI calls"
    rules:
      - resource: "openai"
        requests_per_minute: 30
        monthly_budget: 300
        action: "block"

  # Background task limits
  - id: "celery_tasks"
    description: "Limit concurrent background tasks"
    rules:
      - resource: "heavy_computation"
        concurrent_limit: 5
        action: "queue"

  # Email sending limits
  - id: "email_rate_limit"
    description: "Prevent email spam"
    rules:
      - resource: "email"
        requests_per_hour: 100
        daily_limit: 500
        action: "block"

  # Admin operations
  - id: "admin_actions"
    description: "Protect destructive admin operations"
    rules:
      - operation: "bulk_delete"
        action: "require_confirmation"
```

## myapp/decorators.py

```python
from functools import wraps
from django.http import JsonResponse
from hexarch_guardrails import Guardian

guardian = Guardian()


def check_policy(policy_id):
    """Django view decorator for guardian policy checks"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                # Apply guardian check
                checked_func = guardian.check(policy_id)(view_func)
                return checked_func(request, *args, **kwargs)
            except Exception as e:
                return JsonResponse(
                    {"error": "Policy violation", "detail": str(e)},
                    status=429
                )
        return wrapper
    return decorator
```

## myapp/views.py

```python
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .decorators import check_policy
from .tasks import generate_report, send_bulk_email
import openai


@require_http_methods(["POST"])
@csrf_exempt
@check_policy("openai_protection")
def ai_completion(request):
    """
    Protected AI completion endpoint.
    Rate limited to 30 req/min with $300 monthly budget.
    """
    import json
    data = json.loads(request.body)
    prompt = data.get("prompt", "")
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100
    )
    
    return JsonResponse({
        "completion": response.choices[0].message.content,
        "tokens": response.usage.total_tokens
    })


@require_http_methods(["POST"])
@csrf_exempt
@check_policy("celery_tasks")
def trigger_report(request):
    """
    Trigger background report generation.
    Limited to 5 concurrent heavy tasks.
    """
    import json
    data = json.loads(request.body)
    user_id = data.get("user_id")
    
    task = generate_report.delay(user_id)
    
    return JsonResponse({
        "status": "queued",
        "task_id": task.id
    })


@require_http_methods(["POST"])
@csrf_exempt
@check_policy("email_rate_limit")
def send_email_view(request):
    """
    Send email with rate limiting.
    Max 100/hour, 500/day.
    """
    import json
    data = json.loads(request.body)
    
    # Your email sending logic
    send_email(
        to=data["to"],
        subject=data["subject"],
        body=data["body"]
    )
    
    return JsonResponse({"status": "sent"})


@require_http_methods(["POST"])
@csrf_exempt
@check_policy("admin_actions")
def bulk_delete_users(request):
    """
    Admin endpoint for bulk user deletion.
    Requires explicit confirmation flag.
    """
    import json
    data = json.loads(request.body)
    
    if not data.get("confirmed", False):
        return JsonResponse(
            {"error": "Bulk delete requires explicit confirmation"},
            status=400
        )
    
    user_ids = data.get("user_ids", [])
    # Your bulk delete logic
    User.objects.filter(id__in=user_ids).delete()
    
    return JsonResponse({
        "status": "deleted",
        "count": len(user_ids)
    })
```

## myapp/tasks.py

```python
from celery import shared_task
from hexarch_guardrails import Guardian

guardian = Guardian()


@shared_task
@guardian.check("celery_tasks")
def generate_report(user_id):
    """
    Heavy computation task protected by concurrency limits.
    """
    import time
    # Simulate expensive computation
    time.sleep(10)
    return f"Report generated for user {user_id}"


@shared_task
@guardian.check("openai_protection")
def batch_embeddings(documents):
    """
    Generate embeddings for multiple documents.
    Protected by rate limit and budget.
    """
    import openai
    embeddings = []
    
    for doc in documents:
        response = openai.Embedding.create(
            model="text-embedding-ada-002",
            input=doc
        )
        embeddings.append(response.data[0].embedding)
    
    return embeddings


@shared_task
@guardian.check("email_rate_limit")
def send_bulk_email(recipients, subject, body):
    """
    Send emails in bulk with rate limiting.
    """
    from django.core.mail import send_mail
    
    for recipient in recipients:
        send_mail(
            subject=subject,
            message=body,
            from_email="noreply@example.com",
            recipient_list=[recipient]
        )
    
    return len(recipients)
```

## myproject/urls.py

```python
from django.urls import path
from myapp import views

urlpatterns = [
    path('api/ai/completion/', views.ai_completion),
    path('api/reports/generate/', views.trigger_report),
    path('api/email/send/', views.send_email_view),
    path('api/admin/bulk-delete/', views.bulk_delete_users),
]
```

## myproject/celery.py

```python
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

app = Celery('myproject')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

## requirements.txt

```
Django>=4.2
celery>=5.3.0
redis>=5.0.0
hexarch-guardrails>=0.4.1
openai>=1.0.0
```

## Run the Project

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start Django dev server
python manage.py runserver

# In another terminal, start Celery worker
celery -A myproject worker --loglevel=info

# In another terminal, start Celery beat (optional)
celery -A myproject beat --loglevel=info
```

## Test the Guardrails

### 1. Test AI rate limiting

```bash
# Send 35 requests rapidly
for i in {1..35}; do
  curl -X POST http://localhost:8000/api/ai/completion/ \
    -H "Content-Type: application/json" \
    -d "{\"prompt\": \"Test $i\"}"
done

# Requests after #30 should return 429 status
```

### 2. Test Celery concurrency limits

```python
# In Django shell
from myapp.tasks import generate_report

# Queue 10 tasks
for i in range(10):
    generate_report.delay(i)

# Only 5 will run concurrently, rest queued
```

### 3. Test email rate limiting

```bash
# This script will hit hourly limits
for i in {1..105}; do
  curl -X POST http://localhost:8000/api/email/send/ \
    -H "Content-Type: application/json" \
    -d "{\"to\": \"user$i@example.com\", \"subject\": \"Test\", \"body\": \"Hello\"}"
done
```

## Django Admin Integration

Add policy monitoring to Django admin:

```python
# myapp/admin.py
from django.contrib import admin

@admin.register(PolicyViolation)
class PolicyViolationAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'policy_id', 'resource', 'user', 'reason']
    list_filter = ['policy_id', 'timestamp']
    search_fields = ['user__username', 'reason']
    readonly_fields = ['timestamp', 'policy_id', 'reason']
```

## Middleware for Request-level Protection

```python
# myapp/middleware.py
from hexarch_guardrails import Guardian

guardian = Guardian()


class GuardianMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Apply global rate limiting
        if request.path.startswith('/api/'):
            try:
                guardian.check_rate_limit('api', user_id=request.user.id)
            except Exception as e:
                return JsonResponse(
                    {"error": "Rate limit exceeded"},
                    status=429
                )
        
        response = self.get_response(request)
        return response
```

Add to `settings.py`:

```python
MIDDLEWARE = [
    # ... other middleware
    'myapp.middleware.GuardianMiddleware',
]
```

## Production Tips

1. **Use persistent storage for rate limits** (Redis/PostgreSQL)
2. **Monitor policy violations** via Django signals
3. **Add Sentry integration** for violation alerts
4. **Use environment-specific policies** (dev vs prod limits)

## Links

- [Django Documentation](https://docs.djangoproject.com/)
- [Celery Documentation](https://docs.celeryq.dev/)
- [Hexarch Guardrails](https://github.com/no1rstack/hexarch-guardrails)
