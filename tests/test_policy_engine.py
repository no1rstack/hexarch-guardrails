"""Tests for RegoDecisionEngine behavior."""

from unittest.mock import Mock, patch

from hexarch_guardrails.policy_engine import RegoDecisionEngine


@patch("hexarch_guardrails.policy_engine.requests.post")
def test_engine_accepts_boolean_result(mock_post):
    response = Mock()
    response.json.return_value = {"result": True}
    response.raise_for_status.return_value = None
    mock_post.return_value = response

    engine = RegoDecisionEngine(opa_url="http://opa:8181")
    decision = engine.evaluate({"path": "/anything"})

    assert decision["allow"] is True
    assert decision["error"] is None


@patch("hexarch_guardrails.policy_engine.requests.post")
def test_engine_accepts_dict_allow_result(mock_post):
    response = Mock()
    response.json.return_value = {"result": {"allow": False, "reason": "blocked"}}
    response.raise_for_status.return_value = None
    mock_post.return_value = response

    engine = RegoDecisionEngine()
    decision = engine.evaluate({"path": "/admin"})

    assert decision["allow"] is False
    assert decision["error"] is None


@patch("hexarch_guardrails.policy_engine.requests.post")
def test_engine_fail_closed_on_error(mock_post):
    mock_post.side_effect = RuntimeError("boom")

    engine = RegoDecisionEngine(fail_closed=True)
    decision = engine.evaluate({"path": "/admin"})

    assert decision["allow"] is False
    assert "boom" in decision["error"]


@patch("hexarch_guardrails.policy_engine.requests.post")
def test_engine_fail_open_on_error(mock_post):
    mock_post.side_effect = RuntimeError("boom")

    engine = RegoDecisionEngine(fail_closed=False)
    decision = engine.evaluate({"path": "/admin"})

    assert decision["allow"] is True
    assert "boom" in decision["error"]
