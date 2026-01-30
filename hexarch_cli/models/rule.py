"""
Rule model: Core business logic - conditions, permissions, constraints, and evaluation.
"""

from enum import Enum
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from hexarch_cli.models.base import BaseModel


class RuleType(str, Enum):
    """Types of rules."""
    CONDITION = "CONDITION"         # If-then conditions
    PERMISSION = "PERMISSION"       # Allow/deny permissions
    CONSTRAINT = "CONSTRAINT"       # Operational constraints (rate limits, quotas)
    COMPOSITE = "COMPOSITE"         # Combination of other rules


class RuleOperator(str, Enum):
    """Logical operators for rule composition."""
    AND = "AND"
    OR = "OR"
    NOT = "NOT"


class Rule(BaseModel):
    """
    Represents a single rule: a condition, permission, or constraint.
    
    Rules can be composed together with AND/OR/NOT operators.
    
    Fields:
    - id: UUID primary key
    - name: Human-readable rule name
    - description: Rule explanation
    - rule_type: CONDITION, PERMISSION, CONSTRAINT, or COMPOSITE
    - priority: Numeric priority (lower = higher priority)
    - enabled: Whether rule is active
    - condition: JSON rule definition (varies by type)
    - parent_rule_id: For composite rules, reference to parent
    - operator: Logical operator (AND, OR, NOT) for composition
    - metadata: Additional JSON metadata
    """
    __tablename__ = "rules"
    
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    rule_type = Column(String(50), nullable=False, index=True)  # CONDITION, PERMISSION, CONSTRAINT, COMPOSITE
    
    # Priority and enablement
    priority = Column(Integer, default=100, nullable=False, index=True)
    enabled = Column(Boolean, default=True, nullable=False, index=True)
    
    # Rule definition (JSON)
    # Example: {"field": "user.role", "operator": "equals", "value": "admin"}
    condition = Column(JSON, nullable=False)
    
    # Composition
    parent_rule_id = Column(String(36), ForeignKey("rules.id"), nullable=True)
    operator = Column(String(10), nullable=True)  # AND, OR, NOT
    
    # Metadata (renamed to avoid SQLAlchemy reserved name)
    rule_metadata = Column(JSON, nullable=True)
    
    # Relationships
    parent_rule = relationship("Rule", remote_side="Rule.id", backref="child_rules")
    policies = relationship("Policy", secondary="policy_rules", back_populates="rules")
    
    __table_args__ = (
        Index("ix_rules_type_enabled", "rule_type", "enabled"),
        Index("ix_rules_priority_enabled", "priority", "enabled"),
    )
    
    def evaluate(self, context: dict) -> bool:
        """
        Evaluate this rule against a context.
        
        Args:
            context: Dictionary of variables/facts for evaluation
            
        Returns:
            True if rule condition is met, False otherwise
        """
        from hexarch_cli.rules_engine import RuleEvaluator
        
        if not self.enabled:
            return False
        
        evaluator = RuleEvaluator()
        return evaluator.evaluate_rule(self.condition, context)


class PolicyRule(BaseModel):
    """
    Association table: links policies to rules.
    Allows many-to-many relationship with ordering.
    """
    __tablename__ = "policy_rules"
    
    policy_id = Column(String(36), ForeignKey("policies.id"), nullable=False, index=True)
    rule_id = Column(String(36), ForeignKey("rules.id"), nullable=False, index=True)
    order = Column(Integer, default=0, nullable=False)  # Execution order
    
    # Composite key
    __table_args__ = (
        Index("ix_policy_rules_order", "policy_id", "order"),
    )
