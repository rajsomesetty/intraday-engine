from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.account import Account
from app.models.position import Position
from app.services.market_data_service import market_data_service
from app.services.risk_service import trigger_kill_switch


MAX_DRAWDOWN_LIMIT = Decimal("50000")


def update_mtm_for_symbol(db: Session, symbol: str):
    """
    Compatibility function for tick_worker and market_replay_service.

    MTM is now handled globally by run_mtm_cycle() via scheduler.
    This function simply ensures the latest market price is present
    and avoids breaking older modules that import it.
    """
    return


def run_mtm_cycle(db: Session):

    accounts = db.query(Account).all()

    for account in accounts:

        positions = (
            db.query(Position)
            .filter(Position.account_id == account.id)
            .all()
        )

        unrealized = Decimal("0")

        # -----------------------------------
        # Calculate Unrealized PnL
        # -----------------------------------

        for pos in positions:

            if pos.quantity <= 0:
                continue

            ltp = market_data_service.get_price(pos.symbol)

            # Skip symbols with no price
            if ltp is None:
                continue

            ltp = Decimal(str(ltp))

            if ltp <= 0:
                continue

            entry = Decimal(str(pos.entry_price))
            qty = Decimal(pos.quantity)

            unrealized += (ltp - entry) * qty

        # -----------------------------------
        # Realized PnL already tracked
        # -----------------------------------

        realized = Decimal(str(account.daily_pnl or 0))

        total_pnl = realized + unrealized

        # -----------------------------------
        # Update Equity
        # -----------------------------------

        account.current_equity = account.total_capital + total_pnl

        # -----------------------------------
        # Update Peak Equity
        # -----------------------------------

        if account.intraday_peak_equity is None:
            account.intraday_peak_equity = account.current_equity

        if account.current_equity > account.intraday_peak_equity:
            account.intraday_peak_equity = account.current_equity

        drawdown = account.intraday_peak_equity - account.current_equity

        # -----------------------------------
        # Debug Logs
        # -----------------------------------

        print(
            "MTM | account:",
            account.id,
            "| equity:",
            account.current_equity,
            "| peak:",
            account.intraday_peak_equity,
            "| drawdown:",
            drawdown,
        )

        # -----------------------------------
        # Risk Check
        # -----------------------------------

        if drawdown >= MAX_DRAWDOWN_LIMIT:

            trigger_kill_switch(
                account,
                f"MTM drawdown breach: {drawdown}"
            )

        # -----------------------------------
        # Store Equity Snapshot
        # -----------------------------------

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
