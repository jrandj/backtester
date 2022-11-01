from backtrader.feeds import PandasData


class TickerData(PandasData):
    """
    A subclass of the backtrader PandasData class to define the fields that we will provide.

    Attributes:
        params: Dict.
            The column headers from the dataframe.
    """
    params = {c: -1 for c in ['open', 'high', 'low', 'close', 'volume']}
    params.update({'datetime': 0})
    params = tuple(params.items())
