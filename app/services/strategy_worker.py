import redis
import json
import os

from app.services.strategy_engine import process_tick

REDIS_HOST = os.getenv("REDIS_HOST", "intraday-redis")

r = redis.Redis(host=REDIS_HOST, port=6379)


def start_strategy_worker():

    print("🧠 Strategy worker started")

    while True:

        _, data = r.brpop("tick_queue")

        tick = json.loads(data)

        symbol = tick["symbol"]
        price = tick["price"]

        process_tick(symbol, price)
