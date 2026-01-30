"""Tests for RuleEvaluator DSL."""

import pytest
from hexarch_cli.rules_engine import RuleEvaluator, RuleEvaluationError


@pytest.fixture
def evaluator():
    return RuleEvaluator()


def test_equals_operator(evaluator):
    rule = {"field": "user.role", "op": "equals", "value": "admin"}
    context = {"user": {"role": "admin"}}
    assert evaluator.evaluate_rule(rule, context) is True


def test_not_equals_operator(evaluator):
    rule = {"field": "user.role", "op": "not_equals", "value": "admin"}
    context = {"user": {"role": "guest"}}
    assert evaluator.evaluate_rule(rule, context) is True


def test_in_operator(evaluator):
    rule = {"field": "user.tier", "op": "in", "value": ["pro", "enterprise"]}
    context = {"user": {"tier": "pro"}}
    assert evaluator.evaluate_rule(rule, context) is True


def test_contains_operator(evaluator):
    rule = {"field": "user.tags", "op": "contains", "value": "beta"}
    context = {"user": {"tags": ["alpha", "beta"]}}
    assert evaluator.evaluate_rule(rule, context) is True


def test_numeric_comparison(evaluator):
    rule = {"field": "request.count", "op": "lte", "value": 10}
    context = {"request": {"count": 5}}
    assert evaluator.evaluate_rule(rule, context) is True


def test_between_operator(evaluator):
    rule = {"field": "request.count", "op": "between", "value": [1, 5]}
    context = {"request": {"count": 3}}
    assert evaluator.evaluate_rule(rule, context) is True


def test_regex_operator(evaluator):
    rule = {"field": "user.email", "op": "regex", "value": r".*@example.com"}
    context = {"user": {"email": "admin@example.com"}}
    assert evaluator.evaluate_rule(rule, context) is True


def test_exists_operator(evaluator):
    rule = {"field": "user.id", "op": "exists"}
    context = {"user": {"id": "123"}}
    assert evaluator.evaluate_rule(rule, context) is True


def test_all_operator(evaluator):
    rule = {
        "all": [
            {"field": "user.role", "op": "equals", "value": "admin"},
            {"field": "request.count", "op": "lt", "value": 100},
        ]
    }
    context = {"user": {"role": "admin"}, "request": {"count": 50}}
    assert evaluator.evaluate_rule(rule, context) is True


def test_any_operator(evaluator):
    rule = {
        "any": [
            {"field": "user.role", "op": "equals", "value": "admin"},
            {"field": "user.role", "op": "equals", "value": "editor"},
        ]
    }
    context = {"user": {"role": "editor"}}
    assert evaluator.evaluate_rule(rule, context) is True


def test_not_operator(evaluator):
    rule = {"not": {"field": "user.role", "op": "equals", "value": "guest"}}
    context = {"user": {"role": "admin"}}
    assert evaluator.evaluate_rule(rule, context) is True


def test_allow_wrapper(evaluator):
    rule = {"allow": {"field": "user.role", "op": "equals", "value": "admin"}}
    context = {"user": {"role": "admin"}}
    assert evaluator.evaluate_rule(rule, context) is True


def test_deny_wrapper(evaluator):
    rule = {"deny": {"field": "user.role", "op": "equals", "value": "guest"}}
    context = {"user": {"role": "admin"}}
    assert evaluator.evaluate_rule(rule, context) is True


def test_missing_operator_raises(evaluator):
    rule = {"field": "user.role", "value": "admin"}
    with pytest.raises(RuleEvaluationError):
        evaluator.evaluate_rule(rule, {"user": {"role": "admin"}})


def test_invalid_rule_structure_raises(evaluator):
    rule = {"unknown": "structure"}
    with pytest.raises(RuleEvaluationError):
        evaluator.evaluate_rule(rule, {})


def test_yaml_parsing(evaluator):
    yaml_rule = """
all:
  - field: user.role
    op: equals
    value: admin
  - field: request.count
    op: lt
    value: 10
"""
    context = {"user": {"role": "admin"}, "request": {"count": 5}}
    assert evaluator.evaluate_rule(yaml_rule, context) is True
