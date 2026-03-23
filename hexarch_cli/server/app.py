from __future__ import annotations

import logging
import logging.config
import os
import html
import uuid
from typing import Any, Iterator, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.responses import PlainTextResponse
from fastapi.responses import HTMLResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from starlette.middleware.cors import CORSMiddleware

from hexarch_cli import __version__
from hexarch_cli.db import DatabaseManager
from hexarch_cli.models.audit import AuditCheckpoint, AuditLog
from hexarch_cli.models.api_key import ApiKey
from hexarch_cli.models.decision import Decision
from hexarch_cli.models.entitlement import Entitlement
from hexarch_cli.models.policy import Policy
from hexarch_cli.models.rule import Rule
from hexarch_cli.models.audit import AuditAction, AuditService
from hexarch_cli.server.enforcement import authorize_request
from hexarch_cli.server.middleware import RateLimitMiddleware, RequestIdMiddleware, SecurityHeadersMiddleware
from hexarch_cli.server.security import is_api_key_admin_enabled, is_docs_enabled
from hexarch_cli.server.demo_auth import issue_demo_bootstrap_token, exchange_demo_token, require_demo_session
from hexarch_cli.server.enforcement import (
    authenticate_request,
    build_policy_context,
    evaluate_policies,
    enforce_scopes,
)
from hexarch_cli.server.schemas import (
    AuditLogOut,
    AuditVerifyResponse,
    AuditCheckpointResponse,
    AuditCheckpointCreate,
    AuditCheckpointOut,
    ApiKeyCreate,
    ApiKeyCreateResponse,
    ApiKeyOut,
    DecisionCreate,
    DecisionOut,
    EntitlementCreate,
    EntitlementOut,
    EchoRequest,
    EchoResponse,
    HealthResponse,
    PolicyCreate,
    PolicyOut,
    RuleCreate,
    RuleOut,
    AuthorizeRequest,
    AuthorizeResponse,
    ProviderCallCreate,
    ProviderCallOut,
    DemoSessionCreateResponse,
    DemoExchangeRequest,
    DemoExchangeResponse,
    DemoPolicyOut,
    DemoEvaluateRequest,
    DemoEvaluateResponse,
)


def _parse_cors_origins() -> list[str]:
    raw = os.getenv("HEXARCH_CORS_ORIGINS", "").strip()
    if not raw:
        return []
    return [o.strip() for o in raw.split(",") if o.strip()]


def _configure_trace_logger() -> None:
    """Ensure hexarch.trace emits JSON lines to stdout at INFO level."""
    logger = logging.getLogger("hexarch.trace")
    if logger.handlers:
        return  # already configured
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


def get_session() -> Iterator[Session]:
    session = DatabaseManager.get_session()
    try:
        yield session
    finally:
        session.close()


