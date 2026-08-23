import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.entities import HumanReview, RecoveryCase
from app.core.audit_service import AuditService
from app.schemas.dtos import StateConstants

class HumanReviewService:
    @staticmethod
    def create_or_get_review(
        db: Session,
        recovery_case_id: str,
        customer_id: str,
        trigger_reason: str
    ) -> HumanReview:
        existing = db.query(HumanReview).filter(
            HumanReview.recovery_case_id == recovery_case_id,
            HumanReview.status.in_(["PENDING", "REVIEWED"])
        ).first()

        if existing:
            return existing

        review_id = f"REV-{uuid.uuid4().hex[:8].upper()}"
        review = HumanReview(
            id=review_id,
            recovery_case_id=recovery_case_id,
            customer_id=customer_id,
            trigger_reason=trigger_reason,
            status="PENDING",
            created_at=datetime.now(timezone.utc)
        )
        db.add(review)
        db.flush()

        AuditService.record_event(
            db=db,
            recovery_case_id=recovery_case_id,
            event_type="HUMAN_REVIEW_CREATED",
            description=f"Case queued for Human Review: {trigger_reason}",
            actor="SYSTEM",
            metadata={"review_id": review_id, "trigger_reason": trigger_reason}
        )
        return review

    @staticmethod
    def update_review(
        db: Session,
        review_id: str,
        status: str,
        notes: Optional[str] = None,
        resolution_action: Optional[str] = None
    ) -> HumanReview:
        review = db.query(HumanReview).filter(HumanReview.id == review_id).first()
        if not review:
            raise ValueError(f"Review item {review_id} not found")

        review.status = status
        if notes:
            review.operator_notes = notes
        if resolution_action:
            review.resolution_action = resolution_action
        review.updated_at = datetime.now(timezone.utc)

        case = db.query(RecoveryCase).filter(RecoveryCase.id == review.recovery_case_id).first()
        if case and status == "RESOLVED":
            # If resolved, transition case or mark stopped
            old_status = case.current_status
            case.current_status = StateConstants.STOPPED
            case.stop_reason = f"RESOLVED_BY_OPERATOR: {resolution_action or 'MANUAL_REVIEW'}"
            AuditService.record_event(
                db=db,
                recovery_case_id=case.id,
                event_type="HUMAN_REVIEW_RESOLVED",
                description=f"Human operator resolved case ({status}). Notes: {notes or 'None'}",
                actor="HUMAN_OPERATOR",
                state_before=old_status,
                state_after=case.current_status,
                metadata={"review_id": review_id, "resolution": resolution_action}
            )
        elif case:
            AuditService.record_event(
                db=db,
                recovery_case_id=case.id,
                event_type="HUMAN_REVIEW_UPDATED",
                description=f"Operator updated review status to {status}",
                actor="HUMAN_OPERATOR",
                metadata={"review_id": review_id, "status": status, "notes": notes}
            )

        db.commit()
        db.refresh(review)
        return review
