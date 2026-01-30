"""
Base model class with common fields.
All models inherit from this to get timestamps, soft deletes, and versioning.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Integer, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class TimestampMixin:
    """Mixin providing created_at and updated_at timestamps."""
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class SoftDeleteMixin:
    """Mixin providing soft delete functionality."""
    
    deleted_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    def soft_delete(self):
        """Mark record as deleted without removing from database."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
    
    def restore(self):
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None


class VersioningMixin:
    """Mixin providing versioning/revision tracking."""
    
    version = Column(Integer, default=1, nullable=False)
    
    def increment_version(self):
        """Increment version number."""
        self.version += 1


class AuditableMixin:
    """Mixin providing audit tracking."""
    
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)
    deleted_by = Column(String(255), nullable=True)


class BaseModel(Base, TimestampMixin, SoftDeleteMixin, VersioningMixin, AuditableMixin):
    """
    Abstract base model combining all mixins.
    All data models should inherit from this.
    """
    __abstract__ = True
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def __repr__(self):
        """String representation."""
        return f"<{self.__class__.__name__}(id={self.id})>"
