"""Tests for database models."""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from hexarch_cli.models import (
    Base, Decision, DecisionState, Policy, PolicyScope, FailureMode,
    Rule, RuleType, Entitlement, EntitlementStatus, EntitlementType,
    AuditLog, AuditAction, AuditService
)


@pytest.fixture(scope="function")
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine, checkfirst=False)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    engine.dispose()


class TestRule:
    """Test Rule model."""

    def test_create_rule(self, db_session: Session):
        """Test creating a rule."""
        rule = Rule(
            name="test_rule",
            rule_type=RuleType.CONDITION.value,
            priority=10,
            enabled=True,
            condition={"operator": "equals", "field": "user.role", "value": "admin"}
        )
        db_session.add(rule)
        db_session.commit()

        assert rule.id is not None
        assert rule.name == "test_rule"
        assert rule.rule_type == RuleType.CONDITION.value
        assert rule.priority == 10
        assert rule.enabled is True
        assert rule.created_at is not None

    def test_soft_delete_rule(self, db_session: Session):
        """Test soft deleting a rule."""
        rule = Rule(
            name="test_rule",
            rule_type=RuleType.CONDITION.value,
            condition={"operator": "equals", "field": "user.role", "value": "admin"}
        )
        db_session.add(rule)
        db_session.commit()

        rule.soft_delete()
        db_session.commit()

        assert rule.is_deleted is True
        assert rule.deleted_at is not None

    def test_rule_versioning(self, db_session: Session):
        """Test rule version increment."""
        rule = Rule(
            name="test_rule",
            rule_type=RuleType.CONDITION.value,
            condition={"operator": "equals", "field": "user.role", "value": "admin"}
        )
        db_session.add(rule)
        db_session.commit()

        original_version = rule.version
        rule.increment_version()
        db_session.commit()

        assert rule.version == original_version + 1


class TestPolicy:
    """Test Policy model."""

    def test_create_policy(self, db_session: Session):
        """Test creating a policy."""
        policy = Policy(
            name="test_policy",
            scope=PolicyScope.GLOBAL.value,
            enabled=True,
            failure_mode=FailureMode.FAIL_CLOSED.value
        )
        db_session.add(policy)
        db_session.commit()

        assert policy.id is not None
        assert policy.name == "test_policy"
        assert policy.scope == PolicyScope.GLOBAL.value
        assert policy.enabled is True
        assert policy.failure_mode == FailureMode.FAIL_CLOSED.value

    def test_policy_with_rules(self, db_session: Session):
        """Test policy with associated rules."""
        policy = Policy(
            name="test_policy",
            scope=PolicyScope.GLOBAL.value,
            enabled=True
        )
        rule1 = Rule(
            name="rule1",
            rule_type=RuleType.CONDITION.value,
            priority=10,
            condition={"operator": "equals", "field": "user.role", "value": "admin"}
        )
        rule2 = Rule(
            name="rule2",
            rule_type=RuleType.PERMISSION.value,
            priority=20,
            condition={"operator": "equals", "field": "resource.type", "value": "document"}
        )

        db_session.add_all([policy, rule1, rule2])
        db_session.commit()

        policy.rules.append(rule1)
        policy.rules.append(rule2)
        db_session.commit()

        assert len(policy.rules) == 2
        assert rule1 in policy.rules
        assert rule2 in policy.rules


class TestEntitlement:
    """Test Entitlement model."""

    def test_create_entitlement(self, db_session: Session):
        """Test creating an entitlement."""
        entitlement = Entitlement(
            subject_id="user-123",
            subject_type="USER",
            name="admin_role",
            entitlement_type=EntitlementType.ROLE.value,
            status=EntitlementStatus.ACTIVE.value
        )
        db_session.add(entitlement)
        db_session.commit()

        assert entitlement.id is not None
        assert entitlement.subject_id == "user-123"
        assert entitlement.status == EntitlementStatus.ACTIVE.value

    def test_is_active(self, db_session: Session):
        """Test entitlement is_active check."""
        entitlement = Entitlement(
            subject_id="user-123",
            name="test",
            entitlement_type=EntitlementType.ROLE.value,
            status=EntitlementStatus.ACTIVE.value,
            valid_from=datetime.utcnow() - timedelta(days=1)
        )
        db_session.add(entitlement)
        db_session.commit()

        assert entitlement.is_active() is True

    def test_is_expired(self, db_session: Session):
        """Test entitlement expiration check."""
        entitlement = Entitlement(
            subject_id="user-123",
            name="test",
            entitlement_type=EntitlementType.ROLE.value,
            status=EntitlementStatus.ACTIVE.value,
            expires_at=datetime.utcnow() - timedelta(days=1)
        )
        db_session.add(entitlement)
        db_session.commit()

        assert entitlement.is_expired() is True

    def test_revoke_entitlement(self, db_session: Session):
        """Test revoking an entitlement."""
        entitlement = Entitlement(
            subject_id="user-123",
            name="test",
            entitlement_type=EntitlementType.ROLE.value,
            status=EntitlementStatus.ACTIVE.value
        )
        db_session.add(entitlement)
        db_session.commit()

        entitlement.revoke(revoked_by="admin-123")
        db_session.commit()

        assert entitlement.status == EntitlementStatus.REVOKED.value
        assert entitlement.revoked_by == "admin-123"


