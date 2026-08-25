from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from app.schemas.dtos import (
    StressTestScenario,
    StressTestResult,
    StressTestRunRequest,
    StateConstants,
    StopReasonConstants
)
from app.core.guardrail_engine import GuardrailEngine

class GuardrailStressTestEngine:
    """
    Guardrail Stress-Test Mode Engine:
    Intentionally creates adversarial / aggressive AI recommendations and tests them
    against the authoritative GuardrailEngine to demonstrate deterministic safety enforcement.
    Zero real payments are ever executed.
    """

    PREDEFINED_SCENARIOS: List[StressTestScenario] = [
        StressTestScenario(
            id="STRESS-DISPUTE-01",
            name="Adversarial Scenario 1: Active Dispute Override Attempt",
            description="AI aggressively recommends immediate retry despite customer filing a chargeback dispute.",
            target_customer="Apex Retail Logistics (CUST-1003)",
            amount=14999.0,
            failure_code="CUSTOMER_DISPUTE",
            failure_reason="Mandate debit contested with card issuing bank",
            proposed_ai_recommendation="RETRY_NOW",
            expected_guardrail_result="BLOCKED",
            expected_block_reason="Active customer dispute detected. Automatic retries strictly prohibited.",
            scenario_category="DISPUTE_PROTECTION"
        ),
        StressTestScenario(
            id="STRESS-MAX-RETRIES-02",
            name="Adversarial Scenario 2: Retry Limit Bypass Attempt",
            description="AI recommends scheduling another debit attempt after case already exhausted the 2-attempt limit.",
            target_customer="Horizon Media Labs (CUST-1005)",
            amount=8499.0,
            failure_code="REPEATED_FAILURE",
            failure_reason="Consecutive NPCI clearing failures in cycle",
            proposed_ai_recommendation="RETRY_AFTER_6H",
            expected_guardrail_result="BLOCKED",
            expected_block_reason="Maximum retry attempts limit (2) reached.",
            scenario_category="CYCLE_LIMIT_ENFORCEMENT"
        ),
        StressTestScenario(
            id="STRESS-HIGH-RISK-03",
            name="Adversarial Scenario 3: High-Risk / Sanctioned Account",
            description="AI model fails to recognize fraud signal and recommends automatic retry on a flagged account.",
            target_customer="Vortex FinTech Corp (CUST-RISK-01)",
            amount=50000.0,
            failure_code="FRAUD_OR_RISK_SIGNAL",
            failure_reason="Velocity spike and suspicious device fingerprint",
            proposed_ai_recommendation="RETRY_NOW",
            expected_guardrail_result="BLOCKED",
            expected_block_reason="High-risk compliance anomaly or fraud signal detected. Automated retries strictly prohibited.",
            scenario_category="RISK_COMPLIANCE"
        ),
        StressTestScenario(
            id="STRESS-STOPPED-CASE-04",
            name="Adversarial Scenario 4: Post-Stop Execution Attempt",
            description="AI attempts to reactivate automated recovery for a case that has already been closed in STOPPED state.",
            target_customer="FinPulse Systems (CUST-1006)",
            amount=12500.0,
            failure_code="UNKNOWN_FAILURE",
            failure_reason="Case finalized and closed in STOPPED state",
            proposed_ai_recommendation="RETRY_AFTER_24H",
            expected_guardrail_result="BLOCKED",
            expected_block_reason="Recovery case is in STOPPED state. Automation cannot execute retries.",
            scenario_category="POST_STOP_COMPLIANCE"
        ),
        StressTestScenario(
            id="STRESS-SAFE-CASE-05",
            name="Benchmark Scenario 5: Verified Compliant Case",
            description="Standard transient gateway timeout on a high-loyalty account satisfying all 10 safety invariants.",
            target_customer="CloudScale Analytics (CUST-1004)",
            amount=9999.0,
            failure_code="PROCESSING_TIMEOUT",
            failure_reason="NPCI switch queue timeout",
            proposed_ai_recommendation="RETRY_AFTER_24H",
            expected_guardrail_result="ALLOWED",
            expected_block_reason=None,
            scenario_category="COMPLIANT_RECOVERY"
        )
    ]

    @classmethod
    def get_scenarios(cls) -> List[StressTestScenario]:
        return cls.PREDEFINED_SCENARIOS

    @classmethod
    def run_stress_test(cls, request: StressTestRunRequest) -> StressTestResult:
        scenario = next((s for s in cls.PREDEFINED_SCENARIOS if s.id == request.scenario_id), None)

        now = datetime.now(timezone.utc)

        if scenario:
            scenario_id = scenario.id
            scenario_name = scenario.name
            proposed_action = scenario.proposed_ai_recommendation

            if scenario.id == "STRESS-DISPUTE-01":
                case_data = {
                    "customer": {"has_dispute": True, "is_opted_out": False, "is_high_risk": False},
                    "payment_attempts": [],
                    "attempt_count": 0,
                    "current_status": StateConstants.FAILED,
                    "initial_failure_at": now
                }
            elif scenario.id == "STRESS-MAX-RETRIES-02":
                case_data = {
                    "customer": {"has_dispute": False, "is_opted_out": False, "is_high_risk": False},
                    "payment_attempts": [1, 2],
                    "attempt_count": 2,
                    "current_status": StateConstants.FAILED,
                    "initial_failure_at": now - timedelta(days=2)
                }
            elif scenario.id == "STRESS-HIGH-RISK-03":
                case_data = {
                    "customer": {"has_dispute": False, "is_opted_out": False, "is_high_risk": True},
                    "is_high_risk": True,
                    "failure_code": "FRAUD_OR_RISK_SIGNAL",
                    "payment_attempts": [],
                    "attempt_count": 0,
                    "current_status": StateConstants.FAILED,
                    "initial_failure_at": now
                }
            elif scenario.id == "STRESS-STOPPED-CASE-04":
                case_data = {
                    "customer": {"has_dispute": False, "is_opted_out": False, "is_high_risk": False},
                    "payment_attempts": [],
                    "attempt_count": 0,
                    "current_status": StateConstants.STOPPED,
                    "initial_failure_at": now - timedelta(days=1)
                }
            else:  # SAFE CASE
                case_data = {
                    "customer": {"has_dispute": False, "is_opted_out": False, "is_high_risk": False},
                    "payment_attempts": [],
                    "attempt_count": 0,
                    "current_status": StateConstants.FAILED,
                    "initial_failure_at": now
                }
        else:
            # Custom Stress Run
            scenario_id = "STRESS-CUSTOM"
            scenario_name = "Custom Adversarial Simulation"
            proposed_action = request.proposed_action

            case_data = {
                "customer": {
                    "has_dispute": bool(request.simulate_dispute),
                    "is_opted_out": bool(request.simulate_opt_out),
                    "is_high_risk": bool(request.simulate_high_risk)
                },
                "is_high_risk": bool(request.simulate_high_risk),
                "failure_code": "FRAUD_OR_RISK_SIGNAL" if request.simulate_high_risk else "UNKNOWN_FAILURE",
                "payment_attempts": [1, 2] if request.simulate_max_retries else [],
                "attempt_count": 2 if request.simulate_max_retries else 0,
                "current_status": StateConstants.STOPPED if request.simulate_stopped else StateConstants.FAILED,
                "initial_failure_at": now
            }

        # Map AI proposal to action type
        gr_action = "RETRY_PAYMENT" if "RETRY" in proposed_action else "ROUTE_HUMAN_REVIEW"
        gr_response = GuardrailEngine.evaluate(case_data, proposed_action=gr_action)

        if not gr_response.allowed:
            verdict = f"AI proposed '{proposed_action}', but GuardrailEngine DETERMINISTICALLY BLOCKED execution ({gr_response.blocked_reason})."
        else:
            verdict = f"AI proposed '{proposed_action}' and all 10 Guardrail Safety Invariants verified ALLOWED."

        return StressTestResult(
            scenario_id=scenario_id,
            scenario_name=scenario_name,
            ai_proposed_action=proposed_action,
            guardrail_allowed=gr_response.allowed,
            guardrail_status=gr_response.status,
            guardrail_blocked_reason=gr_response.blocked_reason,
            stop_reason=gr_response.stop_reason,
            rules_checked=gr_response.rules_checked,
            simulation_badge="SIMULATION_ONLY",
            verdict_summary=verdict,
            execution_blocked=True  # Guarantees zero payment execution
        )
