"""Decision query, export, and analytics commands."""

import sys
import json
import csv
import os
from datetime import datetime
from io import StringIO
from typing import Optional
from pathlib import Path
import click
from hexarch_cli.context import HexarchContext
from hexarch_cli.db import DatabaseManager
from hexarch_cli.models import Decision
from hexarch_cli.output.formatter import OutputFormatter


@click.group(name="decision")
def decision_group() -> None:
    """Query and analyze decision logs."""
    pass


@decision_group.command(name="db-list")
@click.option("--limit", type=int, default=50, help="Max results")
@click.option("--format", "output_format", type=click.Choice(["json", "table", "csv"]), default=None, help="Output format")
@click.option("--db-url", default=None, help="Override database URL")
@click.pass_context
def decision_db_list(click_ctx: click.Context, limit: int, output_format: Optional[str], db_url: Optional[str]) -> None:
    """List decisions from the local database."""
    if not click_ctx.obj:
        click.echo("Error: CLI context not initialized", err=True)
        sys.exit(1)

    ctx: HexarchContext = click_ctx.obj
    formatter = ctx.formatter
    if output_format:
        formatter = OutputFormatter(format=output_format, colors=ctx.config_manager.get_config().output.colors)

    _init_db(ctx, db_url)
    session = DatabaseManager.get_session()
    decisions = (
        session.query(Decision)
        .filter(Decision.is_deleted == False)
        .order_by(Decision.created_at.desc())
        .limit(limit)
        .all()
    )

    if formatter.format == "table":
        headers = ["ID", "NAME", "STATE", "ENTITLEMENT", "POLICY", "PRIORITY"]
        data = [[d.id, d.name, d.state, d.entitlement_id, d.policy_id, d.priority] for d in decisions]
        click.echo(formatter.format_output(data, headers=headers))
    else:
        click.echo(json.dumps([d.to_dict() for d in decisions], indent=2, default=str))

    ctx.audit_logger.log_command("decision db-list", result=f"{len(decisions)} decisions")


@decision_group.command(name="db-get")
@click.argument("decision-id")
@click.option("--format", "output_format", type=click.Choice(["json", "table", "csv"]), default=None, help="Output format")
@click.option("--db-url", default=None, help="Override database URL")
@click.pass_context
def decision_db_get(click_ctx: click.Context, decision_id: str, output_format: Optional[str], db_url: Optional[str]) -> None:
    """Get a decision by ID from the local database."""
    if not click_ctx.obj:
        click.echo("Error: CLI context not initialized", err=True)
        sys.exit(1)

    ctx: HexarchContext = click_ctx.obj
    formatter = ctx.formatter
    if output_format:
        formatter = OutputFormatter(format=output_format, colors=ctx.config_manager.get_config().output.colors)

    _init_db(ctx, db_url)
    session = DatabaseManager.get_session()
    decision = session.query(Decision).filter(Decision.id == decision_id, Decision.is_deleted == False).first()

    if not decision:
        formatter.print_error(f"Decision not found: {decision_id}")
        sys.exit(1)

    if formatter.format == "table":
        headers = ["FIELD", "VALUE"]
        data = [[k, v] for k, v in decision.to_dict().items()]
        click.echo(formatter.format_output(data, headers=headers))
    else:
        click.echo(json.dumps(decision.to_dict(), indent=2, default=str))

    ctx.audit_logger.log_command("decision db-get", result=decision_id)


