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

        self.inds[0] = dict()

        self.inds[0]['adx'] = bt.indicators.AverageDirectionalMovementIndex(self.datas[0]).lines.adx
        self.inds[0]['ema'] = bt.indicators.ExponentialMovingAverage(self.datas[0].close, period=20)
        self.inds[0]['local_max'] = bt.indicators.Highest(self.datas[0].high, period=20)

        if self.params.plot_tickers == "False":
            self.inds[0]['adx'].plotinfo.subplot = False
            self.inds[0]['ema'].plotinfo.subplot = False
            self.inds[0]['local_max'].plotinfo.subplot = False

        self.entry_point = None
        self.stop_loss = None
        self.trailing_stop = None
        self.local_max = None

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
            # if self.p.verbose:
            #     self.log(f"Cash: {self.broker.get_cash():.2f}, "
            #              f"Equity: {self.broker.get_value() - self.broker.get_cash():.2f} "
            #              f"Cash %: {cash_percent:.2f}, Positions: {position_count}", dt)

            for i, d in enumerate(self.d_with_len):
                dn = d._name
                # strategy here

                # if there are no orders already
                if not self.o.get(d, None):

                    # if we are long consider setting the trailing stop from a recent (20 day) local maximum
                    if self.getposition(d).size > 0 and not self.trailing_stop and d.close[0] > self.local_max:
                        self.trailing_stop = d.close[0]
                        self.log(f"Long in {dn} and setting a trailing stop of {self.trailing_stop}", dt)

                    # buy signal
                    # must not be long already
                    if self.getposition(d).size <= 0:
                        if self.inds[0]['adx'] > 30:
                            # the ema is touched from above, so we set an entry point
                            if d.low[0] < self.inds[0]['ema'][0] < d.close[0]:
                                self.stop_loss = d.low[0]
                                self.entry_point = d.high[0]
                                self.log(f"For {dn} the EMA has been touched from above, setting stop loss at "
                                         f"{self.stop_loss} (low) and an entry point of {self.entry_point} (high)", dt)

                            # buy as we have gone above the entry point and remain above the EMA
                            if d.close[0] > self.inds[0]['ema'][0] and self.entry_point \
                                    is not None and d.close[0] > self.entry_point:
                                self.o[d] = self.buy(data=d, exectype=bt.Order.Market)
                                self.trade_count = self.trade_count + 1
                                self.local_max = self.inds[0]['local_max'][0]
                                self.log(f"For {dn} buying as close {d.close[0]} has exceeded the entry point of"
                                         f" {self.entry_point}, setting local max of {self.local_max}", dt)
                                self.entry_point = None

                    # sell signal
                    elif self.getposition(d).size > 0:

                        # we have closed below our stop loss so we sell
                        if self.stop_loss is not None and d.close[0] < self.stop_loss:
                            self.o[d] = self.close(data=d, exectype=bt.Order.Market)
                            self.trade_count = self.trade_count + 1
                            self.log(f"Selling as price {d.close[0]} is below our stop "
                                     f"loss of {self.stop_loss}", dt)
                            self.local_max = None
                            self.stop_loss = None

                        # we have exceeded our trailing stop threshold and the close has dropped below the EMA
                        elif self.trailing_stop is not None and self.trailing_stop < d.close[0] < self.inds[0]['ema'][
                            0]:
                            self.o[d] = self.close(data=d, exectype=bt.Order.Market)
                            self.trade_count = self.trade_count + 1
                            self.log(f"Selling as price {d.close[0]} exceeds our trailing stop of {self.trailing_stop} "
                                     f"and dropped below the EMA of {self.inds[0]['ema'][0]}", dt)
                            self.local_max = None
                            self.trailing_stop = None

    def stop(self):
        """
        Runs when the strategy stops. Record the final value of the portfolio and calculate the CAGR.

        Parameters
        ----------

        Raises
        ------

        """
        # end_date = self.datas[0].datetime.date(0)
        # for data in self.datas:
        #     if data.datetime.date(0) > end_date:
        #         end_date = data.datetime.date(0)
        # self.end_date = end_date
        print(f"HolyGrail end date: {self.end_date}")
        self.elapsed_days = (self.end_date - self.start_date).days
        self.end_val = self.broker.get_value()
        self.cagr = 100 * ((self.end_val / self.start_val) ** (
                1 / (self.elapsed_days / 365.25)) - 1)
        print(f"HolyGrail CAGR: {self.cagr:.4f}% (over {(self.elapsed_days / 365.25):.2f} years "
              f"with {self.trade_count} trades)")
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
