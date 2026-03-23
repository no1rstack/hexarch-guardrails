"""FastAPI middleware integration for reusable OPA policy enforcement."""

from typing import Any, Callable, Dict, Optional, Tuple

from .policy_engine import RegoDecisionEngine


def build_policy_input(request: Any, openapi_hint: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Build stable policy input envelope from a FastAPI/Starlette request."""
    return {
        "method": request.method,
        "path": request.url.path,
        "query": dict(request.query_params),
        "identity": {
            "actor_id": request.headers.get("x-actor-id", "anonymous"),
            "role": request.headers.get("x-role", "user"),
        },
        "openapi": openapi_hint or {},
    }


def extract_openapi_policy_hints(app: Any) -> Dict[Tuple[str, str], Dict[str, Any]]:
    """Build (METHOD, path) -> x-policy map from OpenAPI schema."""
    hints: Dict[Tuple[str, str], Dict[str, Any]] = {}

    try:
        schema = app.openapi()
    except Exception:
        return hints

    paths = schema.get("paths", {}) if isinstance(schema, dict) else {}
    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method.upper() not in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}:
                continue
            if not isinstance(operation, dict):
                continue
            x_policy = operation.get("x-policy")
            if isinstance(x_policy, dict):
                hints[(method.upper(), path)] = x_policy

    return hints


class FastAPIPolicyMiddleware:
    """Request boundary enforcement middleware."""

    def __init__(
        self,
        app: Any,
        *,
        engine: Optional[RegoDecisionEngine] = None,
        fail_closed: bool = True,
        exempt_paths: Tuple[str, ...] = ("/health", "/docs", "/openapi.json", "/redoc"),
        openapi_hints: Optional[Dict[Tuple[str, str], Dict[str, Any]]] = None,
        audit_hook: Optional[Callable[[Dict[str, Any], Dict[str, Any]], None]] = None,
    ):
        self.app = app
        self.engine = engine or RegoDecisionEngine(fail_closed=fail_closed)
        self.fail_closed = fail_closed
        self.exempt_paths = set(exempt_paths)
        self.openapi_hints = openapi_hints or {}
        self.audit_hook = audit_hook

    async def __call__(self, scope: Dict[str, Any], receive: Callable, send: Callable):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        try:
            from starlette.requests import Request
            from starlette.responses import JSONResponse
        except Exception as exc:
            raise RuntimeError(
                "FastAPI/Starlette is required for FastAPIPolicyMiddleware. "
                "Install server extras: pip install 'hexarch-guardrails[server]'"
            ) from exc

        request = Request(scope, receive=receive)
        if request.url.path in self.exempt_paths:
            await self.app(scope, receive, send)
            return

        hint = self.openapi_hints.get((request.method.upper(), request.url.path), {})
        input_data = build_policy_input(request, openapi_hint=hint)
        decision = self.engine.evaluate(input_data)

        if self.audit_hook:
            try:
                self.audit_hook(input_data, decision)
            except Exception:
                # never block request path due to audit callback failures
                pass

        if not decision.get("allow", False):
            response = JSONResponse(
                status_code=403,
                content={"error": "access_denied", "decision": decision},
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)


def install_fastapi_policy(
    app: Any,
    *,
    engine: Optional[RegoDecisionEngine] = None,
    fail_closed: bool = True,
    exempt_paths: Tuple[str, ...] = ("/health", "/docs", "/openapi.json", "/redoc"),
    parse_openapi_hints: bool = True,
    audit_hook: Optional[Callable[[Dict[str, Any], Dict[str, Any]], None]] = None,
) -> None:
    """Convenience installer for policy middleware on a FastAPI app."""
    hints = extract_openapi_policy_hints(app) if parse_openapi_hints else {}
    app.add_middleware(
        FastAPIPolicyMiddleware,
        engine=engine,
        fail_closed=fail_closed,
        exempt_paths=exempt_paths,
        openapi_hints=hints,
        audit_hook=audit_hook,
    )
