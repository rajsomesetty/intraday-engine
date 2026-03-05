from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.dependency import get_db
from app.models.trade import Trade

router = APIRouter(prefix="/strategy", tags=["strategy"])


@router.get("/performance")
def strategy_performance(db: Session = Depends(get_db)):

    trades = db.query(Trade).all()

    strategies = {}

    for t in trades:

        name = t.strategy_name or "manual"

        if name not in strategies:
            strategies[name] = {
                "trades": 0,
                "wins": 0,
                "losses": 0,
                "pnl": 0
            }

        strategies[name]["trades"] += 1

        pnl = getattr(t, "realized_pnl", 0) or 0

        strategies[name]["pnl"] += float(pnl)

        if pnl > 0:
            strategies[name]["wins"] += 1
        elif pnl < 0:
            strategies[name]["losses"] += 1

    results = []

    for name, data in strategies.items():

        trades = data["trades"]
        wins = data["wins"]
        losses = data["losses"]

        win_rate = (wins / trades) if trades else 0

        results.append({
            "strategy": name,
            "trades": trades,
            "pnl": round(data["pnl"], 2),
            "wins": wins,
            "losses": losses,
            "win_rate": round(win_rate, 2)
        })

    return results
