"""
Entitlement model: User/entity grants and permissions.
"""

from enum import Enum
from datetime import datetime, timedelta
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from hexarch_cli.models.base import BaseModel


class EntitlementStatus(str, Enum):
    """Status of an entitlement."""
    ACTIVE = "ACTIVE"           # Currently valid
    PENDING = "PENDING"         # Waiting for approval
    SUSPENDED = "SUSPENDED"     # Temporarily disabled
    REVOKED = "REVOKED"         # Permanently disabled
    EXPIRED = "EXPIRED"         # Reached expiration date


class EntitlementType(str, Enum):
    """Type of entitlement."""
    ROLE = "ROLE"               # Role-based (e.g., admin, user)
    PERMISSION = "PERMISSION"   # Specific permission
    GRANT = "GRANT"             # One-time grant
    DELEGATION = "DELEGATION"   # Delegated from another user


class Entitlement(BaseModel):
    """
    Represents an entitlement: a grant of permissions/roles to a user/entity.
    
    Fields:
    - id: UUID primary key
    - subject_id: Who has the entitlement (user_id, org_id, service_id)
    - subject_type: Type of subject (user, org, service, etc.)
    - entitlement_type: ROLE, PERMISSION, GRANT, DELEGATION
    - resource_id: What resource is granted (optional, for resource-specific)
    - resource_type: Type of resource
    - status: Current status (ACTIVE, PENDING, SUSPENDED, REVOKED, EXPIRED)
    - valid_from: When entitlement becomes active
    - expires_at: When entitlement expires (optional)
    - granted_by: User who granted this entitlement
    - reason: Why this entitlement was granted
    - metadata: Additional context (constraints, conditions, etc.)
    """
    __tablename__ = "entitlements"
    
    # Subject
    subject_id = Column(String(255), nullable=False, index=True)
    subject_type = Column(String(50), default="user", nullable=False)  # user, org, service, etc.
    
    # Entitlement details
    entitlement_type = Column(String(50), nullable=False, index=True)  # ROLE, PERMISSION, GRANT, DELEGATION
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Resource
    resource_id = Column(String(255), nullable=True, index=True)
    resource_type = Column(String(50), nullable=True)
    
    # Status
    status = Column(String(50), default=EntitlementStatus.PENDING, nullable=False, index=True)
    
    # Timing
    valid_from = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True, index=True)
    
    # Audit
    granted_by = Column(String(255), nullable=True)
    revoked_by = Column(String(255), nullable=True)
    reason = Column(Text, nullable=True)
    
    # Metadata (JSON) (renamed to avoid SQLAlchemy reserved name)
    entitlement_metadata = Column(JSON, nullable=True)  # constraints, conditions, tags, etc.
    
    # Relationships
    decisions = relationship("Decision", back_populates="entitlement")
    audit_logs = relationship("AuditLog", back_populates="entitlement")
    
    __table_args__ = (
        Index("ix_entitlements_subject", "subject_id", "subject_type"),
        Index("ix_entitlements_status_expires", "status", "expires_at"),
        Index("ix_entitlements_type", "entitlement_type", "status"),
    )
    
    def is_active(self) -> bool:
        """Check if entitlement is currently active."""
        if self.status != EntitlementStatus.ACTIVE:
            return False
        
        now = datetime.utcnow()
        
        # Check valid_from
        if self.valid_from > now:
            return False
        
        # Check expiration
        if self.expires_at and self.expires_at < now:
            return False
        
        return True
    
    def is_expired(self) -> bool:
        """Check if entitlement has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def revoke(self, revoked_by: str):
        """Revoke this entitlement."""
        self.status = EntitlementStatus.REVOKED
        self.revoked_by = revoked_by
    
    def suspend(self):
        """Suspend this entitlement."""
        self.status = EntitlementStatus.SUSPENDED
    
    def reactivate(self):
        """Reactivate a suspended entitlement."""
        if self.status == EntitlementStatus.SUSPENDED:
            self.status = EntitlementStatus.ACTIVE
