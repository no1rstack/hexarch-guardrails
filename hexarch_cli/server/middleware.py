from __future__ import annotations

import os
import hashlib
from uuid import uuid4

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from hexarch_cli.db import DatabaseManager
from hexarch_cli.models.audit import AuditAction, AuditService
from hexarch_cli.server.security import SlidingWindowRateLimiter, get_rate_limit_config


def _parse_cors_origins() -> list[str]:
    raw = os.getenv("HEXARCH_CORS_ORIGINS", "").strip()
    if not raw:
        return []
    return [o.strip() for o in raw.split(",") if o.strip()]


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        response.headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
        response.headers.setdefault("Cross-Origin-Embedder-Policy", "require-corp")
        response.headers.setdefault("Cache-Control", "no-store")

        return response


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-Id") or str(uuid4())
        response: Response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        cfg = get_rate_limit_config()
        self.enabled = cfg.enabled
        self.limiter = SlidingWindowRateLimiter(rpm=cfg.rpm)

    async def dispatch(self, request: Request, call_next):
        if self.enabled:
            client_host = request.client.host if request.client else "unknown"
            auth = request.headers.get("authorization") or request.headers.get("Authorization")
            token_fp = None
            if auth and auth.lower().startswith("bearer "):
                token = auth.split(" ", 1)[1].strip()
                # Fingerprint only; do not log token itself.
                token_fp = hashlib.sha256(token.encode("utf-8")).hexdigest()[:12]

            tenant_id = request.headers.get("X-Tenant-Id")
            if token_fp:
                key = f"auth:{token_fp}:{tenant_id or client_host}:{request.url.path}"
            else:
                key = f"ip:{client_host}:{tenant_id or 'none'}:{request.url.path}"
            try:
                self.limiter.check(key)
            except HTTPException as exc:
                if exc.status_code != 429:
                    raise

                # Best-effort: record quota exhaustion as an audit artifact.
                try:
                    session = DatabaseManager.get_session()
                    try:
                        actor_id = request.headers.get("X-Actor-Id") or request.headers.get("X-User-Id") or "unknown"
                        AuditService.log_action(
                            session,
                            action=AuditAction.EVALUATE,
                            entity_type="RateLimit",
                            entity_id=key,
                            actor_id=actor_id,
                            actor_type=request.headers.get("X-Actor-Type") or "user",
                            changes={
                                "decision": "DENY",
                                "reason": "rate_limited",
                                "method": request.method,
                                "path": request.url.path,
                                "key": key,
                                "rpm": self.limiter.max_requests,
                                "window_seconds": int(self.limiter.window_seconds),
                            },
                            context={
                                "client_host": client_host,
                                "tenant_id": request.headers.get("X-Tenant-Id"),
                                "org_id": request.headers.get("X-Org-Id"),
                                "team_id": request.headers.get("X-Team-Id"),
                            },
                        )
                        session.commit()
                    finally:
                        session.close()
                except Exception:
                    pass

                # Ensure clients get a Retry-After hint.
                raise HTTPException(
                    status_code=429,
                    detail=exc.detail,
                    headers={"Retry-After": str(int(self.limiter.window_seconds))},
                )
        return await call_next(request)