@decision_group.command(name="db-create")
@click.option("--file", "decision_file", type=click.Path(exists=True), help="Decision definition file (JSON)")
@click.option("--json", "decision_json", type=str, help="Inline JSON decision definition")
@click.option("--name", type=str, help="Decision name (overrides file/json)")
@click.option("--state", type=str, default="PENDING", help="Decision state")
@click.option("--entitlement-id", type=str, required=False, help="Entitlement ID")
@click.option("--policy-id", type=str, required=False, help="Policy ID")
@click.option("--creator-id", type=str, required=False, help="Creator ID")
@click.option("--priority", type=str, default="MEDIUM", help="Decision priority")
@click.option("--context", type=str, default=None, help="Decision context JSON")
@click.option("--db-url", default=None, help="Override database URL")
@click.pass_context
def decision_db_create(
    click_ctx: click.Context,
    decision_file: Optional[str],
    decision_json: Optional[str],
    name: Optional[str],
    state: str,
    entitlement_id: Optional[str],
    policy_id: Optional[str],
    creator_id: Optional[str],
    priority: str,
    context: Optional[str],
    db_url: Optional[str]
) -> None:
    """Create a decision in the local database."""
    if not click_ctx.obj:
        click.echo("Error: CLI context not initialized", err=True)
        sys.exit(1)

    ctx: HexarchContext = click_ctx.obj
    _init_db(ctx, db_url)

    try:
        payload = _load_json_definition(decision_file, decision_json)
        decision = Decision(
            name=name or payload.get("name") or "unnamed-decision",
            description=payload.get("description"),
            state=state or payload.get("state") or "PENDING",
            entitlement_id=entitlement_id or payload.get("entitlement_id"),
            policy_id=policy_id or payload.get("policy_id"),
            creator_id=creator_id or payload.get("creator_id") or "system",
            reviewer_id=payload.get("reviewer_id"),
            priority=priority or payload.get("priority") or "MEDIUM",
            expires_at=payload.get("expires_at"),
            context=payload.get("context") or context,
            decision_reason=payload.get("decision_reason")
        )

        if not decision.entitlement_id:
            raise ValueError("entitlement_id is required")

        session = DatabaseManager.get_session()
        session.add(decision)
        session.commit()

        ctx.formatter.print_success(f"Decision created: {decision.id}")
        ctx.audit_logger.log_command("decision db-create", result=decision.id)
    except Exception as exc:
        ctx.formatter.print_error(f"Failed to create decision: {str(exc)}")
        ctx.audit_logger.log_command("decision db-create", error=str(exc))
        sys.exit(1)


@decision_group.command(name="db-delete")
@click.argument("decision-id")
@click.option("--hard", is_flag=True, help="Permanently delete (no soft delete)")
@click.option("--db-url", default=None, help="Override database URL")
@click.pass_context
def decision_db_delete(click_ctx: click.Context, decision_id: str, hard: bool, db_url: Optional[str]) -> None:
    """Delete a decision (soft delete by default)."""
    if not click_ctx.obj:
        click.echo("Error: CLI context not initialized", err=True)
        sys.exit(1)

    ctx: HexarchContext = click_ctx.obj
    _init_db(ctx, db_url)

    session = DatabaseManager.get_session()
    decision = session.query(Decision).filter(Decision.id == decision_id).first()

    if not decision:
        ctx.formatter.print_error(f"Decision not found: {decision_id}")
        sys.exit(1)

    if hard:
        session.delete(decision)
    else:
        decision.soft_delete()

    session.commit()
    ctx.formatter.print_success(f"Decision deleted: {decision_id}")
    ctx.audit_logger.log_command("decision db-delete", result=decision_id)


@decision_group.command(name="query")
@click.option("--from", "from_date", type=str, default=None, help="Start date (YYYY-MM-DD)")
@click.option("--to", "to_date", type=str, default=None, help="End date (YYYY-MM-DD)")
@click.option("--provider", type=str, default=None, help="Filter by provider name")
@click.option("--user-id", type=str, default=None, help="Filter by user ID")
@click.option("--decision", type=click.Choice(["ALLOW", "DENY"]), default=None, help="Filter by decision")
@click.option("--limit", type=int, default=100, help="Max results (default 100, max 1000)")
@click.option("--format", type=click.Choice(["json", "table", "csv"]), default=None, help="Output format")
@click.pass_context
def decision_query(
    click_ctx: click.Context,
    from_date: Optional[str],
    to_date: Optional[str],
    provider: Optional[str],
    user_id: Optional[str],
    decision: Optional[str],
    limit: int,
    format: Optional[str]
) -> None:
    """Query recent decisions with filtering."""
    if not click_ctx.obj:
        click.echo("Error: CLI context not initialized", err=True)
        sys.exit(1)
    
    ctx: HexarchContext = click_ctx.obj
    formatter = ctx.formatter
    
    try:
        # Validate limit
        if limit < 1 or limit > 1000:
            click.echo("Error: --limit must be between 1 and 1000", err=True)
            sys.exit(2)
        
        # Validate dates if provided
        if from_date:
            try:
                datetime.strptime(from_date, "%Y-%m-%d")
            except ValueError:
                click.echo("Error: --from must be YYYY-MM-DD format", err=True)
                sys.exit(2)
        
        if to_date:
            try:
                datetime.strptime(to_date, "%Y-%m-%d")
            except ValueError:
                click.echo("Error: --to must be YYYY-MM-DD format", err=True)
                sys.exit(2)
        
        # Build query parameters
        query_params = {
            "limit": limit
        }
        if from_date:
            query_params["from_date"] = from_date
        if to_date:
            query_params["to_date"] = to_date
        if provider:
            query_params["provider"] = provider
        if user_id:
            query_params["user_id"] = user_id
        if decision:
            query_params["decision"] = decision
        
        # Query API
        decisions = ctx.api_client.query_decisions(**query_params)
        
        if not decisions:
            ctx.audit_logger.log_command(
                command="decision query",
                args=query_params,
                result="No matching data"
            )
            click.echo("No decisions found matching criteria.", err=False)
            sys.exit(0)
        
        # Determine output format
        output_format = format or formatter.format
        
        # Format output
        if output_format == "json":
            output_data = {
                "decisions": decisions,
                "metadata": {
                    "total": len(decisions),
                    "returned": len(decisions),
                    "filters": {k: v for k, v in query_params.items() if k != "limit"}
                }
            }
            click.echo(json.dumps(output_data, indent=2, default=str))
        elif output_format == "csv":
            if decisions:
                output = StringIO()
                keys = decisions[0].keys()
                writer = csv.DictWriter(output, fieldnames=keys)
                writer.writeheader()
                writer.writerows(decisions)
                click.echo(output.getvalue())
        else:  # table
            formatted = formatter.format_output(
                decisions,
                headers=["decision_id", "timestamp", "provider", "decision", "latency_ms", "decision_reason"]
            )
            click.echo(formatted)
        
        # Log to audit trail
        ctx.audit_logger.log_command(
            command="decision query",
            args=query_params,
            result=f"Returned {len(decisions)} decisions"
        )
        
    except Exception as e:
        formatter.print_error(f"Failed to query decisions: {str(e)}")
        ctx.audit_logger.log_command(
            command="decision query",
            error=str(e)
        )
        sys.exit(1)


