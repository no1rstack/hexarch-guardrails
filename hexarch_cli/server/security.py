from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Optional

from fastapi import HTTPException, Request


def _env_truthy(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def is_docs_enabled() -> bool:
    return _env_truthy("HEXARCH_API_DOCS", default=False)


def is_auth_required() -> bool:
    # Default hardened: require auth unless explicitly allowed.
    return not _env_truthy("HEXARCH_API_ALLOW_ANON", default=False)


def is_api_key_admin_enabled() -> bool:
    # Disabled by default; enable explicitly during bootstrap/ops.
    return _env_truthy("HEXARCH_API_KEY_ADMIN_ENABLED", default=False)


def get_api_token() -> Optional[str]:
    token = os.getenv("HEXARCH_API_TOKEN")
    if not token:
        return None
    return token.strip()


def require_bearer_token(request: Request) -> None:
    if not is_auth_required():
        return

    expected = get_api_token()
    if not expected:
        # Auth is required but no token configured.
        raise HTTPException(status_code=503, detail="Server auth not configured")

    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    provided = auth.split(" ", 1)[1].strip()
    if provided != expected:
        raise HTTPException(status_code=403, detail="Invalid token")


@dataclass
class RateLimitConfig:
    enabled: bool
    rpm: int


def get_rate_limit_config() -> RateLimitConfig:
    enabled = _env_truthy("HEXARCH_RATE_LIMIT_ENABLED", default=True)
    rpm = int(os.getenv("HEXARCH_RATE_LIMIT_RPM", "120"))
    return RateLimitConfig(enabled=enabled, rpm=max(1, rpm))


class SlidingWindowRateLimiter:
    """Very small in-memory per-IP sliding window limiter (single-process)."""

    def __init__(self, rpm: int):
        self.window_seconds = 60.0
        self.max_requests = rpm
        self._buckets: dict[str, list[float]] = {}

    def check(self, key: str) -> None:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        bucket = self._buckets.get(key)
        if bucket is None:
            bucket = []
            self._buckets[key] = bucket

        # drop old
        while bucket and bucket[0] < cutoff:
            bucket.pop(0)

        if len(bucket) >= self.max_requests:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

        bucket.append(now)
