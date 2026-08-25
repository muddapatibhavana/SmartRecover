from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.dtos import RevenuePriorityMetrics
from app.core.revenue_prioritizer import RevenuePrioritizationEngine

router = APIRouter(prefix="/prioritization", tags=["Revenue Prioritization"])

@router.get("/metrics", response_model=RevenuePriorityMetrics)
def get_revenue_priorities(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    return RevenuePrioritizationEngine.evaluate_priorities(db=db, limit=limit)
