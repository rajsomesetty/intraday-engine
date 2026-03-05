from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.dependency import get_db
from app.models.risk_config import RiskConfig
from app.schemas.risk_schema import (
    RiskConfigResponse,
    RiskConfigUpdate
)

router = APIRouter(prefix="/accounts", tags=["risk"])

@router.get("/{account_id}/risk", response_model=RiskConfigResponse)
def get_risk_config(account_id: int, db: Session = Depends(get_db)):

    config = (
        db.query(RiskConfig)
        .filter(RiskConfig.account_id == account_id)
        .first()
    )

    if not config:
        raise HTTPException(
            status_code=404,
            detail="Risk config not found"
        )

    return config

@router.patch("/{account_id}/risk", response_model=RiskConfigResponse)
def update_risk_config(
    account_id: int,
    payload: RiskConfigUpdate,
    db: Session = Depends(get_db)
):

    config = (
        db.query(RiskConfig)
        .filter(RiskConfig.account_id == account_id)
        .first()
    )

    if not config:
        raise HTTPException(
            status_code=404,
            detail="Risk config not found"
        )

    if payload.daily_loss_limit is not None:
        config.daily_loss_limit = payload.daily_loss_limit

    if payload.max_allocation_pct is not None:
        config.max_allocation_pct = payload.max_allocation_pct

    if payload.max_exposure_pct is not None:
        config.max_exposure_pct = payload.max_exposure_pct

    if payload.max_open_positions is not None:
        config.max_open_positions = payload.max_open_positions

    if payload.max_symbol_exposure_pct is not None:
        config.max_symbol_exposure_pct = payload.max_symbol_exposure_pct

    db.commit()
    db.refresh(config)

    return config
