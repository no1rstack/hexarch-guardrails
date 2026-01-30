"""Initial schema: Decision, Policy, Rule, Entitlement, Audit models.

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-01-29 11:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial database schema."""
    
    # Rules table
    op.create_table(
        'rules',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('rule_type', sa.String(50), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('condition', sa.JSON(), nullable=False),
        sa.Column('parent_rule_id', sa.String(36), nullable=True),
        sa.Column('operator', sa.String(10), nullable=True),
        sa.Column('rule_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('updated_by', sa.String(255), nullable=True),
        sa.Column('deleted_by', sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['parent_rule_id'], ['rules.id'], ),
    )
    op.create_index('ix_rules_type_enabled', 'rules', ['rule_type', 'enabled'])
    op.create_index('ix_rules_priority_enabled', 'rules', ['priority', 'enabled'])
    op.create_index('ix_rules_name', 'rules', ['name'])
    
    # Policies table
    op.create_table(
        'policies',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('scope', sa.String(50), nullable=False),
        sa.Column('scope_value', sa.String(255), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('failure_mode', sa.String(50), nullable=False),
        sa.Column('config', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('updated_by', sa.String(255), nullable=True),
        sa.Column('deleted_by', sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_policies_name', 'policies', ['name'])
    op.create_index('ix_policies_scope_enabled', 'policies', ['scope', 'enabled'])
    
    # Policy-Rule many-to-many table
    op.create_table(
        'policy_rules',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('policy_id', sa.String(36), nullable=False),
        sa.Column('rule_id', sa.String(36), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('updated_by', sa.String(255), nullable=True),
        sa.Column('deleted_by', sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], ),
        sa.ForeignKeyConstraint(['rule_id'], ['rules.id'], ),
    )
    op.create_index('ix_policy_rules_order', 'policy_rules', ['policy_id', 'order'])
    
    # Entitlements table
    op.create_table(
        'entitlements',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('subject_id', sa.String(255), nullable=False),
        sa.Column('subject_type', sa.String(50), nullable=False),
        sa.Column('entitlement_type', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('resource_id', sa.String(255), nullable=True),
        sa.Column('resource_type', sa.String(50), nullable=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('valid_from', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('granted_by', sa.String(255), nullable=True),
        sa.Column('revoked_by', sa.String(255), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('entitlement_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('updated_by', sa.String(255), nullable=True),
        sa.Column('deleted_by', sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_entitlements_subject', 'entitlements', ['subject_id', 'subject_type'])
    op.create_index('ix_entitlements_status_expires', 'entitlements', ['status', 'expires_at'])
    op.create_index('ix_entitlements_type', 'entitlements', ['entitlement_type', 'status'])
    
    # Decisions table
    op.create_table(
        'decisions',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('state', sa.String(50), nullable=False),
        sa.Column('entitlement_id', sa.String(36), nullable=False),
        sa.Column('policy_id', sa.String(36), nullable=True),
        sa.Column('creator_id', sa.String(255), nullable=False),
        sa.Column('reviewer_id', sa.String(255), nullable=True),
        sa.Column('priority', sa.String(50), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('decision_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('updated_by', sa.String(255), nullable=True),
        sa.Column('deleted_by', sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['entitlement_id'], ['entitlements.id'], ),
        sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], ),
    )
    op.create_index('ix_decisions_name', 'decisions', ['name'])
    op.create_index('ix_decisions_state', 'decisions', ['state'])
    op.create_index('ix_decisions_state_expires', 'decisions', ['state', 'expires_at'])
    op.create_index('ix_decisions_entitlement_state', 'decisions', ['entitlement_id', 'state'])
    
    # Audit logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.String(36), nullable=False),
        sa.Column('actor_id', sa.String(255), nullable=False),
        sa.Column('actor_type', sa.String(50), nullable=False),
        sa.Column('changes', sa.JSON(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('audit_context', sa.JSON(), nullable=True),
        sa.Column('decision_id', sa.String(36), nullable=True),
        sa.Column('policy_id', sa.String(36), nullable=True),
        sa.Column('rule_id', sa.String(36), nullable=True),
        sa.Column('entitlement_id', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('updated_by', sa.String(255), nullable=True),
        sa.Column('deleted_by', sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['decision_id'], ['decisions.id'], ),
        sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], ),
        sa.ForeignKeyConstraint(['rule_id'], ['rules.id'], ),
        sa.ForeignKeyConstraint(['entitlement_id'], ['entitlements.id'], ),
    )
    op.create_index('ix_audit_entity', 'audit_logs', ['entity_type', 'entity_id'])
    op.create_index('ix_audit_actor', 'audit_logs', ['actor_id', 'created_at'])
    op.create_index('ix_audit_action', 'audit_logs', ['action', 'created_at'])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('audit_logs')
    op.drop_table('decisions')
    op.drop_table('entitlements')
    op.drop_table('policy_rules')
    op.drop_table('policies')
    op.drop_table('rules')
