from fastapi import APIRouter
from app.services.metrics_service import (
    current_equity,
    current_exposure,
    kill_switch_state,
)

router = APIRouter(prefix="/system-status", tags=["system"])


@router.get("/")
def system_status():

    return {
        "equity": current_equity(),
        "exposure": current_exposure(),
        "kill_switch": kill_switch_state(),
    }
