import redis
import json
import os

from sqlalchemy import text

from app.db.session import SessionLocal
from app.services.price_feed import update_price
from app.services.tick_queue import enqueue_tick

REDIS_HOST = os.getenv("REDIS_HOST", "intraday-redis")

r = redis.Redis(host=REDIS_HOST, port=6379)


def start_price_listener():

    pubsub = r.pubsub()
    pubsub.subscribe("market_prices")

    print("📡 Listening for market price events...")

    for message in pubsub.listen():

        if message["type"] != "message":
            continue

        try:

            data = json.loads(message["data"])

            event_id = data["event_id"]
            symbol = data["symbol"]
            price = data["price"]

        except Exception as e:

            print("❌ Invalid price event:", e)
            continue

        db = SessionLocal()

        try:

            # Idempotency check
            existing = db.execute(
                text("SELECT 1 FROM event_log WHERE event_id=:id"),
                {"id": event_id}
            ).fetchone()

            if existing:
                continue

            # Update cached price
            price_changed = update_price(symbol, price)

            if not price_changed:
                continue

            # Push tick to processing queue
            enqueue_tick(symbol, price)

            # Record event
            db.execute(
                text("""
                    INSERT INTO event_log(event_id, event_type)
                    VALUES (:id,'PRICE_UPDATE')
                """),
                {"id": event_id}
            )

            db.commit()

        except Exception as e:

            db.rollback()
            print("❌ Price consumer failed:", e)

        finally:

            db.close()
