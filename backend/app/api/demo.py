from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.seed import seed_database
from app.models.entities import Customer, RecoveryCase
from app.schemas.dtos import StateConstants, StopReasonConstants
from app.core.audit_service import AuditService

router = APIRouter(prefix="/demo", tags=["Demo Management"])

@router.post("/reset")
def reset_demo_data(db: Session = Depends(get_db)):
    """
    Reset and re-seed the entire database to baseline demo state.
    """
    seed_database(db=db)
    return {
        "success": True,
        "message": "Demo database successfully reset with fresh customers (A-F), 1,248 total cases, and target metrics."
    }

@router.post("/scenario/successful-recovery")
def prepare_scenario_successful_recovery(db: Session = Depends(get_db)):
    case = db.query(RecoveryCase).filter(RecoveryCase.id == "SR-1027").first()
    if case:
        case.current_status = StateConstants.FAILED
        case.attempt_count = 0
        case.stop_reason = None
        case.recovery_score = None
        case.recovery_probability = None
        case.ai_recommendation = None
        case.guardrail_status = "PENDING"
        db.commit()
    return {
        "success": True,
        "scenario": "Successful Recovery Loop (Customer D - CloudScale Analytics)",
        "case_id": "SR-1027",
        "description": "Ready for live demo: Click 'Analyze', verify AI Score (90+) + Guardrails PASS, then click 'Execute Retry' to see auto-recovery & safe stopping."
    }

@router.post("/scenario/guardrail-blocked")
def prepare_scenario_guardrail_blocked(db: Session = Depends(get_db)):
    case = db.query(RecoveryCase).filter(RecoveryCase.id == "SR-1026").first()
    if case:
        case.customer.has_dispute = True
        case.guardrail_status = "BLOCKED"
        case.guardrail_block_reason = "Customer dispute detected. Automatic retries strictly prohibited."
        db.commit()
    return {
        "success": True,
        "scenario": "Guardrail Blocked via Customer Dispute (Customer C - Apex Retail Logistics)",
        "case_id": "SR-1026",
        "description": "AI recommends RETRY, but GuardrailEngine authoritatively blocks execution due to dispute and routes to Human Review."
    }

@router.post("/scenario/customer-opt-out")
def prepare_scenario_customer_opt_out(db: Session = Depends(get_db)):
    case = db.query(RecoveryCase).filter(RecoveryCase.id == "SR-1029").first()
    if case:
        case.customer.is_opted_out = True
        case.current_status = StateConstants.STOPPED
        case.stop_reason = StopReasonConstants.CUSTOMER_OPTED_OUT
        case.guardrail_status = "BLOCKED"
        db.commit()
    return {
        "success": True,
        "scenario": "Safe Stop on Customer Opt-Out (Customer F - FinPulse Systems)",
        "case_id": "SR-1029",
        "description": "Customer opted out of retries. Guardrail blocks all actions; workflow stops automatically."
    }

@router.post("/scenario/customer-dispute")
def prepare_scenario_customer_dispute(db: Session = Depends(get_db)):
    return prepare_scenario_guardrail_blocked(db=db)

@router.post("/scenario/max-attempts")
def prepare_scenario_max_attempts(db: Session = Depends(get_db)):
    case = db.query(RecoveryCase).filter(RecoveryCase.id == "SR-1028").first()
    if case:
        case.attempt_count = 2
        case.current_status = StateConstants.STOPPED
        case.stop_reason = StopReasonConstants.MAX_ATTEMPTS_REACHED
        case.guardrail_status = "BLOCKED"
        case.guardrail_block_reason = "Maximum retry attempts limit (2) reached."
        db.commit()
    return {
        "success": True,
        "scenario": "Safe Stop on Maximum Attempts (Customer E - Horizon Media Labs)",
        "case_id": "SR-1028",
        "description": "Attempt limit of 2 reached. Guardrails prohibit further retries; workflow stops safely."
    }
