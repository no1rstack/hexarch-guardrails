"""Config initialization commands."""

import sys
from pathlib import Path
from typing import Optional, Dict, Any
import click
import yaml
from hexarch_cli.context import HexarchContext
from hexarch_cli.config.schemas import APIConfig, OutputConfig, AuditConfig, PolicyConfig, DatabaseConfig, HexarchConfig
from hexarch_cli.config.config import ConfigManager


@click.group(name="config")
def config_group() -> None:
    """Manage CLI configuration."""
    pass


@config_group.command(name="init")
@click.option("--output", "output_path", type=click.Path(), default=None, help="Output config file path")
@click.pass_context
def config_init(click_ctx: click.Context, output_path: Optional[str]) -> None:
    """Initialize configuration file interactively."""
    if not click_ctx.obj:
        click.echo("Error: CLI context not initialized", err=True)
        sys.exit(1)

    ctx: HexarchContext = click_ctx.obj

    try:
        api_url = click.prompt("API Server URL", default="http://localhost:8080")
        api_token = click.prompt(
            "API Token (leave blank to use HEXARCH_API_TOKEN env var)",
            default="",
            show_default=False,
            hide_input=True
        )
        output_format = click.prompt(
            "Default output format",
            type=click.Choice(["table", "json", "csv"]),
            default="table"
        )
        colors = click.confirm("Enable colored output", default=True)
        audit_enabled = click.confirm("Enable audit logging", default=True)
        audit_log_path = click.prompt(
            "Audit log location",
            default=AuditConfig().log_path
        )
        db_provider = click.prompt(
            "Database provider",
            type=click.Choice(["sqlite", "postgresql"]),
            default="sqlite"
        )
        db_url = click.prompt(
            "Database URL (leave blank to use provider/path)",
            default="",
            show_default=False
        )
        db_path = click.prompt(
            "SQLite DB path",
            default=DatabaseConfig().path
        ) if db_provider == "sqlite" and not db_url else DatabaseConfig().path

        token_value = api_token or "${HEXARCH_API_TOKEN}"

        config = HexarchConfig(
            api=APIConfig(url=api_url, token=token_value),
            output=OutputConfig(format=output_format, colors=colors),
            audit=AuditConfig(enabled=audit_enabled, log_path=audit_log_path),
            policies=PolicyConfig(),
            db=DatabaseConfig(
                url=db_url or None,
                provider=db_provider,
                path=db_path
            )
        )

        target_path = Path(output_path) if output_path else ConfigManager.DEFAULT_CONFIG_FILE
        target_path.parent.mkdir(parents=True, exist_ok=True)

        with open(target_path, "w") as f:
            yaml.safe_dump(config.model_dump(exclude_none=True), f, default_flow_style=False)

        # Validate connectivity (best effort)
        connectivity_manager = ConfigManager(str(target_path))
        ok, message = connectivity_manager.validate_connectivity()
        if ok:
            click.echo(f"✓ API connectivity: {message}")
        else:
            click.echo(f"Warning: API connectivity check failed: {message}", err=True)

        ctx.formatter.print_success(f"Configuration saved to {target_path}")
        ctx.audit_logger.log_command(
            command="config init",
            args={"output": str(target_path)},
            result="Configuration initialized"
        )

    except Exception as e:
        ctx.formatter.print_error(f"Failed to initialize configuration: {str(e)}")
        ctx.audit_logger.log_command(
            command="config init",
            error=str(e)
        )
        sys.exit(1)


@config_group.command(name="set")
@click.option("--api-url", type=str, default=None, help="Set API URL")
@click.option("--api-token", type=str, default=None, help="Set API token")
@click.option("--format", "output_format", type=click.Choice(["json", "table", "csv"]), default=None, help="Set output format")
@click.option("--db-url", type=str, default=None, help="Set database URL")
@click.option("--db-provider", type=click.Choice(["sqlite", "postgresql"]), default=None, help="Set database provider")
@click.option("--db-path", type=str, default=None, help="Set SQLite database path")
@click.option("--db-echo", type=click.Choice(["true", "false"]), default=None, help="Enable SQL echo (true/false)")
@click.option("--config", "config_path", type=click.Path(), default=None, help="Config file path")
@click.pass_context
def config_set(
    click_ctx: click.Context,
    api_url: Optional[str],
    api_token: Optional[str],
    output_format: Optional[str],
    db_url: Optional[str],
    db_provider: Optional[str],
    db_path: Optional[str],
    db_echo: Optional[str],
    config_path: Optional[str]
) -> None:
    """Update configuration values."""
    if not click_ctx.obj:
        click.echo("Error: CLI context not initialized", err=True)
        sys.exit(1)

    ctx: HexarchContext = click_ctx.obj

    try:
        config_manager = ConfigManager(config_path)
        config = config_manager.get_config()

        updates: Dict[str, Any] = {}
        if api_url:
            config.api.url = api_url
            updates["api_url"] = api_url
        if api_token is not None:
            config.api.token = api_token or "${HEXARCH_API_TOKEN}"
            updates["api_token"] = "***" if api_token else "${HEXARCH_API_TOKEN}"
        if output_format:
            config.output.format = output_format
            updates["format"] = output_format
        if db_url is not None:
            config.db.url = db_url or None
            updates["db_url"] = db_url or None
        if db_provider:
            config.db.provider = db_provider
            updates["db_provider"] = db_provider
        if db_path:
            config.db.path = db_path
            updates["db_path"] = db_path
        if db_echo is not None:
            config.db.echo_sql = db_echo.lower() == "true"
            updates["db_echo"] = config.db.echo_sql

        if not updates:
            click.echo("No configuration updates provided.")
            sys.exit(0)

        config_manager.save_config(config, str(config_manager.config_path))
        ctx.formatter.print_success("Configuration updated")

        ctx.audit_logger.log_command(
            command="config set",
            args=updates,
            result="Configuration updated"
        )

    except Exception as e:
        ctx.formatter.print_error(f"Failed to update configuration: {str(e)}")
        ctx.audit_logger.log_command(
            command="config set",
            error=str(e)
        )
        sys.exit(1)


@config_group.command(name="validate")
@click.option("--config", "config_path", type=click.Path(), default=None, help="Config file path")
@click.pass_context
def config_validate(click_ctx: click.Context, config_path: Optional[str]) -> None:
    """Validate configuration and API connectivity."""
    if not click_ctx.obj:
        click.echo("Error: CLI context not initialized", err=True)
        sys.exit(1)

    ctx: HexarchContext = click_ctx.obj

    try:
        target_path = Path(config_path) if config_path else ConfigManager.DEFAULT_CONFIG_FILE
        click.echo(f"Validating {target_path}...")

        if not target_path.exists():
            click.echo(f"Error: Config file not found: {target_path}", err=True)
            sys.exit(1)

        config_manager = ConfigManager(str(target_path))
        click.echo("✓ Config file format valid")

        ok, message = config_manager.validate_connectivity()
        if ok:
            click.echo(f"✓ API connectivity: {message}")
        else:
            click.echo(f"✗ API connectivity failed: {message}", err=True)
            sys.exit(1)

        ctx.formatter.print_success("Configuration is valid!")
        ctx.audit_logger.log_command(
            command="config validate",
            args={"config": str(target_path)},
            result="Configuration valid"
        )

    except Exception as e:
        ctx.formatter.print_error(f"Failed to validate configuration: {str(e)}")
        ctx.audit_logger.log_command(
            command="config validate",
            error=str(e)
        )
        sys.exit(1)


__all__ = ["config_group"]
