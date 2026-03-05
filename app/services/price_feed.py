from decimal import Decimal
from app.services.strategy_engine import process_tick

# Temporary in-memory price store
price_cache = {
    "RELIANCE": Decimal("100"),
    "TCS": Decimal("3500"),
    "INFY": Decimal("1500"),
}


def get_ltp(symbol: str) -> Decimal:
    return price_cache.get(symbol, Decimal("0"))

def update_price(symbol, price):

    price_cache[symbol] = price

    process_tick(symbol, price)
