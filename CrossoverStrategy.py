from pathlib import Path
import backtrader as bt
import csv


class CrossoverStrategy(bt.Strategy):
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
        Handle orders and provide a notification from the broker based on the order.
    prenext()
        The method is used when all data points are not available.
        Very few (if any) periods will have data for every ticker.
    next()
        The method used for all remaining data points once the minimum period of all data/indicators has been met.
    """
    # parameters for the strategy
    params = (
        ('verbose', True),
        ('sma1', 50),
        ('sma2', 200),
        ('log_file', 'backtest.csv')
    )

    def __init__(self):
        """Create any indicators needed for the strategy.

        Parameters
        ----------

        Raises
        ------

        """
        self.o = dict()
        self.inds = dict()
        # add the indicators for each data feed
        for i, d in enumerate(self.datas):
            self.inds[d] = dict()
            self.inds[d]['sma1'] = bt.indicators.SimpleMovingAverage(
                d.close, period=self.params.sma1)
            self.inds[d]['sma2'] = bt.indicators.SimpleMovingAverage(
                d.close, period=self.params.sma2)
            self.inds[d]['cross'] = bt.indicators.CrossOver(self.inds[d]['sma1'], self.inds[d]['sma2'])  # plot=False

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
        """Handle orders and provide a notification from the broker based on the order.

        Parameters
        ----------

        Raises
        ------

        """
        dt, dn = self.datetime.date(), order.data._name

        if order.status == order.Submitted:
            self.log(f'{dn},Order Submitted')
            return
        elif order.status == order.Accepted:
            self.log(f'{dn},Order Accepted')
            return
        elif order.status == order.Completed:
            # allow orders for this ticker again
            self.o[order.data] = None
            if self.p.verbose:
                p = order.executed.price
                v = order.executed.value
                c = order.executed.comm
                if order.isbuy():
                    self.log(f'{dn},BUY executed, Price:{p:.2f}, Cost: {v:.2f}, Comm: {c:.2f}')
                elif order.issell():
                    self.log(f'{dn},SELL executed, Price:{p:.2f}, Cost: {v:.2f}, Comm: {c:.2f}')
        elif order.status == order.Canceled and self.p.verbose:
            self.log(f'{dn},Order Canceled')
        elif order.status == order.Margin and self.p.verbose:
            self.log(f'{dn},Order Margin')
        elif order.status == order.Rejected and self.p.verbose:
            self.log(f'{dn},Order Rejected')
        elif order.status == order.Partial and self.p.verbose:
            self.log(f'{dn},Order Partial')
        elif order.status == order.Expired and self.p.verbose:
            self.log(f'{dn},Order Expired')

    def start(self):
        self.val_start = self.broker.get_cash()
        self.time_start = self.datas[0].datetime.date(1)

    def prenext(self):
        """The method is used when all data points are not available.
        Very few (if any) periods will have data for every ticker.

        Parameters
        ----------

        Raises
        ------

        """
        self.next()

    def next(self):
        """The method is used all data points once the minimum period of all data/indicators has been met.

        Parameters
        ----------

        Raises
        ------

        """
        if self.p.verbose:
            self.log('Cash: ' + str(self.broker.get_cash()) + ' Equity: ' + str(self.broker.get_fundvalue()))
        # dt = self.datetime.date()
        for i, d in enumerate(self.datas):
            dn = d._name
            # if there are no orders already for this ticker
            if not self.o.get(d, None):
                # check the signals
                if self.inds[d]['cross'] == 1:
                    if not self.getposition(d).size:
                        self.o[d] = self.buy(data=d)
                    else:
                        self.log('Cannot buy ' + dn + 'as I am already long')
                elif self.inds[d]['cross'] == -1:
                    if self.getposition(d).size:
                        self.o[d] = self.close(data=d)
                    else:
                        self.log('Cannot sell ' + dn + ' as I am not long')

    def stop(self):
        self.time_end = self.datas[0].datetime.date(0)
        self.time_elapsed = self.time_end - self.time_start
        print('Strategy CAGR: {:.3f}%'.format(
            100 * ((self.broker.get_value() + self.broker.get_cash()) / self.val_start) ** (
                    1 / (self.time_elapsed.days / 365)) - 100))
        print('Strategy Portfolio Value: ' + str(self.broker.get_cash() + self.broker.get_value()))
