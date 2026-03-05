class BaseStrategy:

    def __init__(self, symbol, account_id):

        self.symbol = symbol
        self.account_id = account_id

    def on_tick(self, price):
        """
        Called whenever market price updates
        """
        raise NotImplementedError
