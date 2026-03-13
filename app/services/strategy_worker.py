import redis
import json
import os
import time
import logging

from app.services.strategy_engine import process_tick

logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "intraday-redis")

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=6379,
    decode_responses=True
)

RECONNECT_SLEEP = 1


def start_strategy_worker():

    logger.info("🧠 Strategy worker started")

    while True:

        try:

            # -----------------------------------
            # Wait for tick from queue
            # -----------------------------------

            result = redis_client.brpop("tick_queue")

            if not result:
                continue

            _, data = result

            # -----------------------------------
            # Parse tick
            # -----------------------------------

            try:
                tick = json.loads(data)
            except Exception as e:
                logger.error(f"Invalid tick format: {e}")
                continue

            symbol = tick.get("symbol")
            price = tick.get("price")

            if not symbol or price is None:
                logger.warning(f"Malformed tick: {tick}")
                continue

            # -----------------------------------
            # Run strategy engine
            # -----------------------------------

            try:
                process_tick(symbol, price)

            except Exception as e:
                # Strategy errors must NEVER crash worker
                logger.error(f"Strategy error for {symbol}: {e}")

        except redis.exceptions.ConnectionError as e:

            logger.error(f"Redis connection lost: {e}")
            time.sleep(RECONNECT_SLEEP)

        except Exception as e:

            logger.error(f"Strategy worker unexpected error: {e}")
            time.sleep(0.5)
