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
from typing import Any, Optional

import requests


@dataclass(frozen=True)
class ServerConfig:
    host: str
    port: int
    token: str
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


def _load_cases(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or "steps" not in raw:
        raise ValueError("Invalid cases file: expected object with 'steps'")
    return raw


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "X-Actor-Id": "credibility-harness",
        "Content-Type": "application/json",
    }


def _write_report(out_dir: Path, *, meta: dict[str, Any], results: list[dict[str, Any]]) -> None:
    (out_dir / "results.json").write_text(
        json.dumps({"meta": meta, "results": results}, indent=2),
        encoding="utf-8",
    )

    passed = sum(1 for r in results if r.get("ok") is True)
    failed = sum(1 for r in results if r.get("ok") is False)

    lines: list[str] = []
    lines.append(f"# Policy Credibility Evals ({meta.get('timestamp_utc')})")
    lines.append("")
    lines.append(f"- Base URL: {meta.get('base_url')}")
    lines.append(f"- Cases: {meta.get('cases_name')}")
    lines.append(f"- Steps: {len(results)} | Passed: {passed} | Failed: {failed}")
    lines.append("")

    for r in results:
        status = "PASS" if r.get("ok") else "FAIL"
        lines.append(f"## {status}: {r.get('id')}")
        lines.append("")
        if r.get("message"):
            lines.append(f"{r['message']}")
            lines.append("")
        if r.get("expected") is not None:
            lines.append("Expected:")
            lines.append("```json")
            lines.append(json.dumps(r["expected"], indent=2))
            lines.append("```")
            lines.append("")
        if r.get("actual") is not None:
            lines.append("Actual:")
            lines.append("```json")
            lines.append(json.dumps(r["actual"], indent=2))
            lines.append("```")
            lines.append("")

    (out_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    root = _repo_root()

    cases_path = Path(os.getenv("HEXARCH_POLICY_EVAL_CASES", str(root / "evals" / "policy_cases.json")))
    cases = _load_cases(cases_path)

    out_dir = root / "evidence" / "credibility" / "policy-evals" / _utc_stamp()
    _ensure_dir(out_dir)

    host = "127.0.0.1"
    port = _pick_free_port()
    token = os.getenv("HEXARCH_API_TOKEN") or "credibility-static-token"

    db_dir = out_dir / "db"
    _ensure_dir(db_dir)
    db_path = db_dir / "credibility.db"

    cfg = ServerConfig(host=host, port=port, token=token, db_path=db_path)

    # Force an isolated DB for credibility runs. If the user's shell has DATABASE_URL
    # set, it would otherwise override DATABASE_PROVIDER/PATH and leak in existing policies.
    sqlite_db_url = f"sqlite:///{cfg.db_path.as_posix()}"

    env = os.environ.copy()
    env.update(
        {
            "HEXARCH_API_DOCS": "true",
            "HEXARCH_RATE_LIMIT_ENABLED": "false",
            "HEXARCH_API_ALLOW_ANON": "false",
            "HEXARCH_API_TOKEN": cfg.token,
            "HEXARCH_BOOTSTRAP_ALLOW": "true",
            "HEXARCH_BOOTSTRAP_TTL_SECONDS": os.getenv("HEXARCH_BOOTSTRAP_TTL_SECONDS", "600"),
            "DATABASE_URL": sqlite_db_url,
            "DATABASE_PROVIDER": "sqlite",
            "DATABASE_PATH": str(cfg.db_path),
            "PYTHONUTF8": "1",
            "PYTHONIOENCODING": "utf-8",
        }
    )

    hexarch_ctl = _find_executable(root, "hexarch-ctl")

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
        "--bootstrap-allow",
        "--bootstrap-ttl-seconds",
        str(int(env["HEXARCH_BOOTSTRAP_TTL_SECONDS"])),
    ]

    server_log = (out_dir / "server.log").open("w", encoding="utf-8")
    proc = subprocess.Popen(server_cmd, env=env, stdout=server_log, stderr=subprocess.STDOUT)  # noqa: S603

    results: list[dict[str, Any]] = []
    base_url = f"http://{cfg.host}:{cfg.port}"

    meta = {
        "timestamp_utc": out_dir.name,
        "base_url": base_url,
        "cases_name": cases.get("name"),
        "cases_path": str(cases_path),
    }

    try:
        _wait_for_health(base_url)

        for step in cases.get("steps", []):
            step_id = step.get("id")
            step_type = step.get("type")
            payload = step.get("request") or {}
            expect = step.get("expect")

            if not step_id or not step_type:
                results.append({"id": step_id or "<missing>", "ok": False, "message": "Invalid step: missing id/type"})
                continue

            try:
                if step_type == "authorize":
                    r = requests.post(
                        f"{base_url}/authorize",
                        headers=_headers(cfg.token),
                        json=payload,
                        timeout=10,
                    )
                    data = r.json() if r.content else {}
                    ok = True
                    mismatches: list[str] = []

                    if expect is not None:
                        for k, v in expect.items():
                            if data.get(k) != v:
                                ok = False
                                mismatches.append(f"{k} expected {v!r} got {data.get(k)!r}")

                    results.append(
                        {
                            "id": step_id,
                            "type": step_type,
                            "ok": ok,
                            "message": "; ".join(mismatches) if mismatches else None,
                            "expected": expect,
                            "actual": {"status_code": r.status_code, **data},
                        }
                    )

                elif step_type == "create_policy":
                    r = requests.post(
                        f"{base_url}/policies",
                        headers=_headers(cfg.token),
                        json=payload,
                        timeout=10,
                    )
                    data = r.json() if r.content else {}
                    ok = r.status_code in {200, 201}
                    results.append(
                        {
                            "id": step_id,
                            "type": step_type,
                            "ok": ok,
                            "message": None if ok else f"Unexpected status {r.status_code}",
                            "expected": {"status_code": 200},
                            "actual": {"status_code": r.status_code, **data},
                        }
                    )

                else:
                    results.append({"id": step_id, "type": step_type, "ok": False, "message": f"Unknown step type: {step_type}"})

            except Exception as exc:  # noqa: BLE001
                results.append({"id": step_id, "type": step_type, "ok": False, "message": repr(exc)})

        _write_report(out_dir, meta=meta, results=results)
        all_ok = all(r.get("ok") is True for r in results)
        return 0 if all_ok else 1

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
