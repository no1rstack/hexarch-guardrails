"""Trace inspection commands for execution traceability."""

import sys
import json
from typing import Optional
import click
from hexarch_cli.context import HexarchContext
from hexarch_cli.output.formatter import OutputFormatter


@click.group(name="trace")
def trace_group() -> None:
    """Inspect structured execution traces."""
    pass


@trace_group.command(name="list")
@click.option("--entity-type", type=str, default=None, help="Filter by entity type")
@click.option("--entity-id", type=str, default=None, help="Filter by entity ID")
@click.option("--actor-id", type=str, default=None, help="Filter by actor ID")
@click.option("--action", type=str, default=None, help="Filter by action")
@click.option("--decision", type=str, default=None, help="Filter by decision")
@click.option("--limit", type=int, default=50, help="Maximum traces to return")
@click.option("--offset", type=int, default=0, help="Pagination offset")
@click.option("--format", "output_format", type=click.Choice(["json", "table", "csv"]), default=None, help="Output format")
@click.pass_context
def trace_list(
    click_ctx: click.Context,
    entity_type: Optional[str],
    entity_id: Optional[str],
    actor_id: Optional[str],
    action: Optional[str],
    decision: Optional[str],
    limit: int,
    offset: int,
    output_format: Optional[str],
) -> None:
    """List structured traces from the API."""
    if not click_ctx.obj:
        click.echo("Error: CLI context not initialized", err=True)
        sys.exit(1)

    ctx: HexarchContext = click_ctx.obj
    formatter = ctx.formatter
    if output_format:
        formatter = OutputFormatter(format=output_format, colors=ctx.config_manager.get_config().output.colors)

    if limit < 1:
        click.echo("Error: --limit must be >= 1", err=True)
        sys.exit(2)
    if offset < 0:
        click.echo("Error: --offset must be >= 0", err=True)
        sys.exit(2)

    query_args = {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "actor_id": actor_id,
        "action": action,
        "decision": decision,
        "limit": limit,
        "offset": offset,
    }

    try:
        traces = ctx.api_client.list_traces(**query_args)

        if formatter.format == "table":
            headers = ["TRACE_ID", "TIMESTAMP", "ACTION", "ENTITY_TYPE", "ENTITY_ID", "DECISION"]
            data = [
                [
                    t.get("trace_id"),
                    t.get("timestamp"),
                    (t.get("input") or {}).get("action"),
                    (t.get("input") or {}).get("entity_type"),
                    (t.get("input") or {}).get("entity_id"),
                    t.get("decision"),
                ]
                for t in traces
            ]
            click.echo(formatter.format_output(data, headers=headers))
        else:
            click.echo(json.dumps(traces, indent=2, default=str))

        ctx.audit_logger.log_command(
            command="trace list",
            args={k: v for k, v in query_args.items() if v is not None},
            result=f"Returned {len(traces)} traces",
        )
    except Exception as exc:
        ctx.formatter.print_error(f"Failed to list traces: {str(exc)}")
        ctx.audit_logger.log_command(command="trace list", error=str(exc))
        sys.exit(1)


@trace_group.command(name="get")
@click.argument("trace-id")
@click.option("--format", "output_format", type=click.Choice(["json", "table", "csv"]), default=None, help="Output format")
@click.pass_context
def trace_get(click_ctx: click.Context, trace_id: str, output_format: Optional[str]) -> None:
    """Get a single trace by trace ID."""
    if not click_ctx.obj:
        click.echo("Error: CLI context not initialized", err=True)
        sys.exit(1)

    ctx: HexarchContext = click_ctx.obj
    formatter = ctx.formatter
    if output_format:
        formatter = OutputFormatter(format=output_format, colors=ctx.config_manager.get_config().output.colors)

    try:
        trace = ctx.api_client.get_trace(trace_id)

        if formatter.format == "table":
            input_data = trace.get("input") or {}
            output_data = trace.get("output") or {}
            headers = ["FIELD", "VALUE"]
            data = [
                ["trace_id", trace.get("trace_id")],
                ["timestamp", trace.get("timestamp")],
                ["decision", trace.get("decision")],
                ["action", input_data.get("action")],
                ["entity_type", input_data.get("entity_type")],
                ["entity_id", input_data.get("entity_id")],
                ["reason", output_data.get("reason")],
            ]
            click.echo(formatter.format_output(data, headers=headers))
        else:
            click.echo(json.dumps(trace, indent=2, default=str))

        ctx.audit_logger.log_command(command="trace get", args={"trace_id": trace_id}, result="ok")
    except Exception as exc:
        ctx.formatter.print_error(f"Failed to get trace: {str(exc)}")
        ctx.audit_logger.log_command(command="trace get", args={"trace_id": trace_id}, error=str(exc))
        sys.exit(1)
