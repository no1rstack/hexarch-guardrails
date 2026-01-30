from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str


class EchoRequest(BaseModel):
    message: str = Field(min_length=0, max_length=10_000)
    metadata: Optional[dict[str, Any]] = None


class EchoResponse(BaseModel):
    ok: bool = True
    message: str
    metadata: Optional[dict[str, Any]] = None


class RuleCreate(BaseModel):
    name: str
    rule_type: str
    condition: dict[str, Any]
    description: Optional[str] = None
    priority: int = 100
    enabled: bool = True
    operator: Optional[str] = None
    parent_rule_id: Optional[str] = None
    rule_metadata: Optional[dict[str, Any]] = None


class RuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None
    rule_type: str
    priority: int
    enabled: bool
    condition: dict[str, Any]
    operator: Optional[str] = None
    parent_rule_id: Optional[str] = None
    rule_metadata: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class PolicyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    scope: str = "GLOBAL"
    scope_value: Optional[str] = None
    enabled: bool = True
    failure_mode: str = "FAIL_CLOSED"
    config: Optional[str] = None
    rule_ids: list[str] = Field(default_factory=list)


class PolicyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None
    scope: str
    scope_value: Optional[str] = None
    enabled: bool
    failure_mode: str
    config: Optional[str] = None
    rule_ids: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class EntitlementCreate(BaseModel):
    subject_id: str
    subject_type: str = "user"
    entitlement_type: str
    name: str
    description: Optional[str] = None
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None
    status: str = "PENDING"
    valid_from: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    granted_by: Optional[str] = None
    reason: Optional[str] = None
    entitlement_metadata: Optional[dict[str, Any]] = None


class EntitlementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    subject_id: str
    subject_type: str
    entitlement_type: str
    name: str
    description: Optional[str] = None
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None
    status: str
    valid_from: datetime
    expires_at: Optional[datetime] = None
    granted_by: Optional[str] = None
    revoked_by: Optional[str] = None
    reason: Optional[str] = None
    entitlement_metadata: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class DecisionCreate(BaseModel):
    name: str
    entitlement_id: str
    creator_id: str
    description: Optional[str] = None
    state: str = "PENDING"
    policy_id: Optional[str] = None
    reviewer_id: Optional[str] = None
    priority: str = "MEDIUM"
    expires_at: Optional[datetime] = None
    context: Optional[str] = None
    decision_reason: Optional[str] = None


class DecisionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None
    state: str
    entitlement_id: str
    policy_id: Optional[str] = None
    creator_id: str
    reviewer_id: Optional[str] = None
    priority: str
    expires_at: Optional[datetime] = None
    context: Optional[str] = None
    decision_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    action: str
    entity_type: str
    entity_id: str
    actor_id: str
    actor_type: str
    changes: Optional[dict[str, Any]] = None
    reason: Optional[str] = None
    audit_context: Optional[dict[str, Any]] = None
    chain_id: Optional[str] = None
    prev_hash: Optional[str] = None
    entry_hash: Optional[str] = None
    retention_until: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class AuditVerifyResponse(BaseModel):
    ok: bool
    chain_id: str
    total: int
    verified: int
    unverified: int
    first_failure_id: Optional[str] = None


class AuditCheckpointResponse(BaseModel):
    chain_id: str
    last_entry_hash: Optional[str] = None
    at: datetime
    signed: bool
    key_id: Optional[str] = None
    signature: Optional[str] = None


class AuditCheckpointCreate(BaseModel):
    chain_id: str = "global"


class AuditCheckpointOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    chain_id: str
    last_entry_hash: Optional[str] = None
    signed: bool
    key_id: Optional[str] = None
    signature: Optional[str] = None
    actor_id: str
    actor_type: str
    checkpoint_context: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class ApiKeyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    tenant_id: Optional[str] = None
    org_id: Optional[str] = None
    scopes: Optional[list[str]] = None


class ApiKeyCreateResponse(BaseModel):
    # Token is returned once; store it securely.
    id: str
    name: str
    token: str
    token_prefix: str


class ApiKeyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None
    token_prefix: str
    tenant_id: Optional[str] = None
    org_id: Optional[str] = None
    scopes: Optional[list[str]] = None
    revoked_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class AuthorizeRequest(BaseModel):
    """Ask the server to evaluate policies and return ALLOW/DENY."""

    action: str = "request"
    resource: Optional[dict[str, Any]] = None
    context: Optional[dict[str, Any]] = None


class AuthorizeResponse(BaseModel):
    allowed: bool
    decision: str
    reason: Optional[str] = None
    policies: list[str] = Field(default_factory=list)


class ProviderCallCreate(BaseModel):
    """Metadata about an external provider call (LLM/API)."""

    resource: str
    action: str

    ok: bool = True
    status_code: Optional[int] = None
    latency_ms: Optional[int] = None

    model: Optional[str] = None
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    cost_usd: Optional[float] = None

    error_type: Optional[str] = None
    error_message: Optional[str] = None

    metadata: Optional[dict[str, Any]] = None


class ProviderCallOut(BaseModel):
    id: str
    resource: str
    action: str
    ok: bool
