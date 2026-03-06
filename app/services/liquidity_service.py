from decimal import Decimal


def simulate_liquidity(price: float, quantity: int, side: str):

    price_dec = Decimal(str(price))
    remaining = quantity

    # simulated market depth levels
    levels = [
        (Decimal("0.00"), 100),
        (Decimal("0.05"), 200),
        (Decimal("0.10"), 300),
        (Decimal("0.20"), 400),
    ]

    total_cost = Decimal("0")
    total_qty = 0

    for offset, depth_qty in levels:

        if remaining <= 0:
            break

        fill_qty = min(remaining, depth_qty)

        if side == "BUY":
            fill_price = price_dec + offset
        else:
            fill_price = price_dec - offset

        total_cost += fill_price * fill_qty
        total_qty += fill_qty

        remaining -= fill_qty

    if total_qty == 0:
        return price

    avg_price = total_cost / total_qty

    return float(avg_price)
