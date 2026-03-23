from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from hexarch_cli.cli import cli
from hexarch_cli.config.schemas import HexarchConfig, APIConfig, OutputConfig, AuditConfig, PolicyConfig


@pytest.fixture
def cli_runner():
    return CliRunner()


@pytest.fixture
def test_config():
    return HexarchConfig(
        api=APIConfig(url="http://localhost:8080", token="test-token"),
        output=OutputConfig(format="table", colors=False),
        audit=AuditConfig(log_path="./test-cli-audit.log"),
        policies=PolicyConfig(cache_ttl_minutes=5),
    )


def _mock_cli_bootstrap(mock_cm, test_config):
    cm_instance = Mock()
    cm_instance.get_config.return_value = test_config
    mock_cm.return_value = cm_instance


def test_init_command_creates_demo_session_and_opens_browser(cli_runner, test_config):
    api_client = Mock()
    api_client.post.return_value = {
        "token": "demo-token",
        "expires_in": 1800,
        "session_id": "demo_abc123",
    }

    with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=api_client):
            with patch("hexarch_cli.cli.webbrowser.open") as mock_open:
                _mock_cli_bootstrap(mock_cm, test_config)
                result = cli_runner.invoke(cli, ["init"])

    assert result.exit_code == 0
    assert "Demo session created" in result.output
    mock_open.assert_called_once()
    assert "token=demo-token" in mock_open.call_args[0][0]


def test_init_command_no_open_browser_prints_url(cli_runner, test_config):
    api_client = Mock()
    api_client.post.return_value = {
        "token": "demo-token",
        "expires_in": 1800,
        "session_id": "demo_abc123",
    }

    with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=api_client):
            with patch("hexarch_cli.cli.webbrowser.open") as mock_open:
                _mock_cli_bootstrap(mock_cm, test_config)
                result = cli_runner.invoke(cli, ["init", "--no-open-browser", "--demo-url", "https://hexarch.systems/demo"])

    assert result.exit_code == 0
    assert "Browser open skipped" in result.output
    assert "https://hexarch.systems/demo?token=demo-token" in result.output
    mock_open.assert_not_called()
