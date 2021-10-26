import configparser

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
    config = configparser.RawConfigParser()
    config.read('config.properties')

    params = (
        ('percents', float(config['global_options']['position_size'])),
        ('starting_cash', float(config['broker']['cash'])),
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
            size = (cash * self.params.percents) / (data.close[0] * 100)

        if self.params.retint:
            size = int(size)

        return size
