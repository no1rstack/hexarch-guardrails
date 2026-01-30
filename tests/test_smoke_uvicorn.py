import os
import socket
import subprocess
import sys
import time
import urllib.request
from contextlib import closing
from tempfile import TemporaryDirectory

import pytest


def _find_free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("127.0.0.1", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return int(s.getsockname()[1])


def _http_get(url: str, timeout: float = 2.0) -> tuple[int, str]:
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        status = int(getattr(resp, "status", resp.getcode()))
        body = resp.read().decode("utf-8", errors="replace")
        return status, body


@pytest.mark.smoke
def test_uvicorn_starts_and_health_responds():
    uvicorn = pytest.importorskip("uvicorn")
    assert uvicorn is not None

    port = _find_free_port()

    # On Windows, SQLite files can remain locked briefly even after the server
    # process is terminated, which can cause TemporaryDirectory cleanup to fail.
    with TemporaryDirectory(ignore_cleanup_errors=(os.name == "nt")) as td:
        env = os.environ.copy()
        env["DATABASE_URL"] = f"sqlite:///{td}/smoke.db"
        env["HEXARCH_API_TOKEN"] = "dev-token"

        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "hexarch_cli.server.app:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ]

        proc = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        try:
            url = f"http://127.0.0.1:{port}/health"
            deadline = time.time() + 15
            last_err: Exception | None = None

            while time.time() < deadline:
                if proc.poll() is not None:
                    break
                time.sleep(0.25)
                try:
                    status, body = _http_get(url, timeout=2.0)
                    if status == 200 and '"status"' in body:
                        assert '"status":"ok"' in body.replace(" ", "")
                        return
                except Exception as exc:  # noqa: BLE001 - best-effort polling
                    last_err = exc

            # If we get here, either the process died or health never responded.
            output = ""
            if proc.stdout is not None:
                try:
                    output = proc.stdout.read()[-4000:]
                except Exception:
                    output = ""

            if proc.poll() is not None:
                raise AssertionError(f"uvicorn exited early (code={proc.returncode}). Output tail:\n{output}")

            raise AssertionError(f"/health did not respond in time. Last error: {last_err}. Output tail:\n{output}")
        finally:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except Exception:
                    proc.kill()
