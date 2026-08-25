from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.entities import RecoveryCase
from app.schemas.dtos import StrategyOptimizerResponse, FailureClassificationDetail
from app.core.intelligence_engine import get_intelligence_engine
from app.core.failure_intelligence import FailureIntelligenceService

router = APIRouter(prefix="/optimizer", tags=["Strategy Optimizer"])

@router.post("/{case_id}/optimize", response_model=StrategyOptimizerResponse)
def optimize_case_strategy(case_id: str, db: Session = Depends(get_db)):
    case = db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Recovery case {case_id} not found")

    customer = case.customer
    attempts = case.payment_attempts

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
        "attempt_count": case.attempt_count,
        "failure_code": case.failure_code,
        "is_temporary": "TIMEOUT" in case.failure_code or "INSUFFICIENT" in case.failure_code,
        "amount": case.amount,
        "last_active_days_ago": 2
    }

    ai_engine = get_intelligence_engine()
    return ai_engine.optimize_strategy(context)

@router.get("/failure-catalog", response_model=List[FailureClassificationDetail])
def get_failure_catalog():
    return FailureIntelligenceService.get_all_classifications()
