import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models.entities import (
    Customer, Subscription, Mandate, RecoveryCase, PaymentAttempt,
    RecoveryAction, GuardrailEvent, AuditLog, HumanReview
)
from app.schemas.dtos import StateConstants, StopReasonConstants
from app.core.intelligence_engine import RuleBasedIntelligenceEngine
from app.core.guardrail_engine import GuardrailEngine
from app.core.workflow_engine import RecoveryWorkflowEngine
from app.core.audit_service import AuditService
from app.core.human_review_service import HumanReviewService

from sqlalchemy.pool import StaticPool

# In-memory test database with StaticPool so all connections share the same memory DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def client(setup_test_db):
    def override_get_db():
        try:
            yield setup_test_db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

def create_sample_case(db, customer_name="Test Corp", amount=14999.0, is_opted_out=False, has_dispute=False, attempt_count=0, initial_failure_days_ago=0, hist_success=10, hist_fail=1):
    now = datetime.now(timezone.utc)
    c_id = f"CUST-TEST-{datetime.now().microsecond}"
    s_id = f"SUB-TEST-{datetime.now().microsecond}"
    m_id = f"MAND-TEST-{datetime.now().microsecond}"
    case_id = f"SR-TEST-{datetime.now().microsecond}"

    cust = Customer(
        id=c_id,
        name=customer_name,
        email=f"{c_id}@test.com",
        is_active=True,
        has_dispute=has_dispute,
        is_opted_out=is_opted_out,
        historical_success_count=hist_success,
        historical_failure_count=hist_fail,
        last_active_at=now - timedelta(days=1),
        created_at=now - timedelta(days=100)
    )
    sub = Subscription(id=s_id, customer_id=c_id, plan_name="Pro Plan", amount=amount)
    mand = Mandate(id=m_id, subscription_id=s_id, max_amount=amount * 2)
    case = RecoveryCase(
        id=case_id,
        customer_id=c_id,
        subscription_id=s_id,
        mandate_id=m_id,
        amount=amount,
        failure_reason="Temporary payment failure",
        failure_code="INSUFFICIENT_FUNDS",
        attempt_count=attempt_count,
        current_status=StateConstants.FAILED,
        initial_failure_at=now - timedelta(days=initial_failure_days_ago),
        created_at=now - timedelta(days=initial_failure_days_ago)
    )
    db.add(cust)
    db.add(sub)
    db.add(mand)
    db.add(case)
    db.commit()
    db.refresh(case)
    return case

# 1. Successful recovery stops workflow
def test_successful_recovery_stops_workflow(setup_test_db):
    db = setup_test_db
    case = create_sample_case(db)

    # Execute retry with forced success
    res = RecoveryWorkflowEngine.execute_action(db=db, case_id=case.id, action_type="RETRY_PAYMENT", force_outcome="SUCCESS")
    assert res.success is True
    assert res.current_case_status == StateConstants.STOPPED
    assert res.stop_reason == StopReasonConstants.PAYMENT_RECOVERED

    db.refresh(case)
    assert case.current_status == StateConstants.STOPPED
    assert case.stop_reason == StopReasonConstants.PAYMENT_RECOVERED

# 2. Maximum retry attempts blocks retry
def test_max_retry_attempts_blocks_retry(setup_test_db):
    db = setup_test_db
    case = create_sample_case(db, attempt_count=2)

    res = RecoveryWorkflowEngine.execute_action(db=db, case_id=case.id, action_type="RETRY_PAYMENT")
    assert res.success is False
    assert res.status == "BLOCKED"
    assert "Maximum retry attempts" in res.message

# 3. Retry before 24 hours blocks retry
def test_retry_before_24_hours_blocks_retry(setup_test_db):
    db = setup_test_db
    case = create_sample_case(db, attempt_count=1)

    # Add an attempt that happened 2 hours ago
    now = datetime.now(timezone.utc)
    att = PaymentAttempt(
        id="ATT-RECENT",
        recovery_case_id=case.id,
        mandate_id=case.mandate_id,
        attempt_number=1,
        amount=case.amount,
        status="FAILED",
        created_at=now - timedelta(hours=2)
    )
    db.add(att)
    db.commit()

    decision = GuardrailEngine.evaluate({
        "customer": {"is_opted_out": False, "has_dispute": False},
        "payment_attempts": [att],
        "attempt_count": 1,
        "current_status": StateConstants.FAILED,
        "initial_failure_at": now - timedelta(hours=2),
        "last_attempt_at": now - timedelta(hours=2)
    }, proposed_action="RETRY_PAYMENT")

    assert decision.allowed is False
    assert "cooldown" in decision.blocked_reason.lower() or "hours" in decision.blocked_reason.lower()

