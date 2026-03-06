from decimal import Decimal
from app.services.strategy_engine import process_tick

# Temporary in-memory price store
price_cache = {
    "RELIANCE": Decimal("100"),
    "TCS": Decimal("3500"),
    "INFY": Decimal("1500"),
}

# Track last processed price to avoid duplicate ticks
_last_price_cache = {}


def get_ltp(symbol: str) -> Decimal:
    return price_cache.get(symbol, Decimal("0"))


def update_price(symbol: str, price):

    price = Decimal(str(price))

    last = _last_price_cache.get(symbol)

    # -----------------------------------
    # Ignore duplicate ticks
    # -----------------------------------

    if last == price:
        return False

    _last_price_cache[symbol] = price

    # Update price cache
    price_cache[symbol] = price

    # Trigger strategies
    process_tick(symbol, price)

    return True
