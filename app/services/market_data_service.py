from threading import Lock


class MarketDataService:
    """
    Simple in-memory LTP cache.
    Thread-safe.
    """

    def __init__(self):
        self._ltp_map = {}
        self._lock = Lock()

    def update_price(self, symbol: str, price: float):
        with self._lock:
            self._ltp_map[symbol] = price

    def get_price(self, symbol: str):
        with self._lock:
            return self._ltp_map.get(symbol)

    def get_all_prices(self):
        with self._lock:
            return dict(self._ltp_map)


# Global singleton
market_data_service = MarketDataService()
