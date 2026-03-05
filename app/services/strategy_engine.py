from app.db.session import SessionLocal
from app.services.execution_service import execute_trade

strategies = []


def register_strategy(strategy):

    strategies.append(strategy)


def process_tick(symbol, price):

    for strategy in strategies:

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
