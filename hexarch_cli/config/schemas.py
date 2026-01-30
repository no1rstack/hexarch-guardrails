"""Configuration schemas for hexarch-ctl."""

from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


class APIConfig(BaseModel):
    """API connection configuration."""
    
    model_config = ConfigDict(env_prefix="HEXARCH_API_")
    
    url: str = Field(
        default="http://localhost:8080",
        description="Backend API URL"
    )
    token: Optional[str] = Field(
        default=None,
        description="Bearer token for authentication (use env var for security)"
    )
    timeout_seconds: int = Field(
        default=30,
        description="Request timeout in seconds",
        ge=1,
        le=300
    )
    verify_ssl: bool = Field(
        default=True,
        description="Verify SSL certificates"
    )


class OutputConfig(BaseModel):
    """Output formatting configuration."""
    
    model_config = ConfigDict(env_prefix="HEXARCH_OUTPUT_")
    
    format: str = Field(
        default="table",
        description="Output format: json, table, or csv",
        pattern="^(json|table|csv)$"
    )
    colors: bool = Field(
        default=True,
        description="Enable colored output"
    )
    page_size: int = Field(
        default=100,
        description="Records per page",
        ge=10,
        le=1000
    )


class AuditConfig(BaseModel):
    """Audit logging configuration."""
    
    model_config = ConfigDict(env_prefix="HEXARCH_AUDIT_")
    
    enabled: bool = Field(
        default=True,
        description="Enable audit logging"
    )
    log_path: str = Field(
        default="~/.hexarch/cli.log",
        description="Audit log file path"
    )
    log_level: str = Field(
        default="info",
        description="Log level: debug, info, warn, error",
        pattern="^(debug|info|warn|error)$"
    )
    max_size_mb: int = Field(
        default=100,
        description="Max log file size before rotation",
        ge=10
    )
    backup_count: int = Field(
        default=10,
        description="Number of backup log files to keep",
        ge=1
    )


class PolicyConfig(BaseModel):
    """Policy cache configuration."""
    
    model_config = ConfigDict(env_prefix="HEXARCH_POLICY_")
    
    cache_ttl_minutes: int = Field(
        default=5,
        description="Policy cache TTL in minutes",
        ge=1,
        le=1440
    )
    validation_strict: bool = Field(
        default=False,
        description="Strict policy validation mode"
    )


class DatabaseConfig(BaseModel):
    """Database configuration for local CLI storage."""

    model_config = ConfigDict(env_prefix="HEXARCH_DB_")

    url: Optional[str] = Field(
        default=None,
        description="Database URL (overrides provider/path if set)"
    )
    provider: str = Field(
        default="sqlite",
        description="Database provider: sqlite or postgresql",
        pattern="^(sqlite|postgresql)$"
    )
    path: str = Field(
        default="./hexarch.db",
        description="SQLite database file path"
    )
    echo_sql: bool = Field(
        default=False,
        description="Enable SQL echo for debugging"
    )
    pool_size: int = Field(
        default=10,
        description="PostgreSQL connection pool size",
        ge=1,
        le=100
    )
    max_overflow: int = Field(
        default=20,
        description="PostgreSQL max overflow connections",
        ge=0,
        le=200
    )


class HexarchConfig(BaseModel):
    """Root configuration for hexarch-ctl."""
    
    model_config = ConfigDict(validate_assignment=True)
    
    version: str = Field(
        default="0.3",
        description="Configuration format version"
    )
    api: APIConfig = Field(
        default_factory=APIConfig,
        description="API configuration"
    )
    output: OutputConfig = Field(
        default_factory=OutputConfig,
        description="Output formatting configuration"
    )
    audit: AuditConfig = Field(
        default_factory=AuditConfig,
        description="Audit logging configuration"
    )
    policies: PolicyConfig = Field(
        default_factory=PolicyConfig,
        description="Policy cache configuration"
    )
    db: DatabaseConfig = Field(
        default_factory=DatabaseConfig,
        description="Local database configuration"
    )
    
    @field_validator("version")
    @classmethod
    def validate_version(cls, v):
        """Validate configuration version."""
        if v not in ["0.3", "0.4", "1.0"]:
            raise ValueError(f"Unsupported config version: {v}")
        return v


__all__ = [
    "APIConfig",
    "OutputConfig",
    "AuditConfig",
    "PolicyConfig",
    "DatabaseConfig",
    "HexarchConfig"
]
