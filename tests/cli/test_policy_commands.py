"""Tests for policy commands."""

import pytest
from click.testing import CliRunner
from unittest.mock import Mock, patch
from hexarch_cli.cli import cli
from hexarch_cli.commands.policy import policy_group
from hexarch_cli.context import HexarchContext
from hexarch_cli.output.formatter import OutputFormatter
from hexarch_cli.config.config import ConfigManager
from hexarch_cli.config.schemas import HexarchConfig, APIConfig, OutputConfig, AuditConfig, PolicyConfig


@pytest.fixture
def cli_runner():
    """Get Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_api_client():
    """Create a mock API client."""
    client = Mock()
    client.list_policies.return_value = []
    client.get_policy.return_value = {
        "name": "test_policy",
        "version": "1.0.0",
        "source": "package test\n\nallow { true }"
    }
    return client


@pytest.fixture
def test_config():
    """Create a test configuration."""
    return HexarchConfig(
        api=APIConfig(url="http://localhost:8080", token="test-token"),
        output=OutputConfig(format="table", colors=False),
        audit=AuditConfig(log_file=None),
        policy=PolicyConfig(cache_ttl=3600)
    )


class TestPolicyList:
    """Tests for policy list command."""
    
    def test_policy_list_no_policies(self, cli_runner, mock_api_client, test_config):
        """Test policy list with no policies."""
        mock_api_client.list_policies.return_value = []
        
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm_instance = Mock()
                mock_cm_instance.get_config.return_value = test_config
                mock_cm.return_value = mock_cm_instance
                
                result = cli_runner.invoke(cli, ["policy", "list"])
        
        # Should succeed even with no policies
        assert result.exit_code == 0
        assert "No policies found" in result.output
    
    def test_policy_list_with_policies(self, cli_runner, mock_api_client, test_config):
        """Test policy list with policies."""
        mock_api_client.list_policies.return_value = [
            {
                "name": "ai_governance",
                "status": "active",
                "version": "1.0.0",
                "updated": "2026-01-29T12:00:00Z",
                "rule_count": 10
            },
            {
                "name": "entitlements",
                "status": "active",
                "version": "2.0.0",
                "updated": "2026-01-28T10:00:00Z",
                "rule_count": 5
            }
        ]
        
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm_instance = Mock()
                mock_cm_instance.get_config.return_value = test_config
                mock_cm.return_value = mock_cm_instance
                
                result = cli_runner.invoke(cli, ["policy", "list"])
        
        # Command should succeed
        assert result.exit_code == 0
        # Output should contain policy names
        assert "ai_governance" in result.output
        assert "entitlements" in result.output
    
    def test_policy_list_api_error(self, cli_runner, mock_api_client, test_config):
        """Test policy list with API error."""
        mock_api_client.list_policies.side_effect = Exception("Connection refused")
        
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm_instance = Mock()
                mock_cm_instance.get_config.return_value = test_config
                mock_cm.return_value = mock_cm_instance
                
                result = cli_runner.invoke(cli, ["policy", "list"])
        
        # Should exit with error code
        assert result.exit_code == 1
        assert "Failed to fetch policies" in result.output
    
    def test_policy_list_json_format(self, cli_runner, mock_api_client, test_config):
        """Test policy list with JSON format."""
        mock_api_client.list_policies.return_value = [
            {"name": "test_policy", "status": "active", "version": "1.0.0", "updated": "2026-01-29T00:00:00Z", "rule_count": 1}
        ]
        
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm_instance = Mock()
                mock_cm_instance.get_config.return_value = test_config
                mock_cm.return_value = mock_cm_instance
                
                result = cli_runner.invoke(cli, ["policy", "list", "--format", "json"])
        
        assert result.exit_code == 0




class TestPolicyExport:
    """Tests for policy export command."""
    
    def test_policy_export_single(self, cli_runner, mock_api_client, test_config):
        """Test exporting a single policy."""
        mock_api_client.get_policy.return_value = {
            "name": "ai_governance",
            "source": "package ai_governance\n\nallow { true }",
            "version": "1.0.0"
        }
        
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm_instance = Mock()
                mock_cm_instance.get_config.return_value = test_config
                mock_cm.return_value = mock_cm_instance
                
                result = cli_runner.invoke(cli, ["policy", "export", "ai_governance"])
        
        # Should succeed
        assert result.exit_code == 0
        # Should show policy source
        assert "package ai_governance" in result.output
    
    def test_policy_export_all(self, cli_runner, mock_api_client, test_config):
        """Test exporting all policies."""
        mock_api_client.list_policies.return_value = [
            {"name": "policy1", "version": "1.0.0"},
            {"name": "policy2", "version": "2.0.0"}
        ]
        
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm_instance = Mock()
                mock_cm_instance.get_config.return_value = test_config
                mock_cm.return_value = mock_cm_instance
                
                result = cli_runner.invoke(cli, ["policy", "export", "--format", "json"])
        
        # Should succeed
        assert result.exit_code == 0
    
    def test_policy_export_api_error(self, cli_runner, mock_api_client, test_config):
        """Test export with API error."""
        mock_api_client.get_policy.side_effect = Exception("Policy not found")
        
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm_instance = Mock()
                mock_cm_instance.get_config.return_value = test_config
                mock_cm.return_value = mock_cm_instance
                
                result = cli_runner.invoke(cli, ["policy", "export", "nonexistent"])
        
        # Should fail gracefully
        assert result.exit_code == 1
        assert "Failed to fetch policy" in result.output


class TestPolicyValidate:
    """Tests for policy validate command."""
    
    def test_policy_validate_valid(self, cli_runner):
        """Test validating a valid policy."""
        with cli_runner.isolated_filesystem():
            # Create a valid policy file
            with open("test.rego", "w") as f:
                f.write("package test\n\nallow :- true")
            
            result = cli_runner.invoke(cli, ["policy", "validate", "test.rego"])
            
            # Should validate successfully
            assert result.exit_code == 0
            assert "valid" in result.output.lower()
    
    def test_policy_validate_invalid(self, cli_runner):
        """Test validating an invalid policy (no package)."""
        with cli_runner.isolated_filesystem():
            # Create an invalid policy file
            with open("test.rego", "w") as f:
                f.write("allow :- true")  # Missing package declaration
            
            result = cli_runner.invoke(cli, ["policy", "validate", "test.rego"])
            
            # Should fail
            assert result.exit_code == 1
            assert "package" in result.output.lower() or "failed" in result.output.lower()
    
    def test_policy_validate_missing_file(self, cli_runner):
        """Test validating a missing file."""
        result = cli_runner.invoke(cli, ["policy", "validate", "nonexistent.rego"])
        
        # Click handles missing files with exit code 2
        assert result.exit_code == 2


class TestPolicyDiff:
    """Tests for policy diff command."""
    
    def test_policy_diff_current_version(self, cli_runner, mock_api_client, test_config):
        """Test policy diff showing current version."""
        mock_api_client.get_policy.return_value = {
            "name": "ai_governance",
            "version": "1.2.3",
            "source": "package ai_governance\n\nallow { true }"
        }
        
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm_instance = Mock()
                mock_cm_instance.get_config.return_value = test_config
                mock_cm.return_value = mock_cm_instance
                
                result = cli_runner.invoke(cli, ["policy", "diff", "ai_governance"])
        
        # Should succeed
        assert result.exit_code == 0
        # Should show policy info
        assert "ai_governance" in result.output
        assert "1.2.3" in result.output


class TestPolicyCommandIntegration:
    """Integration tests for policy commands."""
    
    def test_policy_group_exists(self):
        """Test that policy command group is registered."""
        assert policy_group is not None
        assert policy_group.name == "policy"
    
    def test_policy_help(self, cli_runner):
        """Test policy help text."""
        result = cli_runner.invoke(cli, ["policy", "--help"])
        
        assert result.exit_code == 0
        assert "list" in result.output
        assert "export" in result.output
        assert "validate" in result.output
        assert "diff" in result.output

