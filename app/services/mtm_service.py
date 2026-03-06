from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.account import Account
from app.models.position import Position
from app.services.price_feed import get_ltp
from app.services.risk_service import trigger_kill_switch
from app.services.market_data_service import market_data_service

def update_mtm_for_symbol(db: Session, symbol: str):

    positions = (
        db.query(Position)
        .filter(
            Position.symbol == symbol,
            Position.quantity > 0
        )
        .all()
    )

    ltp = market_data_service.get_price(symbol)

    if ltp is None:
        return

    ltp = Decimal(str(ltp))

    for pos in positions:

        entry = Decimal(str(pos.entry_price))
        qty = Decimal(pos.quantity)

        unrealized = (ltp - entry) * qty

        # optional: store unrealized if you track it
        # pos.unrealized_pnl = unrealized

def run_mtm_cycle(db: Session):

    accounts = db.query(Account).all()

    for account in accounts:

        positions = (
            db.query(Position)
            .filter(Position.account_id == account.id)
            .all()
        )

        unrealized = Decimal("0")

        # -----------------------------
        # Calculate Unrealized PnL
        # -----------------------------
        for pos in positions:

            if pos.quantity <= 0:
                continue

            ltp = get_ltp(pos.symbol)

            unrealized += (
                (Decimal(ltp) - Decimal(pos.entry_price))
                * Decimal(pos.quantity)
            )

        # -----------------------------
        # Update Account Equity
        # -----------------------------
        account.current_equity = account.total_capital + unrealized
        account.daily_pnl = unrealized

        # -----------------------------
        # Update Peak Equity
        # -----------------------------
        if account.current_equity > account.intraday_peak_equity:
            account.intraday_peak_equity = account.current_equity

        drawdown = (
            account.intraday_peak_equity
            - account.current_equity
        )

        # -----------------------------
        # Risk Check (Drawdown)
        # -----------------------------
        if drawdown >= Decimal("1500"):
            trigger_kill_switch(account, "MTM drawdown breach")

        # -----------------------------
        # Store Equity Snapshot
        # -----------------------------
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
