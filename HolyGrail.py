import configparser

from pathlib import Path
import backtrader as bt
import csv


class HolyGrail(bt.Strategy):
    """
    This is an implementation of the "Holy Grail" trading strategy documented at
    https://tradingstrategyguides.com/holy-grail-trading-strategy/.

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
    entry_point : int
        TBC.
    stop_loss : int
        TBC.
    trailing_stop : int
        TBC.
    local_max : int
        TBC

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
        ('log_file', 'HolyGrail.csv')
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

        for i, d in enumerate(self.datas):
            self.inds[d] = dict()
            self.inds[d]['adx'] = bt.indicators.AverageDirectionalMovementIndex(d).lines.adx
            self.inds[d]['ema'] = bt.indicators.ExponentialMovingAverage(d.close, period=20)
            self.inds[d]['ema_slope'] = self.inds[d]['ema'] - self.inds[d]['ema'](-1)
            self.inds[d]['local_max'] = bt.indicators.Highest(d.high, period=20)
            self.inds[d]['local_min'] = bt.indicators.Lowest(d.low, period=20)

            if self.params.plot_tickers == "False":
                self.inds[d]['adx'].plotinfo.subplot = False
                self.inds[d]['ema'].plotinfo.subplot = False
                self.inds[d]['ema_slope'].plotinfo.subplot = False
                self.inds[d]['local_max'].plotinfo.subplot = False
                self.inds[d]['local_min'].plotinfo.subplot = False

        self.entry_point_long = None
        self.stop_loss_long = None
        self.entry_point_short = None
        self.stop_loss_short = None
        self.trailing_stop = None
        self.local_max = None
        self.local_min = None
        self.short_days = 0
        self.long_days = 0

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

        start_date = self.data.num2date(self.datas[0].datetime.array[0])
        end_date = self.data.num2date(self.datas[0].datetime.array[-1])
        for d in self.datas:
            start_date = max(start_date, self.data.num2date(d.datetime.array[0]))
            end_date = min(end_date, self.data.num2date(d.datetime.array[-1]))

        self.start_date = start_date.date()
        self.end_date = end_date.date()
        print(f"HolyGrail start date: {self.start_date} and end date: {self.end_date}")

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

                # track if we are long or short
                if self.getposition(d).size > 0:
                    self.long_days = self.long_days + 1
                elif self.getposition(d).size < 0:
                    self.short_days = self.short_days + 1

                # if there are no orders already
                if not self.o.get(d, None):
                    # if we are long consider setting the trailing stop from a recent (20 day) local maximum
                    if self.getposition(d).size > 0 and not self.trailing_stop and d.close[0] > self.local_max:
                        self.trailing_stop = d.close[0]
                        self.log(f"Long in {dn} and setting a trailing stop of {self.trailing_stop}", dt)

                    # if we are short consider setting the trailing stop from a recent (20 day) local minimum
                    elif self.getposition(d).size < 0 and not self.trailing_stop and d.close[0] < self.local_min:
                        self.trailing_stop = d.close[0]
                        self.log(f"Short in {dn} and setting a trailing stop of {self.trailing_stop}", dt)

                    # handle closing if we have a short position already
                    if self.getposition(d).size < 0:
                        # we have closed above our stop loss
                        if self.stop_loss_short is not None and d.close[0] > self.stop_loss_short:
                            self.o[d] = self.close(data=d, exectype=bt.Order.Market)
                            self.trade_count = self.trade_count + 1
                            self.log(f"Closing short position as price {d.close[0]} is above our stop "
                                     f"loss of {self.stop_loss_short}", dt)
                            self.local_min = None
                            self.stop_loss_short = None

                        # we have exceeded our trailing stop threshold and the close has dropped below the EMA
                        elif self.trailing_stop is not None and self.trailing_stop < d.close[0] < self.inds[d]['ema'][
                            0]:
                            self.o[d] = self.close(data=d, exectype=bt.Order.Market)
                            self.trade_count = self.trade_count + 1
                            self.log(f"Closing short position as price {d.close[0]} is below our trailing stop of"
                                     f" {self.trailing_stop} "
                                     f"and dropped below the EMA of {self.inds[d]['ema'][0]}", dt)
                            self.local_min = None
                            self.trailing_stop = None

                    # handle closing if we have a long position already
                    elif self.getposition(d).size > 0:
                        # we have closed below our stop loss
                        if self.stop_loss_long is not None and d.close[0] < self.stop_loss_long:
                            self.o[d] = self.close(data=d, exectype=bt.Order.Market)
                            self.trade_count = self.trade_count + 1
                            self.log(f"Closing long position as price {d.close[0]} is below our stop "
                                     f"loss of {self.stop_loss_long}", dt)
                            self.local_max = None
                            self.stop_loss_long = None

                        # we have exceeded our trailing stop threshold and the close has dropped below the EMA
                        elif self.trailing_stop is not None and self.trailing_stop < d.close[0] < self.inds[d]['ema'][
                            0]:
                            self.o[d] = self.close(data=d, exectype=bt.Order.Market)
                            self.trade_count = self.trade_count + 1
                            self.log(f"Closing long position as price {d.close[0]} exceeds our trailing stop of"
                                     f" {self.trailing_stop} and dropped below the EMA of {self.inds[d]['ema'][0]}", dt)
                            self.local_min = None
                            self.trailing_stop = None

                    # handle buy/sell
                    elif self.getposition(d).size == 0:

                        # kill the tags if adx is below 30
                        if self.inds[d]['adx'][0] <= 30:
                            if self.entry_point_long:
                                self.entry_point_long = None
                            if self.entry_point_short:
                                self.entry_point_short = None

                        # adx is above 30
                        else:
                            # the ema is touched from below, so we set an entry point for going short
                            if d.close[0] < self.inds[d]['ema'][0] < d.high[0]:
                                self.stop_loss_short = d.high[0]
                                self.entry_point_short = d.low[0]
                                self.log(f"Considering going short for {dn} as the EMA has been touched from below, "
                                         f"setting stop loss at {self.stop_loss_short} (low) and an entry point of "
                                         f"{self.entry_point_short} (high)", dt)

                            # the ema is touched from above, so we set an entry point for going long
                            if d.low[0] < self.inds[d]['ema'][0] < d.close[0]:
                                self.stop_loss_long = d.low[0]
                                self.entry_point_long = d.high[0]
                                self.log(f"Considering going long for {dn} as the EMA has been touched from above, "
                                         f"setting stop loss at {self.stop_loss_long} (low) and an entry point of "
                                         f"{self.entry_point_long} (high)", dt)

                            # sell as we have gone below the entry point and remain below the EMA
                            if d.close[0] < self.inds[d]['ema'][0] and self.entry_point_short \
                                    is not None and d.close[0] < self.entry_point_short:
                                self.o[d] = self.sell(data=d, exectype=bt.Order.Market)
                                self.trade_count = self.trade_count + 1
                                self.local_min = self.inds[d]['local_min'][0]
                                self.log(
                                    f"For {dn} selling as close {d.close[0]} has dropped below the entry point of"
                                    f" {self.entry_point_short}, setting local min of {self.local_min}", dt)
                                self.entry_point_short = None

                            # buy as we have gone above the entry point and remain above the EMA
                            if d.close[0] > self.inds[d]['ema'][0] and self.entry_point_long \
                                    is not None and d.close[0] > self.entry_point_long:
                                self.o[d] = self.buy(data=d, exectype=bt.Order.Market)
                                self.trade_count = self.trade_count + 1
                                self.local_max = self.inds[d]['local_max'][0]
                                self.log(
                                    f"For {dn} buying as close {d.close[0]} has exceeded the entry point of"
                                    f" {self.entry_point_long}, setting local max of {self.local_max}", dt)
                                self.entry_point_long = None

    def stop(self):
        """
        Runs when the strategy stops. Record the final value of the portfolio and calculate the CAGR.

        Parameters
        ----------

        Raises
        ------

        """
        print(f"HolyGrail end date: {self.end_date}")
        self.elapsed_days = (self.end_date - self.start_date).days
        self.end_val = self.broker.get_value()
        self.cagr = 100 * ((self.end_val / self.start_val) ** (
                1 / (self.elapsed_days / 365.25)) - 1)
        print(f"HolyGrail CAGR: {self.cagr:.4f}% (over {(self.elapsed_days / 365.25):.2f} years "
              f"with {self.trade_count} trades). Long {round((self.long_days/self.elapsed_days)*100, 2)}% and short "
              f"{round((self.short_days/self.elapsed_days)*100, 2)}%, for a total of "
              f"{round(((self.long_days+self.short_days)/self.elapsed_days)*100, 2)}%.")
        print(f"HolyGrail portfolio value: {self.end_val}")

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
