from typing import List, Dict
from decimal import Decimal

from app.models.risk_config import RiskConfig
from app.services.portfolio_heat_service import check_portfolio_heat


class RiskException(Exception):
    pass


def trigger_kill_switch(account, reason):

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

    session = account._sa_instance_state.session

    risk_config = (
        session.query(RiskConfig)
        .filter(RiskConfig.account_id == account.id)
        .first()
    )

    if not risk_config:
        raise RiskException(
            f"Risk config missing for account {account.id}"
        )

    if not account.is_trading_enabled:
        raise RiskException("Trading disabled due to prior risk breach")

    # ------------------------------
    # Exposure
    # ------------------------------
    exposure = Decimal("0")

    for pos in simulated_positions:
        qty = Decimal(pos["quantity"])
        avg = Decimal(str(pos["average_price"]))
        exposure += qty * avg

    exposure_after_trade = exposure + Decimal(trade_value)

    # ------------------------------
    # Portfolio Heat Check
    # ------------------------------
    new_trade_risk = Decimal("0")

    last_pos = simulated_positions[-1]

    if last_pos.get("stop_loss"):

        risk_per_share = abs(
            Decimal(str(last_pos["average_price"]))
            - Decimal(str(last_pos["stop_loss"]))
        )

        new_trade_risk = risk_per_share * Decimal(last_pos["quantity"])

        allowed = check_portfolio_heat(
            session,
            account.id,
            new_trade_risk,
        )

        if not allowed:
            raise RiskException("Portfolio heat exceeded")

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

    total_pnl = Decimal(simulated_daily_pnl) + unrealized

    account.current_equity = account.total_capital + total_pnl

    if account.current_equity > account.intraday_peak_equity:
        account.intraday_peak_equity = account.current_equity

    drawdown = account.intraday_peak_equity - account.current_equity

    daily_loss_limit = Decimal(risk_config.daily_loss_limit)

    if drawdown >= daily_loss_limit:
        trigger_kill_switch(account, "Intraday drawdown breached")
        raise RiskException("Intraday drawdown breached")

    if total_pnl <= -daily_loss_limit:
        trigger_kill_switch(account, "Daily loss limit breached")
        raise RiskException("Daily loss breached")

    return {
        "equity": account.current_equity,
        "drawdown": drawdown,
        "total_pnl": total_pnl,
    }
