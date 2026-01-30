from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


@dataclass(frozen=True)
class OpsEvent:
    ts: str
    event_type: str
    status: str
    details: dict[str, Any]

    @staticmethod
    def now(event_type: str, status: str, *, details: Optional[dict[str, Any]] = None) -> "OpsEvent":
        return OpsEvent(
            ts=datetime.now(timezone.utc).isoformat(),
            event_type=event_type,
            status=status,
            details=details or {},
        )


def default_ops_events_path() -> Path:
    return Path.home() / ".hexarch" / "ops" / "events.jsonl"


def append_ops_event(event: OpsEvent, path: Optional[Path] = None) -> None:
    p = path or default_ops_events_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": event.ts, "event_type": event.event_type, "status": event.status, "details": event.details}) + "\n")


def read_ops_events(path: Optional[Path] = None, *, limit: int = 1000) -> list[OpsEvent]:
    p = path or default_ops_events_path()
    if not p.exists():
        return []

    events: list[OpsEvent] = []
    for line in p.read_text(encoding="utf-8").splitlines()[-limit:]:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            events.append(
                OpsEvent(
                    ts=str(obj.get("ts")),
                    event_type=str(obj.get("event_type")),
                    status=str(obj.get("status")),
                    details=dict(obj.get("details") or {}),
                )
            )
        except Exception:
            # Best-effort: skip malformed lines.
            continue
    return events
