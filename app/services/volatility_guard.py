from collections import deque
from decimal import Decimal
import time

from app.services.strategy_engine import disable_all_strategies

# Track recent prices
price_history = {}

WINDOW_SECONDS = 10
MAX_MOVE_PCT = Decimal("5")  # 5%


def check_volatility(symbol: str, price: Decimal):

    now = time.time()

    history = price_history.setdefault(symbol, deque())

    history.append((now, price))

    # remove old entries
    while history and now - history[0][0] > WINDOW_SECONDS:
        history.popleft()

    if len(history) < 2:
        return

    first_price = history[0][1]

    move_pct = abs(price - first_price) / first_price * 100

    if move_pct >= MAX_MOVE_PCT:

        print(
            f"🚨 Volatility guard triggered for {symbol} "
            f"{move_pct:.2f}% move in {WINDOW_SECONDS}s"
        )

        disable_all_strategies()
