from app.db.session import SessionLocal
from app.services.execution_service import execute_trade
from app.services.strategy_state_service import register_strategy_state
from app.services.strategy_state_service import is_strategy_enabled

strategies = []

def register_strategy(strategy):

    strategies.append(strategy)

    register_strategy_state(strategy.__class__.__name__)

def process_tick(symbol, price):

    for strategy in strategies:

        name = strategy.__class__.__name__

        if not is_strategy_enabled(name):
            continue

        if strategy.symbol == symbol:
            strategy.on_tick(price)


def submit_order(account_id, symbol, side, quantity, price, strategy_name):

    db = SessionLocal()

    try:

        execute_trade(
            db=db,
            account_id=account_id,
            symbol=symbol,
            quantity=quantity,
            price=price,
            side=side,
            idempotency_key=f"{strategy_name}_{symbol}_{price}",
            strategy_name=strategy_name
        )

    finally:

        db.close()
