from pydantic import BaseModel


class OrderRequest(BaseModel):
    account_id: int
    symbol: str
    quantity: int
    price: float
    side: str
    idempotency_key: str
