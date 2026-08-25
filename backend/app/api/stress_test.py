from typing import List
from fastapi import APIRouter, HTTPException
from app.schemas.dtos import StressTestScenario, StressTestResult, StressTestRunRequest
from app.core.stress_test_engine import GuardrailStressTestEngine

router = APIRouter(prefix="/stress-test", tags=["Guardrail Stress Test"])

@router.get("/scenarios", response_model=List[StressTestScenario])
def list_stress_test_scenarios():
    return GuardrailStressTestEngine.get_scenarios()

@router.post("/run", response_model=StressTestResult)
def run_guardrail_stress_test(request: StressTestRunRequest):
    return GuardrailStressTestEngine.run_stress_test(request)
