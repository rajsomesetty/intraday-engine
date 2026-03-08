from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.dependency import get_db
from app.services.system_control_service import is_kill_switch_enabled
from app.services.tick_queue import get_tick_queue_size
from app.services.execution_queue import get_execution_queue_size
import redis
import os


router = APIRouter(prefix="/system", tags=["system"])


REDIS_HOST = os.getenv("REDIS_HOST", "intraday-redis")


def check_redis():

    try:

        r = redis.Redis(host=REDIS_HOST, port=6379)

        r.ping()

        return "connected"

    except Exception:

        return "disconnected"


def check_postgres(db: Session):

    try:

        db.execute(text("SELECT 1"))

        return "connected"

    except Exception:

        return "disconnected"


@router.get("/health")
def system_health(db: Session = Depends(get_db)):

    return {

        "redis": check_redis(),

        "postgres": check_postgres(db),

        "kill_switch": is_kill_switch_enabled(),

        "tick_queue_depth": get_tick_queue_size(),

        "execution_queue_depth": get_execution_queue_size(),

    }
