from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

# Base Enums/Constants
class StateConstants:
    FAILED = "FAILED"
    ANALYZING = "ANALYZING"
    AI_RECOMMENDED = "AI_RECOMMENDED"
    GUARDRAIL_CHECK = "GUARDRAIL_CHECK"
    ACTION_ALLOWED = "ACTION_ALLOWED"
    ACTION_BLOCKED = "ACTION_BLOCKED"
    RETRY_SCHEDULED = "RETRY_SCHEDULED"
    RETRYING = "RETRYING"
    NOTIFICATION_SENT = "NOTIFICATION_SENT"
    RECOVERED = "RECOVERED"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    STOPPED = "STOPPED"

class StopReasonConstants:
    PAYMENT_RECOVERED = "PAYMENT_RECOVERED"
    MAX_ATTEMPTS_REACHED = "MAX_ATTEMPTS_REACHED"
    RECOVERY_WINDOW_EXPIRED = "RECOVERY_WINDOW_EXPIRED"
    CUSTOMER_OPTED_OUT = "CUSTOMER_OPTED_OUT"
    CUSTOMER_DISPUTED = "CUSTOMER_DISPUTED"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
    RECOVERY_FAILED = "RECOVERY_FAILED"

# Customer Schemas
class CustomerBase(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    is_active: bool = True
    has_dispute: bool = False
    is_opted_out: bool = False
    historical_success_count: int = 0
    historical_failure_count: int = 0
    last_active_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# Subscription & Mandate Schemas
class SubscriptionBase(BaseModel):
    id: str
    customer_id: str
    plan_name: str
    amount: float
    currency: str = "INR"
    interval: str = "MONTHLY"
    status: str = "ACTIVE"

    model_config = ConfigDict(from_attributes=True)

class MandateBase(BaseModel):
    id: str
    subscription_id: str
    mandate_type: str
    bank_name: str
    status: str
    max_amount: float

    model_config = ConfigDict(from_attributes=True)

# Payment Attempt Schema
class PaymentAttemptBase(BaseModel):
    id: str
    attempt_number: int
    amount: float
    status: str
    failure_code: Optional[str] = None
    failure_reason: Optional[str] = None
    is_temporary: bool = True
    idempotency_key: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# AI Decision Schemas
class AIDecisionResponse(BaseModel):
    score: float = Field(..., ge=0, le=100, description="Explainable recovery score 0-100")
    probability: float = Field(..., ge=0.0, le=1.0, description="Estimated probability 0.0-1.0")
    recommended_action: str = Field(..., description="RETRY, NOTIFY, HUMAN_REVIEW, STOP")
    recommended_delay_hours: int = 24
    explanation: str
    factors: List[str]

# Guardrail Decision Schemas
class RuleCheckDetail(BaseModel):
    rule_name: str
    passed: bool
    description: str
    details: Optional[str] = None

class GuardrailDecisionResponse(BaseModel):
    allowed: bool
    status: str = Field(..., description="ALLOWED or BLOCKED")
    blocked_reason: Optional[str] = None
    stop_reason: Optional[str] = None
    rules_checked: List[RuleCheckDetail]

# Combined Decision Schema
class DualDecisionView(BaseModel):
    ai_decision: AIDecisionResponse
    guardrail_decision: GuardrailDecisionResponse
    final_status: str  # e.g. "RETRY ALLOWED", "ACTION BLOCKED"
    final_allowed: bool
    summary: str

# Recovery Case Summary Schema
class RecoveryCaseSummary(BaseModel):
    id: str
    customer_id: str
    customer_name: str
    customer_email: str
    subscription_plan: str
    amount: float
    currency: str = "INR"
    failure_reason: str
    failure_code: str
    attempt_count: int
    recovery_score: Optional[float] = None
    recovery_probability: Optional[float] = None
    ai_recommendation: Optional[str] = None
    guardrail_status: str
    current_status: str
    stop_reason: Optional[str] = None
    next_action: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# Recovery Case Detail Schema
class RecoveryCaseDetail(BaseModel):
    id: str
    customer: CustomerBase
    subscription: SubscriptionBase
    mandate: MandateBase
    amount: float
    currency: str = "INR"
    failure_reason: str
    failure_code: str
    attempt_count: int
    recovery_score: Optional[float] = None
    recovery_probability: Optional[float] = None
    ai_recommendation: Optional[str] = None
    ai_recommended_delay_hours: int = 24
    ai_explanation: Optional[str] = None
    ai_decision_factors: List[str] = []
    guardrail_status: str
    guardrail_block_reason: Optional[str] = None
    guardrail_rules_checked: List[str] = []
    current_status: str
    stop_reason: Optional[str] = None
    next_action: Optional[str] = None
    next_action_scheduled_at: Optional[datetime] = None
    initial_failure_at: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None
    payment_attempts: List[PaymentAttemptBase] = []

    model_config = ConfigDict(from_attributes=True)

# Action Execution Request / Response
class ExecuteActionRequest(BaseModel):
    action_type: str = "RETRY_PAYMENT"  # RETRY_PAYMENT, SEND_NOTIFICATION, ROUTE_HUMAN_REVIEW
    idempotency_key: Optional[str] = None
    force_simulation_outcome: Optional[str] = None  # None (auto), SUCCESS, FAILED

class ExecuteActionResponse(BaseModel):
    success: bool
    action_id: str
    action_type: str
    status: str
    execution_result: Dict[str, Any]
    current_case_status: str
    stop_reason: Optional[str] = None
    message: str

# Audit Log Schema
class AuditLogEntry(BaseModel):
    id: str
    recovery_case_id: str
    event_type: str
    description: str
    actor: str
    state_before: Optional[str] = None
    state_after: Optional[str] = None
    metadata: Dict[str, Any] = {}
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

# Human Review Schemas
class HumanReviewItem(BaseModel):
    id: str
    recovery_case_id: str
    customer: CustomerBase
    case_amount: float
    case_failure_reason: str
    trigger_reason: str
    status: str
    operator_notes: Optional[str] = None
    resolution_action: Optional[str] = None
    ai_recommendation: Optional[str] = None
    ai_score: Optional[float] = None
    stop_reason: Optional[str] = None
    case_status: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class HumanReviewActionRequest(BaseModel):
    notes: Optional[str] = None
    resolution_action: Optional[str] = None  # RESOLVED_MANUAL_RETRY, RESOLVED_CANCEL_SUB, ESCALATED_LEGAL, etc.

# Dashboard Metrics Schemas
class StopReasonCount(BaseModel):
    reason: str
    label: str
    count: int
    percentage: float
    amount_at_stop: float

class DashboardMetrics(BaseModel):
    failed_mandates_count: int
    revenue_at_risk: float
    ai_eligible_count: int
    recovered_revenue: float
    recovery_rate: float
    expected_recovery_revenue: float
    automation_stopped_count: int
    human_review_count: int
    stop_reasons_breakdown: List[StopReasonCount]

# Simulation Trigger Requests
class SimulateFailureRequest(BaseModel):
    customer_id: str
    amount: float = 14999.0
    failure_code: str = "INSUFFICIENT_FUNDS"
    failure_reason: str = "Temporary bank network failure"

class SimulateDisputeRequest(BaseModel):
    customer_id: str
    reason: str = "Customer contested recurring charge with card issuer"

class SimulateOptOutRequest(BaseModel):
    customer_id: str
    reason: str = "Customer clicked cancel mandate in email notification"
