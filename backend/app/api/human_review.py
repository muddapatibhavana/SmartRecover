from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.entities import HumanReview, Customer, RecoveryCase
from app.schemas.dtos import HumanReviewItem, HumanReviewActionRequest, CustomerBase
from app.core.human_review_service import HumanReviewService

router = APIRouter(prefix="/human-review", tags=["Human Review"])

@router.get("", response_model=List[HumanReviewItem])
def list_human_reviews(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(HumanReview).join(Customer).join(RecoveryCase)
    if status:
        query = query.filter(HumanReview.status == status)

    reviews = query.order_by(desc(HumanReview.created_at)).all()

    items = []
    for r in reviews:
        items.append(HumanReviewItem(
            id=r.id,
            recovery_case_id=r.recovery_case_id,
            customer=CustomerBase.model_validate(r.customer),
            case_amount=r.recovery_case.amount,
            case_failure_reason=r.recovery_case.failure_reason,
            trigger_reason=r.trigger_reason,
            status=r.status,
            operator_notes=r.operator_notes,
            resolution_action=r.resolution_action,
            ai_recommendation=r.recovery_case.ai_recommendation,
            ai_score=r.recovery_case.recovery_score,
            stop_reason=r.recovery_case.stop_reason,
            case_status=r.recovery_case.current_status,
            created_at=r.created_at,
            updated_at=r.updated_at
        ))
    return items

@router.post("/{review_id}/review", response_model=HumanReviewItem)
def mark_as_reviewed(
    review_id: str,
    payload: HumanReviewActionRequest,
    db: Session = Depends(get_db)
):
    try:
        updated = HumanReviewService.update_review(
            db=db,
            review_id=review_id,
            status="REVIEWED",
            notes=payload.notes
        )
        return HumanReviewItem(
            id=updated.id,
            recovery_case_id=updated.recovery_case_id,
            customer=CustomerBase.model_validate(updated.customer),
            case_amount=updated.recovery_case.amount,
            case_failure_reason=updated.recovery_case.failure_reason,
            trigger_reason=updated.trigger_reason,
            status=updated.status,
            operator_notes=updated.operator_notes,
            resolution_action=updated.resolution_action,
            ai_recommendation=updated.recovery_case.ai_recommendation,
            ai_score=updated.recovery_case.recovery_score,
            stop_reason=updated.recovery_case.stop_reason,
            case_status=updated.recovery_case.current_status,
            created_at=updated.created_at,
            updated_at=updated.updated_at
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{review_id}/resolve", response_model=HumanReviewItem)
def resolve_human_review(
    review_id: str,
    payload: HumanReviewActionRequest,
    db: Session = Depends(get_db)
):
    try:
        updated = HumanReviewService.update_review(
            db=db,
            review_id=review_id,
            status="RESOLVED",
            notes=payload.notes,
            resolution_action=payload.resolution_action or "RESOLVED_MANUALLY"
        )
        return HumanReviewItem(
            id=updated.id,
            recovery_case_id=updated.recovery_case_id,
            customer=CustomerBase.model_validate(updated.customer),
            case_amount=updated.recovery_case.amount,
            case_failure_reason=updated.recovery_case.failure_reason,
            trigger_reason=updated.trigger_reason,
            status=updated.status,
            operator_notes=updated.operator_notes,
            resolution_action=updated.resolution_action,
            ai_recommendation=updated.recovery_case.ai_recommendation,
            ai_score=updated.recovery_case.recovery_score,
            stop_reason=updated.recovery_case.stop_reason,
            case_status=updated.recovery_case.current_status,
            created_at=updated.created_at,
            updated_at=updated.updated_at
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{review_id}/escalate", response_model=HumanReviewItem)
def escalate_human_review(
    review_id: str,
    payload: HumanReviewActionRequest,
    db: Session = Depends(get_db)
):
    try:
        updated = HumanReviewService.update_review(
            db=db,
            review_id=review_id,
            status="ESCALATED",
            notes=payload.notes,
            resolution_action=payload.resolution_action or "ESCALATED_LEGAL_FINANCE"
        )
        return HumanReviewItem(
            id=updated.id,
            recovery_case_id=updated.recovery_case_id,
            customer=CustomerBase.model_validate(updated.customer),
            case_amount=updated.recovery_case.amount,
            case_failure_reason=updated.recovery_case.failure_reason,
            trigger_reason=updated.trigger_reason,
            status=updated.status,
            operator_notes=updated.operator_notes,
            resolution_action=updated.resolution_action,
            ai_recommendation=updated.recovery_case.ai_recommendation,
            ai_score=updated.recovery_case.recovery_score,
            stop_reason=updated.recovery_case.stop_reason,
            case_status=updated.recovery_case.current_status,
            created_at=updated.created_at,
            updated_at=updated.updated_at
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
