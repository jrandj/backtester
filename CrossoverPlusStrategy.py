import configparser

from pathlib import Path
import backtrader as bt
import csv


class CrossoverPlusStrategy(bt.Strategy):
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
    trade_count : int
        The total number of trades executed by the strategy.

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
    config = configparser.RawConfigParser()
    config.read('config.properties')

    # parameters for the strategy
    params = (
        ('verbose', True),
        ('sma1', int(config['crossover_plus_strategy_options']['crossover_plus_sma1'])),
        ('sma2', int(config['crossover_plus_strategy_options']['crossover_plus_sma2'])),
        ('RSI_period', int(config['crossover_plus_strategy_options']['RSI_period'])),
        ('RSI_crossover_low', int(config['crossover_plus_strategy_options']['RSI_crossover_low'])),
        ('RSI_crossover_high', int(config['crossover_plus_strategy_options']['RSI_crossover_high'])),
        ('position_limit', int(config['global_options']['position_limit'])),
        ('plot_tickers', config['global_options']['plot_tickers']),
        ('log_file', 'CrossoverPlusStrategy.csv')
    )

    def __init__(self):
        """Create any indicators needed for the strategy.

        Parameters
        ----------

        Raises
        ------

        """
        self.trade_count = 0
        self.o = dict()
        self.inds = dict()
        # add the indicators for each data feed
        for i, d in enumerate(self.datas):
            self.inds[d] = dict()
            self.inds[d]['sma1'] = bt.indicators.SimpleMovingAverage(
                d.close, period=self.params.sma1)
            self.inds[d]['sma2'] = bt.indicators.SimpleMovingAverage(
                d.close, period=self.params.sma2)
            self.inds[d]['RSI'] = bt.indicators.RSI(d.close, period=self.params.RSI_period, safediv=True)
            self.inds[d]['PPO'] = bt.indicators.PercentagePriceOscillator(d.close)
            if self.params.plot_tickers == "False":
                self.inds[d]['sma1'].plotinfo.subplot = False
                self.inds[d]['sma2'].plotinfo.subplot = False
                self.inds[d]['RSI'].plotinfo.subplot = False
                self.inds[d]['PPO'].plotinfo.subplot = False

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
            f"{dn},{order_type} executed,Status: {order.getstatusname()},Executed Price: {executed_price:.6f},"
            f"Executed Value: {executed_value:.6f},Executed Commission: {executed_commission:.6f},"
            f"Created Price: {created_price:.6f},Created Value: {created_value:.6f},"
            f"Created Commission: {created_commission:.6f}", dt)

        if order.status == order.Completed:
            self.log(f"{dn},Completed with slippage (executed_price/created_price)"
                     f": {100 * (executed_price / created_price):.2f}%", dt)

        # allow orders again based on certain order statuses
        if order.status in [order.Partial, order.Margin, order.Expired, order.Completed, order.Rejected]:
            self.o[order.data] = None
            self.log(f"{dn} order available again as status was {order.getstatusname()}", dt)

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
        print(f"Strategy start date: {self.start_date}")

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
        """The method is used for all data points once the minimum period of all data/indicators has been met.

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
        #     self.log(f"Cash: {self.broker.get_cash():.2f}, "
        #              f"Equity: {self.broker.get_value() - self.broker.get_cash():.2f} "
        #              f"Cash %: {cash_percent:.2f}, Positions: {position_count}", dt)
        for i, d in enumerate(self.d_with_len):
            dn = d._name
            # self.log(f"{dn} has close: {d.close[0]} and open {d.open[0]}", dt)
            # if there are no orders already for this ticker
            if not self.o.get(d, None):
                # check the signals
                if self.inds[d]['sma1'] >= self.inds[d]['sma2'] \
                        and self.inds[d]['RSI'] <= self.params.RSI_crossover_low and self.inds[d]['PPO'] > 0:
                    if not self.getposition(d).size:
                        if position_count < self.params.position_limit:
                            # self.log(f"Buying {dn} with close: {d.close[0]} or open {d.open[0]}", dt)
                            # self.o[d] = [self.buy(data=d), d.close.get(size=1, ago=-1)[0]]
                            self.o[d] = self.buy(data=d, exectype=bt.Order.Market)
                            self.trade_count = self.trade_count + 1
                        else:
                            self.log(f"Cannot buy {dn} as I have {position_count} positions already", dt)
                    else:
                        self.log(f"Cannot buy {dn} as I already long", dt)
                elif self.inds[d]['sma1'] < self.inds[d]['sma2'] \
                        and self.inds[d]['RSI'] >= self.params.RSI_crossover_high and self.inds[d]['PPO'] < 0:
                    if self.getposition(d).size:
                        self.o[d] = self.close(data=d, exectype=bt.Order.Market)
                        self.trade_count = self.trade_count + 1
                    else:
                        self.log(f"Cannot sell {dn} as I am not long", dt)

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
        print(f"Strategy end date: {self.end_date}")
        # print(f"sma1 {self.params.sma1} sma2 {self.params.sma2} RSI_period {self.params.RSI_period} "
        #       f"RSI_crossover_low {self.params.RSI_crossover_low} RSI_crossover_high {self.params.RSI_crossover_high}")
        self.elapsed_days = (self.end_date - self.start_date).days
        self.end_val = self.broker.get_value()
        self.cagr = 100 * ((self.end_val / self.start_val) ** (
                1 / (self.elapsed_days / 365.25)) - 1)
        print(f"Strategy CAGR: {self.cagr:.4f}% (over {(self.elapsed_days / 365.25):.2f} years "
              f"with {self.trade_count} trades)")
        print(f"Strategy portfolio value: {self.end_val}")

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
            self.log(f"Position in {trade.data._name} opened on {trade.open_datetime().date()} and closed "
                     f"on {trade.close_datetime().date()} with PnL Gross {trade.pnl:.2f} and PnL Net "
                     f"{trade.pnlcomm:.2f}", dt)
