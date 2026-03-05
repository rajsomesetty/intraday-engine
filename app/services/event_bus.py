import redis
import json
import uuid
import os

REDIS_HOST = os.getenv("REDIS_HOST", "intraday-redis")

r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)


def publish_price(symbol, price):

    event = {
        "event_id": str(uuid.uuid4()),
        "type": "PRICE_UPDATE",
        "symbol": symbol,
        "price": price
    }

    r.publish("market_prices", json.dumps(event))
