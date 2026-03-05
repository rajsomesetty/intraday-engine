from pydantic import BaseModel
from decimal import Decimal
from typing import Optional


class RiskConfigResponse(BaseModel):
    account_id: int
    daily_loss_limit: Decimal
    max_allocation_pct: Decimal
    max_exposure_pct: Decimal
    max_symbol_exposure_pct: Decimal
    max_open_positions: int

    class Config:
        orm_mode = True

class RiskConfigUpdate(BaseModel):
    daily_loss_limit: Optional[Decimal] = None
    max_allocation_pct: Optional[Decimal] = None
    max_exposure_pct: Optional[Decimal] = None
    max_open_positions: Optional[int] = None
    max_symbol_exposure_pct: Optional[Decimal] = None
