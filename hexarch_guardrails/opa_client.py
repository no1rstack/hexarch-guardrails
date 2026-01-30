"""
OPA Client - Communicates with Open Policy Agent server
"""
import requests
import json
from typing import Dict, Any, Optional
from .exceptions import OPAConnectionError, OPAPolicyError


class OPAClient:
    """Wrapper for OPA REST API"""
    
    def __init__(self, opa_url: str = "http://localhost:8181"):
        self.opa_url = opa_url.rstrip("/")
        self._verify_connection()
    
    def _verify_connection(self):
        """Verify OPA server is reachable"""
        try:
            response = requests.get(f"{self.opa_url}/health", timeout=2)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise OPAConnectionError(
                f"Cannot connect to OPA at {self.opa_url}. "
                f"Make sure OPA is running. Error: {e}"
            )
    
    def check_policy(
        self,
        policy_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check a policy against the given context
        
        Args:
            policy_id: Policy identifier (e.g., "api_budget")
            context: Dict with request context (operation, resource, user, etc.)
        
        Returns:
            Policy decision with decision, reason, action
        """
        try:
            payload = {
                "input": {
                    "policy_id": policy_id,
                    **context
                }
            }
            
            response = requests.post(
                f"{self.opa_url}/v1/data/guardrails/evaluate",
                json=payload,
                timeout=2
            )
            response.raise_for_status()
            
            result = response.json()
            
            if "result" not in result:
                raise OPAPolicyError(f"Invalid OPA response: {result}")
            
            return result["result"]
        
        except requests.exceptions.RequestException as e:
            raise OPAConnectionError(f"OPA request failed: {e}")
        except json.JSONDecodeError as e:
            raise OPAPolicyError(f"Failed to parse OPA response: {e}")
    
    def get_policy(self, policy_path: str) -> Dict[str, Any]:
        """Get policy data from OPA"""
        try:
            response = requests.get(
                f"{self.opa_url}/v1/data/{policy_path}",
                timeout=2
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise OPAConnectionError(f"Failed to get policy: {e}")
    
    def publish_policy(self, policy_name: str, policy_content: str) -> bool:
        """Publish a policy to OPA"""
        try:
            response = requests.put(
                f"{self.opa_url}/v1/policies/{policy_name}",
                data=policy_content,
                headers={"Content-Type": "text/plain"},
                timeout=5
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            raise OPAConnectionError(f"Failed to publish policy: {e}")
