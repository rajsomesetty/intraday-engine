import redis
import json
import os

REDIS_HOST = os.getenv("REDIS_HOST", "intraday-redis")

r = redis.Redis(host=REDIS_HOST, port=6379)

LAST_PRICE_CACHE = "tick_last_price"


def enqueue_tick(symbol, price):

    try:

        last_price = r.hget(LAST_PRICE_CACHE, symbol)

        if last_price and float(last_price) == float(price):
            return

        r.hset(LAST_PRICE_CACHE, symbol, price)

        r.lpush(
            "tick_queue",
            json.dumps({
                "symbol": symbol,
                "price": price
            })
        )

    except Exception as e:

        print("❌ Tick enqueue failed:", e)

def get_tick_queue_size():

    try:

        return r.llen("tick_queue")

    except Exception:

        return 0
