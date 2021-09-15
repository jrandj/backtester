from backtrader.feeds import PandasData


class SignalData(PandasData):
    """
    A class that enables the use of pandas dataframes with cerebro.

    Attributes
    ----------
    params : dict
        The column headers from the dataframe.

    Methods
    -------

    """
    cols = ['open', 'high', 'low', 'close', 'volume']
    params = {c: -1 for c in cols}
    params.update({'datetime': 0})
    params = tuple(params.items())
