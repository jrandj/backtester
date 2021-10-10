import backtrader as bt


class CustomSizer(bt.Sizer):
    """
    A class that contains the logic for the order sizing.

    Attributes
    ----------
    params : tuple
        Parameters for the sizer.

    Methods
    -------
    _getsizing()
        Returns the number of shares to purchase. Attempts to use 1/50th of the available cash.
    """
    params = (
        ('percents', 2),
        ('starting_cash', 1000000),
        ('retint', False)
    )

    def _getsizing(self, comminfo, cash, data, isbuy):
        """Returns the number of shares to purchase. Attempts to use 1/50th of the available cash.

        Parameters
        ----------
        comminfo : CustomCommissionScheme.CustomCommissionScheme
            The commission scheme.
        cash : float
            The available cash.
        data : TickerData.TickerData
            The asset being considered for the order.
        isbuy : bool
            A flag indicating if the order is a buy order.

        Raises
        ------

        """
        if cash > self.params.starting_cash / 50:
            size = (self.params.starting_cash / 50) / data.close[0]
        else:
            size = cash / data.close[0] * (self.params.percents / 100)

        if self.params.retint:
            size = int(size)

        return size
