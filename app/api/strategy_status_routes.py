from fastapi import APIRouter

from app.services.strategy_state_service import strategy_states

router = APIRouter(prefix="/strategy", tags=["strategy"])


@router.get("/status")
def strategy_status():

    return strategy_states
