import pytest
from datetime import datetime, timezone, timedelta
from app.models.entities import Customer, Subscription, Mandate, RecoveryCase, PaymentAttempt, AuditLog
from app.schemas.dtos import StateConstants, StopReasonConstants, StressTestRunRequest
from app.core.guardrail_engine import GuardrailEngine
from app.core.workflow_engine import RecoveryWorkflowEngine
from app.core.stress_test_engine import GuardrailStressTestEngine

def create_audit_case(db, has_dispute=False, is_opted_out=False, attempts=0, amount=15000.0, current_status=StateConstants.FAILED):
    import uuid
    uid = str(uuid.uuid4())[:8]
    cust = Customer(
        id=f"CUST-AUDIT-{uid}",
        name=f"Audit Corp {uid}",
        email=f"audit_{uid}@test.com",
        has_dispute=has_dispute,
        is_opted_out=is_opted_out,
        historical_success_count=10,
        historical_failure_count=0
    )
    sub = Subscription(
        id=f"SUB-AUDIT-{uid}",
        customer_id=cust.id,
        plan_name="Enterprise Cloud",
        amount=amount,
        interval="MONTHLY"
    )
    man = Mandate(
        id=f"MAN-AUDIT-{uid}",
        subscription_id=sub.id,
        max_amount=50000.0,
        status="ACTIVE"
    )
    case = RecoveryCase(
        id=f"SR-AUDIT-{uid}",
        customer_id=cust.id,
        mandate_id=man.id,
        subscription_id=sub.id,
        amount=amount,
        failure_code="BANK_NETWORK_TIMEOUT" if not has_dispute else "CUSTOMER_DISPUTE",
        failure_reason="Audit test failure reason",
        attempt_count=attempts,
        current_status=current_status,
        recovery_score=85.0,
        recovery_probability=0.85
    )
    db.add_all([cust, sub, man, case])
    db.commit()
    db.refresh(case)
    return case

# 1. Recovery Strategy Optimizer Safety & Advisory Verification
def test_audit_optimizer_does_not_execute_payment_and_returns_structured_strategy(client, setup_test_db):
    db = setup_test_db
    case = create_audit_case(db, amount=14999.0)

    # Initial attempts count
    init_attempts = len(case.payment_attempts)

    res = client.post(f"/api/optimizer/{case.id}/optimize")
    assert res.status_code == 200
    data = res.json()

    assert data["case_id"] == case.id
    assert "strategy" in data
    assert "recovery_score" in data
    assert data["recovery_score"] >= 0 and data["recovery_score"] <= 100
    assert "estimated_success_probability" in data
    assert "expected_recovery_amount" in data
    assert data["expected_recovery_amount"] == pytest.approx(case.amount * data["estimated_success_probability"], 0.1)
    assert len(data["positive_factors"]) >= 0

    # Verify zero database payment executions occurred
    db.refresh(case)
    assert len(case.payment_attempts) == init_attempts
    assert case.current_status == StateConstants.FAILED

