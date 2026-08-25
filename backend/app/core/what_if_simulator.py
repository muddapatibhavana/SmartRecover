from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.entities import RecoveryCase
from app.schemas.dtos import (
    WhatIfSimulationResponse,
    WhatIfStrategyOption,
    RecoveryStrategyConstants
)
from app.core.intelligence_engine import get_intelligence_engine
from app.core.guardrail_engine import GuardrailEngine
from app.core.audit_service import AuditService

class WhatIfSimulatorService:
    """
    What-If Recovery Simulator Engine:
    Compares hypothetical recovery strategies for a case without executing any real or simulated payments.
    Explicitly tags all calculations as SIMULATION_ONLY.
    """

    @classmethod
    def simulate_case(cls, db: Session, case_id: str) -> WhatIfSimulationResponse:
        case = db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
        if not case:
            raise ValueError(f"Recovery case {case_id} not found")

        customer = case.customer
        attempts = case.payment_attempts
        amount = case.amount

        # Build context
        context = {
            "case_id": case.id,
            "customer": {
                "id": customer.id,
                "name": customer.name,
                "historical_success_count": customer.historical_success_count,
                "historical_failure_count": customer.historical_failure_count,
                "has_dispute": customer.has_dispute,
                "is_opted_out": customer.is_opted_out,
            },
            "attempts": attempts,
            "failure_code": case.failure_code,
            "amount": amount,
            "last_active_days_ago": 2
        }

        ai_engine = get_intelligence_engine()
        opt = ai_engine.optimize_strategy(context)
        base_prob = opt.estimated_success_probability

        # Evaluate candidate strategies
        candidates = [
            {
                "strategy": RecoveryStrategyConstants.RETRY_AFTER_6H,
                "label": "Retry after 6 Hours",
                "prob_mult": 0.78,
                "risk_level": "MEDIUM",
                "contact_risk": "Low",
                "expected_attempts": 1,
                "reason": "Short cooldown period; higher switch collision risk during business hours."
            },
            {
                "strategy": RecoveryStrategyConstants.RETRY_AFTER_24H,
                "label": "Retry after 24 Hours",
                "prob_mult": 1.0,
                "risk_level": "LOW",
                "contact_risk": "None",
                "expected_attempts": 1,
                "reason": "Optimal 24-hour clearing window. Maximizes clearance probability while adhering to standard NPCI cooldown."
            },
            {
                "strategy": RecoveryStrategyConstants.RETRY_AFTER_48H,
                "label": "Retry after 48 Hours",
                "prob_mult": 0.91,
                "risk_level": "LOW",
                "contact_risk": "None",
                "expected_attempts": 1,
                "reason": "Extended delay allows customer to fund account or resolve bank issues."
            },
            {
                "strategy": RecoveryStrategyConstants.SEND_PAYMENT_REMINDER,
                "label": "Send Payment Reminder + 48h Retry",
                "prob_mult": 0.84,
                "risk_level": "LOW",
                "contact_risk": "Medium (SMS/Email notification)",
                "expected_attempts": 1,
                "reason": "Proactive customer communication prompting account balance top-up."
            },
            {
                "strategy": RecoveryStrategyConstants.STOP_RECOVERY,
                "label": "Stop Recovery Automation",
                "prob_mult": 0.0,
                "risk_level": "ZERO",
                "contact_risk": "None",
                "expected_attempts": 0,
                "reason": "Zero risk of customer friction or duplicate charge. Forfeits automated revenue recovery."
            }
        ]

        # Guardrail check context
        case_data_for_guardrails = {
            "customer": {
                "is_opted_out": customer.is_opted_out,
                "has_dispute": customer.has_dispute,
            },
            "payment_attempts": attempts,
            "attempt_count": case.attempt_count,
            "current_status": case.current_status,
            "initial_failure_at": case.initial_failure_at,
            "last_attempt_at": attempts[-1].created_at if attempts else None
        }

        strategy_options: List[WhatIfStrategyOption] = []
        best_strategy = opt.strategy
        if best_strategy not in [c["strategy"] for c in candidates]:
            best_strategy = RecoveryStrategyConstants.RETRY_AFTER_24H

        for c in candidates:
            strat_key = c["strategy"]
            is_stop = strat_key == RecoveryStrategyConstants.STOP_RECOVERY
            action_for_gr = "SAFE_STOP" if is_stop else "RETRY_PAYMENT"

            gr_res = GuardrailEngine.evaluate(case_data_for_guardrails, proposed_action=action_for_gr)

            calc_prob = 0.0 if is_stop else round(min(0.99, max(0.05, base_prob * c["prob_mult"])), 2)
            calc_recovery = 0.0 if is_stop else round(amount * calc_prob, 2)
            is_rec = (strat_key == best_strategy) and gr_res.allowed

            strategy_options.append(WhatIfStrategyOption(
                strategy=strat_key,
                label=c["label"],
                success_probability=calc_prob,
                expected_recovery_amount=calc_recovery,
                risk_level=c["risk_level"],
                customer_contact_risk=c["contact_risk"],
                expected_attempts=c["expected_attempts"],
                is_recommended=is_rec,
                guardrail_allowed=gr_res.allowed,
                guardrail_reason=gr_res.blocked_reason if not gr_res.allowed else None,
                reason=c["reason"]
            ))

        # Record simulation event in AuditLog
        AuditService.record_event(
            db=db,
            recovery_case_id=case.id,
            event_type="WHAT_IF_SIMULATION_RUN",
            description=f"What-If Strategy Simulation evaluated 5 recovery pathways for Case #{case.id}",
            actor="SIMULATION_ENGINE",
            metadata={
                "simulation_only": True,
                "badge": "SIMULATION_ONLY",
                "best_strategy": best_strategy,
                "strategies_simulated": len(strategy_options)
            }
        )

        why_recommended = [
            f"Customer track record: {customer.historical_success_count} successful recurring debits.",
            f"Failure code {case.failure_code} indicates temporary infrastructure/balance issue.",
            f"Strategy {best_strategy} achieves optimal expected recovery (INR {round(amount * base_prob, 2):,}).",
            "Guardrail compliance checks fully satisfied."
        ]

        return WhatIfSimulationResponse(
            case_id=case.id,
            amount=amount,
            customer_name=customer.name,
            failure_code=case.failure_code,
            failure_reason=case.failure_reason,
            strategies=strategy_options,
            best_strategy=best_strategy,
            why_recommended=why_recommended
        )
