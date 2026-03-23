"""Tests for runtime policy CLI commands."""

import json
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


def test_policy_profiles_lists_packaged_profiles(cli_runner, test_config):
    with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=Mock()):
            _mock_cli_bootstrap(mock_cm, test_config)
            result = cli_runner.invoke(cli, ["policy", "profiles"])

    assert result.exit_code == 0
    assert "default" in result.output
    assert "strict" in result.output
    assert "permissive" in result.output


def test_policy_status_shows_runtime_settings(cli_runner, test_config):
    with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=Mock()):
            _mock_cli_bootstrap(mock_cm, test_config)
            result = cli_runner.invoke(cli, ["policy", "status", "--profile", "strict", "--engine-mode", "local"])

    assert result.exit_code == 0
    assert "strict" in result.output
    assert "local" in result.output


def test_policy_status_uses_configured_runtime_defaults(cli_runner, test_config):
    test_config.policies.profile = "strict"
    test_config.policies.engine_mode = "local"
    test_config.policies.merge_mode = "replace"
    test_config.policies.opa_url = "http://localhost:8282"

    with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=Mock()):
            _mock_cli_bootstrap(mock_cm, test_config)
            result = cli_runner.invoke(cli, ["policy", "status"])

    assert result.exit_code == 0
    assert "strict" in result.output
    assert "local" in result.output
    assert "replace" in result.output
    assert "8282" in result.output


def test_eval_command_outputs_decision_json(cli_runner, test_config):
    with cli_runner.isolated_filesystem():
        with open("input.json", "w", encoding="utf-8") as handle:
            json.dump({"method": "GET", "path": "/health", "identity": {"role": "user"}}, handle)

        with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
            with patch("hexarch_cli.cli.HexarchAPIClient", return_value=Mock()):
                with patch("hexarch_cli.commands.policy._evaluate_runtime_policy", return_value={"allow": True, "error": None, "raw": True}):
                    _mock_cli_bootstrap(mock_cm, test_config)
                    result = cli_runner.invoke(cli, ["eval", "input.json"])

    assert result.exit_code == 0
    assert '"allow": true' in result.output.lower()


def test_eval_command_uses_configured_runtime_defaults(cli_runner, test_config):
    test_config.policies.profile = "strict"
    test_config.policies.policy_path = "./override.rego"
    test_config.policies.merge_mode = "replace"
    test_config.policies.engine_mode = "local"
    test_config.policies.opa_url = "http://localhost:8282"
    test_config.policies.fail_closed = True

    with cli_runner.isolated_filesystem():
        with open("input.json", "w", encoding="utf-8") as handle:
            json.dump({"path": "/health"}, handle)

        with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
            with patch("hexarch_cli.cli.HexarchAPIClient", return_value=Mock()):
                with patch("hexarch_cli.commands.policy._evaluate_runtime_policy", return_value={"allow": True, "error": None, "raw": True}) as mock_eval:
                    _mock_cli_bootstrap(mock_cm, test_config)
                    result = cli_runner.invoke(cli, ["eval", "input.json"])

        args, kwargs = mock_eval.call_args
    assert result.exit_code == 0
    assert args[0] is not None
    assert kwargs["profile"] is None
    assert kwargs["policy_path"] is None
    assert kwargs["merge_mode"] is None
    assert kwargs["engine_mode"] is None
    assert kwargs["opa_url"] is None
    assert kwargs["fail_closed"] is None


def test_enforce_command_denies_with_exit_code_one(cli_runner, test_config):
    with cli_runner.isolated_filesystem():
        with open("input.json", "w", encoding="utf-8") as handle:
            json.dump({"path": "/admin"}, handle)

        with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
            with patch("hexarch_cli.cli.HexarchAPIClient", return_value=Mock()):
                with patch("hexarch_cli.commands.policy._evaluate_runtime_policy", return_value={"allow": False, "error": None, "raw": False}):
                    _mock_cli_bootstrap(mock_cm, test_config)
                    result = cli_runner.invoke(cli, ["enforce", "input.json"])

    assert result.exit_code == 1
    assert "denied" in result.output.lower()


def test_enforce_command_runs_subprocess_when_allowed(cli_runner, test_config):
    with cli_runner.isolated_filesystem():
        with open("input.json", "w", encoding="utf-8") as handle:
            json.dump({"path": "/ok"}, handle)

        proc = Mock()
        proc.returncode = 0

        with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
            with patch("hexarch_cli.cli.HexarchAPIClient", return_value=Mock()):
                with patch("hexarch_cli.commands.policy._evaluate_runtime_policy", return_value={"allow": True, "error": None, "raw": True}):
                    with patch("hexarch_cli.commands.policy.subprocess.run", return_value=proc) as mock_run:
                        _mock_cli_bootstrap(mock_cm, test_config)
                        result = cli_runner.invoke(cli, ["enforce", "input.json", "echo", "hello"])

        mock_run.assert_called_once()
    assert result.exit_code == 0
