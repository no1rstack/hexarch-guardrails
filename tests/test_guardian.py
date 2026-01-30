"""
Tests for Guardian class
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from hexarch_guardrails import Guardian
from hexarch_guardrails.exceptions import PolicyViolation, PolicyConfigError
import tempfile
import os


@pytest.fixture
def temp_policy_file():
    """Create a temporary policy file for testing"""
    content = """
policies:
  - id: "test_policy"
    description: "Test policy"
    rules:
      - action: "allow"
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(content)
        f.flush()
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def mock_opa_client():
    """Mock OPA client"""
    with patch('hexarch_guardrails.guardian.OPAClient') as mock:
        yield mock


def test_guardian_initialization(temp_policy_file, mock_opa_client):
    """Test Guardian initializes correctly"""
    guardian = Guardian(policy_file=temp_policy_file)
    assert guardian.policy_file == temp_policy_file
    assert "test_policy" in guardian.policies


def test_guardian_list_policies(temp_policy_file, mock_opa_client):
    """Test listing policies"""
    guardian = Guardian(policy_file=temp_policy_file)
    policies = guardian.list_policies()
    assert "test_policy" in policies


def test_guardian_get_policy(temp_policy_file, mock_opa_client):
    """Test getting policy by ID"""
    guardian = Guardian(policy_file=temp_policy_file)
    policy = guardian.get_policy("test_policy")
    assert policy["id"] == "test_policy"


def test_guardian_missing_policy_file():
    """Test error when policy file not found"""
    with pytest.raises(PolicyConfigError):
        Guardian(policy_file="/nonexistent/path/hexarch.yaml")


def test_decorator_allowed(temp_policy_file, mock_opa_client):
    """Test decorator allows execution when policy passes"""
    mock_opa = MagicMock()
    mock_opa.check_policy.return_value = {"allowed": True, "reason": "OK"}
    
    with patch('hexarch_guardrails.guardian.OPAClient', return_value=mock_opa):
        guardian = Guardian(policy_file=temp_policy_file)
        
        @guardian.check("test_policy")
        def test_func():
            return "success"
        
        result = test_func()
        assert result == "success"


def test_decorator_blocked(temp_policy_file, mock_opa_client):
    """Test decorator blocks execution when policy fails"""
    mock_opa = MagicMock()
    mock_opa.check_policy.return_value = {"allowed": False, "reason": "Policy violated"}
    
    with patch('hexarch_guardrails.guardian.OPAClient', return_value=mock_opa):
        guardian = Guardian(policy_file=temp_policy_file)
        
        @guardian.check("test_policy")
        def test_func():
            return "success"
        
        with pytest.raises(PolicyViolation):
            test_func()


def test_decorator_with_context(temp_policy_file, mock_opa_client):
    """Test decorator passes context to policy evaluation"""
    mock_opa = MagicMock()
    mock_opa.check_policy.return_value = {"allowed": True, "reason": "OK"}
    
    with patch('hexarch_guardrails.guardian.OPAClient', return_value=mock_opa):
        guardian = Guardian(policy_file=temp_policy_file)
        
        @guardian.check("test_policy", context={"user_id": "123"})
        def test_func():
            return "success"
        
        test_func()
        
        # Verify context was passed
        call_args = mock_opa.check_policy.call_args
        assert call_args[0][0] == "test_policy"
        assert call_args[0][1]["user_id"] == "123"


def test_guard_function_programmatic(temp_policy_file, mock_opa_client):
    """Test programmatic function guarding"""
    mock_opa = MagicMock()
    mock_opa.check_policy.return_value = {"allowed": True, "reason": "OK"}
    
    with patch('hexarch_guardrails.guardian.OPAClient', return_value=mock_opa):
        guardian = Guardian(policy_file=temp_policy_file)
        
        def original_func():
            return "success"
        
        guarded_func = guardian.guard_function(original_func, "test_policy")
        result = guarded_func()
        assert result == "success"


def test_unknown_policy(temp_policy_file, mock_opa_client):
    """Test error when checking unknown policy"""
    mock_opa = MagicMock()
    
    with patch('hexarch_guardrails.guardian.OPAClient', return_value=mock_opa):
        guardian = Guardian(policy_file=temp_policy_file)
        
        with pytest.raises(ValueError):
            guardian.evaluate_policy("unknown_policy", {})