# 2. Failure-Reason Intelligence Taxonomy & Safety
def test_audit_failure_intelligence_handles_all_9_categories(client):
    res = client.get("/api/optimizer/failure-catalog")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 9

    catalog_dict = {item["code"]: item for item in data}
    expected_codes = [
        "BANK_NETWORK_TIMEOUT", "PROCESSING_TIMEOUT", "INSUFFICIENT_FUNDS",
        "MANDATE_EXPIRED", "PAYMENT_METHOD_INVALID", "CUSTOMER_DISPUTE",
        "FRAUD_OR_RISK_SIGNAL", "REPEATED_FAILURE", "UNKNOWN_FAILURE"
    ]
    for code in expected_codes:
        assert code in catalog_dict
        detail = catalog_dict[code]
        assert detail["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        assert len(detail["explanation_template"]) > 0

    # Verify dispute and fraud are flagged as non-retryable and critical risk
    assert catalog_dict["CUSTOMER_DISPUTE"]["retry_suitable"] is False
    assert catalog_dict["CUSTOMER_DISPUTE"]["risk_level"] == "CRITICAL"
    assert catalog_dict["FRAUD_OR_RISK_SIGNAL"]["retry_suitable"] is False
    assert catalog_dict["FRAUD_OR_RISK_SIGNAL"]["risk_level"] == "CRITICAL"

# 3. What-If Simulator Strictly Read-Only & Simulation-Only
def test_audit_what_if_simulator_is_strictly_simulation_only(client, setup_test_db):
    db = setup_test_db
    case = create_audit_case(db, amount=25000.0)
    init_attempts = len(case.payment_attempts)

    res = client.post(f"/api/what-if/{case.id}")
    assert res.status_code == 200
    data = res.json()

    assert data["disclaimer"] == "SIMULATION — NO PAYMENT WILL BE EXECUTED"
    assert len(data["strategies"]) == 5

    # Verify zero database mutation on attempts or monetary balance
    db.refresh(case)
    assert len(case.payment_attempts) == init_attempts

    # Verify simulation audit trail entry marked SIMULATION_ONLY
    logs = db.query(AuditLog).filter(
        AuditLog.recovery_case_id == case.id,
        AuditLog.event_type == "WHAT_IF_SIMULATION_RUN"
    ).all()
    assert len(logs) > 0
    assert logs[0].actor == "SIMULATION_ENGINE"
    assert logs[0].log_metadata["badge"] == "SIMULATION_ONLY"
    assert logs[0].log_metadata["simulation_only"] is True

# 4. Revenue-at-Risk Prioritization Calculations
def test_audit_revenue_prioritization_expected_recovery_formula(client, setup_test_db):
    db = setup_test_db
    case = create_audit_case(db, amount=10000.0)
    case.recovery_probability = 0.80
    db.commit()

    res = client.get("/api/prioritization/metrics")
    assert res.status_code == 200
    data = res.json()

    assert data["total_revenue_at_risk"] >= 10000.0
    assert data["expected_recoverable_revenue"] > 0
    found_case = next((c for c in data["top_opportunities"] if c["id"] == case.id), None)
    assert found_case is not None
    assert found_case["expected_recovery_amount"] == 8000.0
    assert found_case["priority_tier"] in ["HIGH", "MEDIUM", "LOW"]

# 5. Guardrail Stress-Test Predefined Scenarios & Safe Case
def test_audit_stress_test_predefined_scenarios_and_invariants(client):
    res_scenarios = client.get("/api/stress-test/scenarios")
    assert res_scenarios.status_code == 200
    scenarios = res_scenarios.json()
    assert len(scenarios) == 5

    # Run Active Dispute Scenario
    res_dispute = client.post("/api/stress-test/run", json={"scenario_id": "STRESS-DISPUTE-01"})
    assert res_dispute.status_code == 200
    d_data = res_dispute.json()
    assert d_data["guardrail_allowed"] is False
    assert d_data["guardrail_status"] == "BLOCKED"
    assert d_data["execution_blocked"] is True

    # Run Max Retries Scenario
    res_max = client.post("/api/stress-test/run", json={"scenario_id": "STRESS-MAX-RETRIES-02"})
    assert res_max.status_code == 200
    m_data = res_max.json()
    assert m_data["guardrail_allowed"] is False
    assert m_data["guardrail_status"] == "BLOCKED"

    # Run High Risk Scenario
    res_hr = client.post("/api/stress-test/run", json={"scenario_id": "STRESS-HIGH-RISK-03"})
    assert res_hr.status_code == 200
    hr_data = res_hr.json()
    assert hr_data["guardrail_allowed"] is False
    assert hr_data["guardrail_status"] == "BLOCKED"
    assert "fraud" in hr_data["guardrail_blocked_reason"].lower() or "risk" in hr_data["guardrail_blocked_reason"].lower()

    # Run Post-Stop Execution Scenario (Scenario 4)
    res_stop = client.post("/api/stress-test/run", json={"scenario_id": "STRESS-STOPPED-CASE-04"})
    assert res_stop.status_code == 200
    stop_data = res_stop.json()
    assert stop_data["guardrail_allowed"] is False
    assert stop_data["guardrail_status"] == "BLOCKED"
    assert "STOPPED" in stop_data["guardrail_blocked_reason"]
    failed_rules = [r["rule_name"] for r in stop_data["rules_checked"] if not r["passed"]]
    assert failed_rules == ["workflow_stopped_state"]

    # Run Safe Benchmark Scenario
    res_safe = client.post("/api/stress-test/run", json={"scenario_id": "STRESS-SAFE-CASE-05"})
    assert res_safe.status_code == 200
    s_data = res_safe.json()
    assert s_data["guardrail_allowed"] is True
    assert s_data["guardrail_status"] == "ALLOWED"
    assert s_data["execution_blocked"] is True

# 5b. Custom Adversarial Simulation: High Risk ONLY blocks without dispute
def test_audit_stress_test_custom_high_risk_without_dispute(client):
    payload = {
        "proposed_action": "RETRY_NOW",
        "simulate_dispute": False,
        "simulate_max_retries": False,
        "simulate_opt_out": False,
        "simulate_high_risk": True,
        "simulate_stopped": False
    }
    res = client.post("/api/stress-test/run", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["guardrail_allowed"] is False
    assert data["guardrail_status"] == "BLOCKED"
    assert "Active customer dispute" not in data["guardrail_blocked_reason"]
    assert "fraud" in data["guardrail_blocked_reason"].lower() or "risk" in data["guardrail_blocked_reason"].lower()

    # Verify individual rule checks
    dispute_rule = next((r for r in data["rules_checked"] if r["rule_name"] == "customer_dispute"), None)
    assert dispute_rule is not None
    assert dispute_rule["passed"] is True  # Dispute was false, so dispute check passes

    fraud_rule = next((r for r in data["rules_checked"] if r["rule_name"] == "fraud_risk_signal"), None)
    assert fraud_rule is not None
    assert fraud_rule["passed"] is False  # High risk was true, so fraud risk rule triggers block

# 6. Frontend Security: Modified / Malicious Payload Re-evaluation
def test_audit_malicious_frontend_request_cannot_bypass_backend_guardrails(client, setup_test_db):
    db = setup_test_db
    # Create case with active dispute
    case = create_audit_case(db, has_dispute=True, amount=50000.0)

    # Malicious attempt: client sends direct execute request pretending action is allowed
    res = client.post(f"/api/recovery-cases/{case.id}/execute", json={
        "action_type": "RETRY_PAYMENT",
        "force_simulation_outcome": "SUCCESS"
    })
    assert res.status_code == 200
    data = res.json()

    # Authoritative backend MUST block
    assert data["success"] is False
    assert data["status"] == "BLOCKED"
    assert "dispute" in data["message"].lower()

    # Case must NOT be recovered
    db.refresh(case)
    assert case.current_status != StateConstants.RECOVERED
    assert case.current_status in [StateConstants.HUMAN_REVIEW, StateConstants.ACTION_BLOCKED]

# 7. State Machine Rejection of Illegal Transitions
def test_audit_state_machine_rejects_illegal_transitions(setup_test_db):
    db = setup_test_db
    case = create_audit_case(db)

    # FAILED cannot jump directly to RECOVERED without RETRYING
    with pytest.raises(ValueError) as excinfo:
        RecoveryWorkflowEngine.transition_state(
            db=db,
            case=case,
            new_status=StateConstants.RECOVERED,
            reason="Illegal jump attempt"
        )
    assert "Invalid state transition attempted" in str(excinfo.value)

# 8. Complete Auditability of Decision Telemetry
def test_audit_comprehensive_decision_telemetry_fields_logged(setup_test_db):
    db = setup_test_db
    case = create_audit_case(db, amount=12000.0)

    # Run analysis
    res = RecoveryWorkflowEngine.analyze_case(db=db, case_id=case.id)
    assert "ai_decision" in res
    assert "guardrail_decision" in res

    # Verify audit log records all mandatory compliance fields
    logs = db.query(AuditLog).filter(AuditLog.recovery_case_id == case.id).all()
    ai_log = next((l for l in logs if l.event_type == "STATE_TRANSITION" and l.state_after == StateConstants.AI_RECOMMENDED), None)
    assert ai_log is not None
    meta = ai_log.log_metadata
    assert meta["case_id"] == case.id
    assert "recommendation" in meta
    assert "recovery_score" in meta
    assert "probability" in meta
    assert "expected_recovery" in meta
    assert meta["expected_recovery"] > 0
    assert "timestamp" in meta
    assert meta["simulation_status"] == "SIMULATION_ONLY"
