from __future__ import annotations

import os
import hmac
import hashlib
from datetime import datetime, timedelta, UTC
from dataclasses import dataclass
from typing import Any, Optional

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from hexarch_cli.models.audit import AuditAction, AuditService
from hexarch_cli.models.api_key import ApiKey
from hexarch_cli.models.policy import Policy, PolicyScope
from hexarch_cli.server.security import get_api_token, is_api_key_admin_enabled, is_auth_required


@dataclass(frozen=True)
class Identity:
    actor_id: str
    actor_type: str = "user"
    tenant_id: Optional[str] = None
    org_id: Optional[str] = None
    team_id: Optional[str] = None
    user_id: Optional[str] = None
    scopes: Optional[list[str]] = None


def get_identity(request: Request) -> Identity:
    # Minimal normalized identity until JWT support lands.
    actor_id = request.headers.get("X-Actor-Id") or request.headers.get("X-User-Id") or "unknown"
    tenant_id = request.headers.get("X-Tenant-Id")
    org_id = request.headers.get("X-Org-Id")
    team_id = request.headers.get("X-Team-Id")
    user_id = request.headers.get("X-User-Id")

    actor_type = request.headers.get("X-Actor-Type") or "user"

    return Identity(
        actor_id=actor_id,
        actor_type=actor_type,
        tenant_id=tenant_id,
        org_id=org_id,
        team_id=team_id,
        user_id=user_id,
    )


