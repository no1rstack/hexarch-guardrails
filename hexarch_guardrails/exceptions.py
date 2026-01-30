"""
Custom exceptions for Hexarch Guardrails
"""


class GuardrailException(Exception):
    """Base exception for guardrails"""
    pass


class OPAConnectionError(GuardrailException):
    """Failed to connect to OPA server"""
    pass


class OPAPolicyError(GuardrailException):
    """OPA policy evaluation error"""
    pass


class PolicyViolation(GuardrailException):
    """Policy violation - action blocked"""
    pass


class PolicyWarning(GuardrailException):
    """Policy warning - action allowed but flagged"""
    pass


class PolicyConfigError(GuardrailException):
    """Invalid policy configuration"""
    pass
