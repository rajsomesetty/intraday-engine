from fastapi import APIRouter, Query
import threading

from app.services.market_replay_service import replay_market_data

router = APIRouter(prefix="/backtest", tags=["backtest"])


@router.post("/start")
def start_backtest(
    file: str = Query("sample_prices.csv"),
    speed: float = Query(5.0)
):

    thread = threading.Thread(
        target=replay_market_data,
        kwargs={
            "file_name": file,
            "speed": speed
        },
        daemon=True
    )

    thread.start()

    return {
        "message": "Backtest started",
        "dataset": file,
        "speed": speed
    }
