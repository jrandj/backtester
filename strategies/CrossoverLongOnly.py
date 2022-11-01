import configparser

import backtrader as bt
import utils


class CrossoverLongOnly(bt.Strategy):
    """
    This strategy uses 2 ETFs to represent long and short positions. Requires that data.bulk is set to False,
    and data.tickers=long_ETF,short_ETF.

    Attributes:
        config: Configparser.RawConfigParser.
            The object that will read configuration from the configuration file.
        d_with_len: List.
            The subset of data that is guaranteed to be available.
        end_date: Datetime.Date.
            The ending date of the strategy.
        inds: Dict.
            The indicators for all tickers.
        o: Dict.
            The orders for all tickers.
        open_order_count: Int.
            The number of open orders.
        params: Tuple.
            Parameters for the strategy.
        position_count: Int.
            The number of open positions.
        ready_to_buy_long: Bool.
            A flag used to track when we can open a long position.
        ready_to_buy_short: Bool.
            A flag used to track when we can open a short position.
        start_date: Datetime.Date.
            The starting date of the strategy.
    """
    config = configparser.RawConfigParser()
    config.read('config.properties')

    # parameters for the strategy
    params = (
        ('verbose', True),
        ('sma1', int(config['crossover_strategy_long_only_options']['crossover_strategy_long_only_sma1'])),
        ('sma2', int(config['crossover_strategy_long_only_options']['crossover_strategy_long_only_sma2'])),
        ('position_limit', int(config['global_options']['position_limit'])),
        ('plot_tickers', config.getboolean('global_options', 'plot_tickers')),
        ('log_file', 'CrossoverStrategy.csv')
    )

    def __init__(self):
        """
        Create any indicators needed for the strategy.
        """
        self.end_date = None
        self.start_date = None
        self.position_count = 0
        self.open_order_count = 0
        self.o = dict()
        self.inds = dict()
        self.inds[0] = dict()
        self.inds[0]['sma1'] = bt.indicators.SimpleMovingAverage(self.datas[0].close, period=self.params.sma1)
        self.inds[0]['sma2'] = bt.indicators.SimpleMovingAverage(self.datas[0].close, period=self.params.sma2)
        self.inds[0]['cross'] = bt.indicators.CrossOver(self.inds[0]['sma1'], self.inds[0]['sma2'])
        if not self.params.plot_tickers:
            self.inds[0]['sma1'].plotinfo.subplot = False
            self.inds[0]['sma2'].plotinfo.subplot = False
            self.inds[0]['cross'].plotinfo.subplot = False
        self.ready_to_buy_short = False
        self.ready_to_buy_long = False

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
        :return: The open order count.
        :rtype: Int.
        :raises ValueError: If an unhandled order type occurs.
        """
        self.open_order_count = utils.notify_order(self.datetime.date(), order.data._name, self.broker.get_value(),
                                                   self.broker.get_cash(), self.p.log_file, self.p.verbose, order,
                                                   self.o, self.position_count, self.open_order_count)

    def start(self):
        """
        Runs at the start. Records starting portfolio value and time.

        :return: NoneType.
        :rtype: NoneType.
        """
        # as the strategy requires buying and selling across 2 equities we can only use overlapping dates
        self.start_date = max(self.data.num2date(self.datas[0].datetime.array[0]),
                              self.data.num2date(self.datas[1].datetime.array[0])).date()
        self.end_date = min(self.data.num2date(self.datas[0].datetime.array[-1]),
                            self.data.num2date(self.datas[1].datetime.array[-1])).date()

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
        self.d_with_len = [d for d in self.datas if len(d.array) > 0]
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

        if self.start_date <= dt <= self.end_date:
            for i, d in enumerate(self.d_with_len):
                dn = d._name

                # if there are no orders for either ticker
                if not self.o.get(self.d_with_len[0], None) and not self.o.get(self.d_with_len[1], None):

                    # wait until we have funds
                    if self.ready_to_buy_long and not self.o.get(self.d_with_len[1], None):
                        self.o[self.d_with_len[0]] = self.buy(data=self.d_with_len[0], exectype=bt.Order.Market)
                        self.ready_to_buy_long = False
                        utils.log(self.p.verbose, self.p.log_file, f"Buying {self.d_with_len[0]._name} after closing "
                                                                   f"short position", "Strategy", dt, dn,
                                  self.position_count, self.open_order_count)
                    # wait until we have funds
                    elif self.ready_to_buy_short and not self.o.get(self.d_with_len[0], None):
                        self.o[self.d_with_len[1]] = self.buy(data=self.d_with_len[1], exectype=bt.Order.Market)
                        self.ready_to_buy_short = False
                        utils.log(self.p.verbose, self.p.log_file, f"Buying {self.d_with_len[1]._name} after closing "
                                                                   f"long position", "Strategy", dt, dn,
                                  self.position_count, self.open_order_count)

                    # buy signal
                    if self.inds[0]['cross'] == 1:
                        utils.log(self.p.verbose, self.p.log_file, f"Looking at {d._name} with BUY signal", "Strategy",
                                  dt, dn, self.position_count, self.open_order_count)

                        # we are short currently (we are long on the short instrument)
                        if self.getposition(self.d_with_len[1]).size > 0:
                            # close short position and open long position
                            utils.log(self.p.verbose, self.p.log_file, f"Selling {self.d_with_len[1]._name}",
                                      "Strategy", dt, dn, self.position_count, self.open_order_count)
                            self.o[self.d_with_len[1]] = self.close(data=self.d_with_len[1], exectype=bt.Order.Market)
                            self.ready_to_buy_long = True

                        # we are long currently so no action is required
                        elif self.getposition(self.d_with_len[0]).size > 0:
                            utils.log(self.p.verbose, self.p.log_file, f"Cannot action buy signal for {dn} as I am "
                                                                       f"long already", "Strategy", dt, dn,
                                      self.position_count, self.open_order_count)

                        # there is no open position
                        else:
                            utils.log(self.p.verbose, self.p.log_file, f"Buying {self.d_with_len[0]._name} with no "
                                                                       f"previous position", "Strategy", dt, dn,
                                      self.position_count, self.open_order_count)
                            self.o[self.d_with_len[0]] = self.buy(data=self.d_with_len[0], exectype=bt.Order.Market)

                    # sell signal
                    elif self.inds[0]['cross'] == -1:
                        utils.log(self.p.verbose, self.p.log_file, f"Looking at {d._name} with SELL signal",
                                  "Strategy", dt, dn, self.position_count, self.open_order_count)

                        # we are short currently so no action is required
                        if self.getposition(self.d_with_len[1]).size > 0:
                            utils.log(self.p.verbose, self.p.log_file, f"Cannot action sell signal for {dn} as I am "
                                                                       f"short already", "Strategy", dt, dn,
                                      self.position_count, self.open_order_count)

                        # we are long currently
                        elif self.getposition(self.d_with_len[0]).size > 0:
                            # close long position and open short position
                            utils.log(self.p.verbose, self.p.log_file, f"Selling {self.d_with_len[0]._name}",
                                      "Strategy", dt, dn, self.position_count, self.open_order_count)
                            self.o[self.d_with_len[0]] = self.close(data=self.d_with_len[0], exectype=bt.Order.Market)
                            self.ready_to_buy_short = True

                        # there is no open position
                        else:
                            utils.log(self.p.verbose, self.p.log_file, f"Buying {self.d_with_len[1]._name} with no "
                                                                       f"previous position", "Strategy", dt, dn,
                                      self.position_count, self.open_order_count)
                            self.o[self.d_with_len[1]] = self.buy(data=self.d_with_len[1], exectype=bt.Order.Market)

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
