from backtrader.feeds import PandasData


class TickerData(PandasData):
    """
    A subclass of backtrader's PandasData class to define the fields that we will provide.

    Attributes
    ----------
    params : dict
        The column headers from the dataframe.

    Methods
    -------

    """
    params = {c: -1 for c in ['open', 'high', 'low', 'close', 'volume']}
    params.update({'datetime': 0})
    params = tuple(params.items())
