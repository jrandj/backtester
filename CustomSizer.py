import configparser

import backtrader as bt
import math


class CustomSizer(bt.Sizer):
    """
    A class that contains the logic for the order sizing.

    Attributes:
        config: Configparser.RawConfigParser.
            The object that will read configuration from the configuration file.
        params: Tuple.
            Parameters for the strategy.
    """
    config = configparser.RawConfigParser()
    config.read('config.properties')

    params = (
        ('percents', float(config['global_options']['position_size'])),
        ('starting_cash', float(config['broker']['cash'])),
        ('retint', False)
    )

    def _getsizing(self, comminfo, cash, data, isbuy):
        """
        Returns the number of shares to purchase.

        :param comminfo: CustomCommissionScheme.CustomCommissionScheme.
        :type comminfo: The commission scheme.
        :param cash: The available cash.
        :type cash: Float.
        :param data: The asset being considered for the order.
        :type data: TickerData.TickerData.
        :param isbuy: A flag indicating if the order is a buy order.
        :type isbuy: Bool.
        :return: The size of the order.
        :rtype: Float or Int.
        """
        size = math.floor((cash * self.params.percents) / (data.close[0] * 100))

        # e.g. the order must be at least 2.5% for 5% position sizing (prevents orders with low amounts of cash)
        if round(100 * size * data.close[0] / self.broker.get_value(), 2) < self.params.percents / 2:
            # print(f"Did not open position for {data._name} as it is a small position with"
            #       f" {round(100 * size * data.close[0] / self.broker.get_value(), 2)}% of the portfolio value, "
            #       f"less than the limit {self.params.percents / 2}%")
            size = 0

        if self.params.retint:
            size = int(size)

        return size
