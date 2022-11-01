import backtrader as bt


class CustomCommissionScheme(bt.CommInfoBase):
    """
    A class that sets the commission for the broker.

    Attributes:
        params: Tuple.
            Parameters for the strategy.
    """

    # parameters for the commission scheme
    params = (
        ('stocklike', True),
        ('commtype', bt.CommInfoBase.COMM_FIXED)
    )

    def _getcommission(self, size, price, pseudoexec):
        """
        The method that provides the implementation for calculating the commission.

        :param size: The number of shares.
        :type size: Float.
        :param price: The price per share.
        :type price:  Float.
        :param pseudoexec: Indicates whether the call corresponds to the actual execution of an order.
        :type pseudoexec: Bool.
        :return: The commission to be paid.
        :rtype: Float.
        """
        value = abs(size) * price
        if value < 1000:
            return 9.95
        elif value <= 5000:
            return 14.95
        elif value <= 20000:
            return 19.95
        else:
            return 0.0011 * value
