from pathlib import Path
import backtrader as bt
import csv


class MLStrategy(bt.Strategy):
    """
    A class that contains the trading strategy.

    Attributes
    ----------
    params : tuple
        Parameters for the strategy.

    Methods
    -------
    log()
        The logger for the strategy.
    notify_order()
        Provide a notification from the broker based on the order.
    prenext()
        The method used for data points before the minimum period of all data/indicators has been met.
    next()
        The method used for all remaining data points once the minimum period of all data/indicators has been met.
    """
    # parameters for the strategy
    params = (
        ('verbose', True),
        ('sma1', 50),
        ('sma2', 200),
        ('log_file', 'backtest.csv'))

    def __init__(self):
        """Create any indicators needed for the strategy.

        Parameters
        ----------

        Raises
        ------

        """
        self.inds = dict()
        # add the indicators for each data feed
        for i, d in enumerate(self.datas):
            self.inds[d] = dict()
            self.inds[d]['sma1'] = bt.indicators.SimpleMovingAverage(
                d.close, period=self.params.sma1)
            self.inds[d]['sma2'] = bt.indicators.SimpleMovingAverage(
                d.close, period=self.params.sma2)
            self.inds[d]['cross'] = bt.indicators.CrossOver(self.inds[d]['sma1'], self.inds[d]['sma2'], plot=False)

    def log(self, txt, dt=None):
        """The logger for the strategy.

        Parameters
        ----------

        Raises
        ------

        """
        dt = dt or self.datas[0].datetime.datetime(0)
        with Path(self.p.log_file).open('a', newline='', encoding='utf-8') as f:
            log_writer = csv.writer(f)
            log_writer.writerow([dt.isoformat()] + txt.split('~'))

    def notify_order(self, order):
        """Provide a notification from the broker based on the order.

        Parameters
        ----------

        Raises
        ------

        """
        if order.status in [order.Submitted, order.Accepted]:
            return

        # check if an order has been completed, broker could reject order if not enough cash
        if self.p.verbose:
            if order.status in [order.Completed]:
                p = order.executed.price
                if order.isbuy():
                    self.log(f'{order.data._name},BUY executed,{p:.2f}')
                elif order.issell():
                    self.log(f'{order.data._name},SELL executed,{p:.2f}')

            elif order.status in [order.Canceled, order.Margin, order.Rejected]:
                self.log(f'{order.data._name},Order Canceled/Margin/Rejected')

    def next(self):
        """The method used for all remaining data points once the minimum period of all data/indicators has been met.

        Parameters
        ----------

        Raises
        ------

        """
        for i, d in enumerate(self.datas):
            # dt, dn = self.datetime.date(), d._name

            # check if we are in the market already
            if not self.getposition(d).size:
                # buy if sma1 > sma2
                if self.inds[d]['cross'][0] == 1:
                    self.buy(data=d)
                # go short if sma1 < sma2 (commented out as not considering short selling)
                # elif self.inds[d]['cross'][0] == -1:
                # self.sell(data=d)
            # this means are are already have a position
            else:
                if self.inds[d]['cross'][0] == -1:
                    self.close(data=d)


                # # buy if sma1 > sma2, but we are already in so have to close the position
                # # it doesn't make sense to close and buy again (without short positions) - leave for now
                # if self.inds[d]['cross'][0] == 1:
                #     self.close(data=d)
                #     self.buy(data=d)
                # # close and go short if sma1 < sma2 (commented out as not considering short selling)
                # elif self.inds[d]['cross'][0] == -1:
                #     self.close(data=d)
                #     # self.sell(data=d)
        # self.log('Close, %.2f' % self.datas[0].close[0])
