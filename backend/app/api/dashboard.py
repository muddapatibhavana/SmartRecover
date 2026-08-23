from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.entities import RecoveryCase, HumanReview
from app.schemas.dtos import DashboardMetrics, StopReasonCount, StateConstants, StopReasonConstants

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("", response_model=DashboardMetrics)
def get_dashboard_metrics(db: Session = Depends(get_db)):
    """
    Dynamically calculate all revenue recovery KPIs and stop reasons from live database records.
    """
    total_cases = db.query(RecoveryCase).all()

    failed_mandates_count = len(total_cases)

    # Revenue At Risk: Sum of active recovery case amounts (not recovered, not stopped with recovery)
    active_cases = [c for c in total_cases if c.current_status not in [StateConstants.RECOVERED] and c.stop_reason != StopReasonConstants.PAYMENT_RECOVERED]
    revenue_at_risk = sum(c.amount for c in active_cases)

    # AI Eligible: Cases with score >= 40 or recommended for retry/notify
    ai_eligible_cases = [c for c in total_cases if (c.recovery_score is not None and c.recovery_score >= 40) or (c.ai_recommendation in ["RETRY", "NOTIFY"])]
    ai_eligible_count = len(ai_eligible_cases)

    # Recovered Revenue: Sum of amounts where state is RECOVERED or stop_reason is PAYMENT_RECOVERED
    recovered_cases = [c for c in total_cases if c.current_status == StateConstants.RECOVERED or c.stop_reason == StopReasonConstants.PAYMENT_RECOVERED]
    recovered_revenue = sum(c.amount for c in recovered_cases)

    # Total Recoverable Revenue = Revenue At Risk + Recovered Revenue
    total_recoverable = revenue_at_risk + recovered_revenue
    recovery_rate = (recovered_revenue / total_recoverable * 100.0) if total_recoverable > 0 else 0.0

    # Expected Recovery: Revenue at Risk * Recovery Probability
    expected_recovery_revenue = sum(
        c.amount * (c.recovery_probability if c.recovery_probability is not None else 0.5)
        for c in active_cases
    )

    # Automation Stopped Count
    stopped_cases = [c for c in total_cases if c.current_status == StateConstants.STOPPED or c.stop_reason is not None]
    automation_stopped_count = len(stopped_cases)

    # Human Review Count
    human_review_count = db.query(HumanReview).filter(HumanReview.status.in_(["PENDING", "REVIEWED"])).count()

    # Stop reasons breakdown
    stop_reasons_map = {
        StopReasonConstants.PAYMENT_RECOVERED: {"label": "Payment Recovered (Success Stop)", "count": 0, "amount": 0.0},
        StopReasonConstants.MAX_ATTEMPTS_REACHED: {"label": "Maximum Retry Attempts Reached", "count": 0, "amount": 0.0},
        StopReasonConstants.CUSTOMER_DISPUTED: {"label": "Customer Dispute Detected", "count": 0, "amount": 0.0},
        StopReasonConstants.CUSTOMER_OPTED_OUT: {"label": "Customer Opt-Out Received", "count": 0, "amount": 0.0},
        StopReasonConstants.RECOVERY_WINDOW_EXPIRED: {"label": "Recovery Window Expired (7 Days)", "count": 0, "amount": 0.0},
        StopReasonConstants.HUMAN_REVIEW_REQUIRED: {"label": "Human Review Required", "count": 0, "amount": 0.0},
        StopReasonConstants.RECOVERY_FAILED: {"label": "Permanent Mandate Failure", "count": 0, "amount": 0.0},
    }

    for c in total_cases:
        if c.stop_reason and c.stop_reason in stop_reasons_map:
            stop_reasons_map[c.stop_reason]["count"] += 1
            stop_reasons_map[c.stop_reason]["amount"] += c.amount

    total_stopped = sum(item["count"] for item in stop_reasons_map.values())
    breakdown = []
    for reason_key, data in stop_reasons_map.items():
        pct = (data["count"] / total_stopped * 100.0) if total_stopped > 0 else 0.0
        breakdown.append(StopReasonCount(
            reason=reason_key,
            label=data["label"],
            count=data["count"],
            percentage=round(pct, 1),
            amount_at_stop=round(data["amount"], 2)
        ))

    # Sort breakdown by count descending
    breakdown.sort(key=lambda x: x.count, reverse=True)

    return DashboardMetrics(
        failed_mandates_count=failed_mandates_count,
        revenue_at_risk=round(revenue_at_risk, 2),
        ai_eligible_count=ai_eligible_count,
        recovered_revenue=round(recovered_revenue, 2),
        recovery_rate=round(recovery_rate, 1),
        expected_recovery_revenue=round(expected_recovery_revenue, 2),
        automation_stopped_count=automation_stopped_count,
        human_review_count=human_review_count,
        stop_reasons_breakdown=breakdown
    )
