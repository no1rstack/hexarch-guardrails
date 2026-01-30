"""Rules Engine DSL and evaluation logic."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml


class RuleEvaluationError(ValueError):
    """Raised when a rule cannot be evaluated due to invalid structure."""


_MISSING = object()


@dataclass
class RuleEvaluationResult:
    """Evaluation result with optional trace."""
    allowed: bool
    trace: Optional[Dict[str, Any]] = None


class RuleEvaluator:
    """Evaluates JSON/YAML rule definitions against a context."""

    def parse_rule(self, rule_input: Union[str, Dict[str, Any], List[Any]]) -> Dict[str, Any]:
        """
        Parse rule input from JSON/YAML string or dict.
        
        Args:
            rule_input: JSON/YAML string, dict, or list of rules
            
        Returns:
            Parsed rule dict
        """
        if isinstance(rule_input, dict):
            return rule_input
        if isinstance(rule_input, list):
            return {"all": rule_input}
        if isinstance(rule_input, str):
            try:
                return json.loads(rule_input)
            except json.JSONDecodeError:
                try:
                    return yaml.safe_load(rule_input)
                except yaml.YAMLError as exc:
                    raise RuleEvaluationError("Invalid rule input: not valid JSON or YAML") from exc
        raise RuleEvaluationError("Invalid rule input type")

    def evaluate_rule(self, rule: Union[str, Dict[str, Any], List[Any]], context: Dict[str, Any]) -> bool:
        """
        Evaluate a rule against context.
        
        Args:
            rule: Rule definition (dict or JSON/YAML string)
            context: Evaluation context
            
        Returns:
            True if rule passes, False otherwise
        """
        parsed = self.parse_rule(rule)
        result = self._evaluate(parsed, context)
        return result.allowed

    def evaluate_with_trace(self, rule: Union[str, Dict[str, Any], List[Any]], context: Dict[str, Any]) -> RuleEvaluationResult:
        """Evaluate a rule and return detailed trace."""
        parsed = self.parse_rule(rule)
        return self._evaluate(parsed, context)

    def _evaluate(self, rule: Dict[str, Any], context: Dict[str, Any]) -> RuleEvaluationResult:
        # Composite operators
        if "all" in rule:
            results = [self._evaluate(r, context) for r in rule["all"]]
            allowed = all(r.allowed for r in results)
            return RuleEvaluationResult(allowed=allowed, trace={"all": results})

        if "any" in rule:
            results = [self._evaluate(r, context) for r in rule["any"]]
            allowed = any(r.allowed for r in results)
            return RuleEvaluationResult(allowed=allowed, trace={"any": results})

        if "not" in rule:
            result = self._evaluate(rule["not"], context)
            return RuleEvaluationResult(allowed=not result.allowed, trace={"not": result})

        # Permission wrappers
        if "allow" in rule:
            result = self._evaluate(rule["allow"], context)
            return RuleEvaluationResult(allowed=result.allowed, trace={"allow": result})

        if "deny" in rule:
            result = self._evaluate(rule["deny"], context)
            return RuleEvaluationResult(allowed=not result.allowed, trace={"deny": result})

        # Leaf condition
        if "field" in rule:
            field = rule.get("field")
            operator = rule.get("op") or rule.get("operator")
            value = rule.get("value", _MISSING)
            
            if not operator:
                raise RuleEvaluationError("Missing operator in rule")
            
            field_value = self._get_field_value(context, field)
            allowed = self._evaluate_operator(operator, field_value, value)
            return RuleEvaluationResult(allowed=allowed, trace={"field": field, "op": operator, "value": value, "actual": field_value})

        # Unknown rule structure
        raise RuleEvaluationError("Invalid rule structure")

    def _get_field_value(self, context: Dict[str, Any], field: str) -> Any:
        """
        Get a value from context by dotted path.
        Supports list indexing: "user.roles[0]".
        """
        if not field:
            return _MISSING

        current = context
        parts = field.split(".")

        for part in parts:
            match = re.match(r"^(\w+)(\[(\d+)\])?$", part)
            if not match:
                return _MISSING

            key = match.group(1)
            index = match.group(3)

            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return _MISSING

            if index is not None:
                if isinstance(current, list):
                    idx = int(index)
                    if idx < 0 or idx >= len(current):
                        return _MISSING
                    current = current[idx]
                else:
                    return _MISSING

        return current

    def _evaluate_operator(self, operator: str, actual: Any, expected: Any) -> bool:
        """Evaluate a single operator."""
        op = operator.strip().lower()

        if op == "exists":
            return actual is not _MISSING and actual is not None

        if actual is _MISSING:
            return False

        if op == "equals":
            return actual == expected
        if op == "not_equals":
            return actual != expected
        if op == "in":
            return actual in (expected or [])
        if op == "not_in":
            return actual not in (expected or [])
        if op == "contains":
            if isinstance(actual, (list, tuple, set)):
                return expected in actual
            if isinstance(actual, str):
                return str(expected) in actual
            return False
        if op == "not_contains":
            if isinstance(actual, (list, tuple, set)):
                return expected not in actual
            if isinstance(actual, str):
                return str(expected) not in actual
            return False
        if op == "gt":
            return actual > expected
        if op == "gte":
            return actual >= expected
        if op == "lt":
            return actual < expected
        if op == "lte":
            return actual <= expected
        if op == "starts_with":
            return isinstance(actual, str) and isinstance(expected, str) and actual.startswith(expected)
        if op == "ends_with":
            return isinstance(actual, str) and isinstance(expected, str) and actual.endswith(expected)
        if op == "regex":
            if not isinstance(actual, str) or not isinstance(expected, str):
                return False
            return re.search(expected, actual) is not None
        if op == "between":
            if not isinstance(expected, (list, tuple)) or len(expected) != 2:
                raise RuleEvaluationError("'between' expects a list of two values")
            low, high = expected
            return low <= actual <= high

        raise RuleEvaluationError(f"Unsupported operator: {operator}")
