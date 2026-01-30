"""Add DB-backed API keys.

Revision ID: 004_api_keys
Revises: 003_audit_checkpoints
Create Date: 2026-01-29 00:00:00

"""

from alembic import op
import sqlalchemy as sa


revision = "004_api_keys"
down_revision = "003_audit_checkpoints"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "api_keys",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("token_prefix", sa.String(16), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("tenant_id", sa.String(255), nullable=True),
        sa.Column("org_id", sa.String(255), nullable=True),
        sa.Column("scopes", sa.JSON(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("updated_by", sa.String(255), nullable=True),
        sa.Column("deleted_by", sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ux_api_keys_prefix", "api_keys", ["token_prefix"], unique=True)
    op.create_index("ix_api_keys_hash", "api_keys", ["token_hash"])
    op.create_index("ix_api_keys_tenant", "api_keys", ["tenant_id"])
    op.create_index("ix_api_keys_org", "api_keys", ["org_id"])


def downgrade() -> None:
    op.drop_index("ix_api_keys_org", table_name="api_keys")
    op.drop_index("ix_api_keys_tenant", table_name="api_keys")
    op.drop_index("ix_api_keys_hash", table_name="api_keys")
    op.drop_index("ux_api_keys_prefix", table_name="api_keys")
    op.drop_table("api_keys")
