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
        Returns the number of shares to purchase.
    """
    params = (
        ('percents', 2),
        ('starting_cash', 1000000),
        ('retint', False)
    )

    def _getsizing(self, comminfo, cash, data, isbuy):
        """Returns the number of shares to purchase.

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
        # use a percentage of the starting cash if possible (to keep the total amount neat)
        if cash > (self.params.starting_cash * self.params.percents) / 100:
            size = (self.params.starting_cash * self.params.percents) / (100 * data.close[0])
        # otherwise use a percentage of the remaining cash
        else:
            size = (100 * cash / data.close[0] * self.params.percents)

        if self.params.retint:
            size = int(size)

        return size
