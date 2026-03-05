import csv
import time
import os
from decimal import Decimal

from app.services.price_feed import update_price


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")


def replay_market_data(file_name: str = "sample_prices.csv", speed: float = 1.0):

    file_path = os.path.join(DATA_DIR, file_name)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dataset not found: {file_path}")

    print(f"Starting backtest using {file_path}")

    with open(file_path) as f:

        reader = csv.DictReader(f)

        for row in reader:

            symbol = row["symbol"]
            price = Decimal(row["price"])

            update_price(symbol, price)

            print(f"Replay tick → {symbol} {price}")

            time.sleep(1 / speed)

    print("Backtest finished")
