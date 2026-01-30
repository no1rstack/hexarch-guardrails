"""
Guardian - Main guardrails enforcement engine
"""
import functools
import inspect
from typing import Optional, Dict, Any, Callable
from .opa_client import OPAClient
from .policy_loader import PolicyLoader
from .exceptions import PolicyViolation, PolicyWarning


class Guardian:
    """Main guardrails enforcement class"""
    
    def __init__(
        self,
        policy_file: Optional[str] = None,
        opa_url: str = "http://localhost:8181",
        enforce: bool = True
    ):
        """
        Initialize Guardian
        
        Args:
            policy_file: Path to hexarch.yaml. If None, auto-discovers.
            opa_url: OPA server URL
            enforce: If True, block violating requests. If False, warn only.
        """
        self.policy_file = policy_file
        self.opa_url = opa_url
        self.enforce = enforce
        
        # Load configuration
        self.config = PolicyLoader.load(policy_file)
        PolicyLoader.validate(self.config)
        
        # Initialize OPA client
        self.opa = OPAClient(opa_url)
        
        # Index policies by ID
        self.policies = {p["id"]: p for p in self.config.get("policies", [])}
    
    def check(
        self,
        policy_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Callable:
        """
        Decorator to check a policy before function execution
        
        Args:
            policy_id: ID of the policy to check
            context: Additional context dict (caller, metadata, etc.)
        
        Returns:
            Decorated function
        
        Example:
            @guardian.check("api_budget")
            def call_openai(prompt):
                return openai.ChatCompletion.create(...)
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Build context
                check_context = {
                    "function": func.__name__,
                    "policy_id": policy_id,
                    **(context or {})
                }
                
                # Evaluate policy
                decision = self.evaluate_policy(policy_id, check_context)
                
                # Handle decision
                if decision["allowed"]:
                    if decision.get("action") == "warn":
                        print(f"⚠️  WARNING: {decision.get('reason', 'Policy warning')}")
                    return func(*args, **kwargs)
                else:
                    reason = decision.get("reason", f"Policy '{policy_id}' violated")
                    raise PolicyViolation(reason)
            
            return wrapper
        
        return decorator
    
    def evaluate_policy(
        self,
        policy_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate a policy against the given context
        
        Args:
            policy_id: Policy ID to evaluate
            context: Context dict with operation details
        
        Returns:
            Decision dict with 'allowed' boolean and 'reason' string
        """
        if policy_id not in self.policies:
            raise ValueError(f"Unknown policy: {policy_id}")
        
        # Query OPA
        decision = self.opa.check_policy(policy_id, context)
        
        # Ensure we have required fields
        if "allowed" not in decision:
            decision["allowed"] = True
        
        if "reason" not in decision:
            decision["reason"] = ""
        
        return decision
    
    def guard_function(
        self,
        func: Callable,
        policy_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Callable:
        """
        Guard a function programmatically (non-decorator approach)
        
        Args:
            func: Function to guard
            policy_id: Policy to enforce
            context: Additional context
        
        Returns:
            Guarded function
        """
        return self.check(policy_id, context)(func)
    
    def get_policy(self, policy_id: str) -> Dict[str, Any]:
        """Get policy definition by ID"""
        if policy_id not in self.policies:
            raise ValueError(f"Unknown policy: {policy_id}")
        return self.policies[policy_id]
    
    def list_policies(self):
        """List all available policies"""
        return list(self.policies.keys())
