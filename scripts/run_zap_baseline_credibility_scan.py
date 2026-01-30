from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests


@dataclass(frozen=True)
class ServerConfig:
    host: str
    port: int
    token: str
    allow_anon: bool
    db_path: Path


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


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


def _find_executable(root: Path, name: str) -> str:
    venv_candidate = root / ".venv" / "Scripts" / (name + (".exe" if os.name == "nt" else ""))
    if venv_candidate.exists():
        return str(venv_candidate)
    found = shutil.which(name)
    if found:
        return found
    raise RuntimeError(f"Could not find executable '{name}'. Is it installed in your environment?")


def _docker_host_for_local_server() -> str:
    # In Docker Desktop (Windows/macOS), containers reach host via host.docker.internal.
    if sys.platform.startswith("win") or sys.platform == "darwin":
        return "host.docker.internal"
    # On Linux, we prefer host networking.
    return "127.0.0.1"


def _write_meta(out_dir: Path, cfg: ServerConfig, *, zap_image: str, zap_args: list[str]) -> None:
    meta = {
        "tool": "owasp-zap",
        "mode": "baseline",
        "timestamp_utc": _utc_stamp(),
        "server": {
            "base_url": f"http://{cfg.host}:{cfg.port}",
            "docs_enabled": True,
            "allow_anon": cfg.allow_anon,
        },
        "zap": {
            "image": zap_image,
            "args": zap_args,
        },
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


def main() -> int:
    root = _repo_root()

    mins = int(os.getenv("HEXARCH_ZAP_MINS", "1"))
    max_wait_mins = int(os.getenv("HEXARCH_ZAP_MAX_WAIT_MINS", "5"))
    ignore_warn = os.getenv("HEXARCH_ZAP_IGNORE_WARN", "true").strip().lower() in {"1", "true", "yes", "y", "on"}
    allow_anon = os.getenv("HEXARCH_ZAP_ALLOW_ANON", "false").strip().lower() in {"1", "true", "yes", "y", "on"}
    ignore_rules_raw = os.getenv("HEXARCH_ZAP_IGNORE_RULES", "10049")
    ignore_rules = [r.strip() for r in ignore_rules_raw.split(",") if r.strip()]

    evidence_root = root / "evidence" / "credibility" / "zap-baseline" / _utc_stamp()
    _ensure_dir(evidence_root)

    host = "127.0.0.1"
    port = _pick_free_port()
    token = os.getenv("HEXARCH_API_TOKEN") or "credibility-static-token"

    db_dir = evidence_root / "db"
    _ensure_dir(db_dir)
    db_path = db_dir / "credibility.db"

    cfg = ServerConfig(host=host, port=port, token=token, allow_anon=allow_anon, db_path=db_path)

    env = os.environ.copy()
    env.update(
        {
            "HEXARCH_API_DOCS": "true",
            "HEXARCH_RATE_LIMIT_ENABLED": "false",
            "HEXARCH_API_ALLOW_ANON": "true" if cfg.allow_anon else "false",
            "HEXARCH_API_TOKEN": cfg.token,
            "DATABASE_PROVIDER": "sqlite",
            "DATABASE_PATH": str(cfg.db_path),
            "PYTHONUTF8": "1",
            "PYTHONIOENCODING": "utf-8",
        }
    )

    hexarch_ctl = _find_executable(root, "hexarch-ctl")
    docker = _find_executable(root, "docker")

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
    if cfg.allow_anon:
        server_cmd.append("--allow-anon")

    server_log = (evidence_root / "server.log").open("w", encoding="utf-8")
    proc = subprocess.Popen(server_cmd, env=env, stdout=server_log, stderr=subprocess.STDOUT)  # noqa: S603

    try:
        base_url = f"http://{cfg.host}:{cfg.port}"
        _wait_for_health(base_url)

        zap_image = os.getenv("HEXARCH_ZAP_IMAGE", "ghcr.io/zaproxy/zaproxy:stable")

        # Target URL as seen from inside the container.
        docker_host = _docker_host_for_local_server()
        target = f"http://{docker_host}:{cfg.port}"

        # Output files written inside /zap/wrk.
        report_html = "zap-report.html"
        report_md = "zap-report.md"
        report_json = "zap-report.json"
        report_xml = "zap-report.xml"

        # Optional rule config to make results less noisy while remaining explicit/reproducible.
        # By default ignores rule 10049 (Non-Storable Content), which often flags intentionally no-store responses.
        config_filename = "zap-baseline.conf"
        config_path = evidence_root / config_filename
        if ignore_rules:
            lines = [
                "# zap-baseline rule configuration file",
                "# Change WARN to IGNORE to ignore rule or FAIL to fail if rule matches",
            ]
            for rule_id in ignore_rules:
                lines.append(f"{rule_id}\tIGNORE\t(hexarch-credibility-ignore)")
            config_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        zap_args = [
            "zap-baseline.py",
            "-t",
            target,
            "-m",
            str(max(1, mins)),
            "-T",
            str(max(1, max_wait_mins)),
            "-c",
            config_filename,
            "-r",
            report_html,
            "-w",
            report_md,
            "-J",
            report_json,
            "-x",
            report_xml,
        ]
        if ignore_warn:
            zap_args.append("-I")

        docker_cmd = [
            docker,
            "run",
            "--rm",
            "-t",
            "-v",
            f"{str(evidence_root)}:/zap/wrk/:rw",
            zap_image,
            *zap_args,
        ]

        # On Linux, prefer host networking for local connectivity.
        if not (sys.platform.startswith("win") or sys.platform == "darwin"):
            docker_cmd = [
                docker,
                "run",
                "--rm",
                "-t",
                "--network",
                "host",
                "-v",
                f"{str(evidence_root)}:/zap/wrk/:rw",
                zap_image,
                *zap_args,
            ]

        _write_meta(evidence_root, cfg, zap_image=zap_image, zap_args=zap_args)

        completed = subprocess.run(  # noqa: S603
            docker_cmd,
            cwd=str(root),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        (evidence_root / "zap-stdout.txt").write_text(completed.stdout or "", encoding="utf-8")
        (evidence_root / "zap-stderr.txt").write_text(completed.stderr or "", encoding="utf-8")
        (evidence_root / "zap-exit.json").write_text(
            json.dumps({"exit_code": int(completed.returncode)}, indent=2),
            encoding="utf-8",
        )

        # Don't crash if ZAP returns WARN/FAIL exit codes; evidence is still useful.
        # Set HEXARCH_ZAP_STRICT=true to propagate the exit code.
        strict = os.getenv("HEXARCH_ZAP_STRICT", "false").strip().lower() in {"1", "true", "yes", "y", "on"}
        return int(completed.returncode) if strict else 0
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
