"""
Default policy templates for Individual Edition
"""

DEFAULT_POLICY_TEMPLATES = {
    "api_budget": """
# API Budget Protection
# Prevents overspending on API calls
package guardrails

import future.keywords

evaluate {
    input.policy_id == "api_budget"
    allowed := true
    reason := "Budget check passed"
}
""",
    "rate_limit": """
# Rate Limiting
# Prevents API abuse and throttling
package guardrails

import future.keywords

evaluate {
    input.policy_id == "rate_limit"
    allowed := true
    reason := "Within rate limits"
}
""",
    "safe_delete": """
# Safe Deletion
# Requires confirmation for destructive operations
package guardrails

import future.keywords

evaluate {
    input.policy_id == "safe_delete"
    allowed := true
    reason := "Deletion allowed"
}
"""
}

DEFAULT_HEXARCH_YAML = """
# Hexarch Guardrails Configuration
# Lightweight policy-driven API protection

policies:
  - id: "api_budget"
    description: "Protect against overspending on API calls"
    enabled: true
    rules:
      - resource: "openai"
        monthly_budget: 10
        alert_at_percentage: 80
        action: "warn_at_80%"
      
      - resource: "anthropic"
        monthly_budget: 5
        alert_at_percentage: 80
        action: "warn_at_80%"

  - id: "rate_limit"
    description: "Prevent API abuse and rate limiting"
    enabled: true
    rules:
      - resource: "*"
        requests_per_minute: 100
        requests_per_hour: 1000
        action: "block"

  - id: "safe_delete"
    description: "Require confirmation for destructive operations"
    enabled: true
    rules:
      - operation: "delete"
        resource_types: ["file", "directory", "database"]
        action: "require_confirmation"
"""
