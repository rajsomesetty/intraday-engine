from collections import deque

from app.strategies.base_strategy import BaseStrategy
from app.services.strategy_engine import submit_order


class MovingAverageCross(BaseStrategy):

    def __init__(self, symbol, account_id):

        super().__init__(symbol, account_id)

        # Smaller windows for backtest testing
        self.short_window = deque(maxlen=2)
        self.long_window = deque(maxlen=4)

    def on_tick(self, price):

        # Store price history
        self.short_window.append(price)
        self.long_window.append(price)

        # Wait until enough ticks arrive
        if len(self.long_window) < 4:
            return

        short_ma = sum(self.short_window) / len(self.short_window)
        long_ma = sum(self.long_window) / len(self.long_window)

        print(f"Strategy check → short:{short_ma} long:{long_ma}")

        # Allow equality to trigger for testing
        if short_ma >= long_ma:

            print("Strategy BUY signal")

            submit_order(
                account_id=self.account_id,
                symbol=self.symbol,
                side="BUY",
                quantity=1,
                price=price,
                strategy_name="MovingAverageCross"
            )

        else:

            print("Strategy SELL signal")

            submit_order(
                account_id=self.account_id,
                symbol=self.symbol,
                side="SELL",
                quantity=1,
                price=price,
                strategy_name="MovingAverageCross"
            )
