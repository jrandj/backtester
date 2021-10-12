from pathlib import Path
import backtrader as bt
import csv


class Benchmark(bt.Strategy):
    """
    A class that contains the trading strategy for buying and holding the index.

    Attributes
    ----------
    params : tuple
        The local parameters for the strategy.
    start_val : float
        The starting value of the strategy.
    end_val : float
        The ending value of the strategy.
    start_date : datetime.date
        The starting date of the strategy.
    end_date : datetime.date
        The ending date of the strategy.
    elapsed_days : int
        The amount of days between the start and end date.
    cagr : float
        The Compound Annual Growth Rate (CAGR) for the strategy.

    Methods
    -------
    log()
        The logger for the strategy.
    nextstart()
        Runs exactly once when the minimum period has been met. Buy the index with all cash.
    notify_order()
        Handle orders and provide a notification from the broker based on the order.
    stop()
        Runs when the strategy stops. Record the final value of the portfolio and calculate the CAGR.
    """
    params = (
        ('verbose', True),
        ('log_file', 'benchmark.csv')
    )

    def log(self, txt, dt=None):
        """The logger for the strategy.

        Parameters
        ----------
        txt : str
            The text to be logged.
        dt : NoneType
            The date which is typically passed by the client.

        Raises
        ------

        """
        dt = dt or self.datas[0].datetime.date
        with Path(self.p.log_file).open('a', newline='', encoding='utf-8') as f:
            log_writer = csv.writer(f)
            log_writer.writerow([dt.isoformat()] + txt.split('~'))

    def nextstart(self):
        """Runs exactly once when the minimum period has been met. Buy the index with all cash.

        Parameters
        ----------

        Raises
        ------

        """
        dt = self.datetime.date()
        self.start_val = self.broker.get_cash()
        self.start_date = self.datas[0].datetime.date(1)
        print("Benchmark start date: " + str(self.start_date))

        # estimate commission based on today's close price
        if self.broker.get_cash() <= 5000:
            commission = 14.95
        elif 5000 < self.broker.get_cash() < 20000:
            commission = 19.95
        else:
            commission = 0.0011 * self.broker.get_cash()
        size = int((self.broker.get_cash() - commission) / self.data)

        # attempt to account for slippage against tomorrow's open
        size = int(0.995 * size)
        self.log(f'Creating Buy order with price {self.data.lines.close[0]}, size {size}, '
                 'and commission {commission}', dt)
        self.o = self.buy(size=size)

    def notify_order(self, order):
        """Handle orders and provide a notification from the broker based on the order.

        Parameters
        ----------
        order : backtrader.order.BuyOrder
            The order object.

        Raises
        ------

        """
        dt, dn = self.datetime.date(), order.data._name
        if order.isbuy():
            order_type = 'BUY'
        else:
            order_type = 'SELL'
        executed_price = order.executed.price
        executed_value = order.executed.value
        executed_commission = order.executed.comm
        created_price = order.created.price
        created_value = order.created.value
        created_commission = order.created.comm
        self.log(
            f'{dn},{order_type} executed,Status: {order.getstatusname()},Executed Price: {executed_price:.6f},'
            f'Executed Value: {executed_value:.6f},Executed Commission: {executed_commission:.6f},'
            f'Created Price: {created_price:.6f},Created Value: {created_value:.6f},'
            f'Created Commission: {created_commission:.6f}', dt)

    def stop(self):
        """Runs when the strategy stops. Record the final value of the portfolio and calculate the CAGR.

        Parameters
        ----------

        Raises
        ------

        """
        self.end_date = self.datas[0].datetime.date(0)
        print("Benchmark end date: " + str(self.end_date))
        self.elapsed_days = (self.end_date - self.start_date).days
        self.end_val = self.broker.get_value()
        self.cagr = 100 * ((self.end_val / self.start_val) ** (
                1 / (self.elapsed_days / 365.25)) - 1)
        print(f'Benchmark CAGR: {self.cagr:.4f}% (over {(self.elapsed_days / 365.25):.2f} years)')
        print('Benchmark Portfolio Value: ' + str(self.end_val))
