"""Rule evaluation commands for hexarch-ctl."""

import json
import os
from pathlib import Path
from typing import Optional

import click

from hexarch_cli.context import HexarchContext
from hexarch_cli.db import DatabaseManager
from hexarch_cli.models import Rule
from hexarch_cli.output.formatter import OutputFormatter
from hexarch_cli.rules_engine import RuleEvaluator, RuleEvaluationError


@click.group(name="rule")
def rule_group():
    """Evaluate and validate rules.

    Commands for testing JSON/YAML rule DSL definitions against a context.
    """
    pass


@rule_group.command(name="create")
@click.option("--file", "rule_file", type=click.Path(exists=True), help="Rule definition file (JSON or YAML)")
@click.option("--json", "rule_json", type=str, help="Inline JSON rule definition")
@click.option("--name", type=str, help="Rule name (overrides file/json)")
@click.option("--type", "rule_type", type=str, help="Rule type: CONDITION, PERMISSION, CONSTRAINT, COMPOSITE")
@click.option("--priority", type=int, default=100, help="Rule priority (lower = higher priority)")
@click.option("--enabled/--disabled", default=True, help="Enable or disable the rule")
@click.option("--db-url", default=None, help="Override database URL")
@click.pass_context
def rule_create(
    click_ctx: click.Context,
    rule_file: Optional[str],
    rule_json: Optional[str],
    name: Optional[str],
    rule_type: Optional[str],
    priority: int,
    enabled: bool,
    db_url: Optional[str]
) -> None:
    """Create a rule in the local database."""
    if not click_ctx.obj:
        click.echo("Error: CLI context not initialized", err=True)
        raise SystemExit(1)

    ctx: HexarchContext = click_ctx.obj
    _init_db(ctx, db_url)

    try:
        rule_payload = _load_rule_definition(rule_file, rule_json)
        condition = rule_payload.get("condition") or rule_payload

        rule = Rule(
            name=name or rule_payload.get("name") or "unnamed-rule",
            description=rule_payload.get("description"),
            rule_type=rule_type or rule_payload.get("rule_type") or "CONDITION",
            priority=priority if priority is not None else rule_payload.get("priority", 100),
            enabled=enabled,
            condition=condition,
            operator=rule_payload.get("operator"),
            rule_metadata=rule_payload.get("rule_metadata") or rule_payload.get("metadata"),
        )

        session = DatabaseManager.get_session()
        session.add(rule)
        session.commit()

        ctx.formatter.print_success(f"Rule created: {rule.id}")
        ctx.audit_logger.log_command("rule create", result=rule.id)
    except Exception as exc:
        ctx.formatter.print_error(f"Failed to create rule: {str(exc)}")
        ctx.audit_logger.log_command("rule create", error=str(exc))
        raise SystemExit(1)


@rule_group.command(name="list")
@click.option("--limit", type=int, default=50, help="Max results")
@click.option("--format", "output_format", type=click.Choice(["json", "table", "csv"]), default=None, help="Output format")
@click.option("--db-url", default=None, help="Override database URL")
@click.pass_context
def rule_list(click_ctx: click.Context, limit: int, output_format: Optional[str], db_url: Optional[str]) -> None:
    """List rules from the local database."""
    if not click_ctx.obj:
        click.echo("Error: CLI context not initialized", err=True)
        raise SystemExit(1)

    ctx: HexarchContext = click_ctx.obj
    formatter = ctx.formatter
    if output_format:
        formatter = OutputFormatter(format=output_format, colors=ctx.config_manager.get_config().output.colors)

    _init_db(ctx, db_url)

    session = DatabaseManager.get_session()
    rules = (
        session.query(Rule)
        .filter(Rule.is_deleted == False)
        .order_by(Rule.created_at.desc())
        .limit(limit)
        .all()
    )

    if formatter.format == "table":
        headers = ["ID", "NAME", "TYPE", "PRIORITY", "ENABLED"]
        data = [[r.id, r.name, r.rule_type, r.priority, "yes" if r.enabled else "no"] for r in rules]
        print(formatter.format_output(data, headers=headers))
    else:
        print(json.dumps([r.to_dict() for r in rules], indent=2, default=str))

    ctx.audit_logger.log_command("rule list", result=f"{len(rules)} rules")


@rule_group.command(name="get")
@click.argument("rule-id")
@click.option("--format", "output_format", type=click.Choice(["json", "table", "csv"]), default=None, help="Output format")
@click.option("--db-url", default=None, help="Override database URL")
@click.pass_context
def rule_get(click_ctx: click.Context, rule_id: str, output_format: Optional[str], db_url: Optional[str]) -> None:
    """Get a rule by ID from the local database."""
    if not click_ctx.obj:
        click.echo("Error: CLI context not initialized", err=True)
        raise SystemExit(1)

    ctx: HexarchContext = click_ctx.obj
    formatter = ctx.formatter
    if output_format:
        formatter = OutputFormatter(format=output_format, colors=ctx.config_manager.get_config().output.colors)

    _init_db(ctx, db_url)

    session = DatabaseManager.get_session()
    rule = session.query(Rule).filter(Rule.id == rule_id, Rule.is_deleted == False).first()

    if not rule:
        formatter.print_error(f"Rule not found: {rule_id}")
        raise SystemExit(1)

    if formatter.format == "table":
        headers = ["FIELD", "VALUE"]
        data = [[k, v] for k, v in rule.to_dict().items()]
        print(formatter.format_output(data, headers=headers))
    else:
        print(json.dumps(rule.to_dict(), indent=2, default=str))

    ctx.audit_logger.log_command("rule get", result=rule_id)


