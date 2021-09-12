from pathlib import Path
import backtrader as bt
import csv


class MLStrategy(bt.Strategy):
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
    params = (('n_positions', 10),
              ('min_positions', 5),
              ('verbose', False),
              ('log_file', 'backtest.csv'))

    def log(self, txt, dt=None):
        """Logger for the strategy.

        Parameters
        ----------

        Raises
        ------

        """
        dt = dt or self.datas[0].datetime.datetime(0)
        with Path(self.p.log_file).open('a') as f:
            log_writer = csv.writer(f)
            log_writer.writerow([dt.isoformat()] + txt.split(','))

    def notify_order(self, order):
        """TBC.

        Parameters
        ----------

        Raises
        ------

        """
        if order.status in [order.Submitted, order.Accepted]:
            return

        # Check if an order has been completed
        # broker could reject order if not enough cash
        if self.p.verbose:
            if order.status in [order.Completed]:
                p = order.executed.price
                if order.isbuy():
                    self.log(f'{order.data._name},BUY executed,{p:.2f}')
                elif order.issell():
                    self.log(f'{order.data._name},SELL executed,{p:.2f}')

            elif order.status in [order.Canceled, order.Margin, order.Rejected]:
                self.log(f'{order.data._name},Order Canceled/Margin/Rejected')

    # bt calls prenext instead of next unless
    # all datafeeds have current values
    # => call next to avoid duplicating logic
    def prenext(self):
        """TBC.

        Parameters
        ----------

        Raises
        ------

        """
        self.next()

    def next(self):
        """TBC.

        Parameters
        ----------

        Raises
        ------

        """
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.datas[0].close[0])
