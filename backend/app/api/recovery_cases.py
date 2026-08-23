from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.entities import RecoveryCase, Customer, Subscription, Mandate, PaymentAttempt
from app.schemas.dtos import (
    RecoveryCaseSummary, RecoveryCaseDetail, DualDecisionView,
    ExecuteActionRequest, ExecuteActionResponse, CustomerBase,
    SubscriptionBase, MandateBase, PaymentAttemptBase
)
from app.core.workflow_engine import RecoveryWorkflowEngine

router = APIRouter(prefix="/recovery-cases", tags=["Recovery Cases"])

@router.get("", response_model=List[RecoveryCaseSummary])
def list_recovery_cases(
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    query = db.query(RecoveryCase).join(Customer).join(Subscription)

    if status:
        query = query.filter(RecoveryCase.current_status == status)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Customer.name.ilike(search_pattern)) |
            (Customer.email.ilike(search_pattern)) |
            (RecoveryCase.id.ilike(search_pattern)) |
            (RecoveryCase.failure_reason.ilike(search_pattern))
        )

    cases = query.order_by(desc(RecoveryCase.created_at)).offset(offset).limit(limit).all()

    summaries = []
    for c in cases:
        summaries.append(RecoveryCaseSummary(
            id=c.id,
            customer_id=c.customer.id,
            customer_name=c.customer.name,
            customer_email=c.customer.email,
            subscription_plan=c.subscription.plan_name,
            amount=c.amount,
            currency=c.currency,
            failure_reason=c.failure_reason,
            failure_code=c.failure_code,
            attempt_count=c.attempt_count,
            recovery_score=c.recovery_score,
            recovery_probability=c.recovery_probability,
            ai_recommendation=c.ai_recommendation,
            guardrail_status=c.guardrail_status,
            current_status=c.current_status,
            stop_reason=c.stop_reason,
            next_action=c.next_action,
            created_at=c.created_at,
            updated_at=c.updated_at
        ))
    return summaries

@router.get("/{case_id}", response_model=RecoveryCaseDetail)
def get_recovery_case(case_id: str, db: Session = Depends(get_db)):
    case = db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Recovery case {case_id} not found")

    payment_attempts = [
        PaymentAttemptBase.model_validate(p) for p in case.payment_attempts
    ]

    return RecoveryCaseDetail(
        id=case.id,
        customer=CustomerBase.model_validate(case.customer),
        subscription=SubscriptionBase.model_validate(case.subscription),
        mandate=MandateBase.model_validate(case.mandate),
        amount=case.amount,
        currency=case.currency,
        failure_reason=case.failure_reason,
        failure_code=case.failure_code,
        attempt_count=case.attempt_count,
        recovery_score=case.recovery_score,
        recovery_probability=case.recovery_probability,
        ai_recommendation=case.ai_recommendation,
        ai_recommended_delay_hours=case.ai_recommended_delay_hours,
        ai_explanation=case.ai_explanation,
        ai_decision_factors=case.ai_decision_factors,
        guardrail_status=case.guardrail_status,
        guardrail_block_reason=case.guardrail_block_reason,
        guardrail_rules_checked=case.guardrail_rules_checked,
        current_status=case.current_status,
        stop_reason=case.stop_reason,
        next_action=case.next_action,
        next_action_scheduled_at=case.next_action_scheduled_at,
        initial_failure_at=case.initial_failure_at,
        created_at=case.created_at,
        updated_at=case.updated_at,
        payment_attempts=payment_attempts
    )

@router.post("/{case_id}/analyze")
def analyze_recovery_case(case_id: str, db: Session = Depends(get_db)):
    try:
        result = RecoveryWorkflowEngine.analyze_case(db=db, case_id=case_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/{case_id}/validate-action", response_model=DualDecisionView)
def validate_action(
    case_id: str,
    action_type: str = Query("RETRY_PAYMENT"),
    db: Session = Depends(get_db)
):
    try:
        return RecoveryWorkflowEngine.validate_action(db=db, case_id=case_id, proposed_action=action_type)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{case_id}/execute", response_model=ExecuteActionResponse)
def execute_recovery_action(
    case_id: str,
    payload: ExecuteActionRequest,
    db: Session = Depends(get_db)
):
    try:
        return RecoveryWorkflowEngine.execute_action(
            db=db,
            case_id=case_id,
            action_type=payload.action_type,
            idempotency_key=payload.idempotency_key,
            force_outcome=payload.force_simulation_outcome
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")
