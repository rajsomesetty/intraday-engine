from decimal import Decimal

from app.ml.model_service import ml_model_service
from app.services.strategy_engine import submit_order


BUY_THRESHOLD = 0.70
SELL_THRESHOLD = 0.30


def process_ml_signal(symbol: str, price: float):

    probability = ml_model_service.predict(symbol, Decimal(str(price)))

    if probability >= BUY_THRESHOLD:

        submit_order(
            account_id=1,
            symbol=symbol,
            side="BUY",
            quantity=1,
            price=price,
            strategy_name="ML_STRATEGY",
        )

    elif probability <= SELL_THRESHOLD:

        submit_order(
            account_id=1,
            symbol=symbol,
            side="SELL",
            quantity=1,
            price=price,
            strategy_name="ML_STRATEGY",
        )
