"""Database migration commands for hexarch-ctl."""

from typing import Optional
import os

import click
from alembic import command
from alembic.config import Config

from hexarch_cli.context import HexarchContext
from hexarch_cli.db import DatabaseManager


def _get_alembic_config(db_url: Optional[str] = None) -> Config:
    from pathlib import Path
    base_dir = Path(__file__).resolve().parents[2]
    cfg = Config(str(base_dir / "alembic.ini"))
    if db_url:
        cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


def _init_db_from_context(ctx: HexarchContext, db_url: Optional[str]) -> str:
    if db_url:
        DatabaseManager.initialize(db_url)
        return db_url

    config = ctx.config_manager.get_config()
    os.environ["SQL_ECHO"] = "true" if config.db.echo_sql else "false"
    if config.db.url:
        DatabaseManager.initialize(config.db.url)
        return config.db.url

    if config.db.provider == "sqlite":
        db_url = f"sqlite:///{config.db.path}"
        DatabaseManager.initialize(db_url)
        return db_url

    DatabaseManager.initialize()
    return ""


@click.group(name="db")
def db_group():
    """Manage local database and migrations."""
    pass


@db_group.command(name="upgrade")
@click.argument("revision", required=False, default="head")
@click.option("--db-url", default=None, help="Override database URL")
@click.pass_context
def db_upgrade(click_ctx: click.Context, revision: str, db_url: Optional[str]) -> None:
    """Apply migrations up to the given revision (default: head)."""
    if not click_ctx.obj:
        click.echo("Error: CLI context not initialized", err=True)
        raise SystemExit(1)

    ctx: HexarchContext = click_ctx.obj
    url = _init_db_from_context(ctx, db_url)
    cfg = _get_alembic_config(url or None)

    try:
        command.upgrade(cfg, revision)
        ctx.formatter.print_success(f"Database upgraded to {revision}")
        ctx.audit_logger.log_command("db upgrade", result=f"{revision}")
    except Exception as exc:
        ctx.formatter.print_error(f"Migration failed: {str(exc)}")
        ctx.audit_logger.log_command("db upgrade", error=str(exc))
        raise SystemExit(1)


@db_group.command(name="downgrade")
@click.argument("revision", required=True)
@click.option("--db-url", default=None, help="Override database URL")
@click.pass_context
def db_downgrade(click_ctx: click.Context, revision: str, db_url: Optional[str]) -> None:
    """Downgrade database to a specific revision."""
    if not click_ctx.obj:
        click.echo("Error: CLI context not initialized", err=True)
        raise SystemExit(1)

    ctx: HexarchContext = click_ctx.obj
    url = _init_db_from_context(ctx, db_url)
    cfg = _get_alembic_config(url or None)

    try:
        command.downgrade(cfg, revision)
        ctx.formatter.print_success(f"Database downgraded to {revision}")
        ctx.audit_logger.log_command("db downgrade", result=f"{revision}")
    except Exception as exc:
        ctx.formatter.print_error(f"Downgrade failed: {str(exc)}")
        ctx.audit_logger.log_command("db downgrade", error=str(exc))
        raise SystemExit(1)


@db_group.command(name="current")
@click.option("--db-url", default=None, help="Override database URL")
@click.pass_context
def db_current(click_ctx: click.Context, db_url: Optional[str]) -> None:
    """Show current database revision."""
    if not click_ctx.obj:
        click.echo("Error: CLI context not initialized", err=True)
        raise SystemExit(1)

    ctx: HexarchContext = click_ctx.obj
    url = _init_db_from_context(ctx, db_url)
    cfg = _get_alembic_config(url or None)

    try:
        command.current(cfg)
        ctx.audit_logger.log_command("db current", result="ok")
    except Exception as exc:
        ctx.formatter.print_error(f"Failed to get current revision: {str(exc)}")
        ctx.audit_logger.log_command("db current", error=str(exc))
        raise SystemExit(1)


@db_group.command(name="history")
@click.option("--db-url", default=None, help="Override database URL")
@click.pass_context
def db_history(click_ctx: click.Context, db_url: Optional[str]) -> None:
    """Show migration history."""
    if not click_ctx.obj:
        click.echo("Error: CLI context not initialized", err=True)
        raise SystemExit(1)

    ctx: HexarchContext = click_ctx.obj
    url = _init_db_from_context(ctx, db_url)
    cfg = _get_alembic_config(url or None)

    try:
        command.history(cfg)
        ctx.audit_logger.log_command("db history", result="ok")
    except Exception as exc:
        ctx.formatter.print_error(f"Failed to get history: {str(exc)}")
        ctx.audit_logger.log_command("db history", error=str(exc))
        raise SystemExit(1)
