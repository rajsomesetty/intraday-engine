from decimal import Decimal
import random

SLIPPAGE_PCT = Decimal("0.05")  # 0.05%


def apply_slippage(price: float, side: str):

    price = Decimal(str(price))

    slip = price * SLIPPAGE_PCT / Decimal("100")

    if side == "BUY":
        price += slip

    elif side == "SELL":
        price -= slip

    return float(price)