def create_app(init_db: bool = False) -> FastAPI:
    DatabaseManager.initialize()
    if init_db:
        DatabaseManager.create_all()

    _configure_trace_logger()

    docs_enabled = is_docs_enabled()
    app = FastAPI(
        title="Hexarch Guardrails API",
        version=__version__,
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        openapi_url="/openapi.json" if docs_enabled else None,
    )

    # Middleware: request IDs, headers, rate limiting
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)

    # CORS: default deny; enable via HEXARCH_CORS_ORIGINS
    cors_origins = _parse_cors_origins()
    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
            allow_headers=["Authorization", "Content-Type", "X-Request-Id"],
            expose_headers=["X-Request-Id"],
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        # Best-effort audit for authz/authn failures and rate limiting.
        try:
            session = DatabaseManager.get_session()
            try:
                actor_id = request.headers.get("X-Actor-Id") or request.headers.get("X-User-Id") or "unknown"
                AuditService.log_action(
                    session,
                    action=AuditAction.EVALUATE,
                    entity_type="HTTPException",
                    entity_id=request.headers.get("X-Request-Id") or request.url.path,
                    actor_id=actor_id,
                    actor_type=request.headers.get("X-Actor-Type") or "user",
                    changes={
                        "status_code": exc.status_code,
                        "detail": exc.detail,
                        "method": request.method,
                        "path": request.url.path,
                    },
                    context={
                        "client_host": request.client.host if request.client else None,
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

        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        # Avoid leaking internals by default.
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    def enforced_identity(request: Request, session: Session = Depends(get_session)):
        # Shared enforcement dependency for endpoints that don't need payload-aware context.
        return authorize_request(request=request, session=session)

    @app.get("/")
    def root() -> dict:
        # Public landing endpoint to improve discoverability and avoid scanner false-positives.
        return {"status": "ok", "service": "hexarch-guardrails"}

    @app.get("/robots.txt")
    def robots() -> PlainTextResponse:
        # Ensure common probes get a deterministic response.
        return PlainTextResponse("User-agent: *\nDisallow: /\n", media_type="text/plain")

    @app.get("/sitemap.xml")
    def sitemap() -> PlainTextResponse:
        # Minimal sitemap to reduce noisy 404s from scanners.
        return PlainTextResponse(
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
            "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n"
            "  <url><loc>/</loc></url>\n"
            "</urlset>\n",
            media_type="application/xml",
        )

    @app.get("/health", response_model=HealthResponse)
    def health(session: Session = Depends(get_session)) -> HealthResponse:
        try:
            session.execute(text("SELECT 1"))
            db_status = "ok"
        except Exception:
            db_status = "error"
        return HealthResponse(status="ok", version=__version__, database=db_status)

    @app.post("/echo", response_model=EchoResponse)
    def echo(payload: EchoRequest) -> EchoResponse:
        # Public utility endpoint used for local workflow smoke tests.
        return EchoResponse(ok=True, message=payload.message, metadata=payload.metadata)

    @app.post("/api/demo/session", response_model=DemoSessionCreateResponse)
    def create_demo_session(request: Request):
        """Public demo onboarding endpoint. Issues a short-lived bootstrap token."""
        payload = issue_demo_bootstrap_token(request=request, ttl_seconds=30 * 60)
        return DemoSessionCreateResponse(**payload)

    @app.post("/api/demo/exchange", response_model=DemoExchangeResponse)
    def exchange_demo_session(request: Request, body: DemoExchangeRequest):
        """Exchange bootstrap demo token for a short-lived constrained session token."""
        payload = exchange_demo_token(request=request, token=body.token, ttl_seconds=15 * 60)
        return DemoExchangeResponse(**payload)

    @app.get("/demo")
    def demo_page(token: Optional[str] = Query(default=None)) -> HTMLResponse:
        """Minimal sandbox onboarding page that exchanges token immediately."""
        escaped_token = html.escape(token or "")
        html_doc = f"""
<!doctype html>
<html lang="en" data-bs-theme="dark">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Hexarch Demo Sandbox</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">
        <style>
            body {{
                min-height: 100vh;
                background: radial-gradient(circle at top left, #2d1b69 0%, #111827 45%, #030712 100%);
            }}
            .glass {{
                background: rgba(17, 24, 39, 0.72);
                border: 1px solid rgba(148, 163, 184, 0.25);
                backdrop-filter: blur(8px);
            }}
            .badge-soft {{
                background: rgba(56, 189, 248, 0.16);
                color: #bae6fd;
                border: 1px solid rgba(56, 189, 248, 0.35);
            }}
        </style>
    </head>
    <body class="d-flex align-items-center py-5">
        <main class="container py-4">
            <div class="row justify-content-center g-4">
                <div class="col-lg-8 col-xl-7">
                    <div class="glass rounded-4 p-4 p-md-5 shadow-lg">
                        <div class="d-flex align-items-center justify-content-between mb-3">
                            <h1 class="h3 mb-0">Hexarch Demo Sandbox</h1>
                            <span class="badge badge-soft rounded-pill px-3 py-2">Demo Session</span>
                        </div>
                        <p class="text-secondary mb-4">
                            Secure onboarding is active. We are exchanging your bootstrap token for a short-lived sandbox session.
                        </p>

                        <div id="statusBox" class="alert alert-info mb-4" role="status">
                            Exchanging demo token...
                        </div>

                        <div class="row g-3 mb-4">
                            <div class="col-md-4">
                                <div class="p-3 rounded-3 border border-secondary-subtle h-100">
                                    <div class="fw-semibold">One-time exchange</div>
                                    <small class="text-secondary">Bootstrap token can only be exchanged once.</small>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="p-3 rounded-3 border border-secondary-subtle h-100">
                                    <div class="fw-semibold">Scoped session</div>
                                    <small class="text-secondary">Session token is restricted to demo routes.</small>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="p-3 rounded-3 border border-secondary-subtle h-100">
                                    <div class="fw-semibold">Sandboxed eval</div>
                                    <small class="text-secondary">No production writes. Destructive actions are denied.</small>
                                </div>
                            </div>
                        </div>

                        <div class="d-flex gap-2 flex-wrap">
                            <button id="refreshBtn" type="button" class="btn btn-outline-light btn-sm">Re-check session</button>
                            <button id="copyBtn" type="button" class="btn btn-primary btn-sm" disabled>Copy session token</button>
                        </div>

                        <p class="text-secondary mt-4 mb-0 small">
                            Template style adapted from Bootstrap examples (MIT).
                        </p>
                    </div>
                </div>
            </div>
        </main>

        <script>
            const statusBox = document.getElementById('statusBox');
            const copyBtn = document.getElementById('copyBtn');
            const refreshBtn = document.getElementById('refreshBtn');

            async function exchangeToken() {{
                const url = new URL(window.location.href);
                const token = url.searchParams.get('token') || {escaped_token!r};
                if (!token) {{
                    statusBox.className = 'alert alert-warning mb-4';
                    statusBox.textContent = 'Missing demo token in URL.';
                    copyBtn.disabled = true;
                    return;
                }}

                const res = await fetch('/api/demo/exchange', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ token }})
                }});

                if (!res.ok) {{
                    statusBox.className = 'alert alert-danger mb-4';
                    statusBox.textContent = 'Token exchange failed or expired. Please start a new demo session.';
                    copyBtn.disabled = true;
                    return;
                }}

                const data = await res.json();
                window.__hexarchDemoSession = data;
                statusBox.className = 'alert alert-success mb-4';
                statusBox.textContent = `Sandbox session active (expires in ${{data.expires_in}}s).`;
                copyBtn.disabled = false;
            }}

            refreshBtn.addEventListener('click', async () => {{
                await exchangeToken();
            }});

            copyBtn.addEventListener('click', async () => {{
                const token = window.__hexarchDemoSession?.session_token;
                if (!token) return;
                await navigator.clipboard.writeText(token);
                copyBtn.textContent = 'Copied';
                setTimeout(() => copyBtn.textContent = 'Copy session token', 1200);
            }});

            exchangeToken();
        </script>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js" integrity="sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz" crossorigin="anonymous"></script>
    </body>
</html>
""".strip()
        return HTMLResponse(content=html_doc)

    @app.get("/demo/policies", response_model=list[DemoPolicyOut])
    def demo_policies(request: Request):
        """Sandbox-safe policy list. No production DB access."""
        require_demo_session(request)
        return [
            DemoPolicyOut(id="demo-read", name="Demo Read Policy", description="Allows safe read/evaluate actions."),
            DemoPolicyOut(id="demo-deny-destructive", name="Demo Destructive Guard", description="Denies destructive actions in sandbox."),
        ]

    @app.post("/demo/evaluate", response_model=DemoEvaluateResponse)
    def demo_evaluate(request: Request, payload: DemoEvaluateRequest):
        """Sandbox-only evaluator with synthetic non-persistent behavior."""
        require_demo_session(request)

        action = (payload.action or "").strip().lower()
        resource = (payload.resource or "").strip().lower()
        text = f"{action} {resource}"

        destructive = any(word in text for word in ["delete", "drop", "revoke", "truncate", "admin", "write"])
        if destructive:
            return DemoEvaluateResponse(
                allowed=False,
                decision="DENY",
                reason="Sandbox denies destructive operations.",
                sandboxed=True,
                persisted=False,
            )

        return DemoEvaluateResponse(
            allowed=True,
            decision="ALLOW",
            reason="Sandbox policy allows this demo action.",
            sandboxed=True,
            persisted=False,
        )

    @app.post("/authorize", response_model=AuthorizeResponse)
    def authorize(payload: AuthorizeRequest, request: Request, session: Session = Depends(get_session)):
        # This endpoint is for asking "what would happen"; it authenticates but does not
        # itself require a prior policy decision.
        identity = authenticate_request(request, session=session)
        enforce_scopes(request=request, session=session, identity=identity)

        input_data = {
            "action": payload.action,
            "resource": payload.resource,
            "context": payload.context,
        }

        ctx = build_policy_context(request=request, identity=identity, input_data=input_data)
        allowed, reason, policies = evaluate_policies(
            request=request,
            session=session,
            identity=identity,
            ctx=ctx,
        )

        return AuthorizeResponse(
            allowed=allowed,
            decision="ALLOW" if allowed else "DENY",
            reason=reason,
            policies=policies,
        )

    # Provider call events (for orchestration tools like n8n)
    @app.post("/events/provider-calls", response_model=ProviderCallOut)
    def create_provider_call_event(
        payload: ProviderCallCreate,
        request: Request,
        session: Session = Depends(get_session),
    ):
        # Enforced like any other write endpoint.
        identity = authorize_request(request=request, session=session, context_extra={"payload": payload.model_dump()})

        call_id = str(uuid.uuid4())
        AuditService.log_action(
            session,
            action=AuditAction.CREATE,
            entity_type="ProviderCall",
            entity_id=call_id,
            actor_id=identity.actor_id,
            actor_type=identity.actor_type,
            changes={
                "resource": payload.resource,
                "action": payload.action,
                "ok": payload.ok,
                "status_code": payload.status_code,
                "latency_ms": payload.latency_ms,
                "model": payload.model,
                "tokens_in": payload.tokens_in,
                "tokens_out": payload.tokens_out,
                "cost_usd": payload.cost_usd,
                "error_type": payload.error_type,
            },
            reason=payload.error_message,
            context={
                "tenant_id": identity.tenant_id,
                "org_id": identity.org_id,
                "resource": payload.resource,
                "action": payload.action,
                "metadata": payload.metadata,
                "client_host": request.client.host if request.client else None,
            },
        )
        session.commit()

        return ProviderCallOut(id=call_id, resource=payload.resource, action=payload.action, ok=payload.ok)

    @app.get("/events/provider-calls", response_model=list[AuditLogOut])
    def list_provider_call_events(
        request: Request,
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0, le=10_000),
        session: Session = Depends(get_session),
        _identity=Depends(enforced_identity),
    ):
        # Stored as audit logs under entity_type=ProviderCall.
        q = (
            session.query(AuditLog)
            .filter(AuditLog.is_deleted == False)
            .filter(AuditLog.entity_type == "ProviderCall")
        )
        return q.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()

    def _to_trace_event(log: AuditLog) -> dict[str, Any]:
        changes = log.changes if isinstance(log.changes, dict) else {}
        audit_context = log.audit_context if isinstance(log.audit_context, dict) else {}
        decision = (
            changes.get("decision")
            or changes.get("state")
            or ("ERROR" if str(log.action).upper() in {"DELETE", "HARD_DELETE", "REVOKE", "REJECT"} else "RECORDED")
        )

        return {
            "trace_id": log.id,
            "timestamp": log.created_at.isoformat() if log.created_at else None,
            "input": {
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "action": log.action,
                "context": audit_context,
            },
            "decision": decision,
            "output": {
                "changes": changes,
                "reason": log.reason,
            },
            "actor": {
                "actor_id": log.actor_id,
                "actor_type": log.actor_type,
            },
        }

    @app.get("/traces")
    @app.get("/api/traces")
    def list_traces(
        request: Request,
        entity_type: Optional[str] = Query(default=None),
        entity_id: Optional[str] = Query(default=None),
        actor_id: Optional[str] = Query(default=None),
        action: Optional[str] = Query(default=None),
        decision: Optional[str] = Query(default=None),
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0, le=10_000),
        session: Session = Depends(get_session),
        _identity=Depends(enforced_identity),
    ) -> list[dict[str, Any]]:
        """List structured trace events from persisted audit logs."""
        q = session.query(AuditLog).filter(AuditLog.is_deleted == False)
        if entity_type:
            q = q.filter(AuditLog.entity_type == entity_type)
        if entity_id:
            q = q.filter(AuditLog.entity_id == entity_id)
        if actor_id:
            q = q.filter(AuditLog.actor_id == actor_id)
        if action:
            q = q.filter(AuditLog.action == action)

        logs = q.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
        events = [_to_trace_event(log) for log in logs]

        if decision:
            wanted = decision.upper()
            events = [e for e in events if str(e.get("decision", "")).upper() == wanted]

        return events

    @app.get("/traces/{trace_id}")
    @app.get("/api/traces/{trace_id}")
    def get_trace(
        trace_id: str,
        request: Request,
        session: Session = Depends(get_session),
        _identity=Depends(enforced_identity),
    ) -> dict[str, Any]:
        """Get one structured trace event by trace ID."""
        log = session.query(AuditLog).filter(AuditLog.id == trace_id, AuditLog.is_deleted == False).first()
        if not log:
            raise HTTPException(status_code=404, detail="Trace not found")
        return _to_trace_event(log)

    # Rules
    @app.get("/rules", response_model=list[RuleOut])
    def list_rules(
        request: Request,
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0, le=10_000),
        session: Session = Depends(get_session),
        _identity=Depends(enforced_identity),
    ):
        rules = (
            session.query(Rule)
            .filter(Rule.is_deleted == False)
            .order_by(Rule.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return rules

    @app.post("/rules", response_model=RuleOut)
    def create_rule(payload: RuleCreate, request: Request, session: Session = Depends(get_session)):
        identity = authorize_request(request=request, session=session, context_extra={"payload": payload.model_dump()})
        rule = Rule(
            name=payload.name,
            description=payload.description,
            rule_type=payload.rule_type,
            priority=payload.priority,
            enabled=payload.enabled,
            condition=payload.condition,
            parent_rule_id=payload.parent_rule_id,
            operator=payload.operator,
            rule_metadata=payload.rule_metadata,
        )
        session.add(rule)
        session.commit()
        session.refresh(rule)

        AuditService.log_action(
            session,
            action=AuditAction.CREATE,
            entity_type="Rule",
            entity_id=rule.id,
            actor_id=identity.actor_id,
            actor_type=identity.actor_type,
            changes={"created": True},
        )
        session.commit()
        return rule

    @app.get("/rules/{rule_id}", response_model=RuleOut)
    def get_rule(
        rule_id: str,
        request: Request,
        session: Session = Depends(get_session),
        _identity=Depends(enforced_identity),
    ):
        rule = session.query(Rule).filter(Rule.id == rule_id, Rule.is_deleted == False).first()
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        return rule

    # Policies
    @app.get("/policies", response_model=list[PolicyOut])
    def list_policies(
        request: Request,
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0, le=10_000),
        session: Session = Depends(get_session),
        _identity=Depends(enforced_identity),
    ):
        policies = (
            session.query(Policy)
            .filter(Policy.is_deleted == False)
            .order_by(Policy.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        out: list[PolicyOut] = []
        for p in policies:
            out.append(
                PolicyOut(
                    **p.to_dict(),
                    rule_ids=[r.id for r in getattr(p, "rules", [])],
                )
            )
        return out

    @app.post("/policies", response_model=PolicyOut)
    def create_policy(payload: PolicyCreate, request: Request, session: Session = Depends(get_session)):
        identity = authorize_request(request=request, session=session, context_extra={"payload": payload.model_dump()})
        policy = Policy(
            name=payload.name,
            description=payload.description,
            scope=payload.scope,
            scope_value=payload.scope_value,
            enabled=payload.enabled,
            failure_mode=payload.failure_mode,
            config=payload.config,
        )

        if payload.rule_ids:
            rules = session.query(Rule).filter(Rule.id.in_(payload.rule_ids), Rule.is_deleted == False).all()
            found_ids = {r.id for r in rules}
            missing = [rid for rid in payload.rule_ids if rid not in found_ids]
            if missing:
                raise HTTPException(status_code=400, detail={"missing_rule_ids": missing})
            policy.rules = rules

        session.add(policy)
        session.commit()
        session.refresh(policy)

        AuditService.log_action(
            session,
            action=AuditAction.CREATE,
            entity_type="Policy",
            entity_id=policy.id,
            actor_id=identity.actor_id,
            actor_type=identity.actor_type,
            changes={"created": True, "rule_ids": [r.id for r in policy.rules]},
        )
        session.commit()
        return PolicyOut(**policy.to_dict(), rule_ids=[r.id for r in policy.rules])

    @app.get("/policies/{policy_id}", response_model=PolicyOut)
    def get_policy(
        policy_id: str,
        request: Request,
        session: Session = Depends(get_session),
        _identity=Depends(enforced_identity),
    ):
        policy = session.query(Policy).filter(Policy.id == policy_id, Policy.is_deleted == False).first()
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        return PolicyOut(**policy.to_dict(), rule_ids=[r.id for r in policy.rules])

    # Entitlements
    @app.get("/entitlements", response_model=list[EntitlementOut])
    def list_entitlements(
        request: Request,
        subject_id: Optional[str] = Query(default=None),
        status: Optional[str] = Query(default=None),
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0, le=10_000),
        session: Session = Depends(get_session),
        _identity=Depends(enforced_identity),
    ):
        q = session.query(Entitlement).filter(Entitlement.is_deleted == False)
        if subject_id:
            q = q.filter(Entitlement.subject_id == subject_id)
        if status:
            q = q.filter(Entitlement.status == status)
        return q.order_by(Entitlement.created_at.desc()).offset(offset).limit(limit).all()

    @app.post("/entitlements", response_model=EntitlementOut)
    def create_entitlement(payload: EntitlementCreate, request: Request, session: Session = Depends(get_session)):
        identity = authorize_request(request=request, session=session, context_extra={"payload": payload.model_dump()})
        entitlement = Entitlement(
            subject_id=payload.subject_id,
            subject_type=payload.subject_type,
            entitlement_type=payload.entitlement_type,
            name=payload.name,
            description=payload.description,
            resource_id=payload.resource_id,
            resource_type=payload.resource_type,
            status=payload.status,
            valid_from=payload.valid_from,
            expires_at=payload.expires_at,
            granted_by=payload.granted_by,
            reason=payload.reason,
            entitlement_metadata=payload.entitlement_metadata,
        )
        session.add(entitlement)
        session.commit()
        session.refresh(entitlement)

        AuditService.log_action(
            session,
            action=AuditAction.CREATE,
            entity_type="Entitlement",
            entity_id=entitlement.id,
            actor_id=identity.actor_id,
            actor_type=identity.actor_type,
            changes={"created": True},
        )
        session.commit()
        return entitlement

    @app.get("/entitlements/{entitlement_id}", response_model=EntitlementOut)
    def get_entitlement(
        entitlement_id: str,
        request: Request,
        session: Session = Depends(get_session),
        _identity=Depends(enforced_identity),
    ):
        entitlement = (
            session.query(Entitlement)
            .filter(Entitlement.id == entitlement_id, Entitlement.is_deleted == False)
            .first()
        )
        if not entitlement:
            raise HTTPException(status_code=404, detail="Entitlement not found")
        return entitlement

    # Decisions
    @app.get("/decisions", response_model=list[DecisionOut])
    def list_decisions(
        request: Request,
        state: Optional[str] = Query(default=None),
        entitlement_id: Optional[str] = Query(default=None),
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0, le=10_000),
        session: Session = Depends(get_session),
        _identity=Depends(enforced_identity),
    ):
        q = session.query(Decision).filter(Decision.is_deleted == False)
        if state:
            q = q.filter(Decision.state == state)
        if entitlement_id:
            q = q.filter(Decision.entitlement_id == entitlement_id)
        return q.order_by(Decision.created_at.desc()).offset(offset).limit(limit).all()

    @app.post("/decisions", response_model=DecisionOut)
    def create_decision(payload: DecisionCreate, request: Request, session: Session = Depends(get_session)):
        identity = authorize_request(request=request, session=session, context_extra={"payload": payload.model_dump()})
        # Ensure entitlement exists
        ent = (
            session.query(Entitlement)
            .filter(Entitlement.id == payload.entitlement_id, Entitlement.is_deleted == False)
            .first()
        )
        if not ent:
            raise HTTPException(status_code=400, detail="entitlement_id not found")

        decision = Decision(
            name=payload.name,
            description=payload.description,
            state=payload.state,
            entitlement_id=payload.entitlement_id,
            policy_id=payload.policy_id,
            creator_id=payload.creator_id,
            reviewer_id=payload.reviewer_id,
            priority=payload.priority,
            expires_at=payload.expires_at,
            context=payload.context,
            decision_reason=payload.decision_reason,
        )
        session.add(decision)
        session.commit()
        session.refresh(decision)

        AuditService.log_action(
            session,
            action=AuditAction.CREATE,
            entity_type="Decision",
            entity_id=decision.id,
            actor_id=identity.actor_id,
            actor_type=identity.actor_type,
            changes={"created": True, "state": decision.state},
        )
        session.commit()
        return decision

    @app.get("/decisions/{decision_id}", response_model=DecisionOut)
    def get_decision(
        decision_id: str,
        request: Request,
        session: Session = Depends(get_session),
        _identity=Depends(enforced_identity),
    ):
        decision = session.query(Decision).filter(Decision.id == decision_id, Decision.is_deleted == False).first()
        if not decision:
            raise HTTPException(status_code=404, detail="Decision not found")
        return decision

    # Audit logs
    @app.get("/audit-logs", response_model=list[AuditLogOut])
    def list_audit_logs(
        request: Request,
        entity_type: Optional[str] = Query(default=None),
        entity_id: Optional[str] = Query(default=None),
        actor_id: Optional[str] = Query(default=None),
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0, le=10_000),
        session: Session = Depends(get_session),
        _identity=Depends(enforced_identity),
    ):
        q = session.query(AuditLog).filter(AuditLog.is_deleted == False)
        if entity_type:
            q = q.filter(AuditLog.entity_type == entity_type)
        if entity_id:
            q = q.filter(AuditLog.entity_id == entity_id)
        if actor_id:
            q = q.filter(AuditLog.actor_id == actor_id)
        return q.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()

    @app.get("/audit-logs/verify", response_model=AuditVerifyResponse)
    def verify_audit_chain(
        request: Request,
        chain_id: str = Query(default="global"),
        limit: Optional[int] = Query(default=None, ge=1, le=50_000),
        session: Session = Depends(get_session),
    ):
        authorize_request(request=request, session=session)
        result = AuditService.verify_chain(session, chain_id=chain_id, limit=limit)
        return AuditVerifyResponse(**result)

    @app.get("/audit-logs/checkpoint", response_model=AuditCheckpointResponse)
    def audit_checkpoint(
        request: Request,
        chain_id: str = Query(default="global"),
        session: Session = Depends(get_session),
    ):
        authorize_request(request=request, session=session)
        now = __import__("datetime").datetime.utcnow()
        last_hash = AuditService.get_latest_hash(session, chain_id=chain_id)
        payload = {
            "v": 1,
            "chain_id": chain_id,
            "last_entry_hash": last_hash,
            "at": now.isoformat() + "Z",
        }
        signed = AuditService.sign_checkpoint(payload)
        return AuditCheckpointResponse(
            chain_id=chain_id,
            last_entry_hash=last_hash,
            at=now,
            signed=signed["signed"],
            key_id=signed.get("key_id"),
            signature=signed.get("signature"),
        )

    # API keys (admin)
    @app.post("/api-keys", response_model=ApiKeyCreateResponse)
    def create_api_key(payload: ApiKeyCreate, request: Request, session: Session = Depends(get_session)):
        if not is_api_key_admin_enabled():
            raise HTTPException(status_code=404, detail="Not found")

        # Protected by policy; bootstrap allowlist includes /api-keys for initial setup.
        identity = authorize_request(request=request, session=session, context_extra={"payload": payload.model_dump()})

        # Prevent API keys from minting other API keys.
        if identity.actor_type == "api_key":
            raise HTTPException(status_code=403, detail="API key admin requires admin token")

        token, prefix = ApiKey.generate_token()
        key = ApiKey(
            name=payload.name,
            description=payload.description,
            token_prefix=prefix,
            token_hash=ApiKey.hash_token(token),
            tenant_id=payload.tenant_id,
            org_id=payload.org_id,
            scopes=payload.scopes,
        )
        session.add(key)
        session.commit()
        session.refresh(key)

        AuditService.log_action(
            session,
            action=AuditAction.CREATE,
            entity_type="ApiKey",
            entity_id=key.id,
            actor_id=identity.actor_id,
            actor_type=identity.actor_type,
            changes={"created": True, "token_prefix": key.token_prefix, "tenant_id": key.tenant_id, "org_id": key.org_id},
            context={"tenant_id": identity.tenant_id, "org_id": identity.org_id},
        )
        session.commit()

        return ApiKeyCreateResponse(id=key.id, name=key.name, token=token, token_prefix=key.token_prefix)

    @app.get("/api-keys", response_model=list[ApiKeyOut])
    def list_api_keys(
        request: Request,
        tenant_id: Optional[str] = Query(default=None),
        org_id: Optional[str] = Query(default=None),
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0, le=10_000),
        session: Session = Depends(get_session),
    ):
        if not is_api_key_admin_enabled():
            raise HTTPException(status_code=404, detail="Not found")

        authorize_request(request=request, session=session)
        q = session.query(ApiKey).filter(ApiKey.is_deleted == False)
        if tenant_id:
            q = q.filter(ApiKey.tenant_id == tenant_id)
        if org_id:
            q = q.filter(ApiKey.org_id == org_id)
        return q.order_by(ApiKey.created_at.desc()).offset(offset).limit(limit).all()

    @app.post("/api-keys/{api_key_id}/revoke", response_model=ApiKeyOut)
    def revoke_api_key(api_key_id: str, request: Request, session: Session = Depends(get_session)):
        if not is_api_key_admin_enabled():
            raise HTTPException(status_code=404, detail="Not found")

        identity = authorize_request(request=request, session=session)

        if identity.actor_type == "api_key":
            raise HTTPException(status_code=403, detail="API key admin requires admin token")
        key = session.query(ApiKey).filter(ApiKey.id == api_key_id, ApiKey.is_deleted == False).first()
        if not key:
            raise HTTPException(status_code=404, detail="API key not found")
        key.revoke()
        session.add(key)
        session.commit()
        session.refresh(key)

        AuditService.log_action(
            session,
            action=AuditAction.REVOKE,
            entity_type="ApiKey",
            entity_id=key.id,
            actor_id=identity.actor_id,
            actor_type=identity.actor_type,
            changes={"revoked": True, "token_prefix": key.token_prefix},
            context={"tenant_id": identity.tenant_id, "org_id": identity.org_id},
        )
        session.commit()

        return key

    # Persisted checkpoints (export boundaries)
    @app.post("/audit-checkpoints", response_model=AuditCheckpointOut)
    def create_audit_checkpoint(
        payload: AuditCheckpointCreate,
        request: Request,
        session: Session = Depends(get_session),
    ):
        authorize_request(request=request, session=session)
        actor_id = request.headers.get("X-Actor-Id") or request.headers.get("X-User-Id") or "unknown"
        actor_type = request.headers.get("X-Actor-Type") or "user"
        ctx = {
            "tenant_id": request.headers.get("X-Tenant-Id"),
            "org_id": request.headers.get("X-Org-Id"),
            "team_id": request.headers.get("X-Team-Id"),
            "client_host": request.client.host if request.client else None,
        }

        cp = AuditService.create_persisted_checkpoint(
            session,
            chain_id=payload.chain_id,
            actor_id=actor_id,
            actor_type=actor_type,
            checkpoint_context=ctx,
        )
        session.commit()
        session.refresh(cp)
        return cp

    @app.get("/audit-checkpoints", response_model=list[AuditCheckpointOut])
    def list_audit_checkpoints(
        request: Request,
        chain_id: Optional[str] = Query(default=None),
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0, le=10_000),
        session: Session = Depends(get_session),
    ):
        authorize_request(request=request, session=session)
        q = session.query(AuditCheckpoint).filter(AuditCheckpoint.is_deleted == False)
        if chain_id:
            q = q.filter(AuditCheckpoint.chain_id == chain_id)
        return q.order_by(AuditCheckpoint.created_at.desc()).offset(offset).limit(limit).all()

    @app.get("/audit-checkpoints/latest", response_model=AuditCheckpointOut)
    def latest_audit_checkpoint(
        request: Request,
        chain_id: str = Query(default="global"),
        session: Session = Depends(get_session),
    ):
        authorize_request(request=request, session=session)
        cp = (
            session.query(AuditCheckpoint)
            .filter(AuditCheckpoint.is_deleted == False)
            .filter(AuditCheckpoint.chain_id == chain_id)
            .order_by(AuditCheckpoint.created_at.desc())
            .first()
        )
        if not cp:
            raise HTTPException(status_code=404, detail="No checkpoint for chain")
        return cp

    return app


# Default app for `uvicorn hexarch_cli.server.app:app`
app = create_app(init_db=False)
