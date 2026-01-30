"""Root CLI group for hexarch-ctl."""

import sys
from pathlib import Path
from typing import Optional
import click
from hexarch_cli.context import HexarchContext
from hexarch_cli.config.config import ConfigManager
from hexarch_cli.api.client import HexarchAPIClient
from hexarch_cli.output.formatter import OutputFormatter
from hexarch_cli.logging.audit import AuditLogger
from hexarch_cli.commands.policy import policy_group
from hexarch_cli.commands.decision import decision_group
from hexarch_cli.commands.metrics import metrics_group
from hexarch_cli.commands.config import config_group
from hexarch_cli.commands.rule import rule_group
from hexarch_cli.commands.db import db_group
from hexarch_cli.commands.entitlement import entitlement_group
from hexarch_cli.commands.serve import serve_group
from hexarch_cli.commands.node_red import node_red_group
from hexarch_cli import __version__


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=__version__, prog_name="hexarch-ctl")
@click.option("--config", type=click.Path(), default=None, help="Config file path")
@click.option("--format", type=click.Choice(["json", "table", "csv"]), default="table", help="Output format")
@click.option("--api-url", default=None, help="API server URL")
@click.option("--api-token", default=None, help="API bearer token")
@click.option("--verbose", is_flag=True, help="Enable debug logging")
@click.pass_context
def cli(
    ctx: click.Context,
    config: Optional[str],
    format: str,
    api_url: Optional[str],
    api_token: Optional[str],
    verbose: bool
) -> None:
    """
    Hexarch Admin CLI (hexarch-ctl)
    
    Operational command-line interface for managing policies, querying decisions,
    and monitoring provider performance metrics.
    
    \b
    Examples:
      hexarch-ctl policy list
      hexarch-ctl decision query --from 2026-01-01
      hexarch-ctl metrics show --time-window 1d
      hexarch-ctl config init
    """
    
    try:
        # Load configuration
        config_manager = ConfigManager(config)
        cfg = config_manager.get_config()
        
        # Override with CLI flags
        if api_url:
            cfg.api.url = api_url
        if api_token:
            cfg.api.token = api_token
        if format:
            cfg.output.format = format
        
        # Create API client
        api_client = HexarchAPIClient(cfg.api)
        
        # Create output formatter
        formatter = OutputFormatter(
            format=cfg.output.format,
            colors=cfg.output.colors
        )
        
        # Create audit logger
        audit_logger = AuditLogger(cfg.audit)
        
        # Create context
        hex_ctx = HexarchContext(
            config_manager=config_manager,
            api_client=api_client,
            formatter=formatter,
            audit_logger=audit_logger
        )
        
        ctx.ensure_object(dict)
        ctx.obj = hex_ctx
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_obj
def health(ctx: HexarchContext) -> None:
    """Check API health and connectivity."""
    try:
        is_healthy = ctx.api_client.health_check()
        
        if is_healthy:
            ctx.formatter.print_success(f"API is healthy: {ctx.config_manager.get_config().api.url}")
        else:
            ctx.formatter.print_error(f"API is unreachable: {ctx.config_manager.get_config().api.url}")
            sys.exit(1)
    except Exception as e:
        ctx.formatter.print_error(f"Health check failed: {str(e)}")
        sys.exit(1)


# Register command groups
cli.add_command(policy_group)
cli.add_command(decision_group)
cli.add_command(metrics_group)
cli.add_command(config_group)
cli.add_command(rule_group)
cli.add_command(db_group)
cli.add_command(entitlement_group)
cli.add_command(serve_group)
cli.add_command(node_red_group)


if __name__ == "__main__":
    cli()
