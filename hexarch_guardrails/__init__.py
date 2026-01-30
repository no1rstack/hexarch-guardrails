"""
Hexarch Guardrails Python SDK
Lightweight policy-driven API protection for developers
"""

from .guardian import Guardian
from .exceptions import (
    GuardrailException,
    OPAConnectionError,
    OPAPolicyError,
    PolicyViolation,
    PolicyWarning,
    PolicyConfigError,
)

__version__ = "0.3.1"
__author__ = "Hexarch"

__all__ = [
    "Guardian",
    "GuardrailException",
    "OPAConnectionError",
    "OPAPolicyError",
    "PolicyViolation",
    "PolicyWarning",
    "PolicyConfigError",
]
