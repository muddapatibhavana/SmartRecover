import json
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text
)
from sqlalchemy.orm import relationship
from app.database import Base

def utcnow():
    return datetime.now(timezone.utc)

class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    phone = Column(String(32), nullable=True)
    is_active = Column(Boolean, default=True)
    has_dispute = Column(Boolean, default=False)
    is_opted_out = Column(Boolean, default=False)
    historical_success_count = Column(Integer, default=0)
    historical_failure_count = Column(Integer, default=0)
    last_active_at = Column(DateTime, default=utcnow)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    subscriptions = relationship("Subscription", back_populates="customer", cascade="all, delete-orphan")
    recovery_cases = relationship("RecoveryCase", back_populates="customer")
    customer_events = relationship("CustomerEvent", back_populates="customer")
    human_reviews = relationship("HumanReview", back_populates="customer")

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String(64), primary_key=True, index=True)
    customer_id = Column(String(64), ForeignKey("customers.id"), nullable=False, index=True)
    plan_name = Column(String(128), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(8), default="INR")
    interval = Column(String(32), default="MONTHLY")
    status = Column(String(32), default="ACTIVE")
    created_at = Column(DateTime, default=utcnow)

    customer = relationship("Customer", back_populates="subscriptions")
    mandates = relationship("Mandate", back_populates="subscription", cascade="all, delete-orphan")
    recovery_cases = relationship("RecoveryCase", back_populates="subscription")

class Mandate(Base):
    __tablename__ = "mandates"

    id = Column(String(64), primary_key=True, index=True)
    subscription_id = Column(String(64), ForeignKey("subscriptions.id"), nullable=False, index=True)
    mandate_type = Column(String(32), default="ENACH")  # ENACH, UPI_AUTOPAY, CARD_RECURRING
    bank_name = Column(String(128), default="HDFC Bank")
    status = Column(String(32), default="ACTIVE")  # ACTIVE, FAILED, SUSPENDED, REVOKED
    max_amount = Column(Float, nullable=False)
    created_at = Column(DateTime, default=utcnow)

    subscription = relationship("Subscription", back_populates="mandates")
    payment_attempts = relationship("PaymentAttempt", back_populates="mandate")
    recovery_cases = relationship("RecoveryCase", back_populates="mandate")

