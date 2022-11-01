import configparser

import backtrader as bt
import utils


class HolyGrail(bt.Strategy):
    """
    This is an implementation of the "Holy Grail" trading strategy documented at:
        - https://tradingstrategyguides.com/holy-grail-trading-strategy/.

    Attributes:
        config: Configparser.RawConfigParser.
            The object that will read configuration from the configuration file.
        d_with_len: List[TickerData.TickerData].
            The list of ticker data.
        entry_point_long: Dict.
            The entry points for long positions.
        entry_point_short: Dict.
            The entry points for short positions.
        inds: Dict.
            The indicator.
        local_max: Dict.
            The local maxima.
        local_min: Dict.
            The local minima.
        long_days: Dict.
            The number of days that a long position is held.
        o: Dict.
            The orders.
        open_order_count: Int.
            The number of open orders.
        params: Tuple.
            Parameters for the strategy.
        position_count: Int.
            The number of open positions.
        short_days: Dict.
            The number of days that a short position is held.
        stop_loss_long: Dict.
            The stop losses for long positions.
        stop_loss_short: Dict.
            The stop losses for short positions.
        trailing_stop: Dict.
            The trailing stops.
        waiting_days_long: Dict.
            The number of days waiting to go long once we have considered it.
        waiting_days_short: Dict.
            The number of days waiting to go short once we have considered it.
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
        self.position_count = 0
        self.open_order_count = 0
        self.d_with_len = None
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

            if not self.params.plot_tickers:
                self.inds[d]['adx'].plotinfo.subplot = False
                self.inds[d]['ema_long'].plotinfo.subplot = False
                self.inds[d]['ema_short'].plotinfo.subplot = False
                self.inds[d]['local_max'].plotinfo.subplot = False
                self.inds[d]['local_min'].plotinfo.subplot = False

    def notify_order(self, order):
        """
        Handle orders and provide a notification from the broker based on the order.

        :param order: The order object.
        :type order: Backtrader.order.BuyOrder or Backtrader.order.SellOrder.
        :return: The open order count.
        :rtype: Int.
        :raises ValueError: If an unhandled order type occurs.
        """
        self.open_order_count = utils.notify_order(self.datetime.date(), order.data._name, self.broker.get_value(),
                                                   self.broker.get_cash(), self.p.log_file, self.p.verbose, order,
                                                   self.o, self.position_count, self.open_order_count)

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
        utils.track_daily_stats(self.datetime.date(), self.broker.get_value(), self.broker.get_cash(),
                                self.p.verbose, self.p.log_file, self.position_count, self.open_order_count)

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
                utils.log(self.p.verbose, self.p.log_file, "Unable to proceed as there is an order already",
                          "Strategy", dt, dn, self.position_count, self.open_order_count)

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
            utils.log(self.p.verbose, self.p.log_file,
                      f"Long and setting a trailing stop of {self.trailing_stop[d]:.2f}", "Strategy", dt, dn,
                      self.position_count, self.open_order_count)

        # if we are short consider setting the trailing stop from a recent (20 day) local minimum
        elif self.getposition(d).size < 0 and not self.trailing_stop[d] and self.local_min[d] is not None and \
                d.close[0] < self.local_min[d]:
            self.trailing_stop[d] = d.close[0]
            utils.log(self.p.verbose, self.p.log_file,
                      f"Short and setting a trailing stop of {self.trailing_stop[d]:.2f}", "Strategy", dt, dn,
                      self.position_count, self.open_order_count)

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
            utils.log(self.p.verbose, self.p.log_file, f"Closing short position as price {d.close[0]:.2f} is above "
                                                       f"our stop loss of {self.stop_loss_short[d]:.2f}", "Strategy",
                      dt, dn, self.position_count, self.open_order_count)
            self.local_min[d] = None
            self.stop_loss_short[d] = None

        # we have exceeded our trailing stop threshold and the close has dropped below the EMA
        elif self.trailing_stop[d] is not None and self.trailing_stop[d] > d.close[0] > \
                self.inds[d]['ema_long'][0]:
            self.o[d] = self.close(data=d, exectype=bt.Order.Market)
            utils.log(self.p.verbose, self.p.log_file, f"Closing short position as price {d.close[0]:.2f} is below "
                                                       f"our trailing stop of"
                                                       f" {self.trailing_stop[d]:.2f} and went above the EMA of "
                                                       f"{self.inds[d]['ema_long'][0]:.2f}",
                      f"Strategy", dt, dn, self.position_count, self.open_order_count)
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
            utils.log(self.p.verbose, self.p.log_file, f"Closing long position as price {d.close[0]:.2f} is below our "
                                                       f"stop loss of "
                                                       f"{self.stop_loss_long[d]:.2f}", "Strategy", dt, dn,
                      self.position_count, self.open_order_count)
            self.local_max[d] = None
            self.stop_loss_long[d] = None

        # we have exceeded our trailing stop threshold and the close has dropped below the EMA
        elif self.trailing_stop[d] is not None and self.trailing_stop[d] < \
                d.close[0] < self.inds[d]['ema_long'][0]:
            self.o[d] = self.close(data=d, exectype=bt.Order.Market)
            utils.log(self.p.verbose, self.p.log_file, f"Closing long position as price {d.close[0]:.2f} exceeds our "
                                                       f"trailing stop of"
                                                       f" {self.trailing_stop[d]:.2f} and dropped below the EMA of "
                                                       f"{self.inds[d]['ema_long'][0]:.2f}",
                      "Strategy", dt, dn, self.position_count, self.open_order_count)
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
                utils.log(self.p.verbose, self.p.log_file, f"Killing long condition as the adx of "
                                                           f"{self.inds[d]['adx'].lines.adx[0]:.2f} "
                                                           f"has dropped below 30", "Strategy", dt, dn,
                          self.position_count, self.open_order_count)
            if self.entry_point_short[d]:
                self.entry_point_short[d] = None
                utils.log(self.p.verbose, self.p.log_file,
                          f"Killing short condition as the adx of {self.inds[d]['adx'].lines.adx[0]: .2f} "
                          f"has dropped below 30", "Strategy", dt, dn, self.position_count, self.open_order_count)

        # kill the tags if it has been too long
        if self.waiting_days_short[d] > self.params.lag_days:
            self.entry_point_short[d] = None
            utils.log(self.p.verbose, self.p.log_file,
                      f"Killing short condition as it has been {self.waiting_days_short[d]: .2f} days with no sell "
                      f"trigger reached", "Strategy", dt, dn, self.position_count,
                      self.open_order_count)
            self.waiting_days_short[d] = 0
        if self.waiting_days_long[d] > self.params.lag_days:
            self.entry_point_long[d] = None
            utils.log(self.p.verbose, self.p.log_file,
                      f"Killing long condition as it has been {self.waiting_days_short[d]:.2f} days with no buy "
                      f"trigger reached", "Strategy", dt, dn, self.position_count, self.open_order_count)
            self.waiting_days_long[d] = 0

        # kill the tags if the volume SMA drops below the minimum
        if self.inds[d]['volume_sma'][0] < self.params.minimum_volume:
            if self.entry_point_long[d]:
                self.entry_point_long[d] = None
                utils.log(self.p.verbose, self.p.log_file,
                          f"Killing long condition as the volume {self.inds[d]['volume_sma'][0]:.2f} sma "
                          f"has dropped below {self.params.minimum_volume}", "Strategy", dt, dn, self.position_count,
                          self.open_order_count)
            if self.entry_point_short[d]:
                self.entry_point_short[d] = None
                utils.log(self.p.verbose, self.p.log_file, f"Killing short condition as the volume "
                                                           f"{self.inds[d]['volume_sma'][0]:.2f} sma has dropped "
                                                           f"below {self.params.minimum_volume}", "Strategy", dt,
                          dn, self.position_count, self.open_order_count)

        # adx is above 30 and there is sufficient volume
        elif self.inds[d]['adx'].lines.adx[0] > 30 and self.inds[d]['volume_sma'][0] >= self.params.minimum_volume:
            # the ema is touched from below, so we set an entry point for going short
            if abs(d.close[0] / self.inds[d]['local_min']) > self.params.bounce_off_min and d.close[0] \
                    < \
                    self.inds[d]['ema_long'][0] < d.high[0] and self.inds[d]['ema_short_slope'] > 0 and \
                    self.inds[d]['ema_short_slope'] > self.inds[d]['ema_long_slope']:
                self.stop_loss_short[d] = d.high[0]
                self.entry_point_short[d] = d.low[0]
                utils.log(self.p.verbose, self.p.log_file,
                          f"Considering going short as the EMA has been touched from below, and the close "
                          f"{d.close[0]:.2f} is {(100 * (d.close[0] / self.inds[d]['local_min'])):.2f}% of the "
                          f"local "
                          f"min ({self.inds[d]['local_min'][0]:.2f}). Setting stop loss at "
                          f"{self.stop_loss_short[d]:.2f} (high) and an entry point of "
                          f"{self.entry_point_short[d]:.2f} "
                          f"(low)", "Strategy", dt, dn, self.position_count, self.open_order_count)

            # the ema is touched from above, so we set an entry point for going long
            if abs(d.close[0] / self.inds[d]['local_max']) < self.params.bounce_off_max and d.low[0] \
                    < self.inds[d]['ema_long'][0] < d.close[0] and self.inds[d]['ema_short_slope'] < 0 and \
                    self.inds[d]['ema_short_slope'] < self.inds[d]['ema_long_slope']:
                self.stop_loss_long[d] = d.low[0]
                self.entry_point_long[d] = d.high[0]
                utils.log(self.p.verbose, self.p.log_file, f"Considering going long as the EMA has been touched from "
                                                           f"above, and the close {d.close[0]:.2f} is "
                                                           f"{(100 * (d.close[0] / self.inds[d]['local_max'])):.2f}% "
                                                           f"of the local max ({self.inds[d]['local_max'][0]:.2f}). "
                                                           f"Setting stop loss at {self.stop_loss_long[d]:.2f} (low) "
                                                           f"and an entry point of {self.entry_point_long[d]:.2f} "
                                                           f"(high)", "Strategy", dt, dn, self.position_count,
                          self.open_order_count)

            # sell as we have gone below the entry point and remain below the EMA
            elif d.close[0] < self.inds[d]['ema_long'][0] and self.entry_point_short[d] is not None and d.close[0] < \
                    self.entry_point_short[d]:
                # only enter a position if we are below the limit (note this doesn't seem to guarantee you stay below
                # the limit, potentially due to using vectorisation)
                if self.position_count + self.open_order_count + 1 < self.params.position_limit:
                    if self.config.getboolean('global_options', 'no_penny_stocks') and d.close[0] >= 1:
                        self.o[d] = self.sell(data=d, exectype=bt.Order.Market)
                        self.local_min[d] = self.inds[d]['local_min'][0]
                        utils.log(self.p.verbose, self.p.log_file, f"Selling as close {d.close[0]:.2f} has dropped "
                                                                   f"below the entry point of "
                                                                   f"{self.entry_point_short[d]:.2f}, setting local "
                                                                   f"min of {self.local_min[d]:.2f}",
                                  "Strategy", dt, dn, self.position_count, self.open_order_count)
                        self.entry_point_short[d] = None
                        self.waiting_days_short[d] = 0
                    else:
                        utils.log(self.p.verbose, self.p.log_file,
                                  f"Did not go short as {d.close[0]:.2f} qualifies it as a penny stock", "Strategy",
                                  dt, dn, self.position_count, self.open_order_count)
                        self.entry_point_short[d] = None
                        self.waiting_days_short[d] = 0
                else:
                    utils.log(self.p.verbose, self.p.log_file,
                              f"Did not go short as we have {self.position_count} positions and {self.open_order_count}"
                              f" orders already", "Strategy", dt, dn, self.position_count, self.open_order_count)

            # buy as we have gone above the entry point and remain above the EMA
            elif d.close[0] > self.inds[d]['ema_long'][0] and self.entry_point_long[d] \
                    is not None and d.close[0] > self.entry_point_long[d]:

                # only enter a position if we are below the limit (note this doesn't seem to guarantee you stay below
                # the limit, potentially due to using vectorisation)
                if self.position_count + self.open_order_count + 1 < self.params.position_limit:
                    if self.config.getboolean('global_options', 'no_penny_stocks') and d.close[0] >= 1:
                        self.o[d] = self.buy(data=d, exectype=bt.Order.Market)
                        self.local_max[d] = self.inds[d]['local_max'][0]
                        utils.log(self.p.verbose, self.p.log_file,
                                  f"Buying as close {d.close[0]:.2f} has exceeded the entry point "
                                  f" of {self.entry_point_long[d]:.2f}, setting local max of {self.local_max[d]:.2f}",
                                  f"Strategy", dt, dn, self.position_count, self.open_order_count)
                        self.entry_point_long[d] = None
                        self.waiting_days_long[d] = 0
                    else:
                        utils.log(self.p.verbose, self.p.log_file,
                                  f"Did not go long as {d.close[0]:.2f} qualifies it as a penny stock", "Strategy", dt,
                                  dn, self.position_count, self.open_order_count)
                        self.entry_point_long[d] = None
                        self.waiting_days_long[d] = 0
                else:
                    utils.log(self.p.verbose, self.p.log_file, f"Did not go long as we have {self.position_count} "
                                                               "positions and {self.open_order_count} orders already",
                              "Strategy", dt, dn, self.position_count, self.open_order_count)

        # there is insufficient volume
        elif self.inds[d]['volume_sma'][0] < self.params.minimum_volume:
            utils.log(self.p.verbose, self.p.log_file, f"Not considering entry points as volume {d.volume[0]:.2f} is "
                                                       f"lower than minimum of {self.params.minimum_volume}",
                      "Strategy", dt, dn, self.position_count, self.open_order_count)

    def notify_trade(self, trade):
        """
        Provides a notification when the trade is closed.

        :param trade: The trade to be notified.
        :type trade: Backtrader.trade.Trade.
        :return: NoneType.
        :rtype: NoneType.
        """
        utils.notify_trade(self.datetime.date(), trade, self.p.verbose, self.p.log_file, self.position_count,
                           self.open_order_count)
