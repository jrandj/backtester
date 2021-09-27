from pathlib import Path
import backtrader as bt
import csv


class Benchmark(bt.Strategy):
    """
    A class that contains the trading strategy for buying and holding the index.

    Attributes
    ----------
    roi : TBC
        TBC.

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

    params = (
        ('verbose', True),
        ('log_file', 'benchmark.csv'))

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

    def start(self):
        self.val_start = self.broker.get_cash()
        self.time_start = self.datas[0].datetime.date(1)

    def nextstart(self):
        size = int(self.broker.get_cash() / self.data)
        self.buy(size=size)

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

    def stop(self):
        self.time_end = self.datas[0].datetime.date(0)
        self.time_elapsed = self.time_end - self.time_start
        print('Benchmark CAGR: {:.3f}%'.format(
            100 * ((self.broker.get_value() + self.broker.get_cash()) / self.val_start) ** (
                    1 / (self.time_elapsed.days / 365)) - 100))
        print('Benchmark Portfolio Value: ' + str(self.broker.get_cash() + self.broker.get_value()))