class TestDecision:
    """Test Decision model."""

    def test_create_decision(self, db_session: Session):
        """Test creating a decision."""
        entitlement = Entitlement(
            subject_id="user-123",
            name="test",
            entitlement_type=EntitlementType.ROLE.value,
            status=EntitlementStatus.ACTIVE.value
        )
        policy = Policy(
            name="test_policy",
            scope=PolicyScope.GLOBAL.value,
            enabled=True
        )
        db_session.add_all([entitlement, policy])
        db_session.commit()

        decision = Decision(
            name="test_decision",
            entitlement_id=entitlement.id,
            policy_id=policy.id,
            state=DecisionState.PENDING.value,
            priority=10,
            creator_id="user-456"
        )
        db_session.add(decision)
        db_session.commit()

        assert decision.id is not None
        assert decision.state == DecisionState.PENDING.value
        assert decision.entitlement_id == entitlement.id
        assert decision.policy_id == policy.id

    def test_decision_approve(self, db_session: Session):
        """Test approving a decision."""
        entitlement = Entitlement(
            subject_id="user-123",
            name="test",
            entitlement_type=EntitlementType.ROLE.value,
            status=EntitlementStatus.ACTIVE.value
        )
        policy = Policy(
            name="test_policy",
            scope=PolicyScope.GLOBAL.value,
            enabled=True
        )
        db_session.add_all([entitlement, policy])
        db_session.commit()

        decision = Decision(
            name="test_decision",
            entitlement_id=entitlement.id,
            policy_id=policy.id,
            state=DecisionState.PENDING.value,
            creator_id="user-456"
        )
        db_session.add(decision)
        db_session.commit()

        decision.approve(reviewer_id="reviewer-123")
        db_session.commit()

        assert decision.state == DecisionState.APPROVED.value

    def test_decision_activate(self, db_session: Session):
        """Test activating a decision."""
        entitlement = Entitlement(
            subject_id="user-123",
            name="test",
            entitlement_type=EntitlementType.ROLE.value,
            status=EntitlementStatus.ACTIVE.value
        )
        policy = Policy(
            name="test_policy",
            scope=PolicyScope.GLOBAL.value,
            enabled=True
        )
        db_session.add_all([entitlement, policy])
        db_session.commit()

        decision = Decision(
            name="test_decision",
            entitlement_id=entitlement.id,
            policy_id=policy.id,
            state=DecisionState.APPROVED.value,
            creator_id="user-456"
        )
        db_session.add(decision)
        db_session.commit()

        decision.activate()
        db_session.commit()

        assert decision.state == DecisionState.ACTIVE.value


class TestAuditLog:
    """Test AuditLog model."""

    def test_create_audit_log(self, db_session: Session):
        """Test creating an audit log entry."""
        audit = AuditLog(
            action=AuditAction.CREATE.value,
            entity_type="Rule",
            entity_id="test-id",
            actor_id="user-123",
            changes={"field": "name", "old": None, "new": "test_rule"}
        )
        db_session.add(audit)
        db_session.commit()

        assert audit.id is not None
        assert audit.action == AuditAction.CREATE.value
        assert audit.entity_type == "Rule"
        assert audit.actor_id == "user-123"

    def test_audit_service_log_action(self, db_session: Session):
        """Test AuditService log_action."""
        audit = AuditService.log_action(
            session=db_session,
            action=AuditAction.UPDATE,
            entity_type="Policy",
            entity_id="policy-123",
            actor_id="user-456",
            changes={"enabled": {"old": False, "new": True}}
        )

        assert audit is not None
        assert audit.action == AuditAction.UPDATE.value
        assert audit.entity_id == "policy-123"
