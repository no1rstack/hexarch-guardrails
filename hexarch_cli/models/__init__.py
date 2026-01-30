"""
Models package: Database models and ORM setup.
Supports both SQLite (local) and PostgreSQL (production).
"""

from hexarch_cli.models.base import Base, BaseModel, TimestampMixin, SoftDeleteMixin, VersioningMixin, AuditableMixin
from hexarch_cli.models.decision import Decision, DecisionState
from hexarch_cli.models.policy import Policy, PolicyScope, FailureMode
from hexarch_cli.models.rule import Rule, RuleType, RuleOperator, PolicyRule
from hexarch_cli.models.entitlement import Entitlement, EntitlementStatus, EntitlementType
from hexarch_cli.models.audit import AuditCheckpoint, AuditLog, AuditAction, AuditService
from hexarch_cli.models.api_key import ApiKey

__all__ = [
    # Base
    "Base",
    "BaseModel",
    "TimestampMixin",
    "SoftDeleteMixin",
    "VersioningMixin",
    "AuditableMixin",
    # Decision
    "Decision",
    "DecisionState",
    # Policy
    "Policy",
    "PolicyScope",
    "FailureMode",
    # Rule
    "Rule",
    "RuleType",
    "RuleOperator",
    "PolicyRule",
    # Entitlement
    "Entitlement",
    "EntitlementStatus",
    "EntitlementType",
    # Audit
    "AuditLog",
    "AuditCheckpoint",
    "AuditAction",
    "AuditService",
    # API keys
    "ApiKey",
]
