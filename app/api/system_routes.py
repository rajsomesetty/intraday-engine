from fastapi import APIRouter
from app.services.system_control_service import (
    enable_kill_switch,
    disable_kill_switch,
    is_kill_switch_enabled,
)

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/kill-switch")
def get_kill_switch():

    return {"enabled": is_kill_switch_enabled()}


@router.post("/kill-switch/enable")
def enable():

    enable_kill_switch()

    return {"status": "enabled"}


@router.post("/kill-switch/disable")
def disable():

    disable_kill_switch()

    return {"status": "disabled"}
