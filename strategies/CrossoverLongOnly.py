import configparser

from pathlib import Path
import backtrader as bt
import csv


class CrossoverLongOnly(bt.Strategy):
    """
    This strategy uses 2 ETFs to represent long and short positions. Requires that data.bulk is set to False,
    and data.tickers=long_ETF,short_ETF.

    Attributes
    ----------
    cagr : float
        The Compound Annual Growth Rate (CAGR) for the strategy.
    config : configparser.RawConfigParser
        The object that will read configuration from the configuration file.
    d_with_len : list
        The subset of data that is guaranteed to be available.
    elapsed_days : int
        The amount of days between the start and end date.
    end_date : datetime.date
        The ending date of the strategy.
    end_val : float
        The ending value of the strategy.
    inds : dict
        The indicators for all tickers.
    o : dict
        The orders for all tickers.
    params : tuple
        Parameters for the strategy.
    start_date : datetime.date
        The starting date of the strategy.
    start_val : float
        The starting value of the strategy.
    trade_count : int
        The total number of trades executed by the strategy.
    ready_to_buy_short : bool
        A flag used to track when we can open a short position.
    ready_to_buy_long : bool
        A flag used to track when we can open a long position.

    Methods
    -------
    log()
        The logger for the strategy.
    next()
        The method used for all remaining data points once the minimum period of all data/indicators has been met.
    nextstart()
        This method runs exactly once to mark the switch between prenext and next.
    notify_order()
        Handle orders and provide a notification from the broker based on the order.
    notify_trade()
        Handle trades and provide a notification from the broker based on the trade.
    prenext()
        The method is used all data points once the minimum period of all data/indicators has been met.
    start()
        Runs at the start. Records starting portfolio value and time.
    stop()
        Runs when the strategy stops. Record the final value of the portfolio and calculate the CAGR.
    """
    config = configparser.RawConfigParser()
    config.read('config.properties')

    # parameters for the strategy
    params = (
        ('verbose', True),
        ('sma1', int(config['crossover_strategy_long_only_options']['crossover_strategy_long_only_sma1'])),
        ('sma2', int(config['crossover_strategy_long_only_options']['crossover_strategy_long_only_sma2'])),
        ('position_limit', int(config['global_options']['position_limit'])),
        ('plot_tickers', config['global_options']['plot_tickers']),
        ('log_file', 'CrossoverStrategy.csv')
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

        self.inds[0] = dict()
        self.inds[0]['sma1'] = bt.indicators.SimpleMovingAverage(
            self.datas[0].close, period=self.params.sma1)
        self.inds[0]['sma2'] = bt.indicators.SimpleMovingAverage(
            self.datas[0].close, period=self.params.sma2)
        self.inds[0]['cross'] = bt.indicators.CrossOver(self.inds[0]['sma1'], self.inds[0]['sma2'])  # plot=False
        if self.params.plot_tickers == "False":
            self.inds[0]['sma1'].plotinfo.subplot = False
            self.inds[0]['sma2'].plotinfo.subplot = False
            self.inds[0]['cross'].plotinfo.subplot = False
        self.ready_to_buy_short = False
        self.ready_to_buy_long = False

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
        """
        Handle orders and provide a notification from the broker based on the order.

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
        """
        Runs at the start. Records starting portfolio value and time.

        Parameters
        ----------

        Raises
        ------

        """
        # as the strategy requires buying and selling across 2 equities we can only use overlapping dates
        self.start_val = self.broker.get_cash()
        self.start_date = max(self.data.num2date(self.datas[0].datetime.array[0]),
                              self.data.num2date(self.datas[1].datetime.array[0])).date()
        self.end_date = min(self.data.num2date(self.datas[0].datetime.array[-1]),
                            self.data.num2date(self.datas[1].datetime.array[-1])).date()
        print(f"Strategy start date: {self.start_date}")

    def nextstart(self):
        """
        This method runs exactly once to mark the switch between prenext and next.

        Parameters
        ----------

        Raises
        ------

        """
        self.d_with_len = self.datas
        self.next()

    def prenext(self):
        """
        The method is used when all data points are not available.

        Parameters
        ----------

        Raises
        ------

        """
        self.d_with_len = [d for d in self.datas if len(d.array) > 0]
        self.next()

    def next(self):
        """
        The method is used for all data points once the minimum period of all data/indicators has been met.

        Parameters
        ----------

        Raises
        ------

        """
        dt = self.datetime.date()
        if self.start_date <= dt <= self.end_date:
            position_count = 0
            for position in self.broker.positions:
                if self.broker.getposition(position).size > 0:
                    position_count = position_count + 1
            cash_percent = 100 * (self.broker.get_cash() / self.broker.get_value())
            if self.p.verbose:
                self.log(f"Cash: {self.broker.get_cash():.2f}, "
                         f"Equity: {self.broker.get_value() - self.broker.get_cash():.2f} "
                         f"Cash %: {cash_percent:.2f}, Positions: {position_count}", dt)

            for i, d in enumerate(self.d_with_len):
                dn = d._name

                # if there are no orders for either ticker
                if not self.o.get(self.d_with_len[0], None) and not self.o.get(self.d_with_len[1], None):

                    # wait until we have funds
                    if self.ready_to_buy_long and not self.o.get(self.d_with_len[1], None):
                        self.o[self.d_with_len[0]] = self.buy(data=self.d_with_len[0], exectype=bt.Order.Market)
                        self.trade_count = self.trade_count + 1
                        self.ready_to_buy_long = False
                        self.log(f"Buying {self.d_with_len[0]._name} after closing short position", dt)
                    # wait until we have funds
                    elif self.ready_to_buy_short and not self.o.get(self.d_with_len[0], None):
                        self.o[self.d_with_len[1]] = self.buy(data=self.d_with_len[1], exectype=bt.Order.Market)
                        self.trade_count = self.trade_count + 1
                        self.ready_to_buy_short = False
                        self.log(f"Buying {self.d_with_len[1]._name} after closing long position", dt)

                    # buy signal
                    if self.inds[0]['cross'] == 1:
                        self.log(f"Looking at {d._name} with BUY signal", dt)

                        # we are short currently (we are long on the short instrument)
                        if self.getposition(self.d_with_len[1]).size > 0:
                            # close short position and open long position
                            self.log(f"Selling {self.d_with_len[1]._name}", dt)
                            self.o[self.d_with_len[1]] = self.close(data=self.d_with_len[1], exectype=bt.Order.Market)
                            self.trade_count = self.trade_count + 1
                            self.ready_to_buy_long = True

                        # we are long currently so no action is required
                        elif self.getposition(self.d_with_len[0]).size > 0:
                            self.log(f"Cannot action buy signal for {dn} as I am long already", dt)

                        # there is no open position
                        else:
                            self.log(f"Buying {self.d_with_len[0]._name} with no previous position", dt)
                            self.o[self.d_with_len[0]] = self.buy(data=self.d_with_len[0], exectype=bt.Order.Market)
                            self.trade_count = self.trade_count + 1

                    # sell signal
                    elif self.inds[0]['cross'] == -1:
                        self.log(f"Looking at {d._name} with SELL signal", dt)

                        # we are short currently so no action is required
                        if self.getposition(self.d_with_len[1]).size > 0:
                            self.log(f"Cannot action sell signal for {dn} as I am short already", dt)

                        # we are long currently
                        elif self.getposition(self.d_with_len[0]).size > 0:
                            # close long position and open short position
                            self.log(f"Selling {self.d_with_len[0]._name}", dt)
                            self.o[self.d_with_len[0]] = self.close(data=self.d_with_len[0], exectype=bt.Order.Market)
                            self.trade_count = self.trade_count + 1
                            self.ready_to_buy_short = True

                        # there is no open position
                        else:
                            self.log(f"Buying {self.d_with_len[1]._name} with no previous position", dt)
                            self.o[self.d_with_len[1]] = self.buy(data=self.d_with_len[1], exectype=bt.Order.Market)
                            self.trade_count = self.trade_count + 1

    def stop(self):
        """
        Runs when the strategy stops. Record the final value of the portfolio and calculate the CAGR.

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
        self.elapsed_days = (self.end_date - self.start_date).days
        self.end_val = self.broker.get_value()
        self.cagr = 100 * ((self.end_val / self.start_val) ** (
                1 / (self.elapsed_days / 365.25)) - 1)
        print(f"Crossover strategy CAGR: {self.cagr:.4f}% (over {(self.elapsed_days / 365.25):.2f} years "
              f"with {self.trade_count} trades)")
        print(f"Crossover strategy portfolio value: {self.end_val}")

    def notify_trade(self, trade):
        """
        Handle trades and provide a notification from the broker based on the trade.

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
