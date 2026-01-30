"""Tests for config init, set, and validate commands."""

from pathlib import Path
import yaml
import pytest
from unittest.mock import patch
from click.testing import CliRunner
from hexarch_cli.cli import cli
from hexarch_cli.config.config import ConfigManager
from hexarch_cli.config.schemas import (
    APIConfig, OutputConfig, AuditConfig, PolicyConfig, HexarchConfig
)


@pytest.fixture
def cli_runner():
    return CliRunner()


@pytest.fixture
def test_config():
    return HexarchConfig(
        api=APIConfig(url="http://localhost:8080", token="test-token"),
        output=OutputConfig(format="table", colors=False),
        audit=AuditConfig(enabled=False),
        policies=PolicyConfig(cache_ttl_minutes=5)
    )


def test_config_init_creates_file(cli_runner, test_config):
    # Prompts (in order): api_url, api_token, output_format, colors, audit_enabled,
    # audit_log_path, db_provider, db_url, sqlite_db_path
    user_input = "https://api.hexarch.io\n\njson\ny\ny\n\n\n\n\n"

    with cli_runner.isolated_filesystem():
        with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
            mock_cm.return_value.get_config.return_value = test_config
            with patch.object(ConfigManager, "validate_connectivity", return_value=(True, "ok")):
                result = cli_runner.invoke(cli, ["config", "init", "--output", "config.yml"], input=user_input)

        assert result.exit_code == 0
        assert "Configuration saved" in result.output

        output_path = Path("config.yml")
        assert output_path.exists()

        data = yaml.safe_load(output_path.read_text())
        assert data["api"]["url"] == "https://api.hexarch.io"
        assert data["output"]["format"] == "json"
        assert data["api"]["token"] == "${HEXARCH_API_TOKEN}"


def test_config_init_default_path(cli_runner, test_config):
    user_input = "http://localhost:8080\n\njson\ny\ny\n\n\n\n\n"

    with cli_runner.isolated_filesystem():
        with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
            mock_cm.return_value.get_config.return_value = test_config
            with patch.object(ConfigManager, "DEFAULT_CONFIG_FILE", Path("config.yml")):
                with patch.object(ConfigManager, "validate_connectivity", return_value=(True, "ok")):
                    result = cli_runner.invoke(cli, ["config", "init"], input=user_input)

        assert result.exit_code == 0
        assert "Configuration saved" in result.output


def test_config_init_help(cli_runner):
    result = cli_runner.invoke(cli, ["config", "init", "--help"])
    assert result.exit_code == 0
    assert "--output" in result.output


def test_config_set_updates_file(cli_runner, test_config):
    with cli_runner.isolated_filesystem():
        config_path = Path("config.yml")
        with open(config_path, "w") as f:
            yaml.safe_dump(test_config.model_dump(exclude_none=True), f, default_flow_style=False)

        with patch.object(ConfigManager, "DEFAULT_CONFIG_FILE", config_path):
            result = cli_runner.invoke(cli, [
                "config", "set",
                "--api-url", "https://prod.hexarch.io",
                "--format", "csv"
            ])

        assert result.exit_code == 0
        data = yaml.safe_load(config_path.read_text())
        assert data["api"]["url"] == "https://prod.hexarch.io"
        assert data["output"]["format"] == "csv"


def test_config_set_no_updates(cli_runner):
    result = cli_runner.invoke(cli, ["config", "set"])
    assert result.exit_code == 0
    assert "No configuration updates" in result.output


def test_config_validate_success(cli_runner, test_config):
    with cli_runner.isolated_filesystem():
        config_path = Path("config.yml")
        with open(config_path, "w") as f:
            yaml.safe_dump(test_config.model_dump(exclude_none=True), f, default_flow_style=False)

        with patch.object(ConfigManager, "validate_connectivity", return_value=(True, "ok")):
            result = cli_runner.invoke(cli, ["config", "validate", "--config", "config.yml"])

        assert result.exit_code == 0
        assert "Configuration is valid" in result.output


def test_config_validate_missing_file(cli_runner):
    result = cli_runner.invoke(cli, ["config", "validate", "--config", "missing.yml"])
    assert result.exit_code == 1
    assert "Config file not found" in result.output
