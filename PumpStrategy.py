from pathlib import Path
import backtrader as bt
import csv


class PumpStrategy(bt.Strategy):
    """
    A class that contains the trading strategy.

    Attributes
    ----------
    params : tuple
        Parameters for the strategy.
    o : dict
        The orders for all tickers.
    inds : dict
        The indicators for all tickers.
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
    d_with_len : list
        The subset of data that is guaranteed to be available.

    Methods
    -------
    log()
        The logger for the strategy.
    notify_order()
        Handle orders and provide a notification from the broker based on the order.
    start()
        Runs at the start. Records starting portfolio value and time.
    prenext()
        The method is used all data points once the minimum period of all data/indicators has been met.
    nextstart()
        This method runs exactly once to mark the switch between prenext and next.
    next()
        The method used for all remaining data points once the minimum period of all data/indicators has been met.
    stop()
        Runs when the strategy stops. Record the final value of the portfolio and calculate the CAGR.
    notify_trade()
        Handle trades and provide a notification from the broker based on the trade.
    """
    # parameters for the strategy
    params = (
        ('verbose', True),
        ('volume_average_period', 20),
        ('price_average_period', 365),
        ('volume_factor', 8),
        ('position_limit', 50),
        ('profit_factor', 1.8),
        ('log_file', 'PumpStrategy.csv')
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
        for i, d in enumerate(self.datas):
            self.inds[d] = dict()
            self.inds[d]['volume_average'] = bt.indicators.SimpleMovingAverage(d.volume,
                                                                               period=self.params.volume_average_period)
            self.inds[d]['price_max'] = bt.indicators.Highest(d.close, period=self.params.price_average_period)

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

        if order.status == order.Completed:
            self.log(f'{dn},Completed with slippage (executed_price/created_price)'
                     f': {100 * (executed_price / created_price):.2f}%', dt)

        # allow orders again based on certain order statuses
        if order.status in [order.Partial, order.Margin, order.Expired, order.Completed, order.Rejected]:
            self.o[order.data] = None
            self.log(f'{dn} order available again as status was {order.getstatusname()}', dt)

    def start(self):
        """Runs at the start. Records starting portfolio value and time.

        Parameters
        ----------

        Raises
        ------

        """
        self.start_val = self.broker.get_cash()
        start_date = self.datas[0].datetime.date(1)
        for data in self.datas:
            if data.datetime.date(1) < start_date:
                start_date = data.datetime.date(1)
        self.start_date = start_date
        print("Pump strategy start date: " + str(self.start_date))

    def nextstart(self):
        """This method runs exactly once to mark the switch between prenext and next.

        Parameters
        ----------

        Raises
        ------

        """
        self.d_with_len = self.datas
        self.next()

    def prenext(self):
        """The method is used when all data points are not available.

        Parameters
        ----------

        Raises
        ------

        """
        self.d_with_len = [d for d in self.datas if len(d)]
        self.next()

    def next(self):
        """The method is used all data points once the minimum period of all data/indicators has been met.

        Parameters
        ----------

        Raises
        ------

        """
        dt = self.datetime.date()
        position_count = 0
        for position in self.broker.positions:
            if self.broker.getposition(position).size > 0:
                position_count = position_count + 1
        cash_percent = 100 * (self.broker.get_cash() / self.broker.get_value())
        # if self.p.verbose:
        #     self.log(f'Cash: {self.broker.get_cash():.2f}, '
        #              f'Equity: {self.broker.get_value() - self.broker.get_cash():.2f} '
        #              f'Cash %: {cash_percent:.2f}, Positions: {position_count}', dt)
        for i, d in enumerate(self.d_with_len):
            dn = d._name
            # self.log(f'{dn} has close: {d.close[0]} and open {d.open[0]}', dt)
            # if there are no orders already for this ticker
            if not self.o.get(d, None):
                # check for buy signal
                if len(d.close.get(size=1, ago=-1)) > 0:
                    condition_a = self.params.volume_factor * d.volume[0] > self.inds[d]['volume_average'][0]
                    condition_b = 0.95 < (d.high[0] / d.close.get(size=1, ago=-1)[0]) < 1.10
                    condition_c = d.close[0] >= self.inds[d]['price_max'][0]
                    self.log(f"{dn}: {condition_a} {condition_b} {condition_c}", dt)
                    self.log(f"{dn}: condition_a details: "
                             f"{d.volume[0] * self.params.volume_factor} > {self.inds[d]['volume_average'][0]}", dt)
                    self.log(f"{dn}: condition_b details: {(d.high[0] / d.close.get(size=1, ago=-1)[0])}", dt)
                    self.log(f"{dn}: condition_c details: {d.close[0]} >= {self.inds[d]['price_max'][0]}", dt)

                    if condition_a and condition_b and condition_c:
                        if not self.getposition(d).size:
                            if position_count < self.params.position_limit:
                                self.o[d] = self.buy(data=d)
                            else:
                                self.log(
                                    'Cannot buy ' + dn + ' as I have ' + str(position_count) + ' positions already',
                                    dt)
                        else:
                            self.log('Cannot buy ' + dn + ' as I am already long', dt)

            # take profit
            if self.getposition(data=d).size:
                if d.close[0] >= self.params.profit_factor * self.getposition(data=d).price:
                    self.o[d] = self.close(data=d)

    def stop(self):
        """Runs when the strategy stops. Record the final value of the portfolio and calculate the CAGR.

        Parameters
        ----------

        Raises
        ------

        """
        end_date = self.datas[0].datetime.date(0)
        for data in self.datas:
            if data.datetime.date(0) > end_date:
                end_date = data.datetime.date(0)
        self.end_date = end_date
        print("Pump strategy end date: " + str(self.end_date))

        self.elapsed_days = (self.end_date - self.start_date).days
        self.end_val = self.broker.get_value()
        self.cagr = 100 * ((self.end_val / self.start_val) ** (
                1 / (self.elapsed_days / 365.25)) - 1)
        print(f'Pump strategy CAGR: {self.cagr:.4f}% (over {(self.elapsed_days / 365.25):.2f} years)')
        print('Pump strategy Portfolio Value: ' + str(self.end_val))

    def notify_trade(self, trade):
        """Handle trades and provide a notification from the broker based on the trade.

        Parameters
        ----------
        trade : backtrader.trade.Trade
            The trade object.

        Raises
        ------

        """
        dt = self.datetime.date()
        if trade.isclosed:
            self.log("Position in " + trade.data._name + " opened on " + str(trade.open_datetime().date())
                     + " and closed on " + str(trade.close_datetime().date()) + " with PnL Gross " + str(
                round(trade.pnl, 2))
                     + " and PnL Net " + str(round(trade.pnlcomm, 1)), dt)
