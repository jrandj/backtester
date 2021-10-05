import backtrader as bt


class FixedCommissionScheme(bt.CommInfoBase):
    """
    A class that sets the commission for the broker.

    Attributes
    ----------
    params : tuple
        Parameters for the commission scheme.

    Methods
    -------
    _getcommission()
        The method that provides the implementation for calculating the commission.
    """
    # parameters for the commission scheme
    params = (
        ('commission', .0299),
        ('stocklike', True),
        ('commtype', bt.CommInfoBase.COMM_PERC),
    )

    def _getcommission(self, size, price, pseudoexec):
        """The method that provides the implementation for calculating the commission.

        Parameters
        ----------
        size : float
            The number of shares.
        price : float
            The price per share.
        pseudoexec : bool
            Indicates whether the call corresponds to the actual execution of an order.

        Raises
        ------

        """
        return abs(size) * self.p.commission
