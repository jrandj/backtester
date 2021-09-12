import warnings
from time import time
import datetime
import numpy as np
import pandas as pd
import pandas_datareader.data as web
import matplotlib.pyplot as plt
import seaborn as sns
import backtrader as bt
from backtrader.feeds import PandasData
import pyfolio as pf

from SignalData import SignalData
from MLStrategy import MLStrategy


def format_time(t):
    m_, s = divmod(t, 60)
    h, m = divmod(m_, 60)
    return f'{h:>02.0f}:{m:>02.0f}:{s:>02.0f}'


def main():
    warnings.filterwarnings('ignore')
    print("hi")
    pd.set_option('display.expand_frame_repr', False)
    np.random.seed(42)
    sns.set_style('darkgrid')
    cerebro = bt.Cerebro()  # create a "Cerebro" instance
    cash = 10000
    # comminfo = FixedCommisionScheme()
    # cerebro.broker.addcommissioninfo(comminfo)
    cerebro.broker.setcash(cash)

    # Create and Configure Cerebro Instance
    idx = pd.IndexSlice
    data = pd.read_hdf('D:\Backups\Trading Project\Historical Data\ASX\Equities\data.h5', 'table').sort_index()
    tickers = data.index.get_level_values(0).unique()

    # Add input data
    for ticker in tickers:
        df = data.loc[idx[ticker, :], :].droplevel('ticker', axis=0)
        df.index.name = 'datetime'
        bt_data = SignalData(dataname=df)
        cerebro.adddata(bt_data, name=ticker)

    # Run Strategy Backtest
    cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')
    cerebro.addstrategy(MLStrategy, n_positions=25, min_positions=20,
                        verbose=True, log_file='bt_log.csv')
    start = time()
    results = cerebro.run()
    ending_value = cerebro.broker.getvalue()
    duration = time() - start

    print(f'Final Portfolio Value: {ending_value:,.2f}')
    print(f'Duration: {format_time(duration)}')

main()
