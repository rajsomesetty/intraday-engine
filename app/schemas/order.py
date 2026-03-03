from pydantic import BaseModel

class OrderRequest(BaseModel):
    symbol: str
    quantity: int
    price: float
    side: str
    idempotency_key: str
