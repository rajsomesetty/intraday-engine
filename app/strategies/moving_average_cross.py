from collections import deque
from decimal import Decimal
import time
import logging

from app.strategies.base_strategy import BaseStrategy
from app.services.strategy_engine import submit_order
from app.services.position_sizing_service import calculate_position_size
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


class MovingAverageCross(BaseStrategy):

    def __init__(self, symbol, account_id):

        super().__init__(symbol, account_id)

        self.short_window = deque(maxlen=2)
        self.long_window = deque(maxlen=4)

        # prevent rapid-fire orders
        self.last_trade_time = 0
        self.cooldown_seconds = 5

    def on_tick(self, price):

        price = Decimal(str(price))

        self.short_window.append(price)
        self.long_window.append(price)

        if len(self.long_window) < 4:
            return

        short_ma = sum(self.short_window) / len(self.short_window)
        long_ma = sum(self.long_window) / len(self.long_window)

        logger.info(f"Strategy check → short:{short_ma} long:{long_ma}")

        # cooldown protection
        now = time.time()
        if now - self.last_trade_time < self.cooldown_seconds:
            return

        # -----------------------------------
        # BUY SIGNAL
        # -----------------------------------

        if short_ma >= long_ma:

            logger.info("Strategy BUY signal")

            entry_price = price
            stop_loss = price * Decimal("0.98")

            db = SessionLocal()

            try:

                qty = calculate_position_size(
                    db=db,
                    account_id=self.account_id,
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    risk_per_trade=Decimal("0.01"),
                )

            except Exception as e:

                logger.error(f"Position sizing failed: {e}")
                db.close()
                return

            db.close()

            if qty > 0:

                submit_order(
                    account_id=self.account_id,
                    symbol=self.symbol,
                    side="BUY",
                    quantity=int(qty),
                    price=float(price),
                    strategy_name="MovingAverageCross",
                )

                self.last_trade_time = now

        # -----------------------------------
        # SELL SIGNAL
        # -----------------------------------

        else:

            logger.info("Strategy SELL signal")

            submit_order(
                account_id=self.account_id,
                symbol=self.symbol,
                side="SELL",
                quantity=1,
                price=float(price),
                strategy_name="MovingAverageCross",
            )

            self.last_trade_time = now
