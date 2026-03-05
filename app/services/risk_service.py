from typing import List, Dict
from decimal import Decimal

from app.models.risk_config import RiskConfig


class RiskException(Exception):
    pass

def trigger_kill_switch(account, reason):
    """
    Disable trading for account and record breach reason
    """
    account.is_trading_enabled = False
    account.breach_count = (account.breach_count or 0) + 1
    account.last_breach_reason = reason

def enforce_risk(
    account,
    simulated_positions: List[Dict],
    trade_value,
    ltp_map,
    simulated_daily_pnl,
):
    """
    Enforce risk based on simulated post-trade state.
    """

    session = account._sa_instance_state.session

    # ------------------------------
    # Load Risk Config
    # ------------------------------
    risk_config = (
        session.query(RiskConfig)
        .filter(RiskConfig.account_id == account.id)
        .first()
    )

    if not risk_config:
        raise RiskException(
            f"Risk config missing for account {account.id}"
        )

    # ------------------------------
    # Kill Switch
    # ------------------------------
    if not account.is_trading_enabled:
        raise RiskException("Trading disabled due to prior risk breach")

    # ------------------------------
    # Exposure Calculation
    # ------------------------------
    exposure = Decimal("0")

    for pos in simulated_positions:
        qty = Decimal(pos["quantity"])
        avg = Decimal(str(pos["average_price"]))
        exposure += qty * avg

    exposure_after_trade = exposure + Decimal(trade_value)

    # --------------------------------
    # Symbol Concentration Rule
    # --------------------------------

    symbol = simulated_positions[-1]["symbol"]

    symbol_exposure = Decimal("0")

    for pos in simulated_positions:
        if pos["symbol"] == symbol:
            qty = Decimal(pos["quantity"])
            avg = Decimal(str(pos["average_price"]))
            symbol_exposure += qty * avg

    max_symbol_exposure = (
        account.total_capital *
        Decimal(risk_config.max_exposure_pct) /
        Decimal("100")
    )

    if symbol_exposure > max_symbol_exposure:
        raise RiskException(
            f"Symbol exposure exceeds limit for {symbol}"
        )

    # ------------------------------
    # Unrealized MTM
    # ------------------------------
    unrealized = Decimal("0")

    for pos in simulated_positions:
        qty = Decimal(pos["quantity"])

        if qty <= 0:
            continue

        avg_price = Decimal(str(pos["average_price"]))
        ltp_value = ltp_map.get(pos["symbol"])

        if ltp_value is None:
            symbol_ltp = avg_price
        else:
            symbol_ltp = Decimal(str(ltp_value))

        unrealized += (symbol_ltp - avg_price) * qty

    # ------------------------------
    # Total PnL
    # ------------------------------
    total_pnl = Decimal(simulated_daily_pnl) + unrealized

    # ------------------------------
    # Simulated Equity
    # ------------------------------
    account.current_equity = account.total_capital + total_pnl

    if account.current_equity > account.intraday_peak_equity:
        account.intraday_peak_equity = account.current_equity

    drawdown = account.intraday_peak_equity - account.current_equity

    # ------------------------------
    # Drawdown Stop
    # ------------------------------
    daily_loss_limit = Decimal(risk_config.daily_loss_limit)

    if drawdown >= daily_loss_limit:
        trigger_kill_switch(account, "Intraday drawdown breached")

        raise RiskException(
            f"Intraday drawdown breached. Drawdown={drawdown}"
        )

    # ------------------------------
    # Hard Daily Stop
    # ------------------------------

    if total_pnl <= -daily_loss_limit:
        trigger_kill_switch(account, "Daily loss limit breached")

        raise RiskException(
            f"Daily loss breached (MTM). Total PnL={total_pnl}"
        )

    # ------------------------------
    # Max Open Positions
    # ------------------------------
    open_positions = [
        pos for pos in simulated_positions
        if Decimal(pos["quantity"]) > 0
    ]

    if len(open_positions) >= risk_config.max_open_positions:
        raise RiskException(
            "Max open positions limit reached"
        )

    # ------------------------------
    # Max Allocation
    # ------------------------------
    max_allocation = (
        account.total_capital *
        Decimal(risk_config.max_allocation_pct) /
        Decimal("100")
    )

    if Decimal(trade_value) > max_allocation:
        raise RiskException(
            "Trade exceeds max allocation rule"
        )

    # ------------------------------
    # Max Exposure
    # ------------------------------
    max_exposure = (
        account.total_capital *
        Decimal(risk_config.max_exposure_pct) /
        Decimal("100")
    )

    if exposure_after_trade > max_exposure:
        raise RiskException(
            "Total exposure exceeds allowed limit"
        )

    # ------------------------------
    # Return Metrics
    # ------------------------------
    return {
        "equity": account.current_equity,
        "drawdown": drawdown,
        "total_pnl": total_pnl,
    }
