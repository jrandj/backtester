import backtrader as bt


class FixedCommissionScheme(bt.CommInfoBase):
    """
    TBC.

    Attributes
    ----------
    TBC : TBC
        TBC.

    Methods
    -------
    TBC()
        TBC.
    """
    params = (
        ('commission', .02),
        ('stocklike', True),
        ('commtype', bt.CommInfoBase.COMM_FIXED),
    )

    def _getcommission(self, size, price, pseudoexec):
        """TBC.

        Parameters
        ----------

        Raises
        ------

        """
        return abs(size) * self.p.commission