# 4. Recovery window expiration stops automation
def test_recovery_window_expiration_stops_automation(setup_test_db):
    db = setup_test_db
    case = create_sample_case(db, initial_failure_days_ago=8)

    res = RecoveryWorkflowEngine.execute_action(db=db, case_id=case.id, action_type="RETRY_PAYMENT")
    assert res.success is False
    assert res.status == "BLOCKED"
    assert "recovery window" in res.message.lower()

# 5. Customer opt-out blocks recovery
def test_customer_opt_out_blocks_recovery(setup_test_db):
    db = setup_test_db
    case = create_sample_case(db, is_opted_out=True)

    res = RecoveryWorkflowEngine.execute_action(db=db, case_id=case.id, action_type="RETRY_PAYMENT")
    assert res.success is False
    assert res.status == "BLOCKED"
    assert "opted out" in res.message.lower()

# 6. Customer dispute blocks recovery
def test_customer_dispute_blocks_recovery(setup_test_db):
    db = setup_test_db
    case = create_sample_case(db, has_dispute=True)

    res = RecoveryWorkflowEngine.execute_action(db=db, case_id=case.id, action_type="RETRY_PAYMENT")
    assert res.success is False
    assert res.status == "BLOCKED"
    assert "dispute" in res.message.lower()

# 7. AI recommendation cannot bypass GuardrailEngine
def test_ai_recommendation_cannot_bypass_guardrail(setup_test_db):
    db = setup_test_db
    # High recovery history makes AI recommend RETRY, but customer has dispute
    case = create_sample_case(db, has_dispute=True, hist_success=20, hist_fail=0)

    # Run analysis
    analysis = RecoveryWorkflowEngine.analyze_case(db=db, case_id=case.id)
    assert analysis["ai_decision"].recommended_action == "RETRY"
    assert analysis["guardrail_decision"].allowed is False
    assert analysis["guardrail_decision"].status == "BLOCKED"
    assert analysis["current_status"] == StateConstants.HUMAN_REVIEW

# 8. Low recovery score routes to human review
def test_low_recovery_score_routes_to_human_review(setup_test_db):
    ai_engine = RuleBasedIntelligenceEngine()
    context = {
        "customer": {"historical_success_count": 1, "historical_failure_count": 6},
        "attempts": [{"id": "ATT-1"}],
        "failure_code": "UNAUTHORIZED",
        "is_temporary": False,
        "amount": 4999.0,
        "last_active_days_ago": 60
    }
    decision = ai_engine.evaluate(context)
    assert decision.score < 40
    assert decision.recommended_action == "HUMAN_REVIEW"

# 9. Successful retry creates audit event
def test_successful_retry_creates_audit_event(setup_test_db):
    db = setup_test_db
    case = create_sample_case(db)

    RecoveryWorkflowEngine.execute_action(db=db, case_id=case.id, action_type="RETRY_PAYMENT", force_outcome="SUCCESS")

    logs = db.query(AuditLog).filter(AuditLog.recovery_case_id == case.id).all()
    event_types = [l.event_type for l in logs]
    assert "STATE_TRANSITION" in event_types
    assert any("recovered" in l.description.lower() for l in logs)

# 10. Blocked action creates guardrail event
def test_blocked_action_creates_guardrail_event(setup_test_db):
    db = setup_test_db
    case = create_sample_case(db, has_dispute=True)

    RecoveryWorkflowEngine.analyze_case(db=db, case_id=case.id)
    events = db.query(GuardrailEvent).filter(GuardrailEvent.recovery_case_id == case.id).all()
    assert len(events) >= 1
    assert events[0].allowed is False
    assert events[0].status == "BLOCKED"

