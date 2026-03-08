from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.dependency import get_db
from app.models.position import Position

router = APIRouter(prefix="/positions", tags=["positions"])


@router.get("/")
def get_positions(db: Session = Depends(get_db)):

    positions = db.query(Position).all()

    return positions
