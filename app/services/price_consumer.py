import redis
import json
import os

from app.db.session import SessionLocal
from app.services.price_feed import update_price

REDIS_HOST = os.getenv("REDIS_HOST", "intraday-redis")

r = redis.Redis(host=REDIS_HOST, port=6379)


def start_price_listener():

    pubsub = r.pubsub()
    pubsub.subscribe("market_prices")

    for message in pubsub.listen():

        if message["type"] != "message":
            continue

        data = json.loads(message["data"])

        event_id = data["event_id"]
        symbol = data["symbol"]
        price = data["price"]

        db = SessionLocal()

        try:

            existing = db.execute(
                "SELECT 1 FROM event_log WHERE event_id=:id",
                {"id": event_id}
            ).fetchone()

            if existing:
                continue

            update_price(symbol, price)

            db.execute(
                """
                INSERT INTO event_log(event_id, event_type)
                VALUES (:id,'PRICE_UPDATE')
                """,
                {"id": event_id}
            )

            db.commit()

        finally:
            db.close()
