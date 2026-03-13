import time
import json
import random
import redis
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "intraday-redis")

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=6379,
    decode_responses=True
)

SYMBOLS = {
    "RELIANCE": 500,
    "INFY": 1500,
    "HDFCBANK": 1600,
}

VOLATILITY = 0.5


def generate_tick(symbol, price):

    change = random.uniform(-VOLATILITY, VOLATILITY)

    new_price = round(price + change, 2)

    if new_price <= 0:
        new_price = price

    return new_price


def simulator_loop():

    logger.info("📈 Market Simulator started")

    prices = SYMBOLS.copy()

    while True:

        for symbol in prices:

            new_price = generate_tick(symbol, prices[symbol])

            prices[symbol] = new_price

            tick = {
                "symbol": symbol,
                "price": new_price,
                "timestamp": datetime.utcnow().isoformat()
            }

            redis_client.publish("price_events", json.dumps(tick))

            logger.info(f"TICK {symbol} {new_price}")

        time.sleep(0.5)


if __name__ == "__main__":
    simulator_loop()
