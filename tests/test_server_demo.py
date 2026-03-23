import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("HEXARCH_API_TOKEN", "dev-token")
    monkeypatch.setenv("HEXARCH_BOOTSTRAP_ALLOW", "true")
    monkeypatch.setenv("HEXARCH_DEMO_TOKEN_SECRET", "test-demo-secret")
    monkeypatch.setenv("HEXARCH_DEMO_ISSUE_RPM", "5")
    monkeypatch.setenv("HEXARCH_DEMO_EXCHANGE_RPM", "20")
    monkeypatch.setenv("HEXARCH_DEMO_SESSION_RPM", "60")


@pytest.fixture(autouse=True)
def _reset_demo_state():
    from hexarch_cli.server import demo_auth

    demo_auth.DEMO_ISSUED_SESSIONS.clear()
    demo_auth.DEMO_ACTIVE_SESSIONS.clear()
    demo_auth.ISSUE_LIMITER._buckets.clear()
    demo_auth.EXCHANGE_LIMITER._buckets.clear()
    demo_auth.SESSION_LIMITER._buckets.clear()


def _client():
    from hexarch_cli.server.app import create_app

    app = create_app(init_db=True)
    return TestClient(app)


def test_demo_session_issue_exchange_and_sandbox_evaluate():
    c = _client()

    issue = c.post("/api/demo/session", json={})
    assert issue.status_code == 200
    body = issue.json()
    assert body["token"]
    assert body["session_id"].startswith("demo_")

    exchange = c.post("/api/demo/exchange", json={"token": body["token"]})
    assert exchange.status_code == 200
    session_token = exchange.json()["session_token"]

    policies = c.get("/demo/policies", headers={"Authorization": f"Bearer {session_token}"})
    assert policies.status_code == 200
    assert len(policies.json()) >= 1

    allow = c.post(
        "/demo/evaluate",
        headers={"Authorization": f"Bearer {session_token}"},
        json={"action": "read", "resource": "docs"},
    )
    assert allow.status_code == 200
    assert allow.json()["allowed"] is True
    assert allow.json()["sandboxed"] is True
    assert allow.json()["persisted"] is False

    deny = c.post(
        "/demo/evaluate",
        headers={"Authorization": f"Bearer {session_token}"},
        json={"action": "delete", "resource": "records"},
    )
    assert deny.status_code == 200
    assert deny.json()["allowed"] is False
    assert deny.json()["decision"] == "DENY"


def test_demo_bootstrap_token_cannot_access_demo_routes_without_exchange():
    c = _client()

    issue = c.post("/api/demo/session", json={})
    token = issue.json()["token"]

    r = c.get("/demo/policies", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_demo_token_exchange_is_one_time():
    c = _client()

    issue = c.post("/api/demo/session", json={})
    token = issue.json()["token"]

    first = c.post("/api/demo/exchange", json={"token": token})
    assert first.status_code == 200

    second = c.post("/api/demo/exchange", json={"token": token})
    assert second.status_code == 401


def test_demo_issue_rate_limit_per_ip():
    c = _client()
    for _ in range(5):
        ok = c.post("/api/demo/session", json={})
        assert ok.status_code == 200

    blocked = c.post("/api/demo/session", json={})
    assert blocked.status_code == 429