def _env_truthy(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


_BOOTSTRAP_STARTED_AT_UTC = datetime.now(UTC)


def _bootstrap_active() -> bool:
    if not _env_truthy("HEXARCH_BOOTSTRAP_ALLOW", default=False):
        return False

    ttl_raw = os.getenv("HEXARCH_BOOTSTRAP_TTL_SECONDS")
    if ttl_raw:
        try:
            ttl_seconds = int(ttl_raw)
        except ValueError:
            return False
        if ttl_seconds <= 0:
            return False
        if datetime.now(UTC) - _BOOTSTRAP_STARTED_AT_UTC > timedelta(seconds=ttl_seconds):
            return False

    return True


def _is_bootstrap_request(request: Request) -> bool:
    # Allows bringing the system up from a blank DB.
    if not _bootstrap_active():
        return False

    if request.method not in {"GET", "POST"}:
        return False

    if request.url.path in {"/policies", "/rules"}:
        return True
    if request.url.path == "/api-keys":
        return is_api_key_admin_enabled()
    return False


def _parse_bearer_token(request: Request) -> str | None:
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        return None
    return auth.split(" ", 1)[1].strip()


def _sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def authenticate_request(request: Request, session: Session | None = None) -> Identity:
    if not is_auth_required():
        return get_identity(request)

    token = _parse_bearer_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")

    # Legacy/static token support (admin/bootstrap)
    expected = get_api_token()
    if expected and hmac.compare_digest(token, expected):
        identity = get_identity(request)
        if identity.actor_id == "unknown":
            identity = Identity(actor_id="static-token", actor_type="service")
        # Legacy token is treated as admin/service.
        return Identity(
            actor_id=identity.actor_id,
            actor_type=identity.actor_type,
            tenant_id=identity.tenant_id,
            org_id=identity.org_id,
            team_id=identity.team_id,
            user_id=identity.user_id,
            scopes=["*"],
        )

    # DB-backed API keys
    if session is None:
        raise HTTPException(status_code=403, detail="Invalid token")

    prefix = ApiKey.token_prefix_from_token(token)
    key = (
        session.query(ApiKey)
        .filter(ApiKey.token_prefix == prefix)
        .filter(ApiKey.is_deleted == False)
        .first()
    )
    if not key:
        raise HTTPException(status_code=403, detail="Invalid token")
    if key.revoked_at is not None:
        raise HTTPException(status_code=403, detail="Token revoked")
    if not key.matches_token(token):
        raise HTTPException(status_code=403, detail="Invalid token")

    # Mark key used (best-effort)
    try:
        key.last_used_at = __import__("datetime").datetime.utcnow()
        session.add(key)
        session.commit()
    except Exception:
        session.rollback()

    return Identity(
        actor_id=f"api_key:{key.id}",
        actor_type="api_key",
        tenant_id=key.tenant_id,
        org_id=key.org_id,
        scopes=list(key.scopes or []),
    )


def _required_scopes_for_request(request: Request) -> list[str]:
    # Conservative defaults: GET => read; mutating verbs => write.
    method = request.method.upper()
    path = request.url.path

    # Special-case the decision endpoint: it's an evaluation (read-like).
    if path == "/authorize":
        return ["read"]

    # API key management is always admin.
    if path.startswith("/api-keys"):
        return ["admin"]

    if method in {"GET", "HEAD", "OPTIONS"}:
        return ["read"]
    if method in {"POST", "PUT", "PATCH", "DELETE"}:
        return ["write"]
    return ["read"]


def enforce_scopes(*, request: Request, session: Session, identity: Identity) -> None:
    """Enforce API key scopes and emit an auditable denial on failure."""

    if identity.actor_type != "api_key":
        return

    # API keys are never allowed to manage API keys, even if mis-scoped.
    if request.url.path.startswith("/api-keys"):
        try:
            AuditService.log_action(
                session,
                action=AuditAction.EVALUATE,
                entity_type="Request",
                entity_id=request.headers.get("X-Request-Id") or request.url.path,
                actor_id=identity.actor_id,
                actor_type=identity.actor_type,
                reason="api_key_admin_requires_admin_token",
                changes={
                    "decision": "DENY",
                    "request": {"method": request.method, "path": request.url.path},
                },
                context={
                    "tenant_id": identity.tenant_id,
                    "org_id": identity.org_id,
                    "team_id": identity.team_id,
                    "client_host": request.client.host if request.client else None,
                },
            )
            session.commit()
        except Exception:
            session.rollback()
        raise HTTPException(status_code=403, detail="API key admin requires admin token")

    required = _required_scopes_for_request(request)
    present = set((identity.scopes or []))
    if "*" in present:
        return
    if any(r in present for r in required):
        return

    try:
        AuditService.log_action(
            session,
            action=AuditAction.EVALUATE,
            entity_type="Request",
            entity_id=request.headers.get("X-Request-Id") or request.url.path,
            actor_id=identity.actor_id,
            actor_type=identity.actor_type,
            reason="scope_denied",
            changes={
                "decision": "DENY",
                "required_scopes": required,
                "present_scopes": sorted(present),
                "request": {"method": request.method, "path": request.url.path},
            },
            context={
                "tenant_id": identity.tenant_id,
                "org_id": identity.org_id,
                "team_id": identity.team_id,
                "client_host": request.client.host if request.client else None,
            },
        )
        session.commit()
    except Exception:
        session.rollback()

    raise HTTPException(status_code=403, detail="Insufficient scope")


def build_policy_context(
    *,
    request: Request,
    identity: Identity,
    input_data: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    ctx: dict[str, Any] = {
        "request": {
            "method": request.method,
            "path": request.url.path,
            "query": dict(request.query_params),
        },
        "identity": {
            "actor_id": identity.actor_id,
            "actor_type": identity.actor_type,
            "tenant_id": identity.tenant_id,
            "org_id": identity.org_id,
            "team_id": identity.team_id,
            "user_id": identity.user_id,
        },
    }
    if input_data is not None:
        ctx["input"] = input_data
    return ctx


def _applicable_policy(policy: Policy, identity: Identity) -> bool:
    scope = getattr(policy, "scope", PolicyScope.GLOBAL)
    value = getattr(policy, "scope_value", None)

    # Be liberal: scope stored as str.
    if scope == PolicyScope.GLOBAL or str(scope) == str(PolicyScope.GLOBAL):
        return True

    if value is None:
        return False

    if scope == PolicyScope.ORGANIZATION or str(scope) == str(PolicyScope.ORGANIZATION):
        return identity.org_id == value
    if scope == PolicyScope.TEAM or str(scope) == str(PolicyScope.TEAM):
        return identity.team_id == value
    if scope == PolicyScope.USER or str(scope) == str(PolicyScope.USER):
        return identity.user_id == value

    # RESOURCE scope isn't well-defined for request routing yet.
    return False


def authorize_request(
    *,
    request: Request,
    session: Session,
    context_extra: Optional[dict[str, Any]] = None,
) -> Identity:
    """Centralized auth + policy enforcement.

    - Requires bearer auth (unless explicitly configured off).
    - Builds a normalized identity.
    - Evaluates applicable policies.
    - Writes an audit event for allow/deny.

    Returns the Identity on allow.
    Raises HTTPException on deny.
    """

    identity = authenticate_request(request, session=session)

    # API key scope enforcement happens before policy evaluation.
    enforce_scopes(request=request, session=session, identity=identity)

    ctx = build_policy_context(
        request=request,
        identity=identity,
        input_data=context_extra,
    )

    allowed, deny_reason, policy_ids = evaluate_policies(
        request=request,
        session=session,
        identity=identity,
        ctx=ctx,
    )

    if not allowed:
        raise HTTPException(status_code=403, detail="Denied by policy")

    return identity


def evaluate_policies(
    *,
    request: Request,
    session: Session,
    identity: Identity,
    ctx: dict[str, Any],
) -> tuple[bool, Optional[str], list[str]]:
    """Evaluate policies and write an audit record. Never raises on audit failures."""

    policies = (
        session.query(Policy)
        .filter(Policy.is_deleted == False)
        .filter(Policy.enabled == True)
        .all()
    )
    applicable = [p for p in policies if _applicable_policy(p, identity)]
    policy_ids = [p.id for p in applicable]

    allowed = True
    deny_reason: Optional[str] = None

    if not applicable:
        if _is_bootstrap_request(request):
            allowed = True
            deny_reason = "bootstrap_allow"
        else:
            allowed = False
            deny_reason = "no_applicable_policies"
    else:
        for p in applicable:
            ok = p.evaluate(ctx)
            if not ok:
                allowed = False
                deny_reason = f"policy_denied:{p.id}"
                break

    try:
        AuditService.log_action(
            session,
            action=AuditAction.EVALUATE,
            entity_type="Request",
            entity_id=request.headers.get("X-Request-Id") or request.url.path,
            actor_id=identity.actor_id,
            actor_type=identity.actor_type,
            changes={
                "decision": "ALLOW" if allowed else "DENY",
                "reason": deny_reason,
                "policies": policy_ids,
                "request": {"method": request.method, "path": request.url.path},
            },
            context={
                "tenant_id": identity.tenant_id,
                "org_id": identity.org_id,
                "team_id": identity.team_id,
                "client_host": request.client.host if request.client else None,
            },
        )
        session.commit()
    except Exception:
        session.rollback()

    return allowed, deny_reason, policy_ids
