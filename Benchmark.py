import backtrader as bt


class Benchmark(bt.Strategy):
    """
    A class that contains the trading strategy for buying and holding the index.

    Attributes
    ----------
    roi : TBC
        TBC.

    Methods
    -------
    log()
        The logger for the strategy.
    notify_order()
        Handle orders and provide a notification from the broker based on the order.
    prenext()
        The method is used when all data points are not available.
        Very few (if any) periods will have data for every ticker.
    next()
        The method used for all remaining data points once the minimum period of all data/indicators has been met.
    """

    def start(self):
        self.val_start = self.broker.get_cash()  # keep the starting cash
        print("here")

    def nextstart(self):
        # Buy all the available cash
        size = int(self.broker.get_cash() / self.data)
        self.buy(size=size)

    def notify_order(self, order):
        """Handle orders and provide a notification from the broker based on the order.

        Parameters
        ----------

        Raises
        ------

        """
        dt, dn = self.datetime.date(), order.data._name

        if order.status == order.Submitted:
            print(f'{dn},Order Submitted')
            return
        elif order.status == order.Accepted:
            print(f'{dn},Order Accepted')
            return
        elif order.status == order.Completed:
            p = order.executed.price
            v = order.executed.value
            c = order.executed.comm
            if order.isbuy():
                print(f'{dn},BUY executed, Price:{p:.2f}, Cost: {v:.2f}, Comm: {c:.2f}')
            elif order.issell():
                print(f'{dn},SELL executed, Price:{p:.2f}, Cost: {v:.2f}, Comm: {c:.2f}')
        elif order.status == order.Canceled:
            print(f'{dn},Order Canceled')
        elif order.status == order.Margin:
            print(f'{dn},Order Margin')
        elif order.status == order.Rejected:
            print(f'{dn},Order Rejected')
        elif order.status == order.Partial:
            print(f'{dn},Order Partial')
        elif order.status == order.Expired:
            print(f'{dn},Order Expired')
        else:
            print(str(order.status))

    def next(self):
        print("Value: " + str(self.broker.get_value()))

    def stop(self):
        # calculate the actual returns
        self.roi = (self.broker.get_value() / self.val_start) - 1.0
        print('ROI:        {:.2f}%'.format(100.0 * self.roi))
