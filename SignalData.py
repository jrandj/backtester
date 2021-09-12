from backtrader.feeds import PandasData


class SignalData(PandasData):
    """
    TBC.

    Attributes
    ----------
    TBC : TBC
        TBC.

    Methods
    -------
    TBC()
        TBC.
    """
    OHLCV = ['open', 'high', 'low', 'close', 'volume']
    cols = OHLCV

    # create lines
    lines = tuple(cols)

    # define parameters
    params = {c: -1 for c in cols}
    params.update({'datetime': 0})
    params = tuple(params.items())
