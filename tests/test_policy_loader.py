"""
Tests for Policy Loader
"""
import pytest
import tempfile
import os
from hexarch_guardrails.policy_loader import PolicyLoader
from hexarch_guardrails.exceptions import PolicyConfigError


def test_load_valid_policy():
    """Test loading a valid policy file"""
    content = """
policies:
  - id: "test"
    description: "Test policy"
    rules:
      - action: "allow"
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(content)
        f.flush()
        path = f.name

    config = PolicyLoader.load(path)
    assert "policies" in config
    assert len(config["policies"]) == 1
    assert config["policies"][0]["id"] == "test"

    os.unlink(path)


def test_load_missing_file():
    """Test error when policy file doesn't exist"""
    with pytest.raises(PolicyConfigError):
        PolicyLoader.load("/nonexistent/policy.yaml")


def test_load_invalid_yaml():
    """Test error when YAML is malformed"""
    content = """
policies:
  - id: "test"
    rules: [invalid yaml:::
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(content)
        f.flush()
        path = f.name

    with pytest.raises(PolicyConfigError):
        PolicyLoader.load(path)

    os.unlink(path)


def test_validate_valid_policy():
    """Test validating a valid policy"""
    config = {
        "policies": [
            {
                "id": "test",
                "rules": [{"action": "allow"}]
            }
        ]
    }
    assert PolicyLoader.validate(config) is True


def test_validate_missing_policies_section():
    """Test validation fails without policies section"""
    config = {"some_key": "value"}
    
    with pytest.raises(PolicyConfigError):
        PolicyLoader.validate(config)


def test_validate_policies_not_list():
    """Test validation fails if policies is not a list"""
    config = {"policies": "not_a_list"}
    
    with pytest.raises(PolicyConfigError):
        PolicyLoader.validate(config)


def test_validate_policy_missing_id():
    """Test validation fails if policy missing id"""
    config = {
        "policies": [
            {"rules": [{"action": "allow"}]}
        ]
    }
    
    with pytest.raises(PolicyConfigError):
        PolicyLoader.validate(config)


def test_validate_policy_missing_rules():
    """Test validation fails if policy missing rules"""
    config = {
        "policies": [
            {"id": "test"}
        ]
    }
    
    with pytest.raises(PolicyConfigError):
        PolicyLoader.validate(config)


def test_find_policy_file():
    """Test auto-discovery of policy file"""
    with tempfile.TemporaryDirectory() as tmpdir:
        policy_path = os.path.join(tmpdir, "hexarch.yaml")
        with open(policy_path, 'w') as f:
            f.write("policies: []")
        
        found = PolicyLoader.find_policy_file(tmpdir)
        assert found == policy_path


def test_find_policy_file_not_found():
    """Test policy file not found"""
    with tempfile.TemporaryDirectory() as tmpdir:
        found = PolicyLoader.find_policy_file(tmpdir)
        assert found is None


def test_load_auto_discover():
    """Test auto-discovery when loading"""
    with tempfile.TemporaryDirectory() as tmpdir:
        policy_path = os.path.join(tmpdir, "hexarch.yaml")
        with open(policy_path, 'w') as f:
            f.write("""
policies:
  - id: "test"
    rules: []
""")
        
        # Change to temp directory and load without specifying file
        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            config = PolicyLoader.load()
            assert "policies" in config
        finally:
            os.chdir(old_cwd)
