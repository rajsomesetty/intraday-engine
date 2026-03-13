import time
import logging

from app.db.session import SessionLocal
from app.services.execution_service import execute_trade
from app.services.strategy_state_service import register_strategy_state
from app.services.strategy_state_service import is_strategy_enabled
from app.services.execution_model import apply_slippage

logger = logging.getLogger(__name__)

strategies = []

# Global strategy trading switch
strategies_enabled = True


def register_strategy(strategy):

    strategies.append(strategy)

    register_strategy_state(strategy.__class__.__name__)

    logger.info(f"📈 Strategy registered: {strategy.__class__.__name__} {strategy.symbol}")


def disable_all_strategies():

    global strategies_enabled

    strategies_enabled = False

    logger.warning("🛑 All strategies disabled due to volatility")


def enable_all_strategies():

    global strategies_enabled

    strategies_enabled = True

    logger.info("✅ Strategies re-enabled")


def process_tick(symbol, price):

    if not strategies_enabled:
        return

    for strategy in strategies:

        name = strategy.__class__.__name__

        if not is_strategy_enabled(name):
            continue

        if strategy.symbol != symbol:
            continue

        try:

            strategy.on_tick(price)

        except Exception as e:

            logger.error(f"Strategy error [{name}] {symbol}: {e}")


def submit_order(account_id, symbol, side, quantity, price, strategy_name):

    # Basic order validation
    if quantity <= 0:
        logger.warning(f"Invalid order quantity for {symbol}")
        return

    if price <= 0:
        logger.warning(f"Invalid order price for {symbol}")
        return

    db = SessionLocal()

    try:

        # -----------------------------------
        # Apply slippage model
        # -----------------------------------

        price = apply_slippage(price, side)

        # -----------------------------------
        # Generate unique idempotency key
        # -----------------------------------

        ts = int(time.time() * 1000)

        idempotency_key = f"{strategy_name}_{symbol}_{ts}"

        # -----------------------------------
        # Execute trade
        # -----------------------------------

        execute_trade(
            db=db,
            account_id=account_id,
            symbol=symbol,
            quantity=quantity,
            price=price,
            side=side,
            idempotency_key=idempotency_key,
            strategy_name=strategy_name
        )

        logger.info(
            f"Order submitted | strategy={strategy_name} "
            f"symbol={symbol} side={side} qty={quantity} price={price}"
        )

    except Exception as e:

        logger.error(
            f"Order execution failed | strategy={strategy_name} "
            f"symbol={symbol} error={e}"
        )

    finally:

        db.close()
