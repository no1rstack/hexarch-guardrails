"""
Audit model: Complete audit trail of all changes.
"""

import hashlib
import json
import os
import hmac
from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import relationship
from hexarch_cli.models.base import BaseModel


class AuditAction(str, Enum):
    """Types of audit actions."""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"           # Soft delete
    HARD_DELETE = "HARD_DELETE" # Permanent delete (rare)
    RESTORE = "RESTORE"         # Restore soft-deleted
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    ACTIVATE = "ACTIVATE"
    REVOKE = "REVOKE"
    SUSPEND = "SUSPEND"
    EVALUATE = "EVALUATE"


class AuditLog(BaseModel):
    """
    Complete audit trail of all changes to auditable entities.
    
    Fields:
    - id: UUID primary key
    - action: Type of action (CREATE, UPDATE, DELETE, APPROVE, etc.)
    - entity_type: Type of entity changed (Decision, Policy, Rule, Entitlement, etc.)
    - entity_id: ID of entity changed
    - actor_id: User/service who made the change
    - changes: JSON of what changed (before/after values)
    - reason: Why this change was made
    """
    __tablename__ = "audit_logs"
    
    # Action
    action = Column(String(50), nullable=False, index=True)  # CREATE, UPDATE, DELETE, APPROVE, etc.
    
    # Entity
    entity_type = Column(String(50), nullable=False, index=True)  # Decision, Policy, Rule, Entitlement, etc.
    entity_id = Column(String(36), nullable=False, index=True)
    
    # Actor
    actor_id = Column(String(255), nullable=False, index=True)
    actor_type = Column(String(50), default="user", nullable=False)  # user, service, automation, etc.
    
    # Changes (JSON with before/after)
    # Example: {"before": {...}, "after": {...}, "fields": ["status", "priority"]}
    changes = Column(JSON, nullable=True)
    
    # Reason/context (renamed to avoid SQLAlchemy reserved name)
    reason = Column(Text, nullable=True)
    audit_context = Column(JSON, nullable=True)  # Additional context (IP, user agent, etc.)

    # Evidence integrity (tamper-evident hash chain)
    chain_id = Column(String(64), nullable=True, index=True)  # e.g. tenant_id/org_id/global
    prev_hash = Column(String(64), nullable=True)
    entry_hash = Column(String(64), nullable=True, index=True)
    canonical_payload = Column(Text, nullable=True)

    # Retention
    retention_until = Column(DateTime, nullable=True)
    
    # Relationships
    decision_id = Column(String(36), ForeignKey("decisions.id"), nullable=True)
    policy_id = Column(String(36), ForeignKey("policies.id"), nullable=True)
    rule_id = Column(String(36), ForeignKey("rules.id"), nullable=True)
    entitlement_id = Column(String(36), ForeignKey("entitlements.id"), nullable=True)
    
    decision = relationship("Decision")
    policy = relationship("Policy")
    rule = relationship("Rule")
    entitlement = relationship("Entitlement", back_populates="audit_logs")
    
    __table_args__ = (
        Index("ix_audit_entity", "entity_type", "entity_id"),
        Index("ix_audit_actor", "actor_id", "created_at"),
        Index("ix_audit_action", "action", "created_at"),
        Index("ix_audit_chain_created", "chain_id", "created_at"),
    )
    
    def __repr__(self):
        """String representation."""
        return f"<AuditLog(action={self.action}, entity={self.entity_type}, id={self.entity_id})>"


class AuditCheckpoint(BaseModel):
    """Persisted checkpoint for export/verification boundaries.

    This is deliberately separate from AuditLog so that creating a checkpoint
    does not mutate the audit log chain it is referencing.
    """

    __tablename__ = "audit_checkpoints"

    chain_id = Column(String(64), nullable=False, index=True)
    last_entry_hash = Column(String(64), nullable=True)

    canonical_payload = Column(Text, nullable=False)
    signed = Column(Boolean, nullable=False, default=False)
    key_id = Column(String(64), nullable=True)
    signature = Column(String(128), nullable=True)

    actor_id = Column(String(255), nullable=False, index=True)
    actor_type = Column(String(50), nullable=False, default="user")
    checkpoint_context = Column(JSON, nullable=True)

    __table_args__ = (
        Index("ix_audit_checkpoints_chain_created", "chain_id", "created_at"),
        Index("ix_audit_checkpoints_signature", "signature"),
    )


