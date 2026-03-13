import redis
import json
import os
import time
import logging

from app.db.session import SessionLocal
from app.services.stop_loss_service import check_stop_losses
from app.services.volatility_guard import check_volatility
from app.ml.ml_signal_engine import process_ml_signal
from app.services.market_data_service import market_data_service

logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "intraday-redis")

# Dedicated Redis clients
queue_redis = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
pubsub_redis = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

BATCH_SIZE = 20
EMPTY_SLEEP = 0.01


def create_pubsub():
    """Create a fresh pubsub connection."""
    pubsub = pubsub_redis.pubsub()
    pubsub.subscribe("price_events")
    return pubsub


def start_tick_worker():

    logger.info("📊 Tick worker started")

    pubsub = create_pubsub()

    while True:

        try:

            # -----------------------------------
            # Receive simulator ticks
            # -----------------------------------

            message = pubsub.get_message(ignore_subscribe_messages=True)

            if message:

                try:

                    tick = json.loads(message["data"])

                    queue_redis.rpush(
                        "tick_queue",
                        json.dumps(tick)
                    )

                except Exception as e:

                    logger.error(f"Tick decode error: {e}")

            # -----------------------------------
            # Batch processing
            # -----------------------------------

            ticks = []

            for _ in range(BATCH_SIZE):

                data = queue_redis.lpop("tick_queue")

                if not data:
                    break

                try:
                    ticks.append(json.loads(data))
                except Exception:
                    continue

            if not ticks:

                time.sleep(EMPTY_SLEEP)
                continue

            db = SessionLocal()

            try:

                for tick in ticks:

                    symbol = tick["symbol"]
                    price = tick["price"]

                    # Update price cache
                    market_data_service.update_price(symbol, price)

                    # Volatility guard
                    check_volatility(symbol, price)

                    # Stop loss engine
                    check_stop_losses(symbol, price)

                    # ML signal engine
                    try:
                        process_ml_signal(symbol, price)
                    except Exception as e:
                        logger.error(f"ML engine error: {e}")

            finally:

                db.close()

        except redis.exceptions.ConnectionError as e:

            logger.error(f"Redis connection lost: {e}")

            time.sleep(1)

            pubsub = create_pubsub()

        except Exception as e:

            logger.error(f"Tick worker loop error: {e}")

            time.sleep(0.1)
