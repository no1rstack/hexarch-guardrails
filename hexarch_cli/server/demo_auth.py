from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import time
from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException, Request

from hexarch_cli.server.security import SlidingWindowRateLimiter


logger = logging.getLogger("hexarch.demo")


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("utf-8"))


def _secret() -> str:
    return os.getenv("HEXARCH_DEMO_TOKEN_SECRET", "hexarch-demo-dev-secret-change-me")


def _issue_signed_token(payload: dict[str, Any]) -> str:
    body = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    sig = hmac.new(_secret().encode("utf-8"), body.encode("utf-8"), hashlib.sha256).digest()
    return f"{body}.{_b64url_encode(sig)}"


def _verify_signed_token(token: str) -> dict[str, Any]:
    try:
        body_b64, sig_b64 = token.split(".", 1)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid demo token format") from exc

    expected_sig = hmac.new(_secret().encode("utf-8"), body_b64.encode("utf-8"), hashlib.sha256).digest()
    provided_sig = _b64url_decode(sig_b64)
    if not hmac.compare_digest(expected_sig, provided_sig):
        raise HTTPException(status_code=401, detail="Invalid demo token signature")

    try:
        payload = json.loads(_b64url_decode(body_b64))
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid demo token payload") from exc

    exp = int(payload.get("exp", 0))
    if exp <= int(time.time()):
        raise HTTPException(status_code=401, detail="Demo token expired")

    return payload


@dataclass
class DemoSessionRecord:
    session_id: str
    issued_at: int
    expires_at: int
    source_ip: str
    exchanged: bool = False


DEMO_ISSUED_SESSIONS: dict[str, DemoSessionRecord] = {}
DEMO_ACTIVE_SESSIONS: dict[str, DemoSessionRecord] = {}

ISSUE_LIMITER = SlidingWindowRateLimiter(rpm=int(os.getenv("HEXARCH_DEMO_ISSUE_RPM", "5")))
EXCHANGE_LIMITER = SlidingWindowRateLimiter(rpm=int(os.getenv("HEXARCH_DEMO_EXCHANGE_RPM", "20")))
SESSION_LIMITER = SlidingWindowRateLimiter(rpm=int(os.getenv("HEXARCH_DEMO_SESSION_RPM", "60")))


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _cleanup_expired() -> None:
    now = int(time.time())
    for key in list(DEMO_ISSUED_SESSIONS.keys()):
        if DEMO_ISSUED_SESSIONS[key].expires_at <= now:
            DEMO_ISSUED_SESSIONS.pop(key, None)
    for key in list(DEMO_ACTIVE_SESSIONS.keys()):
        if DEMO_ACTIVE_SESSIONS[key].expires_at <= now:
            DEMO_ACTIVE_SESSIONS.pop(key, None)


def issue_demo_bootstrap_token(request: Request, ttl_seconds: int = 30 * 60) -> dict[str, Any]:
    _cleanup_expired()
    ip = _client_ip(request)
    ISSUE_LIMITER.check(f"demo-issue:{ip}")

    now = int(time.time())
    session_id = f"demo_{secrets.token_urlsafe(8)}"
    exp = now + max(600, min(ttl_seconds, 1800))

    DEMO_ISSUED_SESSIONS[session_id] = DemoSessionRecord(
        session_id=session_id,
        issued_at=now,
        expires_at=exp,
        source_ip=ip,
        exchanged=False,
    )

    payload = {
        "sid": session_id,
        "scope": "demo",
        "iat": now,
        "exp": exp,
    }
    token = _issue_signed_token(payload)

    logger.info("demo_token_issued sid=%s ip=%s exp=%s", session_id, ip, exp)
    return {
        "token": token,
        "expires_in": exp - now,
        "session_id": session_id,
        "issued_at": now,
        "expires_at": exp,
    }


def exchange_demo_token(request: Request, token: str, ttl_seconds: int = 15 * 60) -> dict[str, Any]:
    _cleanup_expired()
    ip = _client_ip(request)
    EXCHANGE_LIMITER.check(f"demo-exchange:{ip}")

    payload = _verify_signed_token(token)
    if payload.get("scope") != "demo":
        raise HTTPException(status_code=403, detail="Invalid demo token scope")

    sid = str(payload.get("sid", ""))
    record = DEMO_ISSUED_SESSIONS.get(sid)
    if not record:
        raise HTTPException(status_code=401, detail="Demo session not found")
    if record.exchanged:
        raise HTTPException(status_code=401, detail="Demo token already exchanged")

    now = int(time.time())
    exp = now + max(300, min(ttl_seconds, 15 * 60))

    record.exchanged = True
    active = DemoSessionRecord(
        session_id=sid,
        issued_at=now,
        expires_at=exp,
        source_ip=record.source_ip,
        exchanged=True,
    )
    DEMO_ACTIVE_SESSIONS[sid] = active

    session_payload = {
        "sid": sid,
        "scope": "demo-session",
        "iat": now,
        "exp": exp,
    }
    session_token = _issue_signed_token(session_payload)

    logger.info("demo_token_exchanged sid=%s ip=%s exp=%s", sid, ip, exp)
    return {
        "session_token": session_token,
        "expires_in": exp - now,
        "session_id": sid,
        "issued_at": now,
        "expires_at": exp,
    }


def _extract_token(request: Request) -> str:
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    header_token = request.headers.get("X-Demo-Token")
    if header_token:
        return header_token.strip()
    raise HTTPException(status_code=401, detail="Missing demo session token")


def require_demo_session(request: Request) -> dict[str, Any]:
    _cleanup_expired()
    token = _extract_token(request)
    payload = _verify_signed_token(token)

    if payload.get("scope") != "demo-session":
        raise HTTPException(status_code=403, detail="Invalid demo session scope")

    sid = str(payload.get("sid", ""))
    record = DEMO_ACTIVE_SESSIONS.get(sid)
    if not record:
        raise HTTPException(status_code=401, detail="Demo session not active")

    if record.expires_at <= int(time.time()):
        DEMO_ACTIVE_SESSIONS.pop(sid, None)
        raise HTTPException(status_code=401, detail="Demo session expired")

    SESSION_LIMITER.check(f"demo-session:{sid}")

    logger.info("demo_session_used sid=%s", sid)
    return payload
