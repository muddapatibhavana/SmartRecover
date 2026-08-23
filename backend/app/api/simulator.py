import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.entities import Customer, Subscription, Mandate, RecoveryCase, CustomerEvent
from app.schemas.dtos import (
    SimulateFailureRequest, SimulateDisputeRequest, SimulateOptOutRequest,
    ExecuteActionResponse, StateConstants, StopReasonConstants
)
from app.core.workflow_engine import RecoveryWorkflowEngine
from app.core.audit_service import AuditService
from app.core.human_review_service import HumanReviewService

router = APIRouter(prefix="/simulator", tags=["Payment Simulator"])

@router.post("/payment-failure")
def simulate_payment_failure(payload: SimulateFailureRequest, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == payload.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer {payload.customer_id} not found")

    sub = customer.subscriptions[0] if customer.subscriptions else None
    if not sub:
        raise HTTPException(status_code=400, detail="Customer has no active subscription")

    mandate = sub.mandates[0] if sub.mandates else None
    if not mandate:
        raise HTTPException(status_code=400, detail="Subscription has no registered mandate")

    now = datetime.now(timezone.utc)
    case_id = f"SR-{uuid.uuid4().hex[:6].upper()}"

    case = RecoveryCase(
        id=case_id,
        customer_id=customer.id,
        subscription_id=sub.id,
        mandate_id=mandate.id,
        amount=payload.amount,
        currency="INR",
        failure_reason=payload.failure_reason,
        failure_code=payload.failure_code,
        attempt_count=0,
        current_status=StateConstants.FAILED,
        initial_failure_at=now,
        created_at=now
    )
    db.add(case)
    db.flush()

    AuditService.record_event(
        db=db,
        recovery_case_id=case.id,
        event_type="PAYMENT_FAILED",
        description=f"Recurring mandate debit failed: {payload.failure_reason} (Code: {payload.failure_code})",
        actor="PAYMENT_SIMULATOR",
        state_after=StateConstants.FAILED,
        metadata={"amount": payload.amount, "currency": "INR", "mandate_id": mandate.id}
    )

    db.commit()
    db.refresh(case)

    return {
        "success": True,
        "message": f"Simulated payment failure created recovery case #{case.id}",
        "case_id": case.id,
        "amount": case.amount,
        "failure_reason": case.failure_reason,
        "status": case.current_status
    }

@router.post("/retry-success/{case_id}", response_model=ExecuteActionResponse)
def simulate_retry_success(case_id: str, db: Session = Depends(get_db)):
    """
    Force a successful simulated retry outcome on a recovery case.
    """
    return RecoveryWorkflowEngine.execute_action(
        db=db,
        case_id=case_id,
        action_type="RETRY_PAYMENT",
        force_outcome="SUCCESS"
    )

@router.post("/retry-failure/{case_id}", response_model=ExecuteActionResponse)
def simulate_retry_failure(case_id: str, db: Session = Depends(get_db)):
    """
    Force a failed simulated retry outcome on a recovery case.
    """
    return RecoveryWorkflowEngine.execute_action(
        db=db,
        case_id=case_id,
        action_type="RETRY_PAYMENT",
        force_outcome="FAILED"
    )

@router.post("/dispute")
def simulate_customer_dispute(payload: SimulateDisputeRequest, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == payload.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer {payload.customer_id} not found")

    customer.has_dispute = True
    now = datetime.now(timezone.utc)

    # Record Customer Event
    cust_event = CustomerEvent(
        id=f"EVT-{uuid.uuid4().hex[:8].upper()}",
        customer_id=customer.id,
        event_type="DISPUTE_FILED",
        details=payload.reason,
        created_at=now
    )
    db.add(cust_event)

    # Update active recovery cases for this customer
    affected_cases = db.query(RecoveryCase).filter(
        RecoveryCase.customer_id == customer.id,
        RecoveryCase.current_status.notin_([StateConstants.RECOVERED, StateConstants.STOPPED])
    ).all()

    for case in affected_cases:
        case.guardrail_status = "BLOCKED"
        case.guardrail_block_reason = "Customer dispute detected"
        case.stop_reason = StopReasonConstants.CUSTOMER_DISPUTED
        case.next_action = None
        case.next_action_scheduled_at = None

        HumanReviewService.create_or_get_review(
            db=db,
            recovery_case_id=case.id,
            customer_id=customer.id,
            trigger_reason=f"Customer dispute filed: {payload.reason}"
        )

        RecoveryWorkflowEngine.transition_state(
            db=db,
            case=case,
            new_status=StateConstants.HUMAN_REVIEW,
            reason=f"Customer dispute filed: {payload.reason}. Retries locked.",
            actor="GUARDRAIL_ENGINE",
            metadata={"dispute_reason": payload.reason}
        )

    db.commit()
    return {
        "success": True,
        "message": f"Customer dispute simulated for {customer.name}. All active recovery cases halted and routed to Human Review.",
        "affected_cases_count": len(affected_cases)
    }

@router.post("/opt-out")
def simulate_customer_opt_out(payload: SimulateOptOutRequest, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == payload.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer {payload.customer_id} not found")

    customer.is_opted_out = True
    now = datetime.now(timezone.utc)

    cust_event = CustomerEvent(
        id=f"EVT-{uuid.uuid4().hex[:8].upper()}",
        customer_id=customer.id,
        event_type="OPT_OUT_REQUESTED",
        details=payload.reason,
        created_at=now
    )
    db.add(cust_event)

    affected_cases = db.query(RecoveryCase).filter(
        RecoveryCase.customer_id == customer.id,
        RecoveryCase.current_status.notin_([StateConstants.RECOVERED, StateConstants.STOPPED])
    ).all()

    for case in affected_cases:
        case.guardrail_status = "BLOCKED"
        case.guardrail_block_reason = "Customer opted out"
        case.stop_reason = StopReasonConstants.CUSTOMER_OPTED_OUT
        case.next_action = None
        case.next_action_scheduled_at = None

        RecoveryWorkflowEngine.transition_state(
            db=db,
            case=case,
            new_status=StateConstants.STOPPED,
            reason=f"Customer opt-out received: {payload.reason}. Automation stopped safely.",
            actor="GUARDRAIL_ENGINE",
            metadata={"opt_out_reason": payload.reason}
        )

    db.commit()
    return {
        "success": True,
        "message": f"Customer opt-out recorded for {customer.name}. All active recovery cases stopped safely.",
        "affected_cases_count": len(affected_cases)
    }
