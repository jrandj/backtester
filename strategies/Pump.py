import configparser

import backtrader as bt
from collections import defaultdict
import utils


class Pump(bt.Strategy):
    """
    A class that contains the trading strategy.

    Attributes:
        position_count: Int.
            The number of open positions.
        open_order_count: Int.
            The number of open orders.
        cagr: Float.
            The Compound Annual Growth Rate (CAGR) for the strategy.
        config: Configparser.RawConfigParser.
            The object that will read configuration from the configuration file.
        d_with_len: List.
            The subset of data that is guaranteed to be available.
        elapsed_days: Int.
            The amount of days between the start and end date.
        end_date: Datetime.Date.
            The ending date of the strategy.
        end_val: Float.
            The ending value of the strategy.
        inds: Dict.
            The indicators for all tickers.
        o: Dict.
            The orders for all tickers.
        params: Tuple.
            Parameters for the strategy.
        position_dt: Dict.
            Start and end dates from a previous position. Required as the backtrader position object does not support
            this.
        start_date: Datetime.Date.
            The starting date of the strategy.
        start_val: Float.
            The starting value of the strategy.
    """
    config = configparser.RawConfigParser()
    config.read('config.properties')

    # parameters for the strategy
    params = (
        ('verbose', True),
        ('volume_average_period', int(config['pump_strategy_options']['volume_average_period'])),
        ('price_max_period', int(config['pump_strategy_options']['price_max_period'])),
        ('sell_timeout', int(config['pump_strategy_options']['sell_timeout'])),
        ('buy_timeout', int(config['pump_strategy_options']['buy_timeout'])),
        ('volume_factor', float(config['pump_strategy_options']['volume_factor'])),
        ('price_comparison_lower_bound', float(config['pump_strategy_options']['price_comparison_lower_bound'])),
        ('price_comparison_upper_bound', float(config['pump_strategy_options']['price_comparison_upper_bound'])),
        ('position_limit', int(config['global_options']['position_limit'])),
        ('profit_factor', float(config['pump_strategy_options']['profit_factor'])),
        ('plot_tickers', config.getboolean('global_options', 'plot_tickers')),
        ('log_file', 'PumpStrategy.csv')
    )

    def __init__(self):
        """
        Create any indicators needed for the strategy.
        """
        self.position_count = 0
        self.open_order_count = 0
        self.position_dt = defaultdict(dict)
        self.o = dict()
        self.inds = dict()
        for i, d in enumerate(self.datas):
            self.inds[d] = dict()
            self.inds[d]['volume_average'] = \
                bt.indicators.SimpleMovingAverage(d.volume, period=self.params.volume_average_period)
            self.inds[d]['price_max'] = bt.indicators.Highest(d.close, period=self.params.price_max_period)
            if not self.params.plot_tickers:
                self.inds[d]['volume_average'].plotinfo.subplot = False
                self.inds[d]['price_max'].plotinfo.subplot = False

    def track_daily_stats(self):
        """
        Log the daily stats for the strategy.

        :return: NoneType.
        :rtype: NoneType.
        """
        utils.track_daily_stats(self.datetime.date(), self.broker.get_value(), self.broker.get_cash(),
                                self.p.verbose, self.p.log_file, self.position_count, self.open_order_count)

    def notify_order(self, order):
        """
        Handle orders and provide a notification from the broker based on the order.

        :param order: The order object.
        :type order: Backtrader.order.BuyOrder or Backtrader.order.SellOrder.
        :return: NoneType.
        :rtype: NoneType.
        :raises ValueError: If an unhandled order type occurs.
        """
        utils.notify_order(self.datetime.date(), order.data._name, self.broker.get_value(), self.broker.get_cash(),
                           self.p.log_file, self.p.verbose, order, self.o, self.position_count, self.open_order_count)

    def start(self):
        """
        Runs at the start. Records starting portfolio value and time.

        :return: NoneType.
        :rtype: NoneType.
        """
        self.start_val = self.broker.get_cash()
        start_date = self.datas[0].datetime.date(1)
        for data in self.datas:
            if data.datetime.date(1) < start_date:
                start_date = data.datetime.date(1)
        self.start_date = start_date
        print(f"Pump strategy start date: {self.start_date}")

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
            # if there are no orders already for this ticker
            if not self.o.get(d, None):
                # need data from yesterday
                if len(d.close.get(size=1, ago=-1)) > 0:
                    condition_a = d.volume[0] > (self.params.volume_factor * self.inds[d]['volume_average'][0])
                    condition_b = self.params.price_comparison_lower_bound < (
                            d.high[0] / d.close.get(size=1, ago=-1)[0]) < self.params.price_comparison_upper_bound
                    condition_c = d.close[0] >= self.inds[d]['price_max'][0]

                    # check for buy signal
                    if condition_a and condition_b and condition_c:
                        # if we don't already have a position
                        if self.getposition(d).size == 0:
                            # if the total portfolio positions limit has not been exceeded
                            if self.position_count < self.params.position_limit:
                                # if we had a position before
                                if self.position_dt[d].get('end'):
                                    days_elapsed = (dt - self.position_dt[d]['end']).days
                                    # enforce a timeout period to avoid buying back soon after closing
                                    if days_elapsed > self.params.buy_timeout:
                                        self.o[d] = self.buy(data=d, exectype=bt.Order.Market)
                                        self.position_dt[d]['start'] = dt
                                        utils.log(self.p.verbose, self.p.log_file,
                                                  f"Buy {dn} after {days_elapsed} days since close of last position",
                                                  "Strategy", dt, dn, self.position_count, self.open_order_count)
                                    else:
                                        utils.log(self.p.verbose, self.p.log_file,
                                                  f"Did not buy {dn} after only {days_elapsed} days since last hold",
                                                  "Strategy", dt, dn, self.position_count, self.open_order_count)
                                # we did not have a position before
                                else:
                                    self.o[d] = self.buy(data=d, exectype=bt.Order.Market)
                                    self.position_dt[d]['start'] = dt
                                    utils.log(self.p.verbose, self.p.log_file, f"Buy {dn} for the first time",
                                              "Strategy", dt, dn, self.position_count, self.open_order_count)
                            else:
                                utils.log(self.p.verbose, self.p.log_file,
                                          f"Cannot buy {dn} as I have {self.position_count} positions already",
                                          "Strategy",
                                          dt, dn, self.position_count, self.open_order_count)
                        else:
                            utils.log(self.p.verbose, self.p.log_file, f"Cannot buy {dn} as I am already long",
                                      "Strategy", dt, dn, self.position_count, self.open_order_count)

                # consider taking profit if we have a position
                if self.getposition(data=d).size > 0:
                    days_elapsed = (dt - self.position_dt[d]['start']).days
                    # take profit based on profit threshold
                    if d.close[0] >= self.params.profit_factor * self.getposition(data=d).price:
                        self.o[d] = self.close(data=d, exectype=bt.Order.Market)
                        self.position_dt[d]['end'] = dt
                        utils.log(self.p.verbose, self.p.log_file,
                                  f"Close {dn} position as {self.params.profit_factor} profit reached", "Strategy",
                                  dt, dn, self.position_count, self.open_order_count)

                    # enforce a timeout to abandon a trade
                    elif days_elapsed > self.params.sell_timeout:
                        self.o[d] = self.close(data=d, exectype=bt.Order.Market)
                        self.position_dt[d]['end'] = dt
                        utils.log(self.p.verbose, self.p.log_file, f"Abandon {dn} position after {days_elapsed} days "
                                                                   f"since start of position", "Strategy", dt, dn,
                                  self.position_count, self.open_order_count)

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
