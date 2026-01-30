"""Add persisted audit checkpoints.

Revision ID: 003_audit_checkpoints
Revises: 002_audit_hash_chain
Create Date: 2026-01-29 00:00:00

"""

from alembic import op
import sqlalchemy as sa


revision = "003_audit_checkpoints"
down_revision = "002_audit_hash_chain"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_checkpoints",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("chain_id", sa.String(64), nullable=False),
        sa.Column("last_entry_hash", sa.String(64), nullable=True),
        sa.Column("canonical_payload", sa.Text(), nullable=False),
        sa.Column("signed", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("key_id", sa.String(64), nullable=True),
        sa.Column("signature", sa.String(128), nullable=True),
        sa.Column("actor_id", sa.String(255), nullable=False),
        sa.Column("actor_type", sa.String(50), nullable=False),
        sa.Column("checkpoint_context", sa.JSON(), nullable=True),
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

    op.create_index("ix_audit_checkpoints_chain_created", "audit_checkpoints", ["chain_id", "created_at"])
    op.create_index("ix_audit_checkpoints_signature", "audit_checkpoints", ["signature"])


def downgrade() -> None:
    op.drop_index("ix_audit_checkpoints_signature", table_name="audit_checkpoints")
    op.drop_index("ix_audit_checkpoints_chain_created", table_name="audit_checkpoints")
    op.drop_table("audit_checkpoints")