@decision_group.command(name="export")
@click.option("--from", "from_date", type=str, default=None, help="Start date (YYYY-MM-DD)")
@click.option("--to", "to_date", type=str, default=None, help="End date (YYYY-MM-DD)")
@click.option("--provider", type=str, default=None, help="Filter by provider")
@click.option("--user-id", type=str, default=None, help="Filter by user ID")
@click.option("--decision", type=click.Choice(["ALLOW", "DENY"]), default=None, help="Filter by decision")
@click.option("--output", "-o", type=click.Path(), required=False, help="Output file path (optional, defaults to stdout)")
@click.option("--format", type=click.Choice(["json", "csv"]), default="json", help="Export format")
@click.pass_context
def decision_export(
    click_ctx: click.Context,
    from_date: Optional[str],
    to_date: Optional[str],
    provider: Optional[str],
    user_id: Optional[str],
    decision: Optional[str],
    output: Optional[str],
    format: str
) -> None:
    """Export decision history to file (supports all available records via pagination)."""
    if not click_ctx.obj:
        click.echo("Error: CLI context not initialized", err=True)
        sys.exit(1)
    
    ctx: HexarchContext = click_ctx.obj
    formatter = ctx.formatter
    
    try:
        # Validate dates if provided
        if from_date:
            try:
                datetime.strptime(from_date, "%Y-%m-%d")
            except ValueError:
                click.echo("Error: --from must be YYYY-MM-DD format", err=True)
                sys.exit(2)
        
        if to_date:
            try:
                datetime.strptime(to_date, "%Y-%m-%d")
            except ValueError:
                click.echo("Error: --to must be YYYY-MM-DD format", err=True)
                sys.exit(2)
        
        # Build base query parameters
        query_params = {
            "from_date": from_date,
            "to_date": to_date,
            "provider": provider,
            "user_id": user_id,
            "decision": decision
        }
        # Remove None values
        query_params = {k: v for k, v in query_params.items() if v is not None}
        
        # Paginate through all results (1000 per page)
        all_decisions = []
        page_size = 1000
        offset = 0
        
        while True:
            # Query API for current page
            page_params = {**query_params, "limit": page_size, "offset": offset}
            page_decisions = ctx.api_client.query_decisions(**page_params)
            
            if not page_decisions:
                break  # No more data
            
            all_decisions.extend(page_decisions)
            
            # If we got fewer than page_size results, we've reached the end
            if len(page_decisions) < page_size:
                break
            
            offset += page_size
        
        if not all_decisions:
            ctx.audit_logger.log_command(
                command="decision export",
                args={**query_params, "output": output or "stdout", "format": format},
                result="No matching data"
            )
            click.echo("No decisions found matching criteria.", err=False)
            sys.exit(0)
        
        # Export to file or stdout
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format == "json":
                with open(output_path, "w") as f:
                    json.dump(all_decisions, f, indent=2, default=str)
            elif format == "csv":
                if all_decisions:
                    keys = all_decisions[0].keys()
                    with open(output_path, "w", newline="") as f:
                        writer = csv.DictWriter(f, fieldnames=keys)
                        writer.writeheader()
                        writer.writerows(all_decisions)
            
            formatter.print_success(f"Exported {len(all_decisions)} decisions to {output_path}")
        else:
            # Output to stdout
            if format == "json":
                click.echo(json.dumps(all_decisions, indent=2, default=str))
            elif format == "csv":
                if all_decisions:
                    keys = all_decisions[0].keys()
                    output_stream = StringIO()
                    writer = csv.DictWriter(output_stream, fieldnames=keys)
                    writer.writeheader()
                    writer.writerows(all_decisions)
                    click.echo(output_stream.getvalue())
        
        # Log to audit trail
        ctx.audit_logger.log_command(
            command="decision export",
            args={**query_params, "output": output or "stdout", "format": format},
            result=f"Exported {len(all_decisions)} decisions"
        )
        
    except Exception as e:
        formatter.print_error(f"Failed to export decisions: {str(e)}")
        ctx.audit_logger.log_command(
            command="decision export",
            error=str(e)
        )
        sys.exit(1)


