from pathlib import Path
import backtrader as bt
import csv


class CrossoverStrategy(bt.Strategy):
    """
    A class that contains the trading strategy.

    Attributes
    ----------
    params : tuple
        Parameters for the strategy.
    o : dict
        The orders for all tickers.
    inds : dict
        The indicators for all tickers.
    start_val : float
        The starting value of the strategy.
    end_val : float
        The ending value of the strategy.
    start_date : datetime.date
        The starting date of the strategy.
    end_date : datetime.date
        The ending date of the strategy.
    elapsed_days : int
        The amount of days between the start and end date.
    cagr : float
        The Compound Annual Growth Rate (CAGR) for the strategy.

    Methods
    -------
    log()
        The logger for the strategy.
    notify_order()
        Handle orders and provide a notification from the broker based on the order.
    start()
        Runs at the start. Records starting portfolio value and time.
    prenext()
        The method is used all data points once the minimum period of all data/indicators has been met.
    next()
        The method used for all remaining data points once the minimum period of all data/indicators has been met.
    stop()
        Runs when the strategy stops. Record the final value of the portfolio and calculate the CAGR.
    notify_trade()
        Handle trades and provide a notification from the broker based on the trade.
    """
    # parameters for the strategy
    params = (
        ('verbose', True),
        ('sma1', 50),
        ('sma2', 200),
        ('log_file', 'strategy.csv')
    )

    def __init__(self):
        """Create any indicators needed for the strategy.

        Parameters
        ----------

        Raises
        ------

        """
        self.o = dict()
        self.inds = dict()
        # add the indicators for each data feed
        for i, d in enumerate(self.datas):
            self.inds[d] = dict()
            self.inds[d]['sma1'] = bt.indicators.SimpleMovingAverage(
                d.close, period=self.params.sma1)
            self.inds[d]['sma2'] = bt.indicators.SimpleMovingAverage(
                d.close, period=self.params.sma2)
            self.inds[d]['cross'] = bt.indicators.CrossOver(self.inds[d]['sma1'], self.inds[d]['sma2'])  # plot=False

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
        """Handle orders and provide a notification from the broker based on the order.

        Parameters
        ----------
        order : backtrader.order.BuyOrder
            The order object.

        Raises
        ------

        """
        dt, dn = self.datetime.date(), order.data._name

        if order.status == order.Submitted:
            self.log(f'{dn},Order Submitted', dt)
            return
        elif order.status == order.Accepted:
            self.log(f'{dn},Order Accepted', dt)
            return
        elif order.status == order.Completed:
            # allow orders for this ticker again
            self.o[order.data] = None
            if self.p.verbose:
                p = order.executed.price
                v = order.executed.value
                c = order.executed.comm
                if order.isbuy():
                    self.log(f'{dn},BUY executed, Price:{p:.2f}, Cost: {v:.2f}, Comm: {c:.2f}', dt)
                elif order.issell():
                    self.log(f'{dn},SELL executed, Price:{p:.2f}, Cost: {v:.2f}, Comm: {c:.2f}', dt)
        elif order.status == order.Canceled and self.p.verbose:
            self.log(f'{dn},Order Canceled', dt)
        elif order.status == order.Margin and self.p.verbose:
            self.log(f'{dn},Order Margin', dt)
        elif order.status == order.Rejected and self.p.verbose:
            self.log(f'{dn},Order Rejected', dt)
        elif order.status == order.Partial and self.p.verbose:
            self.log(f'{dn},Order Partial', dt)
        elif order.status == order.Expired and self.p.verbose:
            self.log(f'{dn},Order Expired', dt)

    def start(self):
        """Runs at the start. Records starting portfolio value and time.

        Parameters
        ----------

        Raises
        ------

        """
        self.start_val = self.broker.get_cash()
        self.start_date = self.datas[0].datetime.date(1)

    def prenext(self):
        """The method is used when all data points are not available.

        Parameters
        ----------

        Raises
        ------

        """
        self.next()

    def next(self):
        """The method is used all data points once the minimum period of all data/indicators has been met.

        Parameters
        ----------

        Raises
        ------

        """
        dt = self.datetime.date()
        # if self.p.verbose:
        #     self.log('Cash: ' + str(self.broker.get_cash()) + ' Equity: ' + str(self.broker.get_fundvalue()), dt)
        for i, d in enumerate(self.datas):
            dn = d._name
            # if there are no orders already for this ticker
            if not self.o.get(d, None):
                # check the signals
                if self.inds[d]['cross'] == 1:
                    if not self.getposition(d).size:
                        self.o[d] = self.buy(data=d)
                    else:
                        self.log('Cannot buy ' + dn + 'as I am already long', dt)
                elif self.inds[d]['cross'] == -1:
                    if self.getposition(d).size:
                        self.o[d] = self.close(data=d)
                    else:
                        self.log('Cannot sell ' + dn + ' as I am not long', dt)

    def stop(self):
        """Runs when the strategy stops. Record the final value of the portfolio and calculate the CAGR.

        Parameters
        ----------

        Raises
        ------

        """
        self.end_date = self.datas[0].datetime.date(0)
        self.elapsed_days = (self.end_date - self.start_date).days
        self.end_val = self.broker.get_value() + self.broker.get_cash()
        self.cagr = 100 * (self.end_val / self.start_val) ** (
                1 / (self.elapsed_days / 365)) - 100
        print('Strategy CAGR: {:.3f}%'.format(self.cagr))
        print('Strategy Portfolio Value: ' + str(self.end_val))

    def notify_trade(self, trade):
        """Handle trades and provide a notification from the broker based on the trade.

        Parameters
        ----------
        trade : backtrader.trade.Trade
            The trade object.

        Raises
        ------

        """
        dt = self.datetime.date()
        if trade.isclosed:
            self.log("Position in " + trade.data._name + " opened on " + str(trade.open_datetime().date())
                     + " and closed on " + str(trade.close_datetime().date()) + " with PnL Gross " + str(
                round(trade.pnl, 2))
                     + " and PnL Net " + str(round(trade.pnlcomm, 1)), dt)