class AuditService:
    """Service for recording audit events."""

    @staticmethod
    def _canonical_json(payload: dict) -> str:
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)

    @staticmethod
    def _sha256_hex(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @staticmethod
    def _retention_until(now: datetime) -> datetime:
        days = int(os.getenv("HEXARCH_AUDIT_RETENTION_DAYS", "365"))
        if days < 1:
            days = 1
        return now + timedelta(days=days)

    @staticmethod
    def _chain_dimension() -> str:
        # tenant: chain per tenant_id
        # org: chain per org_id
        # global: single chain
        return (os.getenv("HEXARCH_AUDIT_CHAIN_DIMENSION", "tenant") or "tenant").strip().lower()

    @staticmethod
    def _chain_id_from_context(context: dict | None) -> str:
        dim = AuditService._chain_dimension()
        ctx = context if isinstance(context, dict) else {}

        tenant_id = ctx.get("tenant_id")
        org_id = ctx.get("org_id")

        if dim == "global":
            return "global"
        if dim == "org":
            return org_id or "global"
        # default tenant
        return tenant_id or org_id or "global"

    @staticmethod
    def _get_prev_hash(session, chain_id: str) -> str | None:
        prev = (
            session.query(AuditLog)
            .filter(AuditLog.chain_id == chain_id)
            .filter(AuditLog.entry_hash.isnot(None))
            .order_by(AuditLog.created_at.desc())
            .first()
        )
        return prev.entry_hash if prev else None

    @staticmethod
    def get_latest_hash(session, chain_id: str = "global") -> str | None:
        # Returns the latest entry_hash for a chain.
        return AuditService._get_prev_hash(session, chain_id)

    @staticmethod
    def _hmac_key() -> str | None:
        key = os.getenv("HEXARCH_AUDIT_HMAC_KEY")
        if not key:
            return None
        return key.strip()

    @staticmethod
    def sign_checkpoint(payload: dict) -> dict:
        """Return a signed checkpoint payload.

        Uses HMAC-SHA256 with `HEXARCH_AUDIT_HMAC_KEY`.
        If no key is configured, returns `{"signed": False}`.
        """

        canonical = AuditService._canonical_json(payload)
        key = AuditService._hmac_key()
        if not key:
            return {"signed": False, "canonical": canonical, "signature": None, "key_id": None}

        sig = hmac.new(key.encode("utf-8"), canonical.encode("utf-8"), hashlib.sha256).hexdigest()
        key_id = (os.getenv("HEXARCH_AUDIT_HMAC_KEY_ID") or "default").strip()
        return {"signed": True, "canonical": canonical, "signature": sig, "key_id": key_id}

    @staticmethod
    def create_persisted_checkpoint(
        session,
        *,
        chain_id: str,
        actor_id: str,
        actor_type: str = "user",
        checkpoint_context: dict | None = None,
    ) -> "AuditCheckpoint":
        now = datetime.utcnow()
        last_hash = AuditService.get_latest_hash(session, chain_id=chain_id)

        payload = {
            "v": 1,
            "chain_id": chain_id,
            "last_entry_hash": last_hash,
            "actor_id": actor_id,
            "actor_type": actor_type,
            "checkpoint_context": checkpoint_context,
            "at": now.isoformat() + "Z",
        }

        signed = AuditService.sign_checkpoint(payload)

        cp = AuditCheckpoint(
            chain_id=chain_id,
            last_entry_hash=last_hash,
            canonical_payload=signed["canonical"],
            signed=bool(signed["signed"]),
            key_id=signed.get("key_id"),
            signature=signed.get("signature"),
            actor_id=actor_id,
            actor_type=actor_type,
            checkpoint_context=checkpoint_context,
            created_at=now,
            updated_at=now,
        )
        session.add(cp)
        return cp
    
    @staticmethod
    def log_action(
        session,
        action: AuditAction,
        entity_type: str,
        entity_id: str,
        actor_id: str,
        changes: dict = None,
        reason: str = None,
        context: dict = None,
        actor_type: str = "user",
    ) -> AuditLog:
        """
        Record an audit action.
        
        Args:
            session: SQLAlchemy session
            action: Type of action
            entity_type: Type of entity changed
            entity_id: ID of entity changed
            actor_id: User/service who made the change
            changes: What changed (optional)
            reason: Why (optional)
            context: Additional context (optional)
            actor_type: Type of actor (user, service, automation)
            
        Returns:
            AuditLog instance
        """
        now = datetime.utcnow()
        chain_id = AuditService._chain_id_from_context(context)

        prev_hash = AuditService._get_prev_hash(session, chain_id)

        # Canonical payload is stored to make verification stable across JSON re-encoding.
        payload = {
            "v": 1,
            "chain_id": chain_id,
            "prev_hash": prev_hash,
            "action": action.value if isinstance(action, AuditAction) else action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "actor_id": actor_id,
            "actor_type": actor_type,
            "reason": reason,
            "changes": changes,
            "audit_context": context,
            "created_at": now.isoformat() + "Z",
        }

        canonical = AuditService._canonical_json(payload)
        entry_hash = AuditService._sha256_hex(canonical)

        log = AuditLog(
            action=action.value if isinstance(action, AuditAction) else action,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id=actor_id,
            actor_type=actor_type,
            changes=changes,
            reason=reason,
            audit_context=context,
            chain_id=chain_id,
            prev_hash=prev_hash,
            entry_hash=entry_hash,
            canonical_payload=canonical,
            retention_until=AuditService._retention_until(now),
            created_at=now,
            updated_at=now,
        )
        session.add(log)
        return log

    @staticmethod
    def verify_chain(session, chain_id: str = "global", limit: int | None = None) -> dict:
        q = (
            session.query(AuditLog)
            .filter(AuditLog.chain_id == chain_id)
            .filter(AuditLog.is_deleted == False)
            .order_by(AuditLog.created_at.asc(), AuditLog.id.asc())
        )
        if limit is not None:
            q = q.limit(limit)

        logs = q.all()
        verified = 0
        unverified = 0
        expected_prev = None
        first_failure_id = None

        for log in logs:
            if not log.canonical_payload or not log.entry_hash:
                unverified += 1
                expected_prev = log.entry_hash or expected_prev
                continue

            computed = AuditService._sha256_hex(log.canonical_payload)
            ok = computed == log.entry_hash
            ok = ok and (log.prev_hash == expected_prev)

            if not ok and first_failure_id is None:
                first_failure_id = log.id
                break

            verified += 1
            expected_prev = log.entry_hash

        return {
            "ok": first_failure_id is None,
            "chain_id": chain_id,
            "total": len(logs),
            "verified": verified,
            "unverified": unverified,
            "first_failure_id": first_failure_id,
        }
    
    @staticmethod
    def get_entity_history(session, entity_type: str, entity_id: str, limit: int = 50):
        """
        Get audit history for an entity.
        
        Args:
            session: SQLAlchemy session
            entity_type: Type of entity
            entity_id: ID of entity
            limit: Maximum results
            
        Returns:
            List of AuditLog instances ordered by created_at DESC
        """
        return (
            session.query(AuditLog)
            .filter(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == entity_id,
                AuditLog.is_deleted == False,
            )
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )
    
    @staticmethod
    def get_actor_history(session, actor_id: str, limit: int = 100):
        """
        Get all actions performed by an actor.
        
        Args:
            session: SQLAlchemy session
            actor_id: User/service ID
            limit: Maximum results
            
        Returns:
            List of AuditLog instances
        """
        return (
            session.query(AuditLog)
            .filter(
                AuditLog.actor_id == actor_id,
                AuditLog.is_deleted == False,
            )
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )
