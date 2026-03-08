import redis
import json
import os
import time

from app.db.session import SessionLocal
from app.services.stop_loss_service import check_stop_losses
from app.services.volatility_guard import check_volatility
from app.ml.ml_signal_engine import process_ml_signal
from app.services.market_data_service import market_data_service


REDIS_HOST = os.getenv("REDIS_HOST", "intraday-redis")

r = redis.Redis(host=REDIS_HOST, port=6379)

# Number of ticks processed per batch
BATCH_SIZE = 20

# Sleep when queue empty (prevents CPU spin)
EMPTY_SLEEP = 0.01


def start_tick_worker():

    print("📊 Tick worker started")

    while True:

        ticks = []

        # -----------------------------------
        # Fetch batch from Redis
        # -----------------------------------

        for _ in range(BATCH_SIZE):

            data = r.lpop("tick_queue")

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

                # -----------------------------------
                # Update Market Price Cache
                # -----------------------------------

                market_data_service.update_price(symbol, price)

                # -----------------------------------
                # Flash Crash Protection
                # -----------------------------------

                check_volatility(symbol, price)

                # -----------------------------------
                # Stop Loss Engine
                # -----------------------------------

                check_stop_losses(symbol, price)

                # -----------------------------------
                # ML Signal Engine
                # -----------------------------------

                try:
                    process_ml_signal(symbol, price)
                except Exception as e:
                    print("❌ ML engine error:", e)

        except Exception as e:

            print("❌ Tick worker error:", e)

        finally:

            db.close()