@rule_group.command(name="delete")
@click.argument("rule-id")
@click.option("--hard", is_flag=True, help="Permanently delete (no soft delete)")
@click.option("--db-url", default=None, help="Override database URL")
@click.pass_context
def rule_delete(click_ctx: click.Context, rule_id: str, hard: bool, db_url: Optional[str]) -> None:
    """Delete a rule (soft delete by default)."""
    if not click_ctx.obj:
        click.echo("Error: CLI context not initialized", err=True)
        raise SystemExit(1)

    ctx: HexarchContext = click_ctx.obj
    _init_db(ctx, db_url)

    session = DatabaseManager.get_session()
    rule = session.query(Rule).filter(Rule.id == rule_id).first()

    if not rule:
        ctx.formatter.print_error(f"Rule not found: {rule_id}")
        raise SystemExit(1)

    if hard:
        session.delete(rule)
    else:
        rule.soft_delete()

    session.commit()
    ctx.formatter.print_success(f"Rule deleted: {rule_id}")
    ctx.audit_logger.log_command("rule delete", result=rule_id)


@rule_group.command(name="evaluate")
@click.option("--rule-file", type=click.Path(exists=True), help="Rule file (JSON or YAML)")
@click.option("--rule-json", type=str, help="Inline JSON rule definition")
@click.option("--rule-yaml", type=str, help="Inline YAML rule definition")
@click.option("--context-file", type=click.Path(exists=True), help="Context file (JSON)")
@click.option("--context-json", type=str, help="Inline JSON context")
@click.option("--trace", is_flag=True, help="Include evaluation trace")
@click.option("--format", "output_format", type=click.Choice(["json", "table", "csv"]), default=None, help="Output format")
@click.pass_context
def rule_evaluate(
    click_ctx: click.Context,
    rule_file: Optional[str],
    rule_json: Optional[str],
    rule_yaml: Optional[str],
    context_file: Optional[str],
    context_json: Optional[str],
    trace: bool,
    output_format: Optional[str]
) -> None:
    """Evaluate a rule against a JSON context.

    
    Examples:
      hexarch-ctl rule evaluate --rule-file rule.yaml --context-file ctx.json
      hexarch-ctl rule evaluate --rule-json '{"field":"user.role","op":"equals","value":"admin"}' --context-json '{"user":{"role":"admin"}}'
      hexarch-ctl rule evaluate --rule-yaml "field: user.role\nop: equals\nvalue: admin" --context-json '{"user":{"role":"admin"}}'
    """
    if not click_ctx.obj:
        click.echo("Error: CLI context not initialized", err=True)
        raise SystemExit(1)

    ctx: HexarchContext = click_ctx.obj
    formatter = ctx.formatter

    try:
        if output_format:
            formatter = OutputFormatter(format=output_format, colors=ctx.config_manager.get_config().output.colors)

        rule_input = _load_rule_input(rule_file, rule_json, rule_yaml)
        context = _load_context_input(context_file, context_json)

        evaluator = RuleEvaluator()

        if trace:
            result = evaluator.evaluate_with_trace(rule_input, context)
            output = {
                "allowed": result.allowed,
                "trace": _serialize_trace(result.trace)
            }
        else:
            allowed = evaluator.evaluate_rule(rule_input, context)
            output = {"allowed": allowed}

        if formatter.format == "table":
            headers = ["ALLOWED"]
            data = [["yes" if output["allowed"] else "no"]]
            print(formatter.format_output(data, headers=headers))
        else:
            print(json.dumps(output, indent=2, default=str))

        ctx.audit_logger.log_command("rule evaluate", result="allowed" if output["allowed"] else "denied")

    except RuleEvaluationError as exc:
        formatter.print_error(f"Rule evaluation error: {str(exc)}")
        ctx.audit_logger.log_command("rule evaluate", error=str(exc))
        raise SystemExit(1)
    except Exception as exc:
        formatter.print_error(f"Unexpected error: {str(exc)}")
        ctx.audit_logger.log_command("rule evaluate", error=str(exc))
        raise SystemExit(1)


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


def _load_rule_input(rule_file: Optional[str], rule_json: Optional[str], rule_yaml: Optional[str]):
    provided = [p for p in [rule_file, rule_json, rule_yaml] if p]
    if len(provided) != 1:
        raise RuleEvaluationError("Provide exactly one of --rule-file, --rule-json, or --rule-yaml")

    if rule_file:
        path = Path(rule_file).expanduser()
        content = path.read_text()
        return content

    if rule_json:
        return rule_json

    return rule_yaml


def _load_rule_definition(rule_file: Optional[str], rule_json: Optional[str]) -> dict:
    provided = [p for p in [rule_file, rule_json] if p]
    if len(provided) != 1:
        raise RuleEvaluationError("Provide exactly one of --file or --json")

    if rule_file:
        path = Path(rule_file).expanduser()
        content = path.read_text()
        evaluator = RuleEvaluator()
        return evaluator.parse_rule(content)

    return json.loads(rule_json)


def _load_context_input(context_file: Optional[str], context_json: Optional[str]) -> dict:
    if not context_file and not context_json:
        return {}

    if context_file and context_json:
        raise RuleEvaluationError("Provide only one of --context-file or --context-json")

    if context_file:
        path = Path(context_file).expanduser()
        content = path.read_text()
        return json.loads(content)

    return json.loads(context_json)


def _serialize_trace(trace):
    if trace is None:
        return None
    if isinstance(trace, list):
        return [_serialize_trace(t) for t in trace]
    if hasattr(trace, "allowed"):
        return {"allowed": trace.allowed, "trace": _serialize_trace(trace.trace)}
    if isinstance(trace, dict):
        return {k: _serialize_trace(v) for k, v in trace.items()}
    return trace
