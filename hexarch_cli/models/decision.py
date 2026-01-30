"""
Decision model: Tracks decisions with state, approval chains, and metadata.
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Text, DateTime, Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.orm import relationship
from hexarch_cli.models.base import BaseModel


class DecisionState(str, Enum):
    """Decision lifecycle states."""
    PENDING = "PENDING"           # Awaiting approval
    APPROVED = "APPROVED"         # Approved, not yet active
    ACTIVE = "ACTIVE"             # Currently in effect
    REJECTED = "REJECTED"         # Rejected by reviewer
    REVOKED = "REVOKED"           # Revoked after activation
    EXPIRED = "EXPIRED"           # Reached expiration


class Decision(BaseModel):
    """
    Represents a decision: a point-in-time authorization or policy decision.
    
    Fields:
    - id: UUID primary key
    - name: Human-readable decision name
    - description: Detailed explanation
    - state: Current decision state (PENDING, APPROVED, ACTIVE, etc.)
    - entitlement_id: Foreign key to Entitlement
    - policy_id: Foreign key to Policy (the rule applied)
    - creator_id: User ID who created this decision
    - reviewer_id: User ID who reviewed/approved
    - priority: Numeric priority (lower = higher priority)
    - expires_at: Optional expiration timestamp
    - context: JSON metadata/context
    - decision_reason: Why this decision was made
    """
    __tablename__ = "decisions"
    
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    state = Column(SQLEnum(DecisionState), default=DecisionState.PENDING, nullable=False, index=True)
    
    # Foreign keys
    entitlement_id = Column(String(36), ForeignKey("entitlements.id"), nullable=False, index=True)
    policy_id = Column(String(36), ForeignKey("policies.id"), nullable=True, index=True)
    
    # Audit
    creator_id = Column(String(255), nullable=False)
    reviewer_id = Column(String(255), nullable=True)
    
    # Priority and expiration
    priority = Column(String(50), default="MEDIUM", nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    expires_at = Column(DateTime, nullable=True, index=True)
    
    # Context and reason
    context = Column(Text, nullable=True)  # JSON
    decision_reason = Column(Text, nullable=True)
    
    # Relationships
    entitlement = relationship("Entitlement", back_populates="decisions")
    policy = relationship("Policy", back_populates="decisions")
    
    __table_args__ = (
        Index("ix_decisions_state_expires", "state", "expires_at"),
        Index("ix_decisions_entitlement_state", "entitlement_id", "state"),
    )
    
    def approve(self, reviewer_id: str):
        """Transition to APPROVED state."""
        if self.state not in [DecisionState.PENDING]:
            raise ValueError(f"Cannot approve decision in {self.state} state")
        self.state = DecisionState.APPROVED
        self.reviewer_id = reviewer_id
    
    def activate(self):
        """Transition to ACTIVE state."""
        if self.state not in [DecisionState.APPROVED]:
            raise ValueError(f"Cannot activate decision in {self.state} state")
        self.state = DecisionState.ACTIVE
    
    def reject(self, reviewer_id: str):
        """Transition to REJECTED state."""
        if self.state not in [DecisionState.PENDING]:
            raise ValueError(f"Cannot reject decision in {self.state} state")
        self.state = DecisionState.REJECTED
        self.reviewer_id = reviewer_id
    
    def revoke(self):
        """Transition to REVOKED state."""
        if self.state not in [DecisionState.ACTIVE]:
            raise ValueError(f"Cannot revoke decision in {self.state} state")
        self.state = DecisionState.REVOKED
    
    def is_expired(self) -> bool:
        """Check if decision has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
