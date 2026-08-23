from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.entities import AuditLog
from app.schemas.dtos import AuditLogEntry

router = APIRouter(prefix="/recovery-cases", tags=["Audit"])

@router.get("/{case_id}/audit", response_model=List[AuditLogEntry])
def get_case_audit_trail(case_id: str, db: Session = Depends(get_db)):
    """
    Retrieve immutable chronological audit trail for a recovery case.
    """
    logs = db.query(AuditLog).filter(
        AuditLog.recovery_case_id == case_id
    ).order_by(AuditLog.timestamp.asc()).all()

    entries = []
    for log in logs:
        entries.append(AuditLogEntry(
            id=log.id,
            recovery_case_id=log.recovery_case_id,
            event_type=log.event_type,
            description=log.description,
            actor=log.actor,
            state_before=log.state_before,
            state_after=log.state_after,
            metadata=log.log_metadata,
            timestamp=log.timestamp
        ))
    return entries
