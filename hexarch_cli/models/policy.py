"""
Policy model: Bundles rules together into enforceable policies.
"""

from enum import Enum
from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Index, JSON, Table
from sqlalchemy.orm import relationship
from hexarch_cli.models.base import BaseModel


class PolicyScope(str, Enum):
    """Scope/level of policy application."""
    GLOBAL = "GLOBAL"           # Apply everywhere
    ORGANIZATION = "ORGANIZATION"  # Apply to org
    TEAM = "TEAM"               # Apply to team
    USER = "USER"               # Apply to specific user
    RESOURCE = "RESOURCE"       # Apply to resource


class FailureMode(str, Enum):
    """How to handle policy evaluation failures."""
    FAIL_OPEN = "FAIL_OPEN"     # Allow access if check fails
    FAIL_CLOSED = "FAIL_CLOSED" # Deny access if check fails


class Policy(BaseModel):
    """
    Represents a policy: a collection of rules applied to decisions.
    
    Fields:
    - id: UUID primary key
    - name: Policy name
    - description: Policy explanation
    - scope: Where policy applies (GLOBAL, ORG, TEAM, USER, RESOURCE)
    - scope_value: Identifier for scope target (org_id, team_id, user_id, resource_id)
    - enabled: Whether policy is active
    - failure_mode: What happens on evaluation failure (FAIL_OPEN, FAIL_CLOSED)
    - rules: Collection of Rule objects linked via many-to-many
    - metadata: Additional JSON config (templates, webhooks, etc.)
    """
    __tablename__ = "policies"
    
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Scope
    scope = Column(String(50), default=PolicyScope.GLOBAL, nullable=False, index=True)
    scope_value = Column(String(255), nullable=True)  # org_id, team_id, etc.
    
    # Enablement and failure handling
    enabled = Column(Boolean, default=True, nullable=False, index=True)
    failure_mode = Column(String(50), default=FailureMode.FAIL_CLOSED, nullable=False)
    
    # Configuration/metadata (JSON for templates, webhooks, integrations)
    config = Column(Text, nullable=True)  # JSON or YAML
    
    # Relationships
    rules = relationship(
        "Rule",
        secondary="policy_rules",
        back_populates="policies",
        lazy="selectin"
    )
    decisions = relationship("Decision", back_populates="policy")
    
    __table_args__ = (
        Index("ix_policies_scope_enabled", "scope", "enabled"),
        Index("ix_policies_scope_value", "scope_value"),
    )
    
    def get_rules_ordered(self) -> list:
        """
        Get rules in execution order.
        
        Returns:
            List of Rule objects sorted by priority
        """
        from hexarch_cli.models.rule import PolicyRule
        # Rules are ordered by priority descending
        return sorted(self.rules, key=lambda r: (r.priority, r.created_at))
    
    def evaluate(self, context: dict) -> bool:
        """
        Evaluate all rules in this policy against context.
        
        Args:
            context: Dictionary of variables/facts for evaluation
            
        Returns:
            True if all rules pass, False otherwise (respects failure_mode)
        """
        if not self.enabled:
            return False
        
        rules = self.get_rules_ordered()

        for rule in rules:
            if not rule.enabled:
                continue

            try:
                result = rule.evaluate(context)
            except Exception:
                # Evaluation error: honor policy failure mode.
                if self.failure_mode == FailureMode.FAIL_OPEN:
                    continue
                return False

            if not result:
                # Rule failed
                if self.failure_mode == FailureMode.FAIL_CLOSED:
                    return False
                # For FAIL_OPEN, continue checking other rules

        return True
