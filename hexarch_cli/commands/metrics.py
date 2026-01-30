"""Metrics show, export, and trends commands."""

import sys
import json
import csv
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Optional, Any, Dict, List
import click
from hexarch_cli.context import HexarchContext


def _validate_date(date_value: Optional[str], flag_name: str) -> None:
    if date_value:
        try:
            datetime.strptime(date_value, "%Y-%m-%d")
        except ValueError:
            click.echo(f"Error: {flag_name} must be YYYY-MM-DD format", err=True)
            sys.exit(2)


def _extract_provider_rows(metrics: Any) -> List[Dict[str, Any]]:
    if isinstance(metrics, list):
        return metrics
    if isinstance(metrics, dict):
        providers = metrics.get("providers")
        if isinstance(providers, list):
            return providers
        data = metrics.get("data")
        if isinstance(data, list):
            return data
    return []


@click.group(name="metrics")
def metrics_group() -> None:
    """View and export provider performance metrics."""
    pass


@metrics_group.command(name="show")
@click.option("--from", "from_date", type=str, default=None, help="Start date (YYYY-MM-DD)")
@click.option("--to", "to_date", type=str, default=None, help="End date (YYYY-MM-DD)")
@click.option("--time-window", type=click.Choice(["1h", "1d", "7d"]), default=None, help="Time window")
@click.pass_context
def metrics_show(
    click_ctx: click.Context,
    from_date: Optional[str],
    to_date: Optional[str],
    time_window: Optional[str]
) -> None:
    """Display provider performance metrics."""
    if not click_ctx.obj:
        click.echo("Error: CLI context not initialized", err=True)
        sys.exit(1)

    ctx: HexarchContext = click_ctx.obj
    formatter = ctx.formatter

    try:
        _validate_date(from_date, "--from")
        _validate_date(to_date, "--to")

        query_params: Dict[str, Any] = {}
        if from_date:
            query_params["date_from"] = from_date
        if to_date:
            query_params["date_to"] = to_date
        if time_window:
            query_params["time_window"] = time_window

        metrics = ctx.api_client.get_metrics(**query_params)

        if not metrics:
            click.echo("No metrics available for the specified range.", err=False)
            sys.exit(0)

        output_format = formatter.format

        if output_format == "json":
            click.echo(json.dumps(metrics, indent=2, default=str))
        else:
            rows = _extract_provider_rows(metrics)
            if rows:
                headers = ["provider", "requests", "avg_latency_ms", "p95_ms", "p99_ms", "error_rate"]
                if output_format == "csv":
                    output = StringIO()
                    writer = csv.DictWriter(output, fieldnames=headers)
                    writer.writeheader()
                    writer.writerows(rows)
                    click.echo(output.getvalue())
                else:
                    formatted = formatter.format_output(rows, headers=headers)
                    click.echo(formatted)
            else:
                click.echo(json.dumps(metrics, indent=2, default=str))

        ctx.audit_logger.log_command(
            command="metrics show",
            args=query_params,
            result="Metrics retrieved"
        )

    except Exception as e:
        formatter.print_error(f"Failed to get metrics: {str(e)}")
        ctx.audit_logger.log_command(
            command="metrics show",
            error=str(e)
        )
        sys.exit(1)


