from fastapi import APIRouter

from app.models.schemas import ProblemInput, SafetyCheckResponse
from app.services.safety_service import check_safety

router = APIRouter(prefix="/api/v1", tags=["safety"])


@router.post("/safety-check", response_model=SafetyCheckResponse)
async def safety_check(payload: ProblemInput):
    """Run safety classification on user problem text.

    Returns safe=True to proceed, or safe=False with crisis resources.
    """
    result = await check_safety(payload.problem)
    return result
