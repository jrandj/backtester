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
        ('stocklike', True),
        ('commtype', bt.CommInfoBase.COMM_FIXED),
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
        value = abs(size) * price
        if value <= 5000:
            return 14.95
        elif 5000 < value < 20000:
            return 19.95
        else:
            return 0.0011 * value
