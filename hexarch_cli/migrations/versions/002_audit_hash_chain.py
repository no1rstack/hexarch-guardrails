"""Add tamper-evident hash chain fields to audit logs.

Revision ID: 002_audit_hash_chain
Revises: 001_initial_schema
Create Date: 2026-01-29 00:00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "002_audit_hash_chain"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # SQLite requires batch operations for some ALTER TABLE scenarios.
    with op.batch_alter_table("audit_logs") as batch:
        batch.add_column(sa.Column("chain_id", sa.String(64), nullable=True))
        batch.add_column(sa.Column("prev_hash", sa.String(64), nullable=True))
        batch.add_column(sa.Column("entry_hash", sa.String(64), nullable=True))
        batch.add_column(sa.Column("canonical_payload", sa.Text(), nullable=True))
        batch.add_column(sa.Column("retention_until", sa.DateTime(), nullable=True))

    op.create_index("ix_audit_chain_created", "audit_logs", ["chain_id", "created_at"])
    op.create_index("ix_audit_entry_hash", "audit_logs", ["entry_hash"])


def downgrade() -> None:
    op.drop_index("ix_audit_entry_hash", table_name="audit_logs")
    op.drop_index("ix_audit_chain_created", table_name="audit_logs")

    with op.batch_alter_table("audit_logs") as batch:
        batch.drop_column("retention_until")
        batch.drop_column("canonical_payload")
        batch.drop_column("entry_hash")
        batch.drop_column("prev_hash")
        batch.drop_column("chain_id")
