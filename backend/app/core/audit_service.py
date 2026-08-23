import uuid
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.entities import AuditLog

logger = logging.getLogger("smartrecover.audit")

class AuditService:
    @staticmethod
    def record_event(
        db: Session,
        recovery_case_id: str,
        event_type: str,
        description: str,
        actor: str = "SYSTEM",
        state_before: Optional[str] = None,
        state_after: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        event_id = f"AUD-{uuid.uuid4().hex[:10].upper()}"
        now = datetime.now(timezone.utc)
        meta = metadata or {}

        log_entry = AuditLog(
            id=event_id,
            recovery_case_id=recovery_case_id,
            event_type=event_type,
            description=description,
            actor=actor,
            state_before=state_before,
            state_after=state_after,
            metadata_json=json.dumps(meta),
            timestamp=now
        )
        db.add(log_entry)
        db.flush()

        logger.info(
            f"[AUDIT] [{event_type}] case={recovery_case_id} actor={actor} "
            f"transition=({state_before} -> {state_after}) - {description}"
        )
        return log_entry
