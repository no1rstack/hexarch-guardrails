from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class EvidenceConfig:
    hexarch_base_url: str
    hexarch_token: str
    node_red_base_url: str


def _http_json(method: str, url: str, *, headers: dict[str, str] | None = None, body: dict | None = None) -> dict:
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
        with urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except HTTPError as e:
        raw = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"HTTP {e.code} for {method} {url}: {raw}") from e


def _write_md(path: Path, sections: list[tuple[str, object]]) -> None:
    lines: list[str] = []
    lines.append(f"# Hexarch Node-RED Milestone Evidence ({datetime.now(timezone.utc).isoformat()})")
    lines.append("")
    for title, obj in sections:
        lines.append(f"## {title}")
        lines.append("")
        if isinstance(obj, str):
            lines.append(obj)
        else:
            lines.append("```json")
            lines.append(json.dumps(obj, indent=2, sort_keys=True))
            lines.append("```")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    cfg = EvidenceConfig(
        hexarch_base_url=os.getenv("HEXARCH_BASE_URL", "http://127.0.0.1:8099").rstrip("/"),
        hexarch_token=os.getenv("HEXARCH_TOKEN", "dev-token"),
        node_red_base_url=os.getenv("NODE_RED_BASE_URL", "http://localhost:1880").rstrip("/"),
    )

    headers = {"Authorization": f"Bearer {cfg.hexarch_token}", "X-Actor-Id": "admin"}

    # Trigger Node-RED run endpoint (no-click)
    node_red_run = _http_json("POST", f"{cfg.node_red_base_url}/hexarch/run")

    health = _http_json("GET", f"{cfg.hexarch_base_url}/health")
    authorize = _http_json(
        "POST",
        f"{cfg.hexarch_base_url}/authorize",
        headers=headers,
        body={"action": "call_provider", "resource": {"name": "hexarch"}, "context": {"provider_action": "echo"}},
    )
    events = _http_json("GET", f"{cfg.hexarch_base_url}/events/provider-calls", headers=headers)
    verify = _http_json("GET", f"{cfg.hexarch_base_url}/audit-logs/verify?chain_id=global&limit=50", headers=headers)

    out_dir = Path(__file__).resolve().parents[1] / "evidence"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"node_red_milestone_{stamp}.md"

    _write_md(
        out_path,
        [
            ("Node-RED Trigger Response", node_red_run),
            ("Hexarch /health", health),
            ("Hexarch /authorize", authorize),
            ("Hexarch provider-call events", events),
            ("Hexarch audit verify", verify),
        ],
    )

    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
