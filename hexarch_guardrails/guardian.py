"""
Guardian - Main guardrails enforcement engine
"""
import functools
import inspect
from typing import Optional, Dict, Any, Callable
from .opa_client import OPAClient
from .policy_loader import PolicyLoader
from .exceptions import PolicyViolation, PolicyWarning
from .runtime_settings import resolve_runtime_settings
from .policy_engine import build_engine_from_bundle


class Guardian:
    """Main guardrails enforcement class"""
    
    def __init__(
        self,
        policy_file: Optional[str] = None,
        opa_url: Optional[str] = None,
        enforce: bool = True,
        runtime_mode: Optional[str] = None,
    ):
        """
        Initialize Guardian
        
        Args:
            policy_file: Path to hexarch.yaml. If None, auto-discovers.
            opa_url: OPA server URL
            enforce: If True, block violating requests. If False, warn only.
            runtime_mode: guardian-yaml (default) or rego-bundle.
        """
        settings = resolve_runtime_settings(
            policy_file=policy_file,
            opa_url=opa_url,
            runtime_mode=runtime_mode,
        )

        self.policy_file = settings.policy_file
        self.opa_url = settings.opa_url
        self.enforce = enforce
        self.runtime_mode = settings.runtime_mode
        self._rego_engine = None
        
        if self.runtime_mode == "rego-bundle":
            self.config = {"mode": "rego-bundle"}
            self.opa = None
            self.policies = {}
            self._rego_engine = build_engine_from_bundle(
                profile=settings.profile,
                policy_path=settings.policy_path,
                merge_mode=settings.merge_mode,
                mode=settings.engine_mode,
                opa_url=settings.opa_url,
                fail_closed=settings.fail_closed,
            )
        else:
            # Load configuration
            self.config = PolicyLoader.load(self.policy_file)
            PolicyLoader.validate(self.config)

            # Initialize OPA client
            self.opa = OPAClient(self.opa_url)

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
        if self.runtime_mode == "rego-bundle":
            if self._rego_engine is None:
                raise RuntimeError("Rego decision engine not initialized")

            input_payload = {
                "policy_id": policy_id,
                **(context or {}),
            }
            decision = self._rego_engine.evaluate(input_payload)
            allowed = bool(decision.get("allow", False))
            return {
                "allowed": allowed,
                "reason": decision.get("error") or "Allowed" if allowed else f"Policy '{policy_id}' violated",
                "action": "allow" if allowed else "deny",
                "raw": decision.get("raw"),
                "mode": "rego-bundle",
            }

        if policy_id not in self.policies:
            raise ValueError(f"Unknown policy: {policy_id}")
        
        # Query OPA
        decision = self.opa.check_policy(policy_id, context)
        
        # Ensure we have required fields
        if "allowed" not in decision:
            decision["allowed"] = True
        
        if "reason" not in decision:
            decision["reason"] = ""

        decision["mode"] = "guardian-yaml"
        
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
        if self.runtime_mode == "rego-bundle":
            raise ValueError("get_policy is unavailable in rego-bundle mode")
        if policy_id not in self.policies:
            raise ValueError(f"Unknown policy: {policy_id}")
        return self.policies[policy_id]
    
    def list_policies(self):
        """List all available policies"""
        if self.runtime_mode == "rego-bundle":
            return ["rego-bundle"]
        return list(self.policies.keys())
