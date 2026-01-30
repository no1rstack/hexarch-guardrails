"""Tests for decision query, export, and stats commands."""

import pytest
from unittest.mock import Mock, patch
from click.testing import CliRunner
from hexarch_cli.cli import cli
from hexarch_cli.config.schemas import (
    APIConfig, OutputConfig, AuditConfig, PolicyConfig, HexarchConfig
)


@pytest.fixture
def cli_runner():
    """Fixture for CLI runner."""
    return CliRunner()


@pytest.fixture
def test_config():
    """Configuration for test environment."""
    return HexarchConfig(
        api=APIConfig(url="http://localhost:8080", token="test-token"),
        output=OutputConfig(format="table", colors=False),
        audit=AuditConfig(log_file=None),
        policy=PolicyConfig(cache_ttl=3600)
    )


@pytest.fixture
def mock_api_client():
    """Mock API client."""
    mock = Mock()
    
    # Default decision data
    mock.query_decisions.return_value = [
        {
            "decision_id": "550e8400-e29b-41d4-a716-446655440000",
            "timestamp": "2026-01-29T14:22:15Z",
            "provider": "openai",
            "decision": "ALLOW",
            "latency_ms": 123,
            "user_id": "user_123",
            "user_tier": "pro",
            "decision_reason": "Within tier limits",
            "policies_evaluated": ["ai_governance", "entitlements"]
        }
    ]
    
    # Default stats data
    mock.get_decision_stats.return_value = {
        "summary": {
            "total": 47234,
            "allowed": 44891,
            "denied": 2343
        },
        "by_provider": {
            "openai": {"count": 22334, "allow_rate": 96.2},
            "claude": {"count": 11456, "allow_rate": 93.8}
        }
    }
    
    mock.health_check.return_value = True
    
    return mock


class TestDecisionQuery:
    """Test decision query command."""
    
    def test_decision_query_no_decisions(self, cli_runner, mock_api_client, test_config):
        """Test query with no results."""
        mock_api_client.query_decisions.return_value = []
        
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, ["decision", "query", "--limit", "50"])
        
        assert result.exit_code == 0
        assert "No decisions found" in result.output
    
    def test_decision_query_with_decisions(self, cli_runner, mock_api_client, test_config):
        """Test query with results."""
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, ["decision", "query", "--limit", "50"])
        
        assert result.exit_code == 0
        assert "openai" in result.output
        assert "ALLOW" in result.output
    
    def test_decision_query_json_format(self, cli_runner, mock_api_client, test_config):
        """Test query with JSON format."""
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, ["decision", "query", "--format", "json"])
        
        assert result.exit_code == 0
        assert '"decision_id"' in result.output
        assert '"provider"' in result.output
    
    def test_decision_query_csv_format(self, cli_runner, mock_api_client, test_config):
        """Test query with CSV format."""
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, ["decision", "query", "--format", "csv"])
        
        assert result.exit_code == 0
        assert "decision_id" in result.output or "550e8400" in result.output
    
    def test_decision_query_with_filters(self, cli_runner, mock_api_client, test_config):
        """Test query with date and provider filters."""
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, [
                    "decision", "query",
                    "--from", "2026-01-01",
                    "--to", "2026-01-31",
                    "--provider", "openai"
                ])
        
        assert result.exit_code == 0
        # Verify API was called with correct params
        mock_api_client.query_decisions.assert_called()
    
    def test_decision_query_invalid_limit(self, cli_runner, mock_api_client, test_config):
        """Test query with invalid limit."""
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, ["decision", "query", "--limit", "2000"])
        
        assert result.exit_code == 2
        assert "must be between 1 and 1000" in result.output
    
    def test_decision_query_invalid_date_format(self, cli_runner, mock_api_client, test_config):
        """Test query with invalid date format."""
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, ["decision", "query", "--from", "01/01/2026"])
        
        assert result.exit_code == 2
        assert "YYYY-MM-DD" in result.output
    
    def test_decision_query_api_error(self, cli_runner, mock_api_client, test_config):
        """Test query with API error."""
        mock_api_client.query_decisions.side_effect = Exception("API Error")
        
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, ["decision", "query"])
        
        assert result.exit_code == 1
        assert "Failed to query decisions" in result.output


