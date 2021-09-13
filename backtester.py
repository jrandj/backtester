import warnings
from time import time
import numpy as np
import pandas as pd
import seaborn as sns
import backtrader as bt
import configparser

from SignalData import SignalData
from MLStrategy import MLStrategy
from FixedCommissionScheme import FixedCommissionScheme


def format_time(t):
    """TBC.

    Parameters
    ----------

    Raises
    ------

    """
    m_, s = divmod(t, 60)
    h, m = divmod(m_, 60)
    return f'{h:>02.0f}:{m:>02.0f}:{s:>02.0f}'


def main():
    config = configparser.RawConfigParser()
    config.read('config.properties')
    warnings.filterwarnings('ignore')
    pd.set_option('display.expand_frame_repr', False)
    np.random.seed(42)
    sns.set_style('darkgrid')
    cerebro = bt.Cerebro()  # create a "Cerebro" instance
    cash = 10000
    comminfo = FixedCommissionScheme()
    cerebro.broker.addcommissioninfo(comminfo)
    cerebro.broker.setcash(cash)

    # Create and Configure Cerebro Instance
    data = pd.read_hdf(config['data']['path'], 'table')
    tickers = ['NAB', 'CBA', 'BHP']
    # tickers = ['ALL', 'ANZ', 'APT', 'BHP', 'CBA', 'CSL', 'FMG', 'GMG', 'MQG', 'NAB', 'NCM', 'REA', 'RIO']
    # tickers = data['ticker'].unique()

    # Add input data
    for ticker in tickers:
        ticker_data = data.loc[data['ticker'] == ticker]
        cerebro.adddata(SignalData(dataname=ticker_data), name=ticker)

    # Run Strategy Backtest
    cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')
    # cerebro.addstrategy(MLStrategy, n_positions=25, min_positions=1,
    #                     verbose=True, log_file='bt_log.csv')
    cerebro.addstrategy(MLStrategy, verbose=True, log_file='bt_log.csv')
    cerebro.addsizer(bt.sizers.PercentSizer, percents=10)
    start = time()
    results = cerebro.run()

    ending_value = cerebro.broker.getvalue()
    cerebro.plot()
    duration = time() - start

    print(f'Final Portfolio Value: {ending_value:,.2f}')
    print(f'Duration: {format_time(duration)}')


if __name__ == "__main__":
    main()
