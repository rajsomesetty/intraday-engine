import redis
import json
import os
import threading
import time

from app.db.session import SessionLocal
from app.services.execution_service import execute_trade

REDIS_HOST = os.getenv("REDIS_HOST", "intraday-redis")

r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)


def start_execution_worker():

    worker_id = threading.get_ident()

    print(f"⚙️ Execution worker started [{worker_id}]")

    while True:

        try:

            # -----------------------------------
            # Wait for next order
            # -----------------------------------

            result = r.brpop("execution_queue")

            if not result:
                continue

            _, data = result

            try:
                order = json.loads(data)
            except Exception:
                print(f"❌ Worker {worker_id} invalid order payload:", data)
                continue

            db = SessionLocal()

            try:

                execute_trade(
                    db=db,
                    account_id=order["account_id"],
                    symbol=order["symbol"],
                    quantity=order["quantity"],
                    price=order["price"],
                    side=order["side"],
                    idempotency_key=order["idempotency_key"],
                    strategy_name=order.get("strategy_name")
                )

            except Exception as e:

                db.rollback()
                print(f"❌ Worker {worker_id} execution failed:", e)

            finally:

                db.close()

        except redis.exceptions.ConnectionError as e:

            print(f"❌ Worker {worker_id} Redis connection lost:", e)

            time.sleep(2)

        except Exception as e:

            print(f"❌ Worker {worker_id} unexpected error:", e)

            time.sleep(1)
