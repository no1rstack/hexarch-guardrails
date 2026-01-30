import os
import click


@click.group(name="serve")
def serve_group() -> None:
    """Run the local Hexarch REST API (for UI/dev)."""


@serve_group.command(name="api")
@click.option("--host", default="127.0.0.1", show_default=True, help="Bind host")
@click.option("--port", default=8000, show_default=True, type=int, help="Bind port")
@click.option("--reload", is_flag=True, help="Auto-reload on code changes")
@click.option("--init-db", is_flag=True, help="Create tables (dev convenience)")
@click.option("--api-token", default=None, help="Bearer token required by the API")
@click.option(
    "--allow-anon",
    is_flag=True,
    help="Allow unauthenticated access (NOT recommended)",
)
@click.option(
    "--cors-origins",
    default=None,
    help="Comma-separated CORS allowlist (e.g. http://localhost:5173)",
)
@click.option(
    "--enable-docs",
    is_flag=True,
    help="Enable Swagger/OpenAPI endpoints (/docs, /openapi.json)",
)
@click.option(
    "--database-url",
    default=None,
    help="Override DATABASE_URL (recommended for production)",
)
@click.option(
    "--database-provider",
    type=click.Choice(["sqlite", "postgresql"], case_sensitive=False),
    default=None,
    help="Set DATABASE_PROVIDER if DATABASE_URL is not provided",
)
@click.option(
    "--database-path",
    default=None,
    help="SQLite file path when using sqlite provider",
)
@click.option(
    "--rate-limit-rpm",
    default=None,
    type=int,
    help="Per-IP requests/minute limit (default 120)",
)
@click.option(
    "--disable-rate-limit",
    is_flag=True,
    help="Disable rate limiting (NOT recommended)",
)
@click.option(
    "--bootstrap-allow",
    is_flag=True,
    help="Enable bootstrap allowlist for initial setup (permits creating policies/rules when DB is empty).",
)
@click.option(
    "--bootstrap-ttl-seconds",
    default=None,
    type=int,
    help="If bootstrap is enabled, limit it to N seconds (recommended).",
)
@click.option(
    "--enable-api-key-admin",
    is_flag=True,
    help="Enable API key admin endpoints (/api-keys). Disabled by default.",
)
def serve_api(
    host: str,
    port: int,
    reload: bool,
    init_db: bool,
    api_token: str | None,
    allow_anon: bool,
    cors_origins: str | None,
    enable_docs: bool,
    database_url: str | None,
    database_provider: str | None,
    database_path: str | None,
    rate_limit_rpm: int | None,
    disable_rate_limit: bool,
    bootstrap_allow: bool,
    bootstrap_ttl_seconds: int | None,
    enable_api_key_admin: bool,
) -> None:
    """Start the FastAPI server via uvicorn."""
    try:
        import uvicorn
    except Exception as exc:
        raise click.ClickException(
            "Missing server dependencies. Install with: pip install 'hexarch-guardrails[server]'"
        ) from exc

    # Security defaults
    if api_token:
        os.environ["HEXARCH_API_TOKEN"] = api_token
    if allow_anon:
        os.environ["HEXARCH_API_ALLOW_ANON"] = "true"
    if cors_origins:
        os.environ["HEXARCH_CORS_ORIGINS"] = cors_origins
    if enable_docs:
        os.environ["HEXARCH_API_DOCS"] = "true"

    # Bootstrap controls (off by default in the server)
    if bootstrap_allow:
        os.environ["HEXARCH_BOOTSTRAP_ALLOW"] = "true"
    if bootstrap_ttl_seconds is not None:
        os.environ["HEXARCH_BOOTSTRAP_TTL_SECONDS"] = str(bootstrap_ttl_seconds)

    # API key admin endpoints are gated off by default.
    if enable_api_key_admin:
        os.environ["HEXARCH_API_KEY_ADMIN_ENABLED"] = "true"

    if disable_rate_limit:
        os.environ["HEXARCH_RATE_LIMIT_ENABLED"] = "false"
    if rate_limit_rpm is not None:
        os.environ["HEXARCH_RATE_LIMIT_RPM"] = str(rate_limit_rpm)

    # DB selection: default to SQLite unless explicitly overridden.
    if database_url:
        os.environ["DATABASE_URL"] = database_url
    else:
        if database_provider:
            os.environ["DATABASE_PROVIDER"] = database_provider.lower()
        else:
            os.environ.setdefault("DATABASE_PROVIDER", "sqlite")

        if database_path:
            os.environ["DATABASE_PATH"] = database_path
        else:
            os.environ.setdefault("DATABASE_PATH", "./hexarch.db")

    # If init_db is requested, initialize tables before starting.
    if init_db:
        from hexarch_cli.db import DatabaseManager

        DatabaseManager.initialize()
        DatabaseManager.create_all()

    uvicorn.run(
        "hexarch_cli.server.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )
