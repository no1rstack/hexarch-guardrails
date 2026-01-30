"""Node-RED helper commands.

These are convenience workflows for local guardrails testing.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import secrets
import socket
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, urlunparse
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from hexarch_cli.ops_events import OpsEvent, append_ops_event, read_ops_events

import click

from hexarch_cli.context import HexarchContext


def _http_json(
    method: str,
    url: str,
    *,
    headers: Optional[dict[str, str]] = None,
    body: Optional[dict] = None,
    timeout_seconds: float = 5.0,
) -> dict:
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")

    req = Request(url, method=method, data=data)
    req.add_header("Accept", "application/json")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)

    try:
        with urlopen(req, timeout=timeout_seconds) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except HTTPError as e:
        raw = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"HTTP {e.code} for {method} {url}: {raw}") from e
    except (URLError, TimeoutError) as e:
        raise RuntimeError(f"Request failed for {method} {url}: {e}") from e


def _wait_for_health(
    base_url: str, timeout_seconds: float = 15.0, *, headers: Optional[dict[str, str]] = None
) -> None:
    deadline = time.time() + timeout_seconds
    last_err: Optional[Exception] = None
    while time.time() < deadline:
        try:
            _http_json(
                "GET",
                f"{base_url}/health",
                timeout_seconds=2.0,
                headers=headers,
            )
            return
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(0.25)
    raise RuntimeError(f"Hexarch did not become healthy at {base_url}/health: {last_err}")


def _port_is_open(host: str, port: int, timeout_seconds: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout_seconds):
            return True
    except OSError:
        return False


def _docker_friendly_base_url(base_url: str) -> str:
    """Convert localhost URLs to a Docker-friendly hostname.

    Node-RED runs in a container, so it usually can't reach `localhost` on the host.
    Docker Desktop provides `host.docker.internal` for this use case.
    """

    parsed = urlparse(base_url)
    host = parsed.hostname or ""
    if host in {"127.0.0.1", "localhost"}:
        netloc = "host.docker.internal"
        if parsed.port:
            netloc = f"{netloc}:{parsed.port}"
        parsed = parsed._replace(netloc=netloc)
    return urlunparse(parsed)


def _host_friendly_base_url(base_url: str) -> str:
    """Convert Docker-only hostnames to a host-friendly address."""

    parsed = urlparse(base_url)
    host = parsed.hostname or ""
    if host == "host.docker.internal":
        netloc = "127.0.0.1"
        if parsed.port:
            netloc = f"{netloc}:{parsed.port}"
        parsed = parsed._replace(netloc=netloc)
    return urlunparse(parsed)


def _find_node_red_dir(start_dir: Path) -> Optional[Path]:
    """Find the node-red directory when running from either repo root or package root."""

    start_dir = start_dir.resolve()
    for base in [start_dir, *start_dir.parents]:
        direct = base / "node-red"
        if direct.is_dir():
            return direct
        nested = base / "hexarch-guardrails-py" / "node-red"
        if nested.is_dir():
            return nested
    return None


def _resolve_env_path(env_path: Path) -> Path:
    """Resolve default env path relative to repo/package layout."""

    if env_path.is_absolute():
        return env_path

    # If the caller runs from repo root, the default relative path won't exist.
    candidate = (Path.cwd() / env_path).resolve()
    if candidate.exists() or candidate.parent.exists():
        return candidate

    node_red_dir = _find_node_red_dir(Path.cwd())
    if node_red_dir and env_path.as_posix() in {"node-red/.env.node-red", "node-red\\.env.node-red", ".env.node-red"}:
        return (node_red_dir / ".env.node-red").resolve()

    # Also handle the common case where user wants node-red/.env.node-red but we're at repo root.
    if node_red_dir and env_path.name == ".env.node-red":
        return (node_red_dir / env_path.name).resolve()

    return candidate


def _resolve_scripts_dir() -> Path:
    # hexarch_cli/commands/node_red.py -> hexarch-guardrails-py/
    repo_root = Path(__file__).resolve().parents[2]
    return repo_root / "scripts"


def _resolve_node_red_compose_file() -> tuple[Path, Path]:
    """Return (node_red_dir, compose_file)."""

    node_red_dir = _find_node_red_dir(Path.cwd())
    if not node_red_dir:
        raise click.ClickException("Could not find node-red/ directory. Run from the repo or hexarch-guardrails-py.")
    compose = node_red_dir / "docker-compose.node-red.yml"
    if not compose.exists():
        raise click.ClickException(f"Missing compose file: {compose}")
    return node_red_dir, compose


def _run_compose(node_red_dir: Path, compose_file: Path, args: list[str]) -> int:
    cmd = ["docker", "compose", "-f", str(compose_file), *args]
    try:
        proc = subprocess.run(cmd, cwd=str(node_red_dir), check=False)  # noqa: S603
        return int(proc.returncode)
    except FileNotFoundError as e:
        raise click.ClickException(
            "Docker Compose not found. Install Docker Desktop and ensure `docker compose` works."
        ) from e


def _track(event_type: str, status: str, *, details: Optional[dict] = None) -> None:
    try:
        append_ops_event(OpsEvent.now(event_type, status, details=details or {}))
    except Exception:
        # Never block the CLI on tracking.
        return


def _read_dotenv(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        out[k.strip()] = v.strip()
    return out


@click.group(name="node-red")
def node_red_group() -> None:
    """Node-RED local workflow helpers."""


@node_red_group.command(name="bootstrap")
@click.option("--hexarch-url", default=None, help="Hexarch base URL (default: config.api.url)")
@click.option("--admin-token", default=None, help="Admin bearer token (default: config.api.token)")
@click.option("--actor-id", default="admin", show_default=True, help="Actor id used for admin calls")
@click.option("--key-name", default="node-red-local", show_default=True, help="API key name")
@click.option(
    "--scope",
    "scopes",
    multiple=True,
    default=("read", "write"),
    show_default=True,
    help="Repeatable. Scopes for the Node-RED API key.",
)
@click.option(
    "--env-out",
    type=click.Path(dir_okay=False, path_type=Path),
    default=Path("node-red/.env.node-red"),
    show_default=True,
    help="Where to write the Node-RED env file.",
)
@click.option(
    "--start-server",
    is_flag=True,
    help="Start a temporary Hexarch server (admin enabled), mint the key, then restart locked-down.",
)
@click.option("--host", default="127.0.0.1", show_default=True, help="Host to bind when --start-server")
@click.option("--port", default=8099, type=int, show_default=True, help="Port to bind when --start-server")
@click.option(
    "--database-url",
    default=None,
    help="DATABASE_URL to use when --start-server (otherwise uses current config/env defaults)",
)
@click.option("--init-db", is_flag=True, help="Create DB tables when --start-server")
@click.option(
    "--bootstrap-ttl-seconds",
    default=900,
    type=int,
    show_default=True,
    help="Bootstrap TTL used when --start-server.",
)
@click.option(
    "--leave-running/--no-leave-running",
    default=True,
    show_default=True,
    help="When --start-server, leave the locked-down server running after bootstrapping.",
)
@click.pass_obj
def node_red_bootstrap(
    ctx: HexarchContext,
    hexarch_url: Optional[str],
    admin_token: Optional[str],
    actor_id: str,
    key_name: str,
    scopes: tuple[str, ...],
    env_out: Path,
    start_server: bool,
    host: str,
    port: int,
    database_url: Optional[str],
    init_db: bool,
    bootstrap_ttl_seconds: int,
    leave_running: bool,
) -> None:
    """Mint a Node-RED API key and write node-red/.env.node-red.

    If --start-server is used, this command will:
    1) start Hexarch with --enable-api-key-admin
    2) create the API key
    3) restart Hexarch without API key admin

    Otherwise it will operate on an already-running Hexarch instance.
    """

    cfg = ctx.config_manager.get_config()

    if start_server:
        base_url = (hexarch_url or f"http://{host}:{port}").rstrip("/")
    else:
        base_url = (hexarch_url or cfg.api.url or f"http://{host}:{port}").rstrip("/")
    token = admin_token or cfg.api.token or os.getenv("HEXARCH_API_TOKEN")

    # If we're starting a temporary server, we can generate a strong token to avoid
    # making the user configure one up front.
    if start_server and not token:
        token = secrets.token_urlsafe(32)

    if not token:
        raise click.ClickException(
            "Missing admin token. Provide --admin-token, set HEXARCH_API_TOKEN, or run: hexarch-ctl config set --api-token <token>"
        )

    run_dir = Path(".run")
    run_dir.mkdir(parents=True, exist_ok=True)

    # Resolve default output path to match repo layout.
    env_out = _resolve_env_path(env_out)

    proc: subprocess.Popen[str] | None = None

    def start_hexarch(*, enable_api_key_admin: bool) -> subprocess.Popen[str]:
        args: list[str] = [
            "hexarch-ctl",
            "serve",
            "api",
            "--host",
            host,
            "--port",
            str(port),
            "--api-token",
            token,
        ]
        if enable_api_key_admin:
            args.append("--enable-api-key-admin")
        # Ensure bootstrap is explicit and time-bound.
        args.extend(["--bootstrap-allow", "--bootstrap-ttl-seconds", str(bootstrap_ttl_seconds)])
        if database_url:
            args.extend(["--database-url", database_url])
        if init_db:
            args.append("--init-db")

        stdout_path = run_dir / "hexarch-node-red-bootstrap.stdout.log"
        stderr_path = run_dir / "hexarch-node-red-bootstrap.stderr.log"
        stdout_f = stdout_path.open("a", encoding="utf-8")
        stderr_f = stderr_path.open("a", encoding="utf-8")

        return subprocess.Popen(args, stdout=stdout_f, stderr=stderr_f, text=True)  # noqa: S603

    try:
        _track(
            "node_red_bootstrap",
            "start",
            details={"hexarch_url": base_url, "env_out": str(env_out), "start_server": start_server},
        )
        if start_server:
            # Refuse to collide with an existing process on this port.
            parsed = urlparse(base_url)
            check_host = parsed.hostname or host
            check_port = parsed.port or port
            if _port_is_open(check_host, check_port):
                # If it is Hexarch, /health should respond (with auth).
                try:
                    _wait_for_health(
                        base_url,
                        timeout_seconds=1.0,
                        headers={"Authorization": f"Bearer {token}"},
                    )
                    raise click.ClickException(
                        f"Hexarch already appears to be running at {base_url}. "
                        "Stop it first, use a different --port, or omit --start-server to use the existing server."
                    )
                except Exception as e:  # noqa: BLE001
                    msg = str(e)
                    if "HTTP 401" in msg or "HTTP 403" in msg:
                        raise click.ClickException(
                            f"Hexarch (or another auth-protected service) is already listening at {base_url}, "
                            "but the provided admin token was rejected. "
                            "Stop the running server, or omit --start-server and re-run with --admin-token that matches it."
                        ) from e

                    raise click.ClickException(
                        f"Port {check_port} on {check_host} is already in use. "
                        "Stop the process using that port or choose a different --port."
                    ) from e

            # Persist the generated token for the user in case they want to reuse it.
            if not admin_token and not cfg.api.token and not os.getenv("HEXARCH_API_TOKEN"):
                (run_dir / "hexarch-node-red-bootstrap.admin-token.txt").write_text(
                    token, encoding="utf-8"
                )

            proc = start_hexarch(enable_api_key_admin=True)
            _wait_for_health(
                base_url,
                timeout_seconds=20.0,
                headers={"Authorization": f"Bearer {token}"},
            )

        # Create API key
        headers = {"Authorization": f"Bearer {token}", "X-Actor-Id": actor_id}
        payload = {
            "name": key_name,
            "description": "Node-RED single-user milestone key",
            "tenant_id": None,
            "org_id": None,
            "scopes": list(scopes),
        }
        resp = _http_json("POST", f"{base_url}/api-keys", headers=headers, body=payload)

        api_key_token = resp.get("token")
        token_prefix = resp.get("token_prefix")
        if not api_key_token or not token_prefix:
            raise click.ClickException(
                "Unexpected response from /api-keys. "
                "Ensure the server is started with --enable-api-key-admin."
            )

        env_out.parent.mkdir(parents=True, exist_ok=True)
        docker_base_url = _docker_friendly_base_url(base_url)
        env_text = "\n".join(
            [
                "# Generated by: hexarch-ctl node-red bootstrap",
                f"HEXARCH_BASE_URL={docker_base_url}",
                f"HEXARCH_TOKEN={api_key_token}",
                "",
            ]
        )
        env_out.write_text(env_text, encoding="utf-8")

        ctx.formatter.print_success(f"Wrote {env_out}")
        ctx.formatter.print_success(f"API key token prefix: {token_prefix}")
        _track("node_red_bootstrap", "success", details={"env_out": str(env_out), "token_prefix": token_prefix})

        if start_server and proc is not None:
            # Stop admin-enabled server.
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except Exception:
                proc.kill()

            if leave_running:
                locked = start_hexarch(enable_api_key_admin=False)
                _wait_for_health(base_url, timeout_seconds=20.0)
                ctx.formatter.print_success(
                    f"Restarted Hexarch without API key admin (pid={locked.pid}). Logs: {run_dir}"
                )
                if (run_dir / "hexarch-node-red-bootstrap.admin-token.txt").exists():
                    ctx.formatter.print_success(
                        f"Admin token saved to {run_dir / 'hexarch-node-red-bootstrap.admin-token.txt'}"
                    )
            else:
                ctx.formatter.print_success("Stopped temporary Hexarch server")

    except RuntimeError as e:
        # Provide a helpful hint for the common case.
        msg = str(e)
        if "/api-keys" in msg and "HTTP 404" in msg:
            raise click.ClickException(
                "API key admin endpoints are disabled. Start Hexarch with --enable-api-key-admin, "
                "or re-run with --start-server."
            ) from e
        _track("node_red_bootstrap", "error", details={"error": msg})
        raise click.ClickException(msg) from e


@node_red_group.command(name="verify")
@click.option(
    "--node-red-url",
    default="http://127.0.0.1:1880",
    show_default=True,
    help="Node-RED base URL.",
)
@click.option(
    "--hexarch-url",
    default=None,
    help="Hexarch base URL. If omitted, reads HEXARCH_BASE_URL from --env-file.",
)
@click.option(
    "--env-file",
    type=click.Path(dir_okay=False, path_type=Path),
    default=Path("node-red/.env.node-red"),
    show_default=True,
    help="Reads HEXARCH_BASE_URL and HEXARCH_TOKEN from here.",
)
@click.option(
    "--chain-id",
    default="global",
    show_default=True,
    help="Audit chain id to verify.",
)
@click.option(
    "--limit",
    default=50,
    type=int,
    show_default=True,
    help="How many audit entries to verify.",
)
@click.option(
    "--run/--no-run",
    default=True,
    show_default=True,
    help="Trigger Node-RED POST /hexarch/run before verification.",
)
@click.pass_obj
def node_red_verify(
    ctx: HexarchContext,
    node_red_url: str,
    hexarch_url: Optional[str],
    env_file: Path,
    chain_id: str,
    limit: int,
    run: bool,
) -> None:
    """Trigger the Node-RED flow and verify Hexarch evidence endpoints."""

    node_red_base = node_red_url.rstrip("/")
    env_file = _resolve_env_path(env_file)
    env = _read_dotenv(env_file)
    base_url = (hexarch_url or env.get("HEXARCH_BASE_URL") or "").rstrip("/")
    token = env.get("HEXARCH_TOKEN")

    if not base_url:
        raise click.ClickException(
            f"Missing Hexarch URL. Provide --hexarch-url or ensure {env_file} contains HEXARCH_BASE_URL."
        )
    if not token:
        raise click.ClickException(
            f"Missing HEXARCH_TOKEN in {env_file}. Run: hexarch-ctl node-red bootstrap"
        )

    try:
        _track(
            "node_red_verify",
            "start",
            details={"node_red_url": node_red_base, "hexarch_url": base_url, "env_file": str(env_file)},
        )
        if run:
            run_resp = _http_json("POST", f"{node_red_base}/hexarch/run", body={})
            ok = run_resp.get("ok")
            ctx.formatter.print_success(
                f"Node-RED run: ok={ok} id={run_resp.get('id')} action={run_resp.get('action')}"
            )

        headers = {"Authorization": f"Bearer {token}"}

        # The env file is written for container use; on host we may need to map back.
        host_base_url = _host_friendly_base_url(base_url)
        _http_json("GET", f"{host_base_url}/health", headers=headers, timeout_seconds=3.0)

        provider_calls = _http_json("GET", f"{host_base_url}/events/provider-calls", headers=headers)
        verify = _http_json(
            "GET",
            f"{host_base_url}/audit-logs/verify?chain_id={chain_id}&limit={limit}",
            headers=headers,
        )

        calls_count = len(provider_calls) if isinstance(provider_calls, list) else None
        ctx.formatter.print_success(f"Hexarch provider-calls count: {calls_count}")
        ctx.formatter.print_success(
            f"Audit verify: ok={verify.get('ok')} verified={verify.get('verified')} errors={verify.get('errors')}"
        )
        _track(
            "node_red_verify",
            "success",
            details={"provider_calls_count": calls_count, "audit_ok": verify.get("ok"), "verified": verify.get("verified")},
        )

    except Exception as e:  # noqa: BLE001
        _track("node_red_verify", "error", details={"error": str(e)})
        raise click.ClickException(str(e)) from e


@node_red_group.command(name="up")
@click.option("--detach/--no-detach", default=True, show_default=True, help="Run in background")
@click.option("--pull", is_flag=True, help="Pull latest image")
@click.option("--build", is_flag=True, help="Build (not usually needed)")
@click.option("--open", "open_browser", is_flag=True, help="Open http://localhost:1880 in a browser")
@click.pass_obj
def node_red_up(ctx: HexarchContext, detach: bool, pull: bool, build: bool, open_browser: bool) -> None:
    """Start Node-RED via Docker Compose."""

    node_red_dir, compose = _resolve_node_red_compose_file()

    args = ["up"]
    if detach:
        args.append("-d")
    if pull:
        args.append("--pull")
        args.append("always")
    if build:
        args.append("--build")

    _track("node_red_up", "start", details={"detach": detach, "pull": pull, "build": build})
    code = _run_compose(node_red_dir, compose, args)
    if code != 0:
        _track("node_red_up", "error", details={"exit": code})
        raise click.ClickException(f"docker compose up failed (exit={code})")

    ctx.formatter.print_success("Node-RED is starting")
    ctx.formatter.print_success("Open: http://localhost:1880")
    _track("node_red_up", "success", details={"exit": 0})

    if open_browser:
        import webbrowser

        webbrowser.open("http://localhost:1880")


@node_red_group.command(name="down")
@click.option("--volumes", is_flag=True, help="Also remove volumes (DANGEROUS: deletes Node-RED data)")
@click.pass_obj
def node_red_down(ctx: HexarchContext, volumes: bool) -> None:
    """Stop Node-RED via Docker Compose."""

    node_red_dir, compose = _resolve_node_red_compose_file()
    args = ["down"]
    if volumes:
        args.append("--volumes")
    _track("node_red_down", "start", details={"volumes": volumes})
    code = _run_compose(node_red_dir, compose, args)
    if code != 0:
        _track("node_red_down", "error", details={"exit": code})
        raise click.ClickException(f"docker compose down failed (exit={code})")
    ctx.formatter.print_success("Node-RED stopped")
    _track("node_red_down", "success", details={"exit": 0})


@node_red_group.command(name="evidence")
@click.option(
    "--env-file",
    type=click.Path(dir_okay=False, path_type=Path),
    default=Path("node-red/.env.node-red"),
    show_default=True,
    help="Reads HEXARCH_BASE_URL and HEXARCH_TOKEN from here.",
)
@click.option(
    "--node-red-url",
    default=None,
    help="Override Node-RED base URL (default from script: http://localhost:1880)",
)
@click.pass_obj
def node_red_evidence(ctx: HexarchContext, env_file: Path, node_red_url: Optional[str]) -> None:
    """Export a dated Markdown evidence file for the Node-RED milestone."""

    env_file = _resolve_env_path(env_file)
    env = os.environ.copy()
    env_map = _read_dotenv(env_file)

    token = env_map.get("HEXARCH_TOKEN")
    if token:
        env["HEXARCH_TOKEN"] = token

    base_url = env_map.get("HEXARCH_BASE_URL")
    if base_url:
        env["HEXARCH_BASE_URL"] = _host_friendly_base_url(base_url)

    if node_red_url:
        env["NODE_RED_BASE_URL"] = node_red_url.rstrip("/")

    script = _resolve_scripts_dir() / "export_node_red_milestone_evidence.py"
    if not script.exists():
        raise click.ClickException(f"Missing evidence script: {script}")

    _track("node_red_evidence", "start", details={"env_file": str(env_file), "node_red_url": node_red_url})
    proc = subprocess.run([sys.executable, str(script)], env=env, check=False)  # noqa: S603
    if proc.returncode != 0:
        _track("node_red_evidence", "error", details={"exit": proc.returncode})
        raise click.ClickException(f"Evidence export failed (exit={proc.returncode})")

    ctx.formatter.print_success("Evidence exported")
    _track("node_red_evidence", "success", details={"exit": 0})


@node_red_group.command(name="logs")
@click.option("--follow/--no-follow", default=True, show_default=True, help="Follow logs")
@click.option("--tail", default=200, type=int, show_default=True, help="Number of lines to show")
@click.option("--timestamps", is_flag=True, help="Show timestamps")
@click.pass_obj
def node_red_logs(ctx: HexarchContext, follow: bool, tail: int, timestamps: bool) -> None:
    """Show Node-RED container logs."""

    node_red_dir, compose = _resolve_node_red_compose_file()
    args = ["logs", "--tail", str(tail)]
    if follow:
        args.append("-f")
    if timestamps:
        args.append("--timestamps")

    _track("node_red_logs", "start", details={"follow": follow, "tail": tail, "timestamps": timestamps})
    code = _run_compose(node_red_dir, compose, args)
    if code != 0:
        _track("node_red_logs", "error", details={"exit": code})
        raise click.ClickException(f"docker compose logs failed (exit={code})")
    _track("node_red_logs", "success", details={"exit": 0})


@node_red_group.command(name="history")
@click.option("--limit", default=25, type=int, show_default=True, help="How many events to show")
@click.pass_obj
def node_red_history(ctx: HexarchContext, limit: int) -> None:
    """Show recent tracked Node-RED ops events."""

    events = [e for e in read_ops_events(limit=1000) if e.event_type.startswith("node_red_")]
    for e in events[-limit:]:
        ctx.formatter.print_info(f"{e.ts} {e.event_type} {e.status}")


__all__ = ["node_red_group"]
