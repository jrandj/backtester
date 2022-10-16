import configparser

from pathlib import Path
import backtrader as bt
import csv
import os.path


class HolyGrail(bt.Strategy):
    """
    This is an implementation of the "Holy Grail" trading strategy documented at:
        - https://tradingstrategyguides.com/holy-grail-trading-strategy/.

    Attributes:
        self.position_count: Int.
            The number of open positions.
        self.open_order_count: Int.
            The number of open orders.
        self.end_date: Datetime.date.
            The end date for the strategy.
        self.start_date: Datetime.date.
            The start date for the strategy.
        self.d_with_len: List[TickerData.TickerData].
            The list of ticker data.
        self.cagr: Float.
            The Compound Annual Growth Rate of the strategy.
        self.o: Dict.
            The orders.
        self.inds = Dict.
            The indicator.
        self.entry_point_long = Dict.
            The entry points for long positions.
        self.stop_loss_long = Dict.
            The stop losses for long positions.
        self.entry_point_short = Dict.
            The entry points for short positions.
        self.stop_loss_short = Dict.
            The stop losses for short positions.
        self.trailing_stop = Dict.
            The trailing stops.
        self.local_max = Dict.
            The local maxima.
        self.local_min = Dict.
            The local minima.
        self.short_days = Dict.
            The number of days that a short position is held.
        self.long_days = Dict.
            The number of days that a long position is held.
        self.waiting_days_short = Dict.
            The number of days waiting to go short once we have considered it.
        self.waiting_days_long = Dict.
            The number of days waiting to go long once we have considered it.
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
        ('volume_period', int(config['holygrail_strategy_options']['volume_period'])),
        ('minimum_volume', int(config['holygrail_strategy_options']['minimum_volume'])),
        ('position_limit', int(config['global_options']['position_limit'])),
        ('lag_days', int(config['holygrail_strategy_options']['lag_days'])),
        ('plot_tickers', config.getboolean('global_options', 'plot_tickers')),
        ('log_file', 'HolyGrail.csv')
    )

    def __init__(self):
        """
        Create any indicators needed for the strategy.
        """
        self.position_count = None
        self.open_order_count = 0
        self.end_date = None
        self.start_date = None
        self.d_with_len = None
        self.cagr = None
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
            self.inds[d] = dict()
            self.inds[d]['adx'] = bt.indicators.AverageDirectionalMovementIndex(d, period=self.params.adx_period)
            self.inds[d]['ema_long'] = bt.indicators.ExponentialMovingAverage(d.close,
                                                                              period=self.params.ema_long_period)
            self.inds[d]['ema_short'] = bt.indicators.ExponentialMovingAverage(d.close,
                                                                               period=self.params.ema_short_period)
            self.inds[d]['volume_sma'] = bt.indicators.ExponentialMovingAverage(d.volume,
                                                                                period=self.params.volume_period)
            self.inds[d]['ema_long_slope'] = self.inds[d]['ema_long'] - self.inds[d]['ema_long'](-1)
            self.inds[d]['ema_short_slope'] = self.inds[d]['ema_short'] - self.inds[d]['ema_short'](-1)
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
            self.position_count = 0

            if not self.params.plot_tickers:
                self.inds[d]['adx'].plotinfo.subplot = False
                self.inds[d]['ema_long'].plotinfo.subplot = False
                self.inds[d]['ema_short'].plotinfo.subplot = False
                self.inds[d]['local_max'].plotinfo.subplot = False
                self.inds[d]['local_min'].plotinfo.subplot = False

    def log(self, txt, log_type, dt, dn, order_type="N/A", order_status="N/A", net_profit="N/A", order_equity_p="N/A",
            order_cash_p="N/A", order_total_p="N/A", order_size="N/A", equity="N/A", cash_percent="N/A",
            equity_percent="N/A"):
        """
        The logger for the strategy.

        :param txt: The text to be logged.
        :type txt: Str.
        :param log_type: The category for the log message.
        :type log_type: Str.
        :param dt: The current date.
        :type dt: DateTime.date.
        :param dn: The name of the ticker.
        :type dn: Str or NoneType.
        :param order_type: The type of order.
        :type order_type: Str.
        :param order_status: The status of the order.
        :type order_status: Str.
        :param net_profit: The net profit of a trade.
        :type net_profit: Str or Float.
        :param order_equity_p: The positions value as a percentage of total equity.
        :type order_equity_p: Str or Float.
        :param order_cash_p: The positions value as a percentage of total cash.
        :type order_cash_p: Str or Float.
        :param order_total_p: The positions value as a percentage of the portfolio (equity plus cash).
        :type order_total_p: Str or Float.
        :param order_size: The value of the order.
        :type order_size: Str or Float.
        :param equity: The total equity accumulated by the strategy.
        :type equity: Str or Float.
        :param cash_percent: The cash percentage of the portfolio value.
        :type cash_percent: Str or Float.
        :param equity_percent: The equity percentage of the portfolio value.
        :type equity_percent: Str or Float.
        :return: NoneType.
        :rtype: NoneType.
        """
        file_exists = os.path.isfile(self.p.log_file)

        with Path(self.p.log_file).open('a', newline='', encoding='utf-8') as f:
            log_writer = csv.writer(f)
            # add the column headers
            if not file_exists:
                log_writer.writerow(["Date", "Ticker", "Event Type", "Details", "Order Type", "Order Status",
                                     "Order Size", "Trade PnL", "Order Equity %", "Order Cash %", "Order Total %",
                                     "Portfolio Cash", "Cash %", "Portfolio Equity", "Equity %", "Total Positions",
                                     "Total Orders"])

            if type(equity) == 'float':
                equity = round(equity, 2)

            log_writer.writerow((dt.isoformat(), dn, log_type, txt, order_type, order_status, order_size, net_profit,
                                 order_equity_p, order_cash_p, order_total_p, round(self.broker.get_cash(), 2),
                                 cash_percent, equity, equity_percent, self.position_count,
                                 self.open_order_count))

    def notify_order(self, order):
        """
        Handle orders and provide a notification from the broker based on the order.

        :param order: The order object.
        :type order: Backtrader.order.BuyOrder or Backtrader.order.SellOrder.
        :return: NoneType.
        :rtype: NoneType.
        :raises ValueError: If an unhandled order type occurs.
        """
        equity = self.broker.get_value() - self.broker.get_cash()
        if equity != 0:
            cash_percent = round(self.broker.get_cash() / self.broker.get_value(), 2) * 100
        else:
            cash_percent = 0
        equity_percent = round(equity / self.broker.get_value(), 2) * 100

        dt, dn = self.datetime.date(), order.data._name

        if order.status in [order.Submitted, order.Rejected]:
            self.log("N/A", "Order", dt, dn, order.ordtypename(), order.getstatusname())
        elif order.status in [order.Accepted]:
            self.log("N/A", "Order", dt, dn, order.ordtypename(), order.getstatusname())
            self.open_order_count += 1
        elif order.status in [order.Completed, order.Partial]:
            if equity == 0:
                order_equity_p = 100
            else:
                order_equity_p = round(100 * (order.executed.value / equity), 2)
            order_total_p = round(100 * (order.executed.value / self.broker.get_value()), 2)
            order_cash_p = round(100 * (order.executed.value / self.broker.get_cash()), 2)
            self.log(f"Slippage (executed_price/created_price): "
                     f"{100 * (order.executed.price / order.created.price):.2f}%", "Order", dt, dn, order.ordtypename(),
                     order.getstatusname(), 0, order_equity_p, order_cash_p, order_total_p,
                     round(order.executed.value, 2), equity, cash_percent, equity_percent)
            del self.o[order.data]
            self.open_order_count -= 1
        elif order.status in [order.Expired, order.Canceled, order.Margin]:
            self.log("Unexpected order status", "Order", dt, dn, order.ordtypename(), order.getstatusname(), "N/A",
                     "N/A", "N/A", equity, cash_percent, equity_percent)
            del self.o[order.data]
        else:
            raise ValueError(f"For {dn}, unexpected order status of {order.getstatusname()}")

    def start(self):
        """
        Runs at the start. Calculates the date range across all tickers.

        :return: NoneType.
        :rtype: NoneType.
        """
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

        :return: NoneType.
        :rtype: NoneType.
        """
        self.d_with_len = self.datas
        self.next()

    def prenext(self):
        """
        The method is used when all data points are not available.

        :return: NoneType.
        :rtype: NoneType.
        """
        self.d_with_len = [d for d in self.datas if len(d)]
        self.next()

    def track_daily_stats(self):
        """
        Log the daily stats for the strategy.

        :return: NoneType.
        :rtype: NoneType.
        """
        dt = self.datetime.date()
        equity = self.broker.get_value() - self.broker.get_cash()
        if equity != 0:
            cash_percent = round(self.broker.get_cash() / self.broker.get_value(), 2) * 100
        else:
            cash_percent = 100
        equity_percent = round(equity / self.broker.get_value(), 2) * 100
        self.log("N/A", "Daily", dt, "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A",
                 "N/A", equity, cash_percent, equity_percent)

    def next(self):
        """
        The method is used for all data points once the minimum period of all data/indicators has been met.

        :return: NoneType.
        :rtype: NoneType.
        """
        dt = self.datetime.date()

        # find the number of positions we already have, so we don't go over the limit
        self.position_count = len([position for position in self.broker.positions if self.broker.getposition(
            position).size != 0])

        self.track_daily_stats()
        for i, d in enumerate(self.d_with_len):
            dn = d._name
            # track if we are long or short
            if self.getposition(d).size > 0:
                self.long_days[d] = self.long_days.get(d, 0) + 1
            elif self.getposition(d).size < 0:
                self.short_days[d] = self.short_days.get(d, 0) + 1

            # we are only interested if there are no orders for this ticker already
            if not self.o.get(d, None):
                self.set_trailing_stops(d, dn, dt)
                # handle closing if we have a short position already
                if self.getposition(d).size < 0:
                    self.close_if_short(d, dn, dt)

                # handle closing if we have a long position already
                elif self.getposition(d).size > 0:
                    self.close_if_long(d, dn, dt)

                # handle buy/sell
                elif self.getposition(d).size == 0:
                    self.handle_buy_and_sell(d, dn, dt)

            else:
                self.log("Unable to proceed as there is an order already", "Strategy", dt, dn)

    def set_trailing_stops(self, d, dn, dt):
        """
        A helper method for next that handles setting the trailing stops for positions.

        :param d: The ticker data.
        :type d: TickerData.TickerData.
        :param dn: The current ticker.
        :type dn: Str.
        :param dt: The current date.
        :type dt: Datetime.date.
        :return: NoneType.
        :rtype: NoneType.
        """
        # if we are long consider setting the trailing stop from a recent (20 day) local maximum
        if self.getposition(d).size > 0 and not self.trailing_stop[d] and self.local_max[d] is not None and \
                d.close[0] > self.local_max[d]:
            self.trailing_stop[d] = d.close[0]
            self.log(f"Long and setting a trailing stop of {self.trailing_stop[d]:.2f}", "Strategy", dt, dn)

        # if we are short consider setting the trailing stop from a recent (20 day) local minimum
        elif self.getposition(d).size < 0 and not self.trailing_stop[d] and self.local_min[d] is not None and \
                d.close[0] < self.local_min[d]:
            self.trailing_stop[d] = d.close[0]
            self.log(f"Short and setting a trailing stop of {self.trailing_stop[d]:.2f}", "Strategy", dt, dn)

    def close_if_short(self, d, dn, dt):
        """
        A helper method for next that handles closing a short position.

        :param d: The ticker data.
        :type d: TickerData.TickerData.
        :param dn: The current ticker.
        :type dn: Str.
        :param dt: The current date.
        :type dt: Datetime.date.
        :return: NoneType.
        :rtype: NoneType.
        """
        # we have closed above our stop loss
        if self.stop_loss_short[d] is not None and d.close[0] > self.stop_loss_short[d]:
            self.o[d] = self.close(data=d, exectype=bt.Order.Market)
            self.log(f"Closing short position as price {d.close[0]:.2f} is above our stop loss of "
                     f"{self.stop_loss_short[d]:.2f}", "Strategy", dt, dn)
            self.local_min[d] = None
            self.stop_loss_short[d] = None

        # we have exceeded our trailing stop threshold and the close has dropped below the EMA
        elif self.trailing_stop[d] is not None and self.trailing_stop[d] > d.close[0] > \
                self.inds[d]['ema_long'][0]:
            self.o[d] = self.close(data=d, exectype=bt.Order.Market)
            self.log(f"Closing short position as price {d.close[0]:.2f} is below our trailing stop of"
                     f" {self.trailing_stop[d]:.2f} and went above the EMA of {self.inds[d]['ema_long'][0]:.2f}",
                     f"Strategy", dt, dn)
            self.local_min[d] = None
            self.trailing_stop[d] = None

    def close_if_long(self, d, dn, dt):
        """
        A helper method for next that handles closing a long position.

        :param d: The ticker data.
        :type d: TickerData.TickerData.
        :param dn: The current ticker.
        :type dn: Str.
        :param dt: The current date.
        :type dt: Datetime.date.
        :return: NoneType.
        :rtype: NoneType.
        """
        # we have closed below our stop loss
        if self.stop_loss_long[d] is not None and d.close[0] < self.stop_loss_long[d]:
            self.o[d] = self.close(data=d, exectype=bt.Order.Market)
            self.log(f"Closing long position as price {d.close[0]:.2f} is below our stop loss of "
                     f"{self.stop_loss_long[d]:.2f}", "Strategy", dt, dn)
            self.local_max[d] = None
            self.stop_loss_long[d] = None

        # we have exceeded our trailing stop threshold and the close has dropped below the EMA
        elif self.trailing_stop[d] is not None and self.trailing_stop[d] < \
                d.close[0] < self.inds[d]['ema_long'][0]:
            self.o[d] = self.close(data=d, exectype=bt.Order.Market)
            self.log(f"Closing long position as price {d.close[0]:.2f} exceeds our trailing stop of"
                     f" {self.trailing_stop[d]:.2f} and dropped below the EMA of {self.inds[d]['ema_long'][0]:.2f}",
                     "Strategy", dt, dn)
            self.local_min[d] = None
            self.trailing_stop[d] = None

    def handle_buy_and_sell(self, d, dn, dt):
        """
        A helper method for next that handles buying and selling.

        :param d: The ticker data.
        :type d: TickerData.TickerData.
        :param dn: The current ticker.
        :type dn: Str.
        :param dt: The current date.
        :type dt: Datetime.date.
        :return: NoneType.
        :rtype: NoneType.
        """
        if self.entry_point_long[d]:
            self.waiting_days_long[d] = self.waiting_days_long.get(d, 0) + 1
        if self.entry_point_short[d]:
            self.waiting_days_short[d] = self.waiting_days_short.get(d, 0) + 1

        # kill the tags if adx is below 30
        if self.inds[d]['adx'].lines.adx[0] <= 30:
            if self.entry_point_long[d]:
                self.entry_point_long[d] = None
                self.log(f"Killing long condition as the adx {self.inds[d]['adx'].lines.adx[0]:.2f} "
                         f"has dropped below 30", "Strategy", dt, dn)
            if self.entry_point_short[d]:
                self.entry_point_short[d] = None
                self.log(f"Killing short condition as the adx {self.inds[d]['adx'].lines.adx[0]:.2f} "
                         f"has dropped below 30", "Strategy", dt, dn)

        # kill the tags if it has been too long
        if self.waiting_days_short[d] > self.params.lag_days:
            self.entry_point_short[d] = None
            self.log(f"Killing short condition as it has been {self.waiting_days_short[d]:.2f} "
                     f"days with no sell trigger reached", "Strategy", dt, dn)
            self.waiting_days_short[d] = 0
        if self.waiting_days_long[d] > self.params.lag_days:
            self.entry_point_long[d] = None
            self.log(f"Killing long condition as it has been {self.waiting_days_short[d]:.2f} "
                     f"days with no buy trigger reached", "Strategy", dt, dn)
            self.waiting_days_long[d] = 0

        # kill the tags if the volume SMA drops below the minimum
        if self.inds[d]['volume_sma'][0] < self.params.minimum_volume:
            if self.entry_point_long[d]:
                self.entry_point_long[d] = None
                self.log(f"Killing long condition as the volume {self.inds[d]['volume_sma'][0]:.2f} sma "
                         f"has dropped below {self.params.minimum_volume}", "Strategy", dt, dn)
            if self.entry_point_short[d]:
                self.entry_point_short[d] = None
                self.log(f"Killing short condition as the volume {self.inds[d]['volume_sma'][0]:.2f} sma "
                         f"has dropped below {self.params.minimum_volume}", "Strategy", dt, dn)

        # adx is above 30 and there is sufficient volume
        elif self.inds[d]['adx'].lines.adx[0] > 30 and self.inds[d]['volume_sma'][0] >= self.params.minimum_volume:
            # the ema is touched from below, so we set an entry point for going short
            if abs(d.close[0] / self.inds[d]['local_min']) > self.params.bounce_off_min and d.close[0] \
                    < \
                    self.inds[d]['ema_long'][0] < d.high[0] and self.inds[d]['ema_short_slope'] > 0 and \
                    self.inds[d]['ema_short_slope'] > self.inds[d]['ema_long_slope']:
                self.stop_loss_short[d] = d.high[0]
                self.entry_point_short[d] = d.low[0]
                self.log(f"Considering going short as the EMA has been touched from below, and the close "
                         f"{d.close[0]:.2f} is {(100 * (d.close[0] / self.inds[d]['local_min'])):.2f}% of the local "
                         f"min ({self.inds[d]['local_min'][0]:.2f}). Setting stop loss at "
                         f"{self.stop_loss_short[d]:.2f} (high) and an entry point of {self.entry_point_short[d]:.2f} "
                         f"(low)", "Strategy", dt, dn)

            # the ema is touched from above, so we set an entry point for going long
            if abs(d.close[0] / self.inds[d]['local_max']) < self.params.bounce_off_max and d.low[0] \
                    < self.inds[d]['ema_long'][0] < d.close[0] and self.inds[d]['ema_short_slope'] < 0 and \
                    self.inds[d]['ema_short_slope'] < self.inds[d]['ema_long_slope']:
                self.stop_loss_long[d] = d.low[0]
                self.entry_point_long[d] = d.high[0]
                self.log(f"Considering going long as the EMA has been touched from above, and the "
                         f"close {d.close[0]:.2f} is {(100 * (d.close[0] / self.inds[d]['local_max'])):.2f}% of the "
                         f"local max ({self.inds[d]['local_max'][0]:.2f}). Setting stop loss at "
                         f"{self.stop_loss_long[d]:.2f} (low) and an entry point of {self.entry_point_long[d]:.2f} "
                         f"(high)", "Strategy", dt, dn)

            # sell as we have gone below the entry point and remain below the EMA
            if d.close[0] < self.inds[d]['ema_long'][0] and self.entry_point_short[d] \
                    is not None and d.close[0] < self.entry_point_short[d]:

                # only enter a position if we are below the limit
                if self.position_count + self.open_order_count < self.params.position_limit - 1:
                    if self.config.getboolean('global_options', 'no_penny_stocks') and d.close[0] >= 1:
                        self.o[d] = self.sell(data=d, exectype=bt.Order.Market)
                        self.local_min[d] = self.inds[d]['local_min'][0]
                        self.log(f"Selling as close {d.close[0]:.2f} has dropped below the entry point of"
                                 f" {self.entry_point_short[d]:.2f}, setting local min of {self.local_min[d]:.2f}",
                                 "Strategy", dt, dn)
                        self.entry_point_short[d] = None
                        self.waiting_days_short[d] = 0
                    else:
                        self.log("did not go short as {d.close[0]:.2f} qualifies it as a penny stock", "Strategy", dt,
                                 dn)
                        self.entry_point_short[d] = None
                        self.waiting_days_short[d] = 0
                else:
                    self.log(f"Did not go short as we have {self.position_count} positions and {self.open_order_count} "
                             f"orders already", "Strategy", dt, dn)

            # buy as we have gone above the entry point and remain above the EMA
            if d.close[0] > self.inds[d]['ema_long'][0] and self.entry_point_long[d] \
                    is not None and d.close[0] > self.entry_point_long[d]:

                # only enter a position if we are below the limit
                if self.position_count + self.open_order_count < self.params.position_limit - 1:
                    if self.config.getboolean('global_options', 'no_penny_stocks') and d.close[0] >= 1:
                        self.o[d] = self.buy(data=d, exectype=bt.Order.Market)
                        self.local_max[d] = self.inds[d]['local_max'][0]
                        self.log(f"Buying as close {d.close[0]:.2f} has exceeded the entry point "
                                 f" of {self.entry_point_long[d]:.2f}, setting local max of {self.local_max[d]:.2f}",
                                 f"Strategy", dt, dn)
                        self.entry_point_long[d] = None
                        self.waiting_days_long[d] = 0
                    else:
                        self.log(f"did not go long as {d.close[0]:.2f} qualifies it as a penny stock", "Strategy", dt,
                                 dn)
                        self.entry_point_long[d] = None
                        self.waiting_days_long[d] = 0
                else:
                    self.log(f"Did not go long as we have {self.position_count} positions and {self.open_order_count} "
                             f"orders already", "Strategy", dt, dn)

            # there not is sufficient volume
            elif self.inds[d]['volume_sma'][0] < self.params.minimum_volume:
                self.log(f"Not considering entry points as volume {d.volume[0]:.2f} is lower than minimum of "
                         f"{self.params.minimum_volume}", "Strategy", dt, dn)

    def notify_trade(self, trade):
        """
        Provides a notification when the trade is closed.

        :param trade: The trade to be notified.
        :type trade: Backtrader.trade.Trade.
        :return: NoneType.
        :rtype: NoneType.
        """
        dt = self.datetime.date()
        if trade.isclosed:
            self.log(f"Position opened on {trade.open_datetime().date()} and closed on {trade.close_datetime().date()} "
                     f"at price {trade.price:.2f} on {trade.close_datetime().date()}", "Trade", dt, trade.data._name,
                     f"N/A", "N/A", round(trade.pnlcomm, 2))

    def stop(self):
        """
        Runs when the strategy stops. Record the final value of the portfolio and calculate the Compound Annual
        Growth Rate (CAGR).

        :return: NoneType.
        :rtype: NoneType.
        """
        elapsed_days = (self.end_date - self.start_date).days
        self.cagr = 100 * (((self.broker.cash + self.broker.fundvalue * self.broker.fundshares) /
                            self.broker.startingcash) ** (1 / (elapsed_days / 365.25)) - 1)

        # provide a view of how often we were long or short across each ticker
        all_long_days = sum(self.long_days.values())
        all_short_days = sum(self.short_days.values())

        print(f"HolyGrail CAGR: {self.cagr:.2f}% (over {(elapsed_days / 365.25):.2f} years "
              f"with {len(self.broker.orders)} trades). Long "
              f"{((all_long_days / (elapsed_days * len(self.d_with_len))) * 100):.2f}% and short "
              f"{((all_short_days / (elapsed_days * len(self.d_with_len))) * 100):.2f}%, for a total "
              f"of {(((all_long_days + all_short_days) / (elapsed_days * len(self.d_with_len))) * 100):.2f}%")
        print(f"HolyGrail portfolio value (incl. cash): "
              f"{(self.broker.cash + self.broker.fundvalue * self.broker.fundshares):.2f}")
