import csv
import time
import os
from decimal import Decimal

from sqlalchemy import text

from app.db.session import SessionLocal
from app.services.price_feed import update_price
from app.services.tick_queue import enqueue_tick
from app.services.mtm_service import update_mtm_for_symbol
from app.services.stop_loss_service import check_stop_losses
from app.services.volatility_guard import check_volatility


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")


def replay_market_data(file_name: str = "sample_prices.csv", speed: float = 1.0):

    file_path = os.path.join(DATA_DIR, file_name)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dataset not found: {file_path}")

    print(f"📊 Starting backtest using {file_path}")

    with open(file_path) as f:

        reader = csv.DictReader(f)

        for row in reader:

            symbol = row["symbol"]
            price = Decimal(row["price"])

            db = SessionLocal()

            try:

                # -----------------------------------
                # Update Market Price
                # -----------------------------------

                price_changed = update_price(symbol, price)

                if not price_changed:
                    db.close()
                    continue

                print(f"Replay tick → {symbol} {price}")

                # -----------------------------------
                # Strategy Pipeline
                # -----------------------------------

                enqueue_tick(symbol, float(price))

                # -----------------------------------
                # Flash Crash Protection
                # -----------------------------------

                try:
                    check_volatility(symbol, float(price))
                except Exception as e:
                    print("Volatility guard error:", e)

                # -----------------------------------
                # Update MTM
                # -----------------------------------

                update_mtm_for_symbol(db, symbol)

                # -----------------------------------
                # Stop Loss Engine
                # -----------------------------------

                try:
                    check_stop_losses(symbol, float(price))
                except Exception as e:
                    print("Stop loss monitor error:", e)

                db.commit()

            except Exception as e:

                db.rollback()
                print("Backtest tick failed:", e)

            finally:

                db.close()

            # -----------------------------------
            # Replay Speed
            # -----------------------------------

            time.sleep(1 / speed)

    print("✅ Backtest finished")