class TestDecisionExport:
    """Test decision export command."""
    
    def test_decision_export_no_decisions(self, cli_runner, mock_api_client, test_config):
        """Test export with no results."""
        mock_api_client.query_decisions.return_value = []
        
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, ["decision", "export"])
        
        assert result.exit_code == 0
        assert "No decisions found" in result.output
    
    def test_decision_export_to_file_json(self, cli_runner, mock_api_client, test_config):
        """Test export to JSON file."""
        with cli_runner.isolated_filesystem():
            with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
                with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                    mock_cm.return_value.get_config.return_value = test_config
                    result = cli_runner.invoke(cli, [
                        "decision", "export",
                        "--output", "decisions.json",
                        "--format", "json"
                    ])
            
            assert result.exit_code == 0
            assert "Exported" in result.output
            assert "decisions.json" in result.output
    
    def test_decision_export_to_file_csv(self, cli_runner, mock_api_client, test_config):
        """Test export to CSV file."""
        with cli_runner.isolated_filesystem():
            with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
                with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                    mock_cm.return_value.get_config.return_value = test_config
                    result = cli_runner.invoke(cli, [
                        "decision", "export",
                        "--output", "decisions.csv",
                        "--format", "csv"
                    ])
            
            assert result.exit_code == 0
            assert "Exported" in result.output
            assert "decisions.csv" in result.output
    
    def test_decision_export_stdout_json(self, cli_runner, mock_api_client, test_config):
        """Test export to stdout as JSON."""
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, ["decision", "export", "--format", "json"])
        
        assert result.exit_code == 0
        assert '"decision_id"' in result.output
    
    def test_decision_export_parquet_no_file(self, cli_runner, mock_api_client, test_config):
        """Test parquet format is not supported."""
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, [
                    "decision", "export",
                    "--format", "parquet"
                ])
        
        assert result.exit_code == 2
        assert "is not one of" in result.output or "Invalid value" in result.output
    
    def test_decision_export_with_date_filter(self, cli_runner, mock_api_client, test_config):
        """Test export with date filters."""
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, [
                    "decision", "export",
                    "--from", "2026-01-01",
                    "--to", "2026-01-31"
                ])
        
        assert result.exit_code == 0
        mock_api_client.query_decisions.assert_called()
    
    def test_decision_export_invalid_date_format(self, cli_runner, mock_api_client, test_config):
        """Test export with invalid date format."""
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, ["decision", "export", "--from", "01-01-2026"])
        
        assert result.exit_code == 2
        assert "YYYY-MM-DD" in result.output
    
    def test_decision_export_api_error(self, cli_runner, mock_api_client, test_config):
        """Test export with API error."""
        mock_api_client.query_decisions.side_effect = Exception("API Error")
        
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, ["decision", "export"])
        
        assert result.exit_code == 1
        assert "Failed to export decisions" in result.output


class TestDecisionStats:
    """Test decision stats command."""
    
    def test_decision_stats_default(self, cli_runner, mock_api_client, test_config):
        """Test stats with default parameters."""
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, ["decision", "stats"])
        
        assert result.exit_code == 0
        assert "summary" in result.output or "total" in result.output
    
    def test_decision_stats_with_date_range(self, cli_runner, mock_api_client, test_config):
        """Test stats with date range."""
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, [
                    "decision", "stats",
                    "--from", "2026-01-01",
                    "--to", "2026-01-31"
                ])
        
        assert result.exit_code == 0
        mock_api_client.get_decision_stats.assert_called()
    
    def test_decision_stats_group_by_provider(self, cli_runner, mock_api_client, test_config):
        """Test stats grouped by provider."""
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, [
                    "decision", "stats",
                    "--group-by", "provider"
                ])
        
        assert result.exit_code == 0
        mock_api_client.get_decision_stats.assert_called()
    
    def test_decision_stats_group_by_decision(self, cli_runner, mock_api_client, test_config):
        """Test stats grouped by decision."""
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, [
                    "decision", "stats",
                    "--group-by", "decision"
                ])
        
        assert result.exit_code == 0
    
    def test_decision_stats_no_data(self, cli_runner, mock_api_client, test_config):
        """Test stats with no data."""
        mock_api_client.get_decision_stats.return_value = {}
        
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, ["decision", "stats"])
        
        assert result.exit_code == 0
        assert "No decision statistics available" in result.output
    
    def test_decision_stats_invalid_date_format(self, cli_runner, mock_api_client, test_config):
        """Test stats with invalid date format."""
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, ["decision", "stats", "--from", "jan-2026"])
        
        assert result.exit_code == 2
        assert "YYYY-MM-DD" in result.output
    
    def test_decision_stats_api_error(self, cli_runner, mock_api_client, test_config):
        """Test stats with API error."""
        mock_api_client.get_decision_stats.side_effect = Exception("API Error")
        
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, ["decision", "stats"])
        
        assert result.exit_code == 1
        assert "Failed to get decision statistics" in result.output


class TestDecisionCommandIntegration:
    """Integration tests for decision commands."""
    
    def test_decision_group_exists(self, cli_runner):
        """Test decision command group exists."""
        result = cli_runner.invoke(cli, ["decision", "--help"])
        assert result.exit_code == 0
        assert "query" in result.output
        assert "export" in result.output
        assert "stats" in result.output
    
    def test_decision_query_help(self, cli_runner):
        """Test decision query help."""
        result = cli_runner.invoke(cli, ["decision", "query", "--help"])
        assert result.exit_code == 0
        assert "--from" in result.output
        assert "--to" in result.output
        assert "--provider" in result.output
    
    def test_decision_export_help(self, cli_runner):
        """Test decision export help."""
        result = cli_runner.invoke(cli, ["decision", "export", "--help"])
        assert result.exit_code == 0
        assert "--output" in result.output
        assert "--format" in result.output
    
    def test_decision_stats_help(self, cli_runner):
        """Test decision stats help."""
        result = cli_runner.invoke(cli, ["decision", "stats", "--help"])
        assert result.exit_code == 0
        assert "--group-by" in result.output
