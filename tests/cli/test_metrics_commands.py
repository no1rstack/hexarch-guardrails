"""Tests for metrics show, export, and trends commands."""

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

    mock.get_metrics.return_value = {
        "providers": [
            {
                "provider": "openai",
                "requests": 5234,
                "avg_latency_ms": 98,
                "p95_ms": 234,
                "p99_ms": 456,
                "error_rate": 0.2
            },
            {
                "provider": "claude",
                "requests": 2156,
                "avg_latency_ms": 112,
                "p95_ms": 267,
                "p99_ms": 512,
                "error_rate": 0.1
            }
        ]
    }

    mock.get_metrics_trends.return_value = {
        "series": [
            {"timestamp": "2026-01-29T00:00:00Z", "value": 120, "provider": "openai"},
            {"timestamp": "2026-01-29T01:00:00Z", "value": 110, "provider": "openai"}
        ]
    }

    mock.health_check.return_value = True

    return mock


class TestMetricsShow:
    """Test metrics show command."""

    def test_metrics_show_default(self, cli_runner, mock_api_client, test_config):
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, ["metrics", "show"])

        assert result.exit_code == 0
        assert "openai" in result.output
        assert "claude" in result.output

    def test_metrics_show_json_format(self, cli_runner, mock_api_client, test_config):
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, ["--format", "json", "metrics", "show"])

        assert result.exit_code == 0
        assert "providers" in result.output

    def test_metrics_show_csv_format(self, cli_runner, mock_api_client, test_config):
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, ["--format", "csv", "metrics", "show"])

        assert result.exit_code == 0
        assert "provider" in result.output

    def test_metrics_show_date_range(self, cli_runner, mock_api_client, test_config):
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, [
                    "metrics", "show",
                    "--from", "2026-01-01",
                    "--to", "2026-01-31"
                ])

        assert result.exit_code == 0
        mock_api_client.get_metrics.assert_called()

    def test_metrics_show_invalid_date(self, cli_runner, mock_api_client, test_config):
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, ["metrics", "show", "--from", "01-01-2026"])

        assert result.exit_code == 2
        assert "YYYY-MM-DD" in result.output

    def test_metrics_show_no_data(self, cli_runner, mock_api_client, test_config):
        mock_api_client.get_metrics.return_value = {}

        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, ["metrics", "show"])

        assert result.exit_code == 0
        assert "No metrics available" in result.output

    def test_metrics_show_api_error(self, cli_runner, mock_api_client, test_config):
        mock_api_client.get_metrics.side_effect = Exception("API Error")

        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, ["metrics", "show"])

        assert result.exit_code == 1
        assert "Failed to get metrics" in result.output


class TestMetricsExport:
    """Test metrics export command."""

    def test_metrics_export_stdout_json(self, cli_runner, mock_api_client, test_config):
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, ["metrics", "export", "--format", "json"])

        assert result.exit_code == 0
        assert "providers" in result.output

    def test_metrics_export_stdout_csv(self, cli_runner, mock_api_client, test_config):
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, ["metrics", "export", "--format", "csv"])

        assert result.exit_code == 0
        assert "provider" in result.output

    def test_metrics_export_to_file_json(self, cli_runner, mock_api_client, test_config):
        with cli_runner.isolated_filesystem():
            with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
                with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                    mock_cm.return_value.get_config.return_value = test_config
                    result = cli_runner.invoke(cli, [
                        "metrics", "export",
                        "--format", "json",
                        "--output", "metrics.json"
                    ])

            assert result.exit_code == 0
            assert "Exported metrics" in result.output

    def test_metrics_export_to_file_csv(self, cli_runner, mock_api_client, test_config):
        with cli_runner.isolated_filesystem():
            with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
                with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                    mock_cm.return_value.get_config.return_value = test_config
                    result = cli_runner.invoke(cli, [
                        "metrics", "export",
                        "--format", "csv",
                        "--output", "metrics.csv"
                    ])

            assert result.exit_code == 0
            assert "Exported metrics" in result.output

    def test_metrics_export_prometheus_requires_file(self, cli_runner, mock_api_client, test_config):
        mock_api_client.get_metrics.return_value = {"prometheus": "metric_name 1"}

        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, ["metrics", "export", "--format", "prometheus"])

        assert result.exit_code == 2
        assert "requires --output" in result.output

    def test_metrics_export_prometheus_to_file(self, cli_runner, mock_api_client, test_config):
        mock_api_client.get_metrics.return_value = {"prometheus": "metric_name 1"}

        with cli_runner.isolated_filesystem():
            with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
                with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                    mock_cm.return_value.get_config.return_value = test_config
                    result = cli_runner.invoke(cli, [
                        "metrics", "export",
                        "--format", "prometheus",
                        "--output", "metrics.txt"
                    ])

            assert result.exit_code == 0
            assert "Exported metrics" in result.output

    def test_metrics_export_invalid_date(self, cli_runner, mock_api_client, test_config):
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, ["metrics", "export", "--from", "2026/01/01"])

        assert result.exit_code == 2
        assert "YYYY-MM-DD" in result.output

    def test_metrics_export_no_data(self, cli_runner, mock_api_client, test_config):
        mock_api_client.get_metrics.return_value = {}

        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, ["metrics", "export"])

        assert result.exit_code == 0
        assert "No metrics available" in result.output

    def test_metrics_export_api_error(self, cli_runner, mock_api_client, test_config):
        mock_api_client.get_metrics.side_effect = Exception("API Error")

        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, ["metrics", "export"])

        assert result.exit_code == 1
        assert "Failed to export metrics" in result.output