def _init_db(ctx: HexarchContext, db_url: Optional[str]) -> None:
    config = ctx.config_manager.get_config()
    os.environ["SQL_ECHO"] = "true" if config.db.echo_sql else "false"
    if db_url:
        DatabaseManager.initialize(db_url)
        return

    if config.db.url:
        DatabaseManager.initialize(config.db.url)
        return

    if config.db.provider == "sqlite":
        DatabaseManager.initialize(f"sqlite:///{config.db.path}")
        return

    DatabaseManager.initialize()


def _load_json_definition(file_path: Optional[str], json_input: Optional[str]) -> dict:
    provided = [p for p in [file_path, json_input] if p]
    if len(provided) == 0:
        return {}
    if len(provided) != 1:
        raise ValueError("Provide exactly one of --file or --json")

    if file_path:
        path = Path(file_path).expanduser()
        content = path.read_text()
        return json.loads(content)

    return json.loads(json_input)


@decision_group.command(name="stats")
@click.option("--from", "from_date", type=str, default=None, help="Start date (YYYY-MM-DD)")
@click.option("--to", "to_date", type=str, default=None, help="End date (YYYY-MM-DD)")
@click.option("--group-by", type=click.Choice(["provider", "decision", "user", "hour"]), default=None, help="Grouping dimension")
@click.pass_context
def decision_stats(
    click_ctx: click.Context,
    from_date: Optional[str],
    to_date: Optional[str],
    group_by: Optional[str]
) -> None:
    """Show decision statistics for time range."""
    if not click_ctx.obj:
        click.echo("Error: CLI context not initialized", err=True)
        sys.exit(1)
    
    ctx: HexarchContext = click_ctx.obj
    formatter = ctx.formatter
    
    try:
        # Validate dates if provided
        if from_date:
            try:
                datetime.strptime(from_date, "%Y-%m-%d")
            except ValueError:
                click.echo("Error: --from must be YYYY-MM-DD format", err=True)
                sys.exit(2)
        
        if to_date:
            try:
                datetime.strptime(to_date, "%Y-%m-%d")
            except ValueError:
                click.echo("Error: --to must be YYYY-MM-DD format", err=True)
                sys.exit(2)
        
        # Build query parameters
        query_params = {}
        if from_date:
            query_params["from_date"] = from_date
        if to_date:
            query_params["to_date"] = to_date
        if group_by:
            query_params["group_by"] = group_by
        
        # Query API for stats
        stats = ctx.api_client.get_decision_stats(**query_params)
        
        if not stats:
            ctx.audit_logger.log_command(
                command="decision stats",
                args=query_params,
                result="No matching data"
            )
            click.echo("No decision statistics available.", err=False)
            sys.exit(0)
        
        # Format output (always JSON for stats)
        click.echo(json.dumps(stats, indent=2, default=str))
        
        # Log to audit trail
        ctx.audit_logger.log_command(
            command="decision stats",
            args=query_params,
            result="Statistics retrieved"
        )
        
    except Exception as e:
        formatter.print_error(f"Failed to get decision statistics: {str(e)}")
        ctx.audit_logger.log_command(
            command="decision stats",
            error=str(e)
        )
        sys.exit(1)


__all__ = ["decision_group"]

