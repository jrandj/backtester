import math

from pathlib import Path
import backtrader as bt
import csv
import os.path


class Benchmark(bt.Strategy):
    """
    This is an implementation of the benchmark trading strategy which buys and holds.

    Attributes:
        cagr: Float.
            The Compound Annual Growth Rate (CAGR) for the strategy.
        elapsed_days: Int.
            The amount of days between the start and end date.
        end_date: Datetime.Date.
            The ending date of the strategy.
        end_val: Float.
            The ending value of the strategy.
        o: Backtrader.Order.BuyOrder or Backtrader.Order.SellOrder.
            The order object.
        params: Tuple.
            The local parameters for the strategy.
        start_date: Datetime.Date.
            The starting date of the strategy.
        start_val: Float.
            The starting value of the strategy.
        position_count: Int.
            The number of open positions.
        self.open_order_count: Int.
            The number of open orders.
    """
    params = (
        ('verbose', True),
        ('log_file', 'benchmark.csv')
    )

    def __init__(self):
        """
        Create any indicators needed for the strategy.
        """
        self.end_val = None
        self.cagr = None
        self.elapsed_days = None
        self.end_date = None
        self.o = dict()
        self.start_date = None
        self.start_val = None
        self.position_count = 0
        self.open_order_count = 0

    def log(self, txt, log_type, dt, dn, order_type=None, order_status=None, net_profit=None, order_equity_p=None,
            order_cash_p=None, order_total_p=None, order_size=None, portfolio_cash=None, equity=None, cash_percent=None,
            equity_percent=None):
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
        :param portfolio_cash: The amount of cash in the portfolio.
        :type portfolio_cash: Str or Float.
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

            log_writer.writerow((dt.strftime('%d/%m/%Y'), dn, log_type, txt, order_type, order_status, order_size,
                                 net_profit, order_equity_p, order_cash_p, order_total_p, portfolio_cash,
                                 cash_percent, equity, equity_percent, self.position_count, self.open_order_count))

    def calculate_commission(self):
        """
        Calculate the commission to pay for the order.

        :return: The amount of commission to pay for the order.
        :rtype: Int.
        """
        # estimate commission based on today's close price
        if self.broker.get_cash() <= 5000:
            commission = 14.95
        elif 5000 < self.broker.get_cash() < 20000:
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
        self.start_val = self.broker.get_cash()
        self.start_date = self.datas[0].datetime.date(1)
        print(f"Benchmark start date: {self.start_date.strftime('%d/%m/%Y')}")
        commission = self.calculate_commission()
        size = math.floor((self.broker.get_cash() - commission) / self.data)
        self.o[self.datas[0]] = self.buy(data=self.datas[0], exectype=bt.Order.Market, size=size)

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
            self.log(None, "Order", dt, dn, order.ordtypename(), order.getstatusname())
        elif order.status in [order.Accepted]:
            self.log(None, "Order", dt, dn, order.ordtypename(), order.getstatusname())
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
                     order.getstatusname(), None, order_equity_p, order_cash_p, order_total_p,
                     round(order.executed.value, 2), round(self.broker.get_cash(), 2), equity, cash_percent,
                     equity_percent)
            del self.o[order.data]
            self.open_order_count -= 1
        elif order.status in [order.Expired, order.Canceled, order.Margin]:
            self.log("Unexpected order status", "Order", dt, dn, order.ordtypename(), order.getstatusname())
            del self.o[order.data]
            self.open_order_count -= 1
        else:
            raise ValueError(f"For {dn}, unexpected order status of {order.getstatusname()}")