class RecoveryCase(Base):
    __tablename__ = "recovery_cases"

    id = Column(String(64), primary_key=True, index=True)
    customer_id = Column(String(64), ForeignKey("customers.id"), nullable=False, index=True)
    subscription_id = Column(String(64), ForeignKey("subscriptions.id"), nullable=False, index=True)
    mandate_id = Column(String(64), ForeignKey("mandates.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(8), default="INR")
    failure_reason = Column(String(255), nullable=False)
    failure_code = Column(String(64), nullable=False)
    attempt_count = Column(Integer, default=0)
    recovery_score = Column(Float, nullable=True)
    recovery_probability = Column(Float, nullable=True)
    ai_recommendation = Column(String(32), nullable=True)  # RETRY, NOTIFY, HUMAN_REVIEW, STOP
    ai_recommended_delay_hours = Column(Integer, default=24)
    ai_explanation = Column(Text, nullable=True)
    ai_decision_factors_json = Column(Text, default="[]")
    guardrail_status = Column(String(32), default="PENDING")  # PENDING, ALLOWED, BLOCKED
    guardrail_block_reason = Column(Text, nullable=True)
    guardrail_rules_checked_json = Column(Text, default="[]")
    current_status = Column(String(32), default="FAILED", index=True)
    stop_reason = Column(String(64), nullable=True, index=True)
    next_action = Column(String(64), nullable=True)
    next_action_scheduled_at = Column(DateTime, nullable=True)
    initial_failure_at = Column(DateTime, default=utcnow)
    created_at = Column(DateTime, default=utcnow, index=True)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    customer = relationship("Customer", back_populates="recovery_cases")
    subscription = relationship("Subscription", back_populates="recovery_cases")
    mandate = relationship("Mandate", back_populates="recovery_cases")
    payment_attempts = relationship("PaymentAttempt", back_populates="recovery_case")
    recovery_actions = relationship("RecoveryAction", back_populates="recovery_case")
    guardrail_events = relationship("GuardrailEvent", back_populates="recovery_case")
    audit_logs = relationship("AuditLog", back_populates="recovery_case", order_by="AuditLog.timestamp")
    human_reviews = relationship("HumanReview", back_populates="recovery_case")

    @property
    def ai_decision_factors(self):
        try:
            return json.loads(self.ai_decision_factors_json or "[]")
        except Exception:
            return []

    @ai_decision_factors.setter
    def ai_decision_factors(self, val):
        self.ai_decision_factors_json = json.dumps(val)

    @property
    def guardrail_rules_checked(self):
        try:
            return json.loads(self.guardrail_rules_checked_json or "[]")
        except Exception:
            return []

    @guardrail_rules_checked.setter
    def guardrail_rules_checked(self, val):
        self.guardrail_rules_checked_json = json.dumps(val)

class PaymentAttempt(Base):
    __tablename__ = "payment_attempts"

    id = Column(String(64), primary_key=True, index=True)
    recovery_case_id = Column(String(64), ForeignKey("recovery_cases.id"), nullable=True, index=True)
    mandate_id = Column(String(64), ForeignKey("mandates.id"), nullable=False, index=True)
    attempt_number = Column(Integer, default=1)
    amount = Column(Float, nullable=False)
    status = Column(String(32), default="PENDING")  # SUCCESS, FAILED, PENDING
    failure_code = Column(String(64), nullable=True)
    failure_reason = Column(String(255), nullable=True)
    is_temporary = Column(Boolean, default=True)
    idempotency_key = Column(String(128), unique=True, index=True)
    created_at = Column(DateTime, default=utcnow, index=True)

    recovery_case = relationship("RecoveryCase", back_populates="payment_attempts")
    mandate = relationship("Mandate", back_populates="payment_attempts")

class RecoveryAction(Base):
    __tablename__ = "recovery_actions"

    id = Column(String(64), primary_key=True, index=True)
    recovery_case_id = Column(String(64), ForeignKey("recovery_cases.id"), nullable=False, index=True)
    action_type = Column(String(32), nullable=False)  # RETRY_PAYMENT, SEND_NOTIFICATION, ROUTE_HUMAN_REVIEW, SAFE_STOP
    status = Column(String(32), default="PENDING")  # PENDING, EXECUTED, BLOCKED, FAILED
    idempotency_key = Column(String(128), unique=True, index=True)
    guardrail_evaluated = Column(Boolean, default=False)
    guardrail_allowed = Column(Boolean, default=False)
    execution_result_json = Column(Text, default="{}")
    executed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    recovery_case = relationship("RecoveryCase", back_populates="recovery_actions")

    @property
    def execution_result(self):
        try:
            return json.loads(self.execution_result_json or "{}")
        except Exception:
            return {}

    @execution_result.setter
    def execution_result(self, val):
        self.execution_result_json = json.dumps(val)

class GuardrailEvent(Base):
    __tablename__ = "guardrail_events"

    id = Column(String(64), primary_key=True, index=True)
    recovery_case_id = Column(String(64), ForeignKey("recovery_cases.id"), nullable=False, index=True)
    action_type = Column(String(32), nullable=False)
    allowed = Column(Boolean, nullable=False)
    status = Column(String(32), nullable=False)  # ALLOWED, BLOCKED
    blocked_reason = Column(Text, nullable=True)
    stop_reason = Column(String(64), nullable=True)
    rules_checked_json = Column(Text, default="[]")
    evaluated_at = Column(DateTime, default=utcnow, index=True)

    recovery_case = relationship("RecoveryCase", back_populates="guardrail_events")

    @property
    def rules_checked(self):
        try:
            return json.loads(self.rules_checked_json or "[]")
        except Exception:
            return []

    @rules_checked.setter
    def rules_checked(self, val):
        self.rules_checked_json = json.dumps(val)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(64), primary_key=True, index=True)
    recovery_case_id = Column(String(64), ForeignKey("recovery_cases.id"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    description = Column(Text, nullable=False)
    actor = Column(String(64), nullable=False)  # SYSTEM, RECOVERY_INTELLIGENCE, GUARDRAIL_ENGINE, PAYMENT_SIMULATOR, HUMAN_OPERATOR
    state_before = Column(String(32), nullable=True)
    state_after = Column(String(32), nullable=True)
    metadata_json = Column(Text, default="{}")
    timestamp = Column(DateTime, default=utcnow, index=True)

    recovery_case = relationship("RecoveryCase", back_populates="audit_logs")

    @property
    def log_metadata(self):
        try:
            return json.loads(self.metadata_json or "{}")
        except Exception:
            return {}

    @log_metadata.setter
    def log_metadata(self, val):
        self.metadata_json = json.dumps(val)

class CustomerEvent(Base):
    __tablename__ = "customer_events"

    id = Column(String(64), primary_key=True, index=True)
    customer_id = Column(String(64), ForeignKey("customers.id"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow, index=True)

    customer = relationship("Customer", back_populates="customer_events")

class HumanReview(Base):
    __tablename__ = "human_reviews"

    id = Column(String(64), primary_key=True, index=True)
    recovery_case_id = Column(String(64), ForeignKey("recovery_cases.id"), nullable=False, index=True)
    customer_id = Column(String(64), ForeignKey("customers.id"), nullable=False, index=True)
    trigger_reason = Column(String(255), nullable=False)
    status = Column(String(32), default="PENDING", index=True)  # PENDING, REVIEWED, RESOLVED, ESCALATED
    operator_notes = Column(Text, nullable=True)
    resolution_action = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=utcnow, index=True)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    recovery_case = relationship("RecoveryCase", back_populates="human_reviews")
    customer = relationship("Customer", back_populates="human_reviews")
