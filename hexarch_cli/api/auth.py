"""Authentication management for hexarch-ctl."""

import os
from typing import Optional, Dict


class AuthManager:
    """Manage authentication tokens."""
    
    def __init__(self, token: Optional[str] = None):
        """Initialize auth manager.
        
        Args:
            token: Bearer token (if None, use HEXARCH_API_TOKEN env var)
        """
        self.token = token or os.getenv("HEXARCH_API_TOKEN")
    
    def get_auth_header(self) -> Dict[str, str]:
        """Get Authorization header for API requests.
        
        Returns:
            Dict with Authorization header, or empty dict if no token
        """
        if not self.token:
            return {}
        
        return {"Authorization": f"Bearer {self.token}"}
    
    def has_token(self) -> bool:
        """Check if token is configured."""
        return bool(self.token)
    
    def set_token(self, token: str) -> None:
        """Set bearer token."""
        self.token = token
    
    def clear_token(self) -> None:
        """Clear bearer token."""
        self.token = None


__all__ = ["AuthManager"]
