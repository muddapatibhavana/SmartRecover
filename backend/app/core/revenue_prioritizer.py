from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.entities import RecoveryCase, Customer
from app.schemas.dtos import (
    RevenuePriorityMetrics,
    PriorityCaseSummary,
    StateConstants,
    StopReasonConstants
)
from app.core.failure_intelligence import FailureIntelligenceService

class RevenuePrioritizationEngine:
    """
    Revenue-at-Risk Prioritization Engine:
    Ranks failed recurring payments not merely by nominal amount, but by
    Expected Recoverable Revenue (Amount × Probability) adjusted for customer loyalty and safety risks.
    """

    @classmethod
    def evaluate_priorities(cls, db: Session, limit: int = 50) -> RevenuePriorityMetrics:
        all_cases = db.query(RecoveryCase).join(Customer).all()

        active_cases = [
            c for c in all_cases
            if c.current_status not in [StateConstants.RECOVERED]
            and c.stop_reason != StopReasonConstants.PAYMENT_RECOVERED
        ]

        total_revenue_at_risk = sum(c.amount for c in active_cases)

        prioritized_items: List[PriorityCaseSummary] = []

        for c in active_cases:
            customer = c.customer
            amount = float(c.amount)
            prob = float(c.recovery_probability if c.recovery_probability is not None else 0.5)

            # Failure classification
            fail_info = FailureIntelligenceService.get_classification(c.failure_code)

            # Expected recovery
            expected_rec = round(amount * prob, 2)

            # Priority Score (0 - 1000 scale)
            # Base: Expected revenue logarithmic scaling + probability weight
            loyalty_bonus = min(200.0, float(customer.historical_success_count) * 15.0)
            dispute_penalty = 500.0 if customer.has_dispute else 0.0
            attempt_penalty = float(c.attempt_count) * 100.0

            # Raw score
            raw_priority = (expected_rec * 0.05) + (prob * 300.0) + loyalty_bonus - dispute_penalty - attempt_penalty

            # Determine Tier
            if customer.has_dispute or c.attempt_count >= 2 or prob < 0.35:
                tier = "LOW"
            elif expected_rec >= 8000.0 or (prob >= 0.75 and amount >= 5000.0):
                tier = "HIGH"
            elif expected_rec >= 3000.0 or prob >= 0.50:
                tier = "MEDIUM"
            else:
                tier = "LOW"

            explainable_factors: List[str] = []
            if expected_rec >= 8000.0:
                explainable_factors.append(f"High expected recovery volume (INR {expected_rec:,.2f})")
            if prob >= 0.80:
                explainable_factors.append(f"High clearance probability ({int(prob*100)}%)")
            if customer.historical_success_count >= 5:
                explainable_factors.append(f"Loyal customer ({customer.historical_success_count} prior debits)")
            if fail_info.retry_suitable:
                explainable_factors.append(f"Transient failure type ({fail_info.name})")
            if customer.has_dispute:
                explainable_factors.append("Active dispute limits automated priority")
            if c.attempt_count > 0:
                explainable_factors.append(f"{c.attempt_count} prior retry attempt(s)")

            guardrail_eligible = (not customer.has_dispute) and (not customer.is_opted_out) and (c.attempt_count < 2)

            prioritized_items.append(PriorityCaseSummary(
                id=c.id,
                customer_name=customer.name,
                customer_email=customer.email,
                amount=amount,
                recovery_probability=prob,
                expected_recovery_amount=expected_rec,
                priority_tier=tier,
                priority_score=round(raw_priority, 1),
                failure_code=c.failure_code,
                failure_reason=c.failure_reason,
                recommended_strategy=c.ai_recommendation or "RETRY_AFTER_24H",
                guardrail_eligible=guardrail_eligible,
                rank=0,  # assigned after sorting
                explainable_factors=explainable_factors
            ))

        # Sort by expected recovery amount descending, then probability
        prioritized_items.sort(key=lambda x: (x.expected_recovery_amount, x.recovery_probability), reverse=True)

        for idx, item in enumerate(prioritized_items):
            item.rank = idx + 1

        # Metrics aggregation
        expected_recoverable_revenue = sum(p.expected_recovery_amount for p in prioritized_items)
        high_items = [p for p in prioritized_items if p.priority_tier == "HIGH"]
        med_items = [p for p in prioritized_items if p.priority_tier == "MEDIUM"]
        low_items = [p for p in prioritized_items if p.priority_tier == "LOW"]

        return RevenuePriorityMetrics(
            total_revenue_at_risk=round(total_revenue_at_risk, 2),
            expected_recoverable_revenue=round(expected_recoverable_revenue, 2),
            high_priority_count=len(high_items),
            high_priority_amount=round(sum(p.amount for p in high_items), 2),
            medium_priority_count=len(med_items),
            medium_priority_amount=round(sum(p.amount for p in med_items), 2),
            low_priority_count=len(low_items),
            low_priority_amount=round(sum(p.amount for p in low_items), 2),
            top_opportunities=prioritized_items[:limit]
        )
