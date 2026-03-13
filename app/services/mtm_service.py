from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

from app.models.account import Account
from app.models.position import Position
from app.services.market_data_service import market_data_service
from app.services.risk_service import trigger_kill_switch

logger = logging.getLogger(__name__)

MAX_DRAWDOWN_LIMIT = Decimal("50000")


def update_mtm_for_symbol(db: Session, symbol: str):
    return


def run_mtm_cycle(db: Session):

    accounts = db.query(Account).all()

    for account in accounts:

        positions = (
            db.query(Position)
            .filter(
                Position.account_id == account.id,
                Position.quantity > 0
            )
            .all()
        )

        unrealized = Decimal("0")

        for pos in positions:

            try:
                ltp = market_data_service.get_price(pos.symbol)
            except Exception:
                continue

            if not ltp:
                continue

            ltp = Decimal(str(ltp))
            entry = Decimal(str(pos.entry_price))
            qty = Decimal(str(pos.quantity))

            unrealized += (ltp - entry) * qty

        realized = Decimal(str(account.daily_pnl or 0))

        total_pnl = realized + unrealized

        account.current_equity = account.total_capital + total_pnl

        if account.intraday_peak_equity is None:
            account.intraday_peak_equity = account.current_equity

        if account.current_equity > account.intraday_peak_equity:
            account.intraday_peak_equity = account.current_equity

        drawdown = (
            account.intraday_peak_equity - account.current_equity
        ).quantize(Decimal("0.01"))

        logger.info(
            f"MTM account={account.id} equity={account.current_equity} drawdown={drawdown}"
        )

        drawdown_limit = Decimal(
            str(account.max_intraday_drawdown or MAX_DRAWDOWN_LIMIT)
        )

        if drawdown >= drawdown_limit and account.is_trading_enabled:

            trigger_kill_switch(
                account,
                f"MTM drawdown breach: {drawdown}"
            )

        db.execute(
            text("""
                INSERT INTO equity_history(account_id, equity)
                SELECT :account_id, :equity
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM equity_history
                    WHERE account_id = :account_id
                    AND created_at > now() - interval '60 seconds'
                )
            """),
            {
                "account_id": account.id,
                "equity": account.current_equity
            }
        )

    db.commit()
