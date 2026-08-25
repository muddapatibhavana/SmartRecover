from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.dtos import WhatIfSimulationResponse
from app.core.what_if_simulator import WhatIfSimulatorService

router = APIRouter(prefix="/what-if", tags=["What-If Simulator"])

@router.post("/{case_id}", response_model=WhatIfSimulationResponse)
def simulate_recovery_case(case_id: str, db: Session = Depends(get_db)):
    try:
        return WhatIfSimulatorService.simulate_case(db=db, case_id=case_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")
