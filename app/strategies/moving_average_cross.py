from collections import deque
from decimal import Decimal

from app.strategies.base_strategy import BaseStrategy
from app.services.strategy_engine import submit_order
from app.services.position_sizing_service import calculate_position_size


class MovingAverageCross(BaseStrategy):

    def __init__(self, symbol, account_id):

        super().__init__(symbol, account_id)

        self.short_window = deque(maxlen=2)
        self.long_window = deque(maxlen=4)

    def on_tick(self, price):

        price = Decimal(str(price))

        self.short_window.append(price)
        self.long_window.append(price)

        if len(self.long_window) < 4:
            return

        short_ma = sum(self.short_window) / len(self.short_window)
        long_ma = sum(self.long_window) / len(self.long_window)

        print(f"Strategy check → short:{short_ma} long:{long_ma}")

        # BUY SIGNAL
        if short_ma >= long_ma:

            print("Strategy BUY signal")

            entry_price = price
            stop_loss = price * Decimal("0.98")

            qty = calculate_position_size(
                account_id=self.account_id,
                entry_price=entry_price,
                stop_loss=stop_loss,
                risk_per_trade=Decimal("0.01"),
            )

            if qty > 0:

                submit_order(
                    account_id=self.account_id,
                    symbol=self.symbol,
                    side="BUY",
                    quantity=qty,
                    price=float(price),
                    strategy_name="MovingAverageCross",
                )

        # SELL SIGNAL
        else:

            print("Strategy SELL signal")

            submit_order(
                account_id=self.account_id,
                symbol=self.symbol,
                side="SELL",
                quantity=1,
                price=float(price),
                strategy_name="MovingAverageCross",
            )
