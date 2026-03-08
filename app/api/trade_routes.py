from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.dependency import get_db
from app.models.trade import Trade

router = APIRouter(prefix="/trades", tags=["trades"])


@router.get("/")
def get_trades(limit: int = 100, db: Session = Depends(get_db)):

    trades = (
        db.query(Trade)
        .order_by(Trade.id.desc())
        .limit(limit)
        .all()
    )

    return trades