class TestMetricsTrends:
    """Test metrics trends command."""

    def test_metrics_trends_default(self, cli_runner, mock_api_client, test_config):
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, ["metrics", "trends"])

        assert result.exit_code == 0
        assert "openai" in result.output or "series" in result.output

    def test_metrics_trends_json_format(self, cli_runner, mock_api_client, test_config):
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, ["--format", "json", "metrics", "trends"])

        assert result.exit_code == 0
        assert "series" in result.output

    def test_metrics_trends_csv_format(self, cli_runner, mock_api_client, test_config):
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, ["--format", "csv", "metrics", "trends"])

        assert result.exit_code == 0
        assert "timestamp" in result.output

    def test_metrics_trends_with_filters(self, cli_runner, mock_api_client, test_config):
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, [
                    "metrics", "trends",
                    "--provider", "openai",
                    "--metric", "latency_ms",
                    "--time-window", "1d"
                ])

        assert result.exit_code == 0
        mock_api_client.get_metrics_trends.assert_called()

    def test_metrics_trends_invalid_date(self, cli_runner, mock_api_client, test_config):
        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, ["metrics", "trends", "--from", "2026.01.01"])

        assert result.exit_code == 2
        assert "YYYY-MM-DD" in result.output

    def test_metrics_trends_no_data(self, cli_runner, mock_api_client, test_config):
        mock_api_client.get_metrics_trends.return_value = {}

        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, ["metrics", "trends"])

        assert result.exit_code == 0
        assert "No trend data" in result.output

    def test_metrics_trends_api_error(self, cli_runner, mock_api_client, test_config):
        mock_api_client.get_metrics_trends.side_effect = Exception("API Error")

        with patch("hexarch_cli.cli.HexarchAPIClient", return_value=mock_api_client):
            with patch("hexarch_cli.cli.ConfigManager") as mock_cm:
                mock_cm.return_value.get_config.return_value = test_config
                result = cli_runner.invoke(cli, ["metrics", "trends"])

        assert result.exit_code == 1
        assert "Failed to get metrics trends" in result.output


class TestMetricsCommandIntegration:
    """Integration tests for metrics commands."""

    def test_metrics_group_exists(self, cli_runner):
        result = cli_runner.invoke(cli, ["metrics", "--help"])
        assert result.exit_code == 0
        assert "show" in result.output
        assert "export" in result.output
        assert "trends" in result.output

    def test_metrics_show_help(self, cli_runner):
        result = cli_runner.invoke(cli, ["metrics", "show", "--help"])
        assert result.exit_code == 0
        assert "--time-window" in result.output

    def test_metrics_export_help(self, cli_runner):
        result = cli_runner.invoke(cli, ["metrics", "export", "--help"])
        assert result.exit_code == 0
        assert "--format" in result.output
        assert "--output" in result.output

    def test_metrics_trends_help(self, cli_runner):
        result = cli_runner.invoke(cli, ["metrics", "trends", "--help"])
        assert result.exit_code == 0
        assert "--metric" in result.output
