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
from .policy_bundles import load_policy_bundle, publish_policy_bundle
from .policy_engine import RegoDecisionEngine, build_engine_from_bundle
from .runtime_settings import RuntimePolicySettings, resolve_runtime_settings

__version__ = "0.4.1"
__author__ = "Hexarch"

__all__ = [
    "Guardian",
    "GuardrailException",
    "OPAConnectionError",
    "OPAPolicyError",
    "PolicyViolation",
    "PolicyWarning",
    "PolicyConfigError",
    "load_policy_bundle",
    "publish_policy_bundle",
    "RegoDecisionEngine",
    "build_engine_from_bundle",
    "RuntimePolicySettings",
    "resolve_runtime_settings",
]
