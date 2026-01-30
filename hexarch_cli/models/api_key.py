from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column, DateTime, Index, JSON, String, Text

from hexarch_cli.models.base import BaseModel


def _sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class ApiKey(BaseModel):
    """Server-side API key (stored hashed; token value is never stored).

    This is designed for hardening beyond a single env token:
    - Revocable
    - Tenant/org scoping
    - Auditable

    Token format is opaque; we rely on `token_prefix` for indexed lookup.
    """

    __tablename__ = "api_keys"

    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    token_prefix = Column(String(16), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, index=True)

    tenant_id = Column(String(255), nullable=True, index=True)
    org_id = Column(String(255), nullable=True, index=True)

    scopes = Column(JSON, nullable=True)  # list[str]

    revoked_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ux_api_keys_prefix", "token_prefix", unique=True),
    )

    @property
    def is_revoked(self) -> bool:
        return self.revoked_at is not None

    def revoke(self) -> None:
        self.revoked_at = datetime.utcnow()

    @staticmethod
    def generate_token(prefix_len: int = 12) -> tuple[str, str]:
        # token is returned to caller once; store only derived data.
        raw = secrets.token_urlsafe(32)
        prefix = raw[:prefix_len]
        token = f"hxk_{raw}"
        return token, prefix

    @staticmethod
    def hash_token(token: str) -> str:
        return _sha256_hex(token)

    @staticmethod
    def token_prefix_from_token(token: str, prefix_len: int = 12) -> str:
        # token may have the hxk_ prefix.
        raw = token
        if raw.startswith("hxk_"):
            raw = raw[4:]
        return raw[:prefix_len]

    def matches_token(self, token: str) -> bool:
        # Constant-time compare.
        return hmac.compare_digest(self.token_hash, ApiKey.hash_token(token))
