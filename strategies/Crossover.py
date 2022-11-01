import configparser

import backtrader as bt
import utils


class Crossover(bt.Strategy):
    """
    A class that contains the trading strategy.

    Attributes:
        config: Configparser.RawConfigParser.
            The object that will read configuration from the configuration file.
        d_with_len: List.
            The subset of data that is guaranteed to be available.
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
    """
    config = configparser.RawConfigParser()
    config.read('config.properties')

    # parameters for the strategy
    params = (
        ('verbose', True),
        ('sma1', int(config['crossover_strategy_options']['crossover_strategy_sma1'])),
        ('sma2', int(config['crossover_strategy_options']['crossover_strategy_sma2'])),
        ('position_limit', int(config['global_options']['position_limit'])),
        ('plot_tickers', config.getboolean('global_options', 'plot_tickers')),
        ('log_file', 'CrossoverStrategy.csv')
    )

    def __init__(self):
        """
        Create any indicators needed for the strategy.
        """
        self.position_count = 0
        self.open_order_count = 0
        self.o = dict()
        self.inds = dict()
        # add the indicators for each data feed
        for i, d in enumerate(self.datas):
            self.inds[d] = dict()
            self.inds[d]['sma1'] = bt.indicators.SimpleMovingAverage(d.close, period=self.params.sma1)
            self.inds[d]['sma2'] = bt.indicators.SimpleMovingAverage(d.close, period=self.params.sma2)
            self.inds[d]['cross'] = bt.indicators.CrossOver(self.inds[d]['sma1'], self.inds[d]['sma2'])
            if not self.params.plot_tickers:
                self.inds[d]['sma1'].plotinfo.subplot = False
                self.inds[d]['sma2'].plotinfo.subplot = False
                self.inds[d]['cross'].plotinfo.subplot = False

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
                                                   self.o,
                                                   self.position_count, self.open_order_count)

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
                # buy signal
                if self.inds[d]['cross'] == 1:
                    # we are short currently
                    if self.getposition(d).size < 0:
                        # close short position and open long position
                        self.o[d] = self.close(data=d, exectype=bt.Order.Market)
                        if self.position_count <= self.params.position_limit:
                            self.o[d] = self.buy(data=d, exectype=bt.Order.Market)
                        else:
                            utils.log(self.p.verbose, self.p.log_file, f"Cannot action buy signal for {dn} as I have"
                                                                       f" {self.position_count} positions already",
                                      "Strategy", dt, dn, self.position_count, self.open_order_count)
                    # we are long currently so no action is required
                    elif self.getposition(d).size > 0:
                        utils.log(self.p.verbose, self.p.log_file, f"Cannot action buy signal for {dn} as I am "
                                                                   f"long already", "Strategy", dt, dn,
                                  self.position_count, self.open_order_count)
                    # there is no open position
                    else:
                        self.o[d] = self.buy(data=d, exectype=bt.Order.Market)

                # sell signal
                elif self.inds[d]['cross'] == -1:
                    if self.getposition(d).size < 0:
                        utils.log(self.p.verbose, self.p.log_file, f"Cannot action sell signal for {dn} as I am "
                                                                   f"short already", "Strategy", dt, dn,
                                  self.position_count, self.open_order_count)
                    # we are long currently
                    elif self.getposition(d).size > 0:
                        # close long position and open short position
                        self.o[d] = self.close(data=d, exectype=bt.Order.Market)
                        if self.position_count <= self.params.position_limit:
                            self.o[d] = self.sell(data=d, exectype=bt.Order.Market)
                        else:
                            utils.log(self.p.verbose, self.p.log_file,
                                      f"Cannot action sell signal for {dn} as I have {self.position_count} positions "
                                      f"already", "Strategy", dt, dn, self.position_count, self.open_order_count)
                    # there is no open position
                    else:
                        self.o[d] = self.sell(data=d, exectype=bt.Order.Market)

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
