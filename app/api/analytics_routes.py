from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.dependency import get_db
from app.models.trade import Trade
from app.models.position import Position
from sqlalchemy import text
import statistics

router = APIRouter(prefix="/analytics", tags=["analytics"])


# --------------------------------
# Positions
# --------------------------------
@router.get("/positions/{account_id}")
def positions(account_id: int, db: Session = Depends(get_db)):

    positions = (
        db.query(Position)
        .filter(Position.account_id == account_id)
        .all()
    )

    return [
        {
            "symbol": p.symbol,
            "quantity": p.quantity,
            "entry_price": float(p.entry_price)
        }
        for p in positions
    ]


# --------------------------------
# Trades
# --------------------------------
@router.get("/trades/{account_id}")
def trades(account_id: int, db: Session = Depends(get_db)):

    trades = (
        db.query(Trade)
        .filter(Trade.account_id == account_id)
        .order_by(Trade.created_at.desc())
        .limit(50)
        .all()
    )

    result = []

    for t in trades:
        result.append({
            "id": t.id,
            "symbol": t.symbol,
            "quantity": t.quantity,
            "price": float(t.entry_price),
            "status": t.status,
            "time": t.created_at
        })

    return result


# --------------------------------
# Summary
# --------------------------------
@router.get("/summary/{account_id}")
def summary(account_id: int, db: Session = Depends(get_db)):

    trades_count = (
        db.query(Trade)
        .filter(Trade.account_id == account_id)
        .count()
    )

    positions_count = (
        db.query(Position)
        .filter(Position.account_id == account_id)
        .count()
    )

    return {
        "account_id": account_id,
        "total_trades": trades_count,
        "open_positions": positions_count
    }

@router.get("/equity-curve/{account_id}")
def equity_curve(account_id: int, db: Session = Depends(get_db)):

    rows = db.execute(
        text("""
        SELECT created_at, equity
        FROM equity_history
        WHERE account_id = :id
        ORDER BY created_at
        """),
        {"id": account_id}
    ).fetchall()

    return [
        {
            "time": r.created_at,
            "equity": float(r.equity)
        }
        for r in rows
    ]

@router.get("/drawdown/{account_id}")
def drawdown(account_id: int, db: Session = Depends(get_db)):

    rows = db.execute(
        text("""
        SELECT equity
        FROM equity_history
        WHERE account_id = :id
        ORDER BY created_at
        """),
        {"id": account_id}
    ).fetchall()

    peak = 0
    drawdowns = []

    for r in rows:

        equity = float(r.equity)

        if equity > peak:
            peak = equity

        drawdown = peak - equity

        drawdowns.append({
            "equity": equity,
            "drawdown": drawdown
        })

    return drawdowns

@router.get("/win-rate/{account_id}")
def win_rate(account_id: int, db: Session = Depends(get_db)):

    trades = (
        db.query(Trade)
        .filter(Trade.account_id == account_id)
        .all()
    )

    if not trades:
        return {"account_id": account_id, "win_rate": 0}

    wins = 0
    total = len(trades)

    for t in trades:
        # placeholder logic
        if t.quantity > 0:
            wins += 1

    win_rate = wins / total

    return {
        "account_id": account_id,
        "total_trades": total,
        "wins": wins,
        "win_rate": round(win_rate, 3)
    }

@router.get("/max-drawdown/{account_id}")
def max_drawdown(account_id: int, db: Session = Depends(get_db)):

    rows = db.execute(
        text("""
        SELECT equity
        FROM equity_history
        WHERE account_id = :id
        ORDER BY created_at
        """),
        {"id": account_id}
    ).fetchall()

    peak = 0
    max_dd = 0

    for r in rows:

        equity = float(r.equity)

        if equity > peak:
            peak = equity

        drawdown = peak - equity

        if drawdown > max_dd:
            max_dd = drawdown

    return {
        "account_id": account_id,
        "max_drawdown": max_dd
    }

@router.get("/sharpe-ratio/{account_id}")
def sharpe_ratio(account_id: int, db: Session = Depends(get_db)):

    rows = db.execute(
        text("""
        SELECT equity
        FROM equity_history
        WHERE account_id = :id
        ORDER BY created_at
        """),
        {"id": account_id}
    ).fetchall()

    if len(rows) < 2:
        return {"account_id": account_id, "sharpe_ratio": 0}

    returns = []

    for i in range(1, len(rows)):

        prev = float(rows[i-1].equity)
        curr = float(rows[i].equity)

        if prev == 0:
            continue

        returns.append((curr - prev) / prev)

    if len(returns) < 2:
        return {"account_id": account_id, "sharpe_ratio": 0}

    mean_return = statistics.mean(returns)
    std_return = statistics.stdev(returns)

    if std_return == 0:
        return {"account_id": account_id, "sharpe_ratio": 0}

    sharpe = mean_return / std_return

    return {
        "account_id": account_id,
        "sharpe_ratio": round(sharpe, 3)
    }

@router.get("/equity/{account_id}")
def get_equity_history(account_id: int, db: Session = Depends(get_db)):

    rows = db.execute(
        text("""
        SELECT
            equity,
            created_at
        FROM equity_history
        WHERE account_id = :account_id
        ORDER BY created_at ASC
        LIMIT 200
        """),
        {"account_id": account_id}
    ).fetchall()

    return [
        {
            "equity": float(r.equity),
            "timestamp": r.created_at.isoformat()
        }
        for r in rows
    ]
