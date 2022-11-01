import os
from pathlib import Path
import csv


def log(verbose, log_file, txt, log_type, dt, dn, position_count, open_order_count, order_type=None,
        order_status=None, net_profit=None, order_equity_p=None, order_cash_p=None, order_total_p=None,
        order_size=None, portfolio_cash=None, equity=None, cash_percent=None, equity_percent=None):
    """
    The logger for the strategy.

    :param verbose: True if detailed logs are required, and False otherwise.
    :type verbose: Bool.
    :param log_file: The path to the strategy log file.
    :type log_file: Str.
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
    :param position_count: The number of positions across all data.
    :type position_count: Int.
    :param open_order_count: The number of open orders across all data.
    :type open_order_count: Int.
    :return: NoneType.
    :rtype: NoneType.
    """
    if verbose:
        file_exists = os.path.isfile(log_file)
        with Path(log_file).open('a', newline='', encoding='utf-8') as f:
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
                                 cash_percent, equity, equity_percent, position_count, open_order_count))


def track_daily_stats(dt, value, cash, verbose, log_file, position_count, open_order_count):
    """
    Log the daily stats for the strategy.

    :param dt: The current date.
    :type dt: Datetime.Date.
    :param value: The total portfolio value.
    :type value: Float.
    :param cash: The cash component of the total portfolio value.
    :type cash: Float.
    :param verbose: True if detailed logs are required, and False otherwise.
    :type verbose: Bool.
    :param log_file: The path to the strategy log file.
    :type log_file: Str.
    :param position_count: The number of positions across all data.
    :type position_count: Int.
    :param open_order_count: The number of open orders across all data.
    :type open_order_count: Int.
    :return: NoneType.
    :rtype: NoneType.
    """
    equity = value - cash
    if equity != 0:
        cash_percent = round(cash / value, 2) * 100
    else:
        cash_percent = 100
    equity_percent = round(equity / value, 2) * 100
    log(verbose, log_file, None, "Daily", dt, None, position_count, open_order_count, None, None, None, None, None,
        None, None, round(cash, 2), equity, cash_percent, equity_percent)


def notify_trade(dt, trade, verbose, log_file, position_count, open_order_count):
    """
    Provides a notification for logging when the trade is closed.

    :param dt: The current date.
    :type dt: Datetime.Date.
    :param trade: The trade object.
    :type trade: Backtrader.Trade.Trade.
    :param verbose: True if detailed logs are required, and False otherwise.
    :type verbose: Bool.
    :param log_file: The path to the strategy log file.
    :type log_file: Str.
    :param position_count: The number of positions across all data.
    :type position_count: Int.
    :param open_order_count: The number of open orders across all data.
    :type open_order_count: Int.
    :return: NoneType.
    :rtype: NoneType.
    """
    if trade.isclosed:
        log(verbose, log_file,
            f"Position opened on {trade.open_datetime().date()} and closed on "
            f"{trade.close_datetime().date()} at price {trade.price:.2f} on "
            f"{trade.close_datetime().date()}", "Trade",
            dt, trade.data._name, position_count, open_order_count,
            None, None, round(trade.pnlcomm, 2))


def notify_order(dt, dn, value, cash, log_file, verbose, order, o, position_count, open_order_count):
    """
    Handle orders and provide a notification from the broker based on the order type.

    :param dt: The current date.
    :type dt: Datetime.Date.
    :param dn: The name of the ticker associated with the order.
    :type dn: Str.
    :param value: The total portfolio value.
    :type value: Float.
    :param cash: The cash component of the total portfolio value.
    :type cash: Float.
    :param verbose: True if detailed logs are required, and False otherwise.
    :type verbose: Bool.
    :param log_file: The path to the strategy log file.
    :type log_file: Str.
    :param order: The current order.
    :type order: Backtrader.Order.SellOrder.
    :param o: A dict containing all order objects.
    :type o: Dict.
    :param position_count: The number of positions across all data.
    :type position_count: Int.
    :param open_order_count: The number of open orders across all data.
    :type open_order_count: Int.
    :return: NoneType.
    :rtype: NoneType.
    """
    equity = value - cash
    if equity != 0:
        cash_percent = round(cash / value, 2) * 100
    else:
        cash_percent = 0
    equity_percent = round(equity / value, 2) * 100

    if order.status in [order.Submitted]:
        open_order_count += 1
        log(verbose, log_file, None, "Order", dt, dn, position_count,
            open_order_count, order.ordtypename(), order.getstatusname())
    elif order.status in [order.Rejected]:
        open_order_count -= 1
        log(verbose, log_file, None, "Order", dt, dn, position_count, open_order_count, order.ordtypename(),
            order.getstatusname())
        o.pop(order.data, None)
    elif order.status in [order.Accepted]:
        log(verbose, log_file, None, "Order", dt, dn, position_count, open_order_count, order.ordtypename(),
            order.getstatusname())
    elif order.status in [order.Completed, order.Partial]:
        open_order_count -= 1
        if equity == 0:
            order_equity_p = 100
        else:
            order_equity_p = round(100 * (order.executed.value / equity), 2)
        order_total_p = round(100 * (order.executed.value / value), 2)
        order_cash_p = round(100 * (order.executed.value / cash), 2)
        log(verbose, log_file, f"Slippage (executed_price/created_price): "
                               f"{100 * (order.executed.price / order.created.price):.2f}%", "Order", dt, dn,
            position_count, open_order_count, order.ordtypename(), order.getstatusname(), None, order_equity_p,
            order_cash_p, order_total_p, round(order.executed.value, 2), round(cash, 2), equity, cash_percent,
            equity_percent)
        o.pop(order.data, None)
    elif order.status in [order.Expired, order.Cancelled, order.Margin]:
        open_order_count -= 1
        log(verbose, log_file, "Unexpected order status", "Order", dt, dn, position_count, open_order_count,
            order.ordtypename(), order.getstatusname())
        o.pop(order.data, None)
    else:
        raise ValueError(f"For {dn}, unexpected order status of {order.getstatusname()}")
    return open_order_count
