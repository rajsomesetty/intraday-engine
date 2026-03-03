from typing import List, Dict


class RiskException(Exception):
    pass


def enforce_risk(
    account,
    simulated_positions: List[Dict],
    trade_value: float,
    ltp: float,
):
    """
    Enforce risk based on simulated post-trade state.
    """

    # --------------------------
    # Calculate Exposure
    # --------------------------
    exposure = sum(
        pos["quantity"] * pos["average_price"]
        for pos in simulated_positions
    )

    # --------------------------
    # Calculate Unrealized MTM
    # --------------------------
    unrealized = 0

    for pos in simulated_positions:
        if pos["quantity"] > 0:
            unrealized += (ltp - pos["average_price"]) * pos["quantity"]

    total_pnl = account.daily_pnl + unrealized

    # --------------------------
    # Hard Daily Stop
    # --------------------------
    if total_pnl <= account.daily_loss_limit:
        raise RiskException(
            f"Daily loss breached (MTM). Total PnL={total_pnl}"
        )

    # --------------------------
    # Max allocation rule (40%)
    # --------------------------
    max_allocation = account.total_capital * 0.40

    if trade_value > max_allocation:
        raise RiskException("Trade exceeds 40% allocation rule")

    # --------------------------
    # Exposure cannot exceed capital
    # --------------------------
    if exposure > account.total_capital:
        raise RiskException("Total exposure exceeds capital")
