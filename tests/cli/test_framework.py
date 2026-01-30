"""Tests for CLI framework."""

import pytest
from click.testing import CliRunner
from hexarch_cli.cli import cli
from hexarch_cli.config.config import ConfigManager
from hexarch_cli.output.formatter import OutputFormatter
from hexarch_cli.config.schemas import HexarchConfig, APIConfig
from hexarch_cli import __version__


@pytest.fixture
def cli_runner():
    """Get Click CLI test runner."""
    return CliRunner()


def test_cli_version(cli_runner):
    """Test --version flag."""
    result = cli_runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_cli_help(cli_runner):
    """Test --help flag."""
    result = cli_runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Hexarch Admin CLI" in result.output
    assert "policy" in result.output or "Usage:" in result.output


class TestConfigManager:
    """Tests for configuration management."""
    
    def test_config_defaults(self):
        """Test default configuration values."""
        config = HexarchConfig()
        
        assert config.api.url == "http://localhost:8080"
        assert config.api.timeout_seconds == 30
        assert config.output.format == "table"
        assert config.output.colors is True
        assert config.audit.enabled is True


class TestOutputFormatter:
    """Tests for output formatting."""
    
    def test_format_json(self):
        """Test JSON output format."""
        formatter = OutputFormatter(format="json", colors=False)
        
        data = [{"name": "policy1", "status": "active"}]
        output = formatter.format_output(data)
        
        assert '"name"' in output
        assert '"policy1"' in output
    
    def test_format_csv(self):
        """Test CSV output format."""
        formatter = OutputFormatter(format="csv", colors=False)
        
        data = [{"name": "policy1", "status": "active"}]
        headers = ["name", "status"]
        output = formatter.format_output(data, headers=headers)
        
        assert "policy1" in output
        assert "active" in output
    
    def test_format_table(self):
        """Test table output format."""
        formatter = OutputFormatter(format="table", colors=False)
        
        data = [{"name": "policy1", "status": "active"}]
        headers = ["name", "status"]
        output = formatter.format_output(data, headers=headers)
        
        assert "policy1" in output
        assert "active" in output
    
    def test_print_success(self, capsys):
        """Test success message printing."""
        formatter = OutputFormatter(format="table", colors=False)
        formatter.print_success("Test message")
        
        captured = capsys.readouterr()
        assert "Test message" in captured.out
        assert "✓" in captured.out


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
