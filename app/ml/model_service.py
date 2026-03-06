import random
from decimal import Decimal


class MLModelService:

    def __init__(self):

        self.model_loaded = False

    def load_model(self):

        # placeholder for real model loading
        # later you can load sklearn / xgboost / torch model
        self.model_loaded = True

        print("ML model loaded")

    def predict(self, symbol: str, price: Decimal):

        """
        Returns probability of price going up
        """

        if not self.model_loaded:
            self.load_model()

        # placeholder prediction
        prob_up = random.uniform(0, 1)

        return prob_up


ml_model_service = MLModelService()
