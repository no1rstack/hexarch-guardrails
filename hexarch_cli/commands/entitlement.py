"""Entitlement management commands for local DB."""

import json
import os
from pathlib import Path
from typing import Optional

import click

from hexarch_cli.context import HexarchContext
from hexarch_cli.db import DatabaseManager
from hexarch_cli.models import Entitlement
from hexarch_cli.output.formatter import OutputFormatter


@click.group(name="entitlement")
def entitlement_group() -> None:
    """Manage entitlements in the local database."""
    pass


@entitlement_group.command(name="db-list")
@click.option("--limit", type=int, default=50, help="Max results")
@click.option("--format", "output_format", type=click.Choice(["json", "table", "csv"]), default=None, help="Output format")
@click.option("--db-url", default=None, help="Override database URL")
@click.pass_context
def entitlement_db_list(click_ctx: click.Context, limit: int, output_format: Optional[str], db_url: Optional[str]) -> None:
    """List entitlements from the local database."""
    if not click_ctx.obj:
        click.echo("Error: CLI context not initialized", err=True)
        raise SystemExit(1)

    ctx: HexarchContext = click_ctx.obj
    formatter = ctx.formatter
    if output_format:
        formatter = OutputFormatter(format=output_format, colors=ctx.config_manager.get_config().output.colors)

    _init_db(ctx, db_url)
    session = DatabaseManager.get_session()
    entitlements = (
        session.query(Entitlement)
        .filter(Entitlement.is_deleted == False)
        .order_by(Entitlement.created_at.desc())
        .limit(limit)
        .all()
    )

    if formatter.format == "table":
        headers = ["ID", "SUBJECT", "TYPE", "NAME", "STATUS"]
        data = [[e.id, e.subject_id, e.entitlement_type, e.name, e.status] for e in entitlements]
        click.echo(formatter.format_output(data, headers=headers))
    else:
        click.echo(json.dumps([e.to_dict() for e in entitlements], indent=2, default=str))

    ctx.audit_logger.log_command("entitlement db-list", result=f"{len(entitlements)} entitlements")


@entitlement_group.command(name="db-get")
@click.argument("entitlement-id")
@click.option("--format", "output_format", type=click.Choice(["json", "table", "csv"]), default=None, help="Output format")
@click.option("--db-url", default=None, help="Override database URL")
@click.pass_context
def entitlement_db_get(click_ctx: click.Context, entitlement_id: str, output_format: Optional[str], db_url: Optional[str]) -> None:
    """Get an entitlement by ID from the local database."""
    if not click_ctx.obj:
        click.echo("Error: CLI context not initialized", err=True)
        raise SystemExit(1)

    ctx: HexarchContext = click_ctx.obj
    formatter = ctx.formatter
    if output_format:
        formatter = OutputFormatter(format=output_format, colors=ctx.config_manager.get_config().output.colors)

    _init_db(ctx, db_url)
    session = DatabaseManager.get_session()
    entitlement = session.query(Entitlement).filter(Entitlement.id == entitlement_id, Entitlement.is_deleted == False).first()

    if not entitlement:
        formatter.print_error(f"Entitlement not found: {entitlement_id}")
        raise SystemExit(1)

    if formatter.format == "table":
        headers = ["FIELD", "VALUE"]
        data = [[k, v] for k, v in entitlement.to_dict().items()]
        click.echo(formatter.format_output(data, headers=headers))
    else:
        click.echo(json.dumps(entitlement.to_dict(), indent=2, default=str))

    ctx.audit_logger.log_command("entitlement db-get", result=entitlement_id)


@entitlement_group.command(name="db-create")
@click.option("--file", "entitlement_file", type=click.Path(exists=True), help="Entitlement definition file (JSON)")
@click.option("--json", "entitlement_json", type=str, help="Inline JSON entitlement definition")
@click.option("--subject-id", type=str, required=False, help="Subject ID")
@click.option("--subject-type", type=str, default="user", help="Subject type")
@click.option("--type", "entitlement_type", type=str, default="ROLE", help="Entitlement type")
@click.option("--name", type=str, default=None, help="Entitlement name")
@click.option("--status", type=str, default="PENDING", help="Entitlement status")
@click.option("--granted-by", type=str, default="system", help="Granted by")
@click.option("--db-url", default=None, help="Override database URL")
@click.pass_context
def entitlement_db_create(
    click_ctx: click.Context,
    entitlement_file: Optional[str],
    entitlement_json: Optional[str],
    subject_id: Optional[str],
    subject_type: str,
    entitlement_type: str,
    name: Optional[str],
    status: str,
    granted_by: str,
    db_url: Optional[str]
) -> None:
    """Create an entitlement in the local database."""
    if not click_ctx.obj:
        click.echo("Error: CLI context not initialized", err=True)
        raise SystemExit(1)

    ctx: HexarchContext = click_ctx.obj
    _init_db(ctx, db_url)

    try:
        payload = _load_json_definition(entitlement_file, entitlement_json)
        entitlement = Entitlement(
            subject_id=subject_id or payload.get("subject_id"),
            subject_type=subject_type or payload.get("subject_type") or "user",
            entitlement_type=entitlement_type or payload.get("entitlement_type") or "ROLE",
            name=name or payload.get("name") or "unnamed-entitlement",
            description=payload.get("description"),
            resource_id=payload.get("resource_id"),
            resource_type=payload.get("resource_type"),
            status=status or payload.get("status") or "PENDING",
            valid_from=payload.get("valid_from"),
            expires_at=payload.get("expires_at"),
            granted_by=granted_by or payload.get("granted_by") or "system",
            revoked_by=payload.get("revoked_by"),
            reason=payload.get("reason"),
            entitlement_metadata=payload.get("entitlement_metadata") or payload.get("metadata"),
        )

        if not entitlement.subject_id:
            raise ValueError("subject_id is required")

        session = DatabaseManager.get_session()
        session.add(entitlement)
        session.commit()

        ctx.formatter.print_success(f"Entitlement created: {entitlement.id}")
        ctx.audit_logger.log_command("entitlement db-create", result=entitlement.id)
    except Exception as exc:
        ctx.formatter.print_error(f"Failed to create entitlement: {str(exc)}")
        ctx.audit_logger.log_command("entitlement db-create", error=str(exc))
        raise SystemExit(1)


@entitlement_group.command(name="db-delete")
@click.argument("entitlement-id")
@click.option("--hard", is_flag=True, help="Permanently delete (no soft delete)")
@click.option("--db-url", default=None, help="Override database URL")
@click.pass_context
def entitlement_db_delete(click_ctx: click.Context, entitlement_id: str, hard: bool, db_url: Optional[str]) -> None:
    """Delete an entitlement (soft delete by default)."""
    if not click_ctx.obj:
        click.echo("Error: CLI context not initialized", err=True)
        raise SystemExit(1)

    ctx: HexarchContext = click_ctx.obj
    _init_db(ctx, db_url)

    session = DatabaseManager.get_session()
    entitlement = session.query(Entitlement).filter(Entitlement.id == entitlement_id).first()

    if not entitlement:
        ctx.formatter.print_error(f"Entitlement not found: {entitlement_id}")
        raise SystemExit(1)

    if hard:
        session.delete(entitlement)
    else:
        entitlement.soft_delete()

    session.commit()
    ctx.formatter.print_success(f"Entitlement deleted: {entitlement_id}")
    ctx.audit_logger.log_command("entitlement db-delete", result=entitlement_id)


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
