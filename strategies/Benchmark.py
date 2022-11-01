import math

import backtrader as bt
import utils


class Benchmark(bt.Strategy):
    """
    This is an implementation of the benchmark trading strategy which buys and holds.

    Attributes:
        o: Backtrader.Order.BuyOrder or Backtrader.Order.SellOrder.
            The order object.
        open_order_count: Int.
            The number of open orders.
        params: Tuple.
            The local parameters for the strategy.
        position_count: Int.
            The number of open positions.
    """
    params = (
        ('verbose', True),
        ('log_file', 'benchmark.csv')
    )

    def __init__(self):
        """
        Create any indicators needed for the strategy.
        """
        self.o = dict()
        self.position_count = 0
        self.open_order_count = 0

    def calculate_commission(self):
        """
        Calculate the commission to pay for the order.

        :return: The amount of commission to pay for the order.
        :rtype: Int.
        """
        # estimate commission based on today's close price
        if self.broker.get_cash() < 1000:
            commission = 9.95
        elif self.broker.get_cash() <= 5000:
            commission = 14.95
        elif self.broker.get_cash() < 20000:
            commission = 19.95
        else:
            commission = 0.0011 * self.broker.get_cash()

        commission = int(math.floor(commission))
        return commission

    def nextstart(self):
        """
        Runs exactly once when the minimum period has been met. Buy the index with all cash.

        :return: NoneType.
        :rtype: NoneType.
        """
        self.position_count = len([position for position in self.broker.positions if self.broker.getposition(
            position).size != 0])
        commission = self.calculate_commission()
        size = math.floor((self.broker.get_cash() - commission) / self.data)
        self.o[self.datas[0]] = self.buy(data=self.datas[0], exectype=bt.Order.Market, size=size)

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