# 11. Frontend cannot bypass backend guardrails
def test_frontend_cannot_bypass_backend_guardrails(client, setup_test_db):
    db = setup_test_db
    case = create_sample_case(db, has_dispute=True)

    # Calling execute API directly as a malicious/buggy client
    response = client.post(f"/api/recovery-cases/{case.id}/execute", json={
        "action_type": "RETRY_PAYMENT"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["status"] == "BLOCKED"

# 12. /execute revalidates guardrails
def test_execute_revalidates_guardrails(setup_test_db):
    db = setup_test_db
    case = create_sample_case(db, has_dispute=False)

    # Pretend case was previously marked allowed in DB
    case.guardrail_status = "ALLOWED"
    case.current_status = StateConstants.ACTION_ALLOWED
    db.commit()

    # Now dispute is filed before execute runs
    case.customer.has_dispute = True
    db.commit()

    # Execution must re-check and BLOCK
    res = RecoveryWorkflowEngine.execute_action(db=db, case_id=case.id, action_type="RETRY_PAYMENT")
    assert res.success is False
    assert res.status == "BLOCKED"

# 13. Duplicate action execution is rejected / idempotent
def test_idempotency_duplicate_action_rejected(setup_test_db):
    db = setup_test_db
    case = create_sample_case(db)
    idem_key = "IDEM-UNIQUE-12345"

    res1 = RecoveryWorkflowEngine.execute_action(
        db=db, case_id=case.id, action_type="RETRY_PAYMENT", idempotency_key=idem_key, force_outcome="SUCCESS"
    )
    assert res1.success is True

    # Call again with same idempotency key
    res2 = RecoveryWorkflowEngine.execute_action(
        db=db, case_id=case.id, action_type="RETRY_PAYMENT", idempotency_key=idem_key
    )
    assert res2.status == "ALREADY_EXECUTED"
    assert "Idempotent response" in res2.message

# 14. Invalid state transitions are rejected
def test_invalid_state_transitions_are_rejected(setup_test_db):
    db = setup_test_db
    case = create_sample_case(db)
    case.current_status = StateConstants.FAILED
    db.commit()

    # Direct transition from FAILED to RECOVERED is invalid without going through workflow
    with pytest.raises(ValueError) as excinfo:
        RecoveryWorkflowEngine.transition_state(
            db=db, case=case, new_status=StateConstants.RECOVERED, reason="Invalid bypass"
        )
    assert "Invalid state transition" in str(excinfo.value)

# 15. Successful recovery records recovered revenue in dashboard
def test_recovered_revenue_metric_calculation(client, setup_test_db):
    db = setup_test_db
    case = create_sample_case(db, amount=25000.0)

    # Prior to recovery
    res_before = client.get("/api/dashboard")
    assert res_before.status_code == 200
    rev_before = res_before.json()["recovered_revenue"]

    # Execute recovery
    RecoveryWorkflowEngine.execute_action(db=db, case_id=case.id, action_type="RETRY_PAYMENT", force_outcome="SUCCESS")

    # After recovery
    res_after = client.get("/api/dashboard")
    assert res_after.status_code == 200
    rev_after = res_after.json()["recovered_revenue"]
    assert rev_after == rev_before + 25000.0

# 16. Human review lifecycle (review and resolve)
def test_human_review_review_and_resolve_flow(client, setup_test_db):
    db = setup_test_db
    case = create_sample_case(db, has_dispute=True)
    review = HumanReviewService.create_or_get_review(
        db=db, recovery_case_id=case.id, customer_id=case.customer.id, trigger_reason="Customer dispute"
    )
    db.commit()

    # Step 1: Mark In-Review via API
    res_review = client.post(f"/api/human-review/{review.id}/review", json={
        "notes": "Spoke with customer support rep"
    })
    assert res_review.status_code == 200
    assert res_review.json()["status"] == "REVIEWED"

    # Step 2: Resolve via API
    res_resolve = client.post(f"/api/human-review/{review.id}/resolve", json={
        "notes": "Customer agreed to new invoice",
        "resolution_action": "RESOLVED_CUSTOMER_CONTACTED"
    })
    assert res_resolve.status_code == 200
    assert res_resolve.json()["status"] == "RESOLVED"
    assert res_resolve.json()["resolution_action"] == "RESOLVED_CUSTOMER_CONTACTED"

    # Verify case status updated to STOPPED
    db.refresh(case)
    assert case.current_status == StateConstants.STOPPED
    assert "RESOLVED_BY_OPERATOR" in case.stop_reason

    # Verify audit trail
    logs = db.query(AuditLog).filter(AuditLog.recovery_case_id == case.id).all()
    event_types = [l.event_type for l in logs]
    assert "HUMAN_REVIEW_RESOLVED" in event_types

# 17. Human review escalation records audit event
def test_human_review_escalation_flow(client, setup_test_db):
    db = setup_test_db
    case = create_sample_case(db, has_dispute=True)
    review = HumanReviewService.create_or_get_review(
        db=db, recovery_case_id=case.id, customer_id=case.customer.id, trigger_reason="High value dispute"
    )
    db.commit()

    res_esc = client.post(f"/api/human-review/{review.id}/escalate", json={
        "notes": "High risk fraud pattern",
        "resolution_action": "ESCALATED_LEGAL"
    })
    assert res_esc.status_code == 200
    assert res_esc.json()["status"] == "ESCALATED"
    assert res_esc.json()["resolution_action"] == "ESCALATED_LEGAL"

# 18. Disputed case cannot execute automated retry through API
def test_disputed_case_cannot_execute_automated_retry(client, setup_test_db):
    db = setup_test_db
    case = create_sample_case(db, has_dispute=True)

    # Calling execute directly
    res = client.post(f"/api/recovery-cases/{case.id}/execute", json={
        "action_type": "RETRY_PAYMENT"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is False
    assert data["status"] == "BLOCKED"
    assert "dispute" in data["message"].lower()

# =================================================================
# TESTS FOR THE 5 NEW CAPABILITIES
# =================================================================

# 19. Strategy optimizer produces structured recommendation
def test_strategy_optimizer_structured_recommendation(client, setup_test_db):
    db = setup_test_db
    case = create_sample_case(db, amount=14999.0, hist_success=14, hist_fail=1)

    res = client.post(f"/api/optimizer/{case.id}/optimize")
    assert res.status_code == 200
    data = res.json()
    assert "strategy" in data
    assert "recovery_score" in data
    assert "estimated_success_probability" in data
    assert "expected_recovery_amount" in data
    assert "confidence" in data
    assert len(data["reasoning"]) > 0
    assert data["expected_recovery_amount"] > 0

# 20. BANK_NETWORK_TIMEOUT recommends delayed retry (24h)
def test_bank_network_timeout_recommends_delayed_retry(client, setup_test_db):
    db = setup_test_db
    case = create_sample_case(db, amount=9999.0)
    case.failure_code = "BANK_NETWORK_TIMEOUT"
    db.commit()

    res = client.post(f"/api/optimizer/{case.id}/optimize")
    assert res.status_code == 200
    data = res.json()
    assert data["strategy"] in ["RETRY_AFTER_24H", "RETRY_AFTER_6H"]
    assert data["recommended_delay_hours"] == 24
    assert data["risk_level"] == "LOW"

# 21. INSUFFICIENT_FUNDS recommends payment reminder and 48h delay
def test_insufficient_funds_recommends_payment_reminder(client, setup_test_db):
    db = setup_test_db
    case = create_sample_case(db, amount=5000.0)
    case.failure_code = "INSUFFICIENT_FUNDS"
    db.commit()

    res = client.post(f"/api/optimizer/{case.id}/optimize")
    assert res.status_code == 200
    data = res.json()
    assert "REMINDER" in data["strategy"] or data["recommended_delay_hours"] >= 24

# 22. CUSTOMER_DISPUTE cannot result in allowed automated retry
def test_customer_dispute_cannot_result_in_allowed_retry(client, setup_test_db):
    db = setup_test_db
    case = create_sample_case(db, has_dispute=True)
    case.failure_code = "CUSTOMER_DISPUTE"
    db.commit()

    res = client.post(f"/api/optimizer/{case.id}/optimize")
    assert res.status_code == 200
    data = res.json()
    assert data["strategy"] == "STOP_RECOVERY"
    assert data["guardrail_precheck_status"] == "BLOCKED"
    assert data["human_review_required"] is True

# 23. Repeated retry case is blocked by guardrails
def test_repeated_retry_case_blocked_by_guardrails(client, setup_test_db):
    db = setup_test_db
    case = create_sample_case(db, attempt_count=2)
    case.failure_code = "REPEATED_FAILURE"
    db.commit()

    res = client.post(f"/api/optimizer/{case.id}/optimize")
    assert res.status_code == 200
    data = res.json()
    assert data["strategy"] == "STOP_RECOVERY"
    assert data["guardrail_precheck_status"] == "BLOCKED"

# 24. What-if simulator never executes payment and returns comparative strategies
def test_what_if_simulator_never_executes_payment(client, setup_test_db):
    db = setup_test_db
    case = create_sample_case(db, amount=14999.0)

    # Initial attempts count
    initial_attempts = len(case.payment_attempts)

    res = client.post(f"/api/what-if/{case.id}")
    assert res.status_code == 200
    data = res.json()

    assert data["case_id"] == case.id
    assert len(data["strategies"]) >= 4
    assert data["disclaimer"] == "SIMULATION — NO PAYMENT WILL BE EXECUTED"

    # Verify no payment attempt was created in DB
    db.refresh(case)
    assert len(case.payment_attempts) == initial_attempts

# 25. Simulation events are recorded with SIMULATION_ONLY badge
def test_simulation_events_marked_simulation_only(client, setup_test_db):
    db = setup_test_db
    case = create_sample_case(db)

    res = client.post(f"/api/what-if/{case.id}")
    assert res.status_code == 200

    # Verify audit log
    logs = db.query(AuditLog).filter(
        AuditLog.recovery_case_id == case.id,
        AuditLog.event_type == "WHAT_IF_SIMULATION_RUN"
    ).all()
    assert len(logs) > 0
    assert logs[0].actor == "SIMULATION_ENGINE"
    assert logs[0].log_metadata.get("badge") == "SIMULATION_ONLY"

# 26. Revenue priority calculation works and ranks by expected recovery
def test_revenue_priority_calculation(client, setup_test_db):
    db = setup_test_db
    case_high = create_sample_case(db, amount=50000.0, hist_success=15)
    case_high.recovery_probability = 0.90
    case_low = create_sample_case(db, amount=500.0, hist_success=0, hist_fail=3)
    case_low.recovery_probability = 0.10
    db.commit()

    res = client.get("/api/prioritization/metrics")
    assert res.status_code == 200
    data = res.json()

    assert data["total_revenue_at_risk"] > 0
    assert data["expected_recoverable_revenue"] > 0
    assert len(data["top_opportunities"]) > 0

    # Top opportunity should have higher expected recovery
    top_case = data["top_opportunities"][0]
    assert top_case["rank"] == 1
    assert top_case["expected_recovery_amount"] >= data["top_opportunities"][-1]["expected_recovery_amount"]

# 27. Stress test correctly blocks unsafe AI recommendation
def test_stress_test_correctly_blocks_unsafe_ai_recommendation(client):
    res = client.post("/api/stress-test/run", json={
        "scenario_id": "STRESS-DISPUTE-01"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["guardrail_allowed"] is False
    assert data["guardrail_status"] == "BLOCKED"
    assert "dispute" in data["guardrail_blocked_reason"].lower()
    assert data["simulation_badge"] == "SIMULATION_ONLY"
    assert data["execution_blocked"] is True

# 28. Safe recommendation can pass guardrails in benchmark scenario
def test_safe_recommendation_can_pass_guardrails(client):
    res = client.post("/api/stress-test/run", json={
        "scenario_id": "STRESS-SAFE-CASE-05"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["guardrail_allowed"] is True
    assert data["guardrail_status"] == "ALLOWED"
    assert data["execution_blocked"] is True

# 29. Failure intelligence catalog endpoint returns all 9 failure categories
def test_failure_catalog_endpoint(client):
    res = client.get("/api/optimizer/failure-catalog")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 9
    codes = [item["code"] for item in data]
    assert "BANK_NETWORK_TIMEOUT" in codes
    assert "INSUFFICIENT_FUNDS" in codes
    assert "CUSTOMER_DISPUTE" in codes
    assert "FRAUD_OR_RISK_SIGNAL" in codes
    assert "MANDATE_EXPIRED" in codes


