import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("HEXARCH_API_TOKEN", "dev-token")
    # keep bootstrap on for initial policy creation
    monkeypatch.setenv("HEXARCH_BOOTSTRAP_ALLOW", "true")
    # Key management endpoints are disabled by default; enable for tests that cover them.
    monkeypatch.setenv("HEXARCH_API_KEY_ADMIN_ENABLED", "true")


def _client():
    from hexarch_cli.server.app import create_app

    app = create_app(init_db=True)
    return TestClient(app)


def test_authorize_requires_bearer_token():
    c = _client()
    r = c.post("/authorize", json={"action": "read"})
    assert r.status_code == 401


def test_echo_is_public():
    c = _client()
    r = c.post("/echo", json={"message": "hello", "metadata": {"k": "v"}})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["message"] == "hello"
    assert body["metadata"]["k"] == "v"


def test_authorize_denies_without_policies_then_allows_after_bootstrap_policy():
    c = _client()

    # No policies yet => deny by default
    r = c.post(
        "/authorize",
        headers={"Authorization": "Bearer dev-token", "X-Actor-Id": "admin"},
        json={"action": "read"},
    )
    assert r.status_code == 200
    assert r.json()["allowed"] is False

    # Bootstrap: create an allow-all global policy (no rules => allow)
    r = c.post(
        "/policies",
        headers={"Authorization": "Bearer dev-token", "X-Actor-Id": "admin"},
        json={
            "name": "bootstrap-allow-all",
            "description": "",
            "enabled": True,
            "scope": "GLOBAL",
            "scope_value": None,
            "failure_mode": "FAIL_CLOSED",
            "rule_ids": [],
        },
    )
    assert r.status_code == 200

    r = c.post(
        "/authorize",
        headers={"Authorization": "Bearer dev-token", "X-Actor-Id": "admin"},
        json={"action": "read"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["allowed"] is True
    assert body["decision"] == "ALLOW"

    # Audit evidence is written
    r = c.get(
        "/audit-logs",
        headers={"Authorization": "Bearer dev-token", "X-Actor-Id": "admin"},
    )
    assert r.status_code == 200
    logs = r.json()
    assert len(logs) >= 1
    # New integrity fields should be present for newly-written logs
    assert any(l.get("entry_hash") for l in logs)

    # Chain should verify
    r = c.get(
        "/audit-logs/verify",
        headers={"Authorization": "Bearer dev-token", "X-Actor-Id": "admin"},
    )
    assert r.status_code == 200
    assert r.json()["ok"] is True

    # Checkpoint should return latest hash
    r = c.get(
        "/audit-logs/checkpoint",
        headers={"Authorization": "Bearer dev-token", "X-Actor-Id": "admin"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["chain_id"] == "global"
    assert body["last_entry_hash"]
    assert "signed" in body

    # Issue a DB-backed API key (hardening beyond a single env token)
    r = c.post(
        "/api-keys",
        headers={"Authorization": "Bearer dev-token", "X-Actor-Id": "admin"},
        json={"name": "ui-key", "tenant_id": "t1", "org_id": "o1", "scopes": ["read", "write"]},
    )
    assert r.status_code == 200
    api_key_token = r.json()["token"]

    # Issue a read-only key
    r = c.post(
        "/api-keys",
        headers={"Authorization": "Bearer dev-token", "X-Actor-Id": "admin"},
        json={"name": "ro-key", "tenant_id": "t1", "org_id": "o1", "scopes": ["read"]},
    )
    assert r.status_code == 200
    ro_id = r.json()["id"]
    ro_token = r.json()["token"]

    # Use the new key to access a protected endpoint (policy exists now)
    r = c.get(
        "/rules",
        headers={"Authorization": f"Bearer {api_key_token}", "X-Tenant-Id": "t1"},
    )
    assert r.status_code == 200

    # API keys must not be able to mint other API keys.
    r = c.post(
        "/api-keys",
        headers={"Authorization": f"Bearer {api_key_token}", "X-Tenant-Id": "t1"},
        json={"name": "nope", "tenant_id": "t1", "org_id": "o1", "scopes": ["read"]},
    )
    assert r.status_code == 403

    # Scope enforcement: read-only key cannot perform write actions
    r = c.post(
        "/audit-checkpoints",
        headers={"Authorization": f"Bearer {ro_token}", "X-Tenant-Id": "t1"},
        json={"chain_id": "global"},
    )
    assert r.status_code == 403

    # Denial is auditable under the api_key actor_id
    r = c.get(
        f"/audit-logs?actor_id=api_key:{ro_id}",
        headers={"Authorization": "Bearer dev-token", "X-Actor-Id": "admin"},
    )
    assert r.status_code == 200
    logs = r.json()
    assert any(l.get("reason") == "scope_denied" for l in logs)

    # Provider-call event ingestion (for orchestration tools like n8n)
    r = c.post(
        "/events/provider-calls",
        headers={"Authorization": "Bearer dev-token", "X-Actor-Id": "admin"},
        json={
            "resource": "ollama",
            "action": "generate",
            "ok": True,
            "status_code": 200,
            "latency_ms": 123,
            "model": "llama3",
            "tokens_in": 10,
            "tokens_out": 20,
            "cost_usd": 0.0,
            "metadata": {"workflow": "n8n"},
        },
    )
    assert r.status_code == 200
    event_id = r.json()["id"]
    assert event_id

    r = c.get(
        "/events/provider-calls",
        headers={"Authorization": "Bearer dev-token", "X-Actor-Id": "admin"},
    )
    assert r.status_code == 200
    events = r.json()
    assert any(e.get("entity_id") == event_id for e in events)

    # Persisted checkpoint acts as an export boundary
    r = c.post(
        "/audit-checkpoints",
        headers={"Authorization": "Bearer dev-token", "X-Actor-Id": "admin"},
        json={"chain_id": "global"},
    )
    assert r.status_code == 200
    persisted = r.json()
    assert persisted["chain_id"] == "global"
    assert persisted["last_entry_hash"]
    assert persisted["actor_id"] == "admin"

    r = c.get(
        "/audit-checkpoints/latest?chain_id=global",
        headers={"Authorization": "Bearer dev-token", "X-Actor-Id": "admin"},
    )
    assert r.status_code == 200
    latest = r.json()
    assert latest["id"] == persisted["id"]

    r = c.get(
        "/audit-checkpoints?chain_id=global",
        headers={"Authorization": "Bearer dev-token", "X-Actor-Id": "admin"},
    )
    assert r.status_code == 200
    cps = r.json()
    assert any(cp["id"] == persisted["id"] for cp in cps)


def test_api_key_admin_endpoints_hidden_when_disabled(monkeypatch):
    monkeypatch.setenv("HEXARCH_API_KEY_ADMIN_ENABLED", "false")

    c = _client()
    r = c.post(
        "/api-keys",
        headers={"Authorization": "Bearer dev-token", "X-Actor-Id": "admin"},
        json={"name": "ui-key", "tenant_id": "t1", "org_id": "o1", "scopes": ["read"]},
    )
    assert r.status_code == 404