@metrics_group.command(name="export")
@click.option("--from", "from_date", type=str, default=None, help="Start date (YYYY-MM-DD)")
@click.option("--to", "to_date", type=str, default=None, help="End date (YYYY-MM-DD)")
@click.option("--output", "-o", type=click.Path(), required=False, help="Output file path (optional, defaults to stdout)")
@click.option("--format", type=click.Choice(["json", "csv", "prometheus"]), default="json", help="Export format")
@click.pass_context
def metrics_export(
    click_ctx: click.Context,
    from_date: Optional[str],
    to_date: Optional[str],
    output: Optional[str],
    format: str
) -> None:
    """Export metrics to file for analysis."""
    if not click_ctx.obj:
        click.echo("Error: CLI context not initialized", err=True)
        sys.exit(1)

    ctx: HexarchContext = click_ctx.obj
    formatter = ctx.formatter

    try:
        _validate_date(from_date, "--from")
        _validate_date(to_date, "--to")

        query_params: Dict[str, Any] = {}
        if from_date:
            query_params["date_from"] = from_date
        if to_date:
            query_params["date_to"] = to_date

        metrics = ctx.api_client.get_metrics(**query_params)

        if not metrics:
            click.echo("No metrics available for the specified range.", err=False)
            sys.exit(0)

        if format == "prometheus":
            if isinstance(metrics, dict) and "prometheus" in metrics:
                prometheus_text = metrics["prometheus"]
            elif isinstance(metrics, str):
                prometheus_text = metrics
            else:
                click.echo("Error: Prometheus export not supported for this response", err=True)
                sys.exit(1)

            if not output:
                click.echo("Error: Prometheus format requires --output file", err=True)
                sys.exit(2)

            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(prometheus_text)
            formatter.print_success(f"Exported metrics to {output_path}")
        else:
            if output:
                output_path = Path(output)
                output_path.parent.mkdir(parents=True, exist_ok=True)

                if format == "json":
                    output_path.write_text(json.dumps(metrics, indent=2, default=str))
                else:
                    rows = _extract_provider_rows(metrics)
                    if not rows:
                        click.echo("Error: No tabular metrics available for CSV export", err=True)
                        sys.exit(1)
                    headers = ["provider", "requests", "avg_latency_ms", "p95_ms", "p99_ms", "error_rate"]
                    with open(output_path, "w", newline="") as csv_file:
                        writer = csv.DictWriter(csv_file, fieldnames=headers)
                        writer.writeheader()
                        writer.writerows(rows)

                formatter.print_success(f"Exported metrics to {output_path}")
            else:
                if format == "json":
                    click.echo(json.dumps(metrics, indent=2, default=str))
                else:
                    rows = _extract_provider_rows(metrics)
                    if not rows:
                        click.echo("Error: No tabular metrics available for CSV export", err=True)
                        sys.exit(1)
                    output = StringIO()
                    headers = ["provider", "requests", "avg_latency_ms", "p95_ms", "p99_ms", "error_rate"]
                    writer = csv.DictWriter(output, fieldnames=headers)
                    writer.writeheader()
                    writer.writerows(rows)
                    click.echo(output.getvalue())

        ctx.audit_logger.log_command(
            command="metrics export",
            args={**query_params, "format": format, "output": output or "stdout"},
            result="Metrics exported"
        )

    except Exception as e:
        formatter.print_error(f"Failed to export metrics: {str(e)}")
        ctx.audit_logger.log_command(
            command="metrics export",
            error=str(e)
        )
        sys.exit(1)


@metrics_group.command(name="trends")
@click.option("--from", "from_date", type=str, default=None, help="Start date (YYYY-MM-DD)")
@click.option("--to", "to_date", type=str, default=None, help="End date (YYYY-MM-DD)")
@click.option("--time-window", type=click.Choice(["1h", "1d", "7d"]), default=None, help="Time window")
@click.option("--provider", type=str, default=None, help="Filter by provider name")
@click.option("--metric", type=click.Choice(["latency_ms", "error_rate", "requests"]), default="latency_ms", help="Metric to trend")
@click.pass_context
def metrics_trends(
    click_ctx: click.Context,
    from_date: Optional[str],
    to_date: Optional[str],
    time_window: Optional[str],
    provider: Optional[str],
    metric: str
) -> None:
    """Show metrics trends for a time range."""
    if not click_ctx.obj:
        click.echo("Error: CLI context not initialized", err=True)
        sys.exit(1)

    ctx: HexarchContext = click_ctx.obj
    formatter = ctx.formatter

    try:
        _validate_date(from_date, "--from")
        _validate_date(to_date, "--to")

        query_params: Dict[str, Any] = {"metric": metric}
        if from_date:
            query_params["date_from"] = from_date
        if to_date:
            query_params["date_to"] = to_date
        if time_window:
            query_params["time_window"] = time_window
        if provider:
            query_params["provider"] = provider

        trends = ctx.api_client.get_metrics_trends(**query_params)

        if not trends:
            click.echo("No trend data available for the specified range.", err=False)
            sys.exit(0)

        output_format = formatter.format

        if output_format == "json":
            click.echo(json.dumps(trends, indent=2, default=str))
        else:
            series = []
            if isinstance(trends, dict):
                series = trends.get("series", [])
            elif isinstance(trends, list):
                series = trends

            if series:
                headers = ["timestamp", "value", "provider"]
                if output_format == "csv":
                    output = StringIO()
                    writer = csv.DictWriter(output, fieldnames=headers)
                    writer.writeheader()
                    writer.writerows(series)
                    click.echo(output.getvalue())
                else:
                    formatted = formatter.format_output(series, headers=headers)
                    click.echo(formatted)
            else:
                click.echo(json.dumps(trends, indent=2, default=str))

        ctx.audit_logger.log_command(
            command="metrics trends",
            args=query_params,
            result="Trend data retrieved"
        )

    except Exception as e:
        formatter.print_error(f"Failed to get metrics trends: {str(e)}")
        ctx.audit_logger.log_command(
            command="metrics trends",
            error=str(e)
        )
        sys.exit(1)


__all__ = ["metrics_group"]
