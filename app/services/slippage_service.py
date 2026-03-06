from decimal import Decimal
import random

# default slippage: 0.05%
DEFAULT_SLIPPAGE = Decimal("0.0005")


def apply_slippage(price: float, side: str):

    price_dec = Decimal(str(price))

    slippage = price_dec * DEFAULT_SLIPPAGE

    # add small randomness
    slippage *= Decimal(str(random.uniform(0.8, 1.2)))

    if side == "BUY":
        return float(price_dec + slippage)

    if side == "SELL":
        return float(price_dec - slippage)

    return price
