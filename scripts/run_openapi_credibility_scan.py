from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import shutil

import requests


@dataclass(frozen=True)
class ServerConfig:
    host: str
    port: int
    token: str
    db_path: Path


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _find_executable(root: Path, name: str) -> str:
    venv_candidate = root / ".venv" / "Scripts" / (name + (".exe" if os.name == "nt" else ""))
    if venv_candidate.exists():
        return str(venv_candidate)
    found = shutil.which(name)
    if found:
        return found
    raise RuntimeError(f"Could not find executable '{name}'. Is it installed in your environment?")


def _wait_for_health(base_url: str, timeout_s: float = 15.0) -> None:
    deadline = time.time() + timeout_s
    last_err: Optional[Exception] = None
    while time.time() < deadline:
        try:
            r = requests.get(f"{base_url}/health", timeout=2)
            if r.status_code == 200:
                return
        except Exception as exc:  # noqa: BLE001
            last_err = exc
        time.sleep(0.25)
    raise RuntimeError(f"Server did not become healthy within {timeout_s}s. Last error: {last_err!r}")


def _write_meta(out_dir: Path, cfg: ServerConfig) -> None:
    meta = {
        "tool": "schemathesis",
        "schema": "openapi",
        "base_url": f"http://{cfg.host}:{cfg.port}",
        "openapi_url": f"http://{cfg.host}:{cfg.port}/openapi.json",
        "timestamp_utc": _utc_stamp(),
        "env": {
            "HEXARCH_API_DOCS": "true",
            "HEXARCH_RATE_LIMIT_ENABLED": "false",
            "HEXARCH_API_ALLOW_ANON": "false",
            "DATABASE_PROVIDER": "sqlite",
            "DATABASE_PATH": str(cfg.db_path),
        },
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


def main() -> int:
    root = _repo_root()
    evidence_root = root / "evidence" / "credibility" / "openapi-schemathesis" / _utc_stamp()
    _ensure_dir(evidence_root)

    host = "127.0.0.1"
    port = _pick_free_port()
    token = os.getenv("HEXARCH_API_TOKEN") or "credibility-static-token"

    db_dir = evidence_root / "db"
    _ensure_dir(db_dir)
    db_path = db_dir / "credibility.db"

    cfg = ServerConfig(host=host, port=port, token=token, db_path=db_path)
    _write_meta(evidence_root, cfg)

    # Start server as a child process so Schemathesis can hit it over HTTP.
    env = os.environ.copy()
    env.update(
        {
            "HEXARCH_API_DOCS": "true",
            "HEXARCH_RATE_LIMIT_ENABLED": "false",
            "HEXARCH_API_ALLOW_ANON": "false",
            "HEXARCH_API_TOKEN": cfg.token,
            "DATABASE_PROVIDER": "sqlite",
            "DATABASE_PATH": str(cfg.db_path),
            # Ensure UTF-8 output across subprocesses (Click/Schemathesis on Windows).
            "PYTHONUTF8": "1",
            "PYTHONIOENCODING": "utf-8",
        }
    )

    hexarch_ctl = _find_executable(root, "hexarch-ctl")
    schemathesis = _find_executable(root, "schemathesis")

    server_cmd = [
        hexarch_ctl,
        "serve",
        "api",
        "--host",
        cfg.host,
        "--port",
        str(cfg.port),
        "--init-db",
        "--enable-docs",
        "--disable-rate-limit",
        "--api-token",
        cfg.token,
    ]

    server_log = (evidence_root / "server.log").open("w", encoding="utf-8")
    proc = subprocess.Popen(server_cmd, env=env, stdout=server_log, stderr=subprocess.STDOUT)  # noqa: S603

    base_url = f"http://{cfg.host}:{cfg.port}"

    try:
        _wait_for_health(base_url)

        openapi_url = f"{base_url}/openapi.json"

        junit_path = evidence_root / "schemathesis-junit.xml"
        ndjson_path = evidence_root / "schemathesis-events.ndjson"

        max_examples = os.getenv("HEXARCH_CREDIBILITY_MAX_EXAMPLES", "25")

        # Run Schemathesis with a single hard credibility check: "no 5xx".
        # This demonstrates robustness under generated inputs without requiring perfect OpenAPI response modeling.
        scan_cmd = [
            schemathesis,
            "run",
            "--no-color",
            openapi_url,
            "--checks",
            "not_a_server_error",
            "--header",
            f"Authorization:Bearer {cfg.token}",
            "--header",
            "X-Actor-Id:credibility-harness",
            "--max-examples",
            str(max_examples),
            "--report-junit-path",
            str(junit_path),
            "--report",
            "ndjson",
            "--report-ndjson-path",
            str(ndjson_path),
        ]

        completed = subprocess.run(  # noqa: S603
            scan_cmd,
            cwd=str(root),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        (evidence_root / "schemathesis-stdout.txt").write_text(completed.stdout or "", encoding="utf-8")
        (evidence_root / "schemathesis-stderr.txt").write_text(completed.stderr or "", encoding="utf-8")

        return int(completed.returncode)
    finally:
        try:
            proc.terminate()
        except Exception:
            pass
        try:
            proc.wait(timeout=8)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        try:
            server_log.close()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
