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
        ('adx_period', int(config['holygrail_strategy_options']['adx_period'])),
        ('ema_long_period', int(config['holygrail_strategy_options']['ema_long_period'])),
        ('ema_short_period', int(config['holygrail_strategy_options']['ema_short_period'])),
        ('bounce_off_min', float(config['holygrail_strategy_options']['bounce_off_min'])),
        ('bounce_off_max', float(config['holygrail_strategy_options']['bounce_off_max'])),
        ('position_limit', int(config['global_options']['position_limit'])),
        ('lag_days', int(config['holygrail_strategy_options']['lag_days'])),
        ('plot_tickers', config['global_options']['plot_tickers']),
        ('log_file', 'HolyGrail.csv')
    )

    def __init__(self):
        """
        Create any indicators needed for the strategy.

        Parameters
        ----------

        Raises
        ------

        """
        self.trade_count = 0
        self.o = dict()
        self.inds = dict()
        self.entry_point_long = dict()
        self.stop_loss_long = dict()
        self.entry_point_short = dict()
        self.stop_loss_short = dict()
        self.trailing_stop = dict()
        self.local_max = dict()
        self.local_min = dict()
        self.short_days = dict()
        self.long_days = dict()
        self.waiting_days_short = dict()
        self.waiting_days_long = dict()

        for i, d in enumerate(self.datas):
            dn = d._name
            self.inds[d] = dict()
            self.inds[d]['adx'] = bt.indicators.AverageDirectionalMovementIndex(d, period=self.params.adx_period)
            self.inds[d]['ema_long'] = bt.indicators.ExponentialMovingAverage(d.close,
                                                                              period=self.params.ema_long_period)
            self.inds[d]['ema_short'] = bt.indicators.ExponentialMovingAverage(d.close,
                                                                               period=self.params.ema_short_period)
            self.inds[d]['ema_long_slope'] = self.inds[d]['ema_long'] - self.inds[d]['ema_long'](-1)
            self.inds[d]['ema_short_slope'] = self.inds[d]['ema_short'] - self.inds[d]['ema_short'](-1)
            # self.inds[d]['ema_long_ROC'] = bt.indicators.ROC100(self.inds[d]['ema_long'],
            #                                                     period=self.params.ema_short_period)
            self.inds[d]['local_max'] = bt.indicators.Highest(d.high, period=self.params.adx_period)
            self.inds[d]['local_min'] = bt.indicators.Lowest(d.low, period=self.params.adx_period)

            self.entry_point_long[d] = None
            self.stop_loss_long[d] = None
            self.entry_point_short[d] = None
            self.stop_loss_short[d] = None
            self.trailing_stop[d] = None
            self.local_max[d] = None
            self.local_min[d] = None
            self.waiting_days_short[d] = 0
            self.waiting_days_long[d] = 0

            if self.params.plot_tickers == "False":
                self.inds[d]['adx'].plotinfo.subplot = False
                self.inds[d]['ema_long'].plotinfo.subplot = False
                # self.inds[d]['ema_long_slope'].plotinfo.subplot = False
                # self.inds[d]['ema_short_slope'].plotinfo.subplot = False
                self.inds[d]['ema_short'].plotinfo.subplot = False
                # self.inds[d]['ema_long_ROC'].plotinfo.subplot = False
                self.inds[d]['local_max'].plotinfo.subplot = False
                self.inds[d]['local_min'].plotinfo.subplot = False

    def log(self, txt, dt=None):
        """
        The logger for the strategy.

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
        self.start_val = self.broker.get_cash()
        start_date = self.data.num2date(self.datas[0].datetime.array[0])
        end_date = self.data.num2date(self.datas[0].datetime.array[-1])

        for d in self.datas:
            start_date = min(start_date, self.data.num2date(d.datetime.array[0]))
            end_date = max(end_date, self.data.num2date(d.datetime.array[-1]))

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
        self.d_with_len = [d for d in self.datas if len(d)]
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
            # self.log(f"For {dn} long slope is: {round(self.inds[d]['ema_long_slope'][0], 3)} and short slope is "
            #          f"{round(self.inds[d]['ema_short_slope'][0], 3)}", dt)

            # track if we are long or short
            if self.getposition(d).size > 0:
                self.long_days[d] = self.long_days.get(d, 0) + 1
            elif self.getposition(d).size < 0:
                self.short_days[d] = self.short_days.get(d, 0) + 1

            # if there are no orders already
            if not self.o.get(d, None):
                # if we are long consider setting the trailing stop from a recent (20 day) local maximum
                if self.getposition(d).size > 0 and not self.trailing_stop[d] and self.local_max[d] is not None and \
                        d.close[0] > self.local_max[d]:
                    self.trailing_stop[d] = d.close[0]
                    self.log(f"Long in {dn} and setting a trailing stop of {self.trailing_stop[d]}", dt)

                # if we are short consider setting the trailing stop from a recent (20 day) local minimum
                elif self.getposition(d).size < 0 and not self.trailing_stop[d] and self.local_min[d] is not None and \
                        d.close[0] < self.local_min[d]:
                    self.trailing_stop[d] = d.close[0]
                    self.log(f"Short in {dn} and setting a trailing stop of {self.trailing_stop[d]}", dt)

                # handle closing if we have a short position already
                if self.getposition(d).size < 0:
                    # we have closed above our stop loss
                    if self.stop_loss_short[d] is not None and d.close[0] > self.stop_loss_short[d]:
                        self.o[d] = self.close(data=d, exectype=bt.Order.Market)
                        self.trade_count = self.trade_count + 1
                        self.log(f"Closing short position as price {d.close[0]} is above our stop "
                                 f"loss of {self.stop_loss_short[d]}", dt)
                        self.local_min[d] = None
                        self.stop_loss_short[d] = None

                    # we have exceeded our trailing stop threshold and the close has dropped below the EMA
                    elif self.trailing_stop[d] is not None and self.trailing_stop[d] > d.close[0] > \
                            self.inds[d]['ema_long'][0]:
                        self.o[d] = self.close(data=d, exectype=bt.Order.Market)
                        self.trade_count = self.trade_count + 1
                        self.log(f"Closing short position as price {d.close[0]} is below our trailing stop of"
                                 f" {self.trailing_stop[d]} and went above the EMA of {self.inds[d]['ema_long'][0]}",
                                 dt)
                        self.local_min[d] = None
                        self.trailing_stop[d] = None

                # handle closing if we have a long position already
                elif self.getposition(d).size > 0:
                    # we have closed below our stop loss
                    if self.stop_loss_long[d] is not None and d.close[0] < self.stop_loss_long[d]:
                        self.o[d] = self.close(data=d, exectype=bt.Order.Market)
                        self.trade_count = self.trade_count + 1
                        self.log(f"Closing long position as price {d.close[0]} is below our stop "
                                 f"loss of {self.stop_loss_long[d]}", dt)
                        self.local_max[d] = None
                        self.stop_loss_long[d] = None

                    # we have exceeded our trailing stop threshold and the close has dropped below the EMA
                    elif self.trailing_stop[d] is not None and self.trailing_stop[d] < \
                            d.close[0] < self.inds[d]['ema_long'][0]:
                        self.o[d] = self.close(data=d, exectype=bt.Order.Market)
                        self.trade_count = self.trade_count + 1
                        self.log(f"Closing long position as price {d.close[0]} exceeds our trailing stop of"
                                 f" {self.trailing_stop[d]} and dropped below the EMA of {self.inds[d]['ema_long'][0]}",
                                 dt)
                        self.local_min[d] = None
                        self.trailing_stop[d] = None

                # handle buy/sell
                elif self.getposition(d).size == 0:
                    if self.entry_point_long[d]:
                        self.waiting_days_long[d] = self.waiting_days_long.get(d, 0) + 1
                    if self.entry_point_short[d]:
                        self.waiting_days_short[d] = self.waiting_days_short.get(d, 0) + 1

                    # kill the tags if adx is below 30
                    if self.inds[d]['adx'].lines.adx[0] <= 30:
                        if self.entry_point_long[d]:
                            self.entry_point_long[d] = None
                            self.log(f"For {dn} killing long condition as the adx "
                                     f"{round(self.inds[d]['adx'].lines.adx[0], 3)} "
                                     f"has dropped below 30", dt)
                        if self.entry_point_short[d]:
                            self.entry_point_short[d] = None
                            self.log(f"For {dn} killing short condition as the adx "
                                     f"{round(self.inds[d]['adx'].lines.adx[0], 3)} "
                                     f"has dropped below 30", dt)

                    # kill the tags if it's been too long
                    if self.waiting_days_short[d] > self.params.lag_days:
                        self.entry_point_short[d] = None
                        self.log(f"For {dn} killing short condition as it has been {self.waiting_days_short[d]} "
                                 f"days with no sell trigger reached", dt)
                        self.waiting_days_short[d] = 0
                    if self.waiting_days_long[d] > self.params.lag_days:
                        self.entry_point_long[d] = None
                        self.log(f"For {dn} killing long condition as it has been {self.waiting_days_long[d]} "
                                 f"days with no buy trigger reached", dt)
                        self.waiting_days_long[d] = 0

                    # adx is above 30
                    else:
                        # the ema is touched from below, so we set an entry point for going short
                        if abs(d.close[0] / self.inds[d]['local_min']) > self.params.bounce_off_min and d.close[0] \
                                < \
                                self.inds[d]['ema_long'][0] < d.high[0] and self.inds[d]['ema_short_slope'] > 0 and \
                                self.inds[d]['ema_short_slope'] > self.inds[d]['ema_long_slope']:
                            self.stop_loss_short[d] = d.high[0]
                            self.entry_point_short[d] = d.low[0]
                            self.log(f"Considering going short for {dn} as the EMA has been touched from below, "
                                     f"and the close {round(d.close[0], 3)} is "
                                     f"{100 * (round((d.close[0] / self.inds[d]['local_min']), 3))}% of the local "
                                     f"min ({self.inds[d]['local_min'][0]}). Setting stop loss at "
                                     f"{self.stop_loss_short[d]} (high) and an entry "
                                     f"point of {self.entry_point_short[d]} (low)", dt)

                        # the ema is touched from above, so we set an entry point for going long
                        if abs(d.close[0] / self.inds[d]['local_max']) < self.params.bounce_off_max and d.low[0] \
                                < self.inds[d]['ema_long'][0] < d.close[0] and self.inds[d]['ema_short_slope'] < 0 and \
                                self.inds[d]['ema_short_slope'] < self.inds[d]['ema_long_slope']:
                            self.stop_loss_long[d] = d.low[0]
                            self.entry_point_long[d] = d.high[0]
                            self.log(f"Considering going long for {dn} as the EMA has been touched from above, and the "
                                     f"close {round(d.close[0], 3)} is "
                                     f" {100 * (round((d.close[0] / self.inds[d]['local_max']), 3))}% of the "
                                     f"local max ({self.inds[d]['local_max'][0]}). Setting stop loss at "
                                     f"{self.stop_loss_long[d]} (low) and an "
                                     f"entry point of {self.entry_point_long[d]} (high)", dt)

                        # sell as we have gone below the entry point and remain below the EMA
                        if d.close[0] < self.inds[d]['ema_long'][0] and self.entry_point_short[d] \
                                is not None and d.close[0] < self.entry_point_short[d]:
                            self.o[d] = self.sell(data=d, exectype=bt.Order.Market)
                            self.trade_count = self.trade_count + 1
                            self.local_min[d] = self.inds[d]['local_min'][0]
                            self.log(
                                f"For {dn} selling as close {d.close[0]} has dropped below the entry point of"
                                f" {self.entry_point_short[d]}, setting local min of {self.local_min[d]}", dt)
                            self.entry_point_short[d] = None
                            self.waiting_days_short[d] = 0

                        # buy as we have gone above the entry point and remain above the EMA
                        if d.close[0] > self.inds[d]['ema_long'][0] and self.entry_point_long[d] \
                                is not None and d.close[0] > self.entry_point_long[d]:
                            self.o[d] = self.buy(data=d, exectype=bt.Order.Market)
                            self.trade_count = self.trade_count + 1
                            self.local_max[d] = self.inds[d]['local_max'][0]
                            self.log(
                                f"For {dn} buying as close {d.close[0]} has exceeded the entry point of"
                                f" {self.entry_point_long[d]}, setting local max of {self.local_max[d]}", dt)
                            self.entry_point_long[d] = None
                            self.waiting_days_long[d] = 0

    def stop(self):
        """
        Runs when the strategy stops. Record the final value of the portfolio and calculate the CAGR.

        Parameters
        ----------

        Raises
        ------

        """
        self.elapsed_days = (self.end_date - self.start_date).days
        self.cagr = 100 * (((self.broker.cash + self.broker.fundvalue * self.broker.fundshares) /
                            self.broker.startingcash) ** (1 / (self.elapsed_days / 365.25)) - 1)
        all_long_days = sum(self.long_days.values())
        all_short_days = sum(self.short_days.values())

        print(f"HolyGrail CAGR: {self.cagr:.4f}% (over {(self.elapsed_days / 365.25):.2f} years "
              f"with {len(self.broker.orders)} trades). Long "
              f"{round((all_long_days / (self.elapsed_days * len(self.d_with_len))) * 100, 2)}% and short "
              f"{round((all_short_days / (self.elapsed_days * len(self.d_with_len))) * 100, 2)}%, for a total "
              f"of {round(((all_long_days + all_short_days) / (self.elapsed_days * len(self.d_with_len))) * 100, 2)}%.")
        print(f"HolyGrail portfolio value (incl. cash): "
              f"{self.broker.cash + self.broker.fundvalue * self.broker.fundshares}")

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
