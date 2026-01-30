"""
Tests for OPA Client
"""
import pytest
from unittest.mock import patch, Mock
import requests
from hexarch_guardrails.opa_client import OPAClient
from hexarch_guardrails.exceptions import OPAConnectionError, OPAPolicyError


@pytest.fixture
def mock_requests():
    """Mock requests library"""
    with patch('hexarch_guardrails.opa_client.requests') as mock:
        # Ensure exception classes remain real exception types.
        mock.exceptions = requests.exceptions
        yield mock


def test_opa_client_connection_success(mock_requests):
    """Test successful OPA connection"""
    mock_requests.get.return_value.status_code = 200
    
    client = OPAClient()
    assert client.opa_url == "http://localhost:8181"


def test_opa_client_connection_failure(mock_requests):
    """Test failed OPA connection"""
    mock_requests.get.side_effect = requests.exceptions.ConnectionError("Connection failed")
    
    with pytest.raises(OPAConnectionError):
        OPAClient()


def test_opa_client_custom_url(mock_requests):
    """Test OPA client with custom URL"""
    mock_requests.get.return_value.status_code = 200
    
    client = OPAClient("http://custom:9999")
    assert client.opa_url == "http://custom:9999"


def test_check_policy_success(mock_requests):
    """Test successful policy check"""
    # Setup health check
    health_response = Mock()
    health_response.status_code = 200
    
    # Setup policy check
    policy_response = Mock()
    policy_response.json.return_value = {
        "result": {
            "allowed": True,
            "reason": "Policy allows"
        }
    }
    
    mock_requests.get.return_value = health_response
    mock_requests.post.return_value = policy_response
    
    client = OPAClient()
    result = client.check_policy("test_policy", {"user": "alice"})
    
    assert result["allowed"] is True
    assert result["reason"] == "Policy allows"


def test_check_policy_failure(mock_requests):
    """Test policy check that denies"""
    health_response = Mock()
    health_response.status_code = 200
    
    policy_response = Mock()
    policy_response.json.return_value = {
        "result": {
            "allowed": False,
            "reason": "Insufficient permissions"
        }
    }
    
    mock_requests.get.return_value = health_response
    mock_requests.post.return_value = policy_response
    
    client = OPAClient()
    result = client.check_policy("test_policy", {"user": "bob"})
    
    assert result["allowed"] is False


def test_check_policy_connection_error(mock_requests):
    """Test policy check with connection error"""
    health_response = Mock()
    health_response.status_code = 200
    
    mock_requests.get.return_value = health_response
    mock_requests.post.side_effect = requests.exceptions.ConnectionError("Connection failed")
    
    client = OPAClient()
    
    with pytest.raises(OPAConnectionError):
        client.check_policy("test_policy", {})


def test_check_policy_invalid_response(mock_requests):
    """Test policy check with invalid OPA response"""
    health_response = Mock()
    health_response.status_code = 200
    
    policy_response = Mock()
    policy_response.json.return_value = {"invalid": "response"}
    
    mock_requests.get.return_value = health_response
    mock_requests.post.return_value = policy_response
    
    client = OPAClient()
    
    with pytest.raises(OPAPolicyError):
        client.check_policy("test_policy", {})


def test_get_policy(mock_requests):
    """Test getting policy definition"""
    health_response = Mock()
    health_response.status_code = 200
    
    policy_response = Mock()
    policy_response.json.return_value = {
        "result": {
            "policy_id": "test",
            "rules": []
        }
    }
    
    mock_requests.get.return_value = health_response
    
    client = OPAClient()
    mock_requests.get.return_value = policy_response
    
    result = client.get_policy("policies/test")
    assert "result" in result


def test_publish_policy(mock_requests):
    """Test publishing a policy"""
    health_response = Mock()
    health_response.status_code = 200
    
    publish_response = Mock()
    publish_response.status_code = 200
    
    mock_requests.get.return_value = health_response
    mock_requests.put.return_value = publish_response
    
    client = OPAClient()
    result = client.publish_policy("test_policy", "policy content")
    
    assert result is True


def test_publish_policy_error(mock_requests):
    """Test policy publish error"""
    health_response = Mock()
    health_response.status_code = 200
    
    mock_requests.get.return_value = health_response
    mock_requests.put.side_effect = requests.exceptions.RequestException("Publish failed")
    
    client = OPAClient()
    
    with pytest.raises(OPAConnectionError):
        client.publish_policy("test_policy", "policy content")
