"""HTTP client for hexarch-ctl API requests."""

from typing import Any, Dict, Optional, List
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError
from hexarch_cli.api.auth import AuthManager
from hexarch_cli.config.schemas import APIConfig


class HexarchAPIClient:
    """HTTP client for Hexarch API."""
    
    def __init__(self, config: APIConfig):
        """Initialize API client.
        
        Args:
            config: API configuration
        """
        self.config = config
        self.auth = AuthManager(config.token)
        self.session = requests.Session()
        
        # Configure session
        self.session.verify = config.verify_ssl
        self.session.timeout = config.timeout_seconds
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> requests.Response:
        """Make HTTP request to API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., "/api/policies")
            **kwargs: Additional request arguments
        
        Returns:
            Response object
        
        Raises:
            RequestException: If request fails
        """
        url = f"{self.config.url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # Add auth header
        headers = kwargs.pop("headers", {})
        headers.update(self.auth.get_auth_header())
        
        try:
            response = self.session.request(
                method,
                url,
                headers=headers,
                timeout=self.config.timeout_seconds,
                **kwargs
            )
            response.raise_for_status()
            return response
        except Timeout:
            raise RequestException(f"Request timeout ({self.config.timeout_seconds}s): {url}")
        except ConnectionError:
            raise RequestException(f"Connection failed: {self.config.url}")
        except RequestException as e:
            raise RequestException(f"Request failed: {str(e)}")
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """GET request.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
        
        Returns:
            JSON response as dict
        """
        response = self._make_request("GET", endpoint, params=params)
        return response.json()
    
    def post(self, endpoint: str, json: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """POST request.
        
        Args:
            endpoint: API endpoint
            json: JSON payload
        
        Returns:
            JSON response as dict
        """
        response = self._make_request("POST", endpoint, json=json)
        return response.json()
    
    def list_policies(self) -> List[Dict[str, Any]]:
        """List all policies.
        
        Returns:
            List of policy objects
        """
        response = self.get("/api/policies")
        return response.get("policies", [])
    
    def get_policy(self, name: str) -> Dict[str, Any]:
        """Get single policy.
        
        Args:
            name: Policy name
        
        Returns:
            Policy object
        """
        response = self.get(f"/api/policies/{name}")
        return response
    
    def export_decisions(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        provider: Optional[str] = None,
        user_id: Optional[str] = None,
        decision: Optional[str] = None,
        page: int = 1,
        page_size: int = 100
    ) -> Dict[str, Any]:
        """Export decisions with filters.
        
        Args:
            date_from: Start date (ISO 8601)
            date_to: End date (ISO 8601)
            provider: Filter by provider
            user_id: Filter by user ID
            decision: Filter by decision (ALLOW/DENY)
            page: Page number
            page_size: Records per page
        
        Returns:
            Response with decisions and pagination
        """
        params = {
            "page": page,
            "page_size": page_size
        }
        
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        if provider:
            params["provider"] = provider
        if user_id:
            params["user_id"] = user_id
        if decision:
            params["decision"] = decision
        
        return self.get("/api/decisions/export", params=params)
    
    def get_metrics(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        time_window: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get provider metrics.
        
        Args:
            date_from: Start date (ISO 8601)
            date_to: End date (ISO 8601)
            time_window: Time window (1h, 1d, 7d, 30d)
        
        Returns:
            Metrics object
        """
        params = {}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        if time_window:
            params["time_window"] = time_window
        
        return self.get("/api/metrics", params=params)

    def get_metrics_trends(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        time_window: Optional[str] = None,
        provider: Optional[str] = None,
        metric: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get metrics trend data.

        Args:
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            time_window: Time window (1h, 1d, 7d)
            provider: Provider name
            metric: Metric name (latency_ms, error_rate, requests)

        Returns:
            Trend data object
        """
        params = {}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        if time_window:
            params["time_window"] = time_window
        if provider:
            params["provider"] = provider
        if metric:
            params["metric"] = metric

        return self.get("/api/metrics/trends", params=params)
    
    def query_decisions(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        provider: Optional[str] = None,
        user_id: Optional[str] = None,
        decision: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Query decisions with filters.
        
        Args:
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            provider: Filter by provider
            user_id: Filter by user ID
            decision: Filter by decision (ALLOW/DENY)
            limit: Max results per page
            offset: Pagination offset
        
        Returns:
            List of decision objects
        """
        params = {"limit": min(limit, 1000), "offset": offset}
        
        if from_date:
            params["from_date"] = from_date
        if to_date:
            params["to_date"] = to_date
        if provider:
            params["provider"] = provider
        if user_id:
            params["user_id"] = user_id
        if decision:
            params["decision"] = decision
        
        response = self.get("/api/decisions/export", params=params)
        return response.get("decisions", [])
    
    def get_decision_stats(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        group_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get decision statistics.
        
        Args:
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            group_by: Grouping dimension (provider, decision, user, hour)
        
        Returns:
            Statistics object
        """
        params = {}
        if from_date:
            params["from_date"] = from_date
        if to_date:
            params["to_date"] = to_date
        if group_by:
            params["group_by"] = group_by
        
        return self.get("/api/decisions/stats", params=params)
    
    def health_check(self) -> bool:
        """Check API health.
        
        Returns:
            True if API is healthy
        """
        try:
            response = self._make_request("GET", "/health")
            return response.status_code == 200
        except Exception:
            return False
    
    def close(self) -> None:
        """Close session."""
        self.session.close()


__all__ = ["HexarchAPIClient"]
