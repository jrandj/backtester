import os
import warnings
import time
import numpy as np
import pandas as pd
import seaborn as sns
import backtrader as bt
import configparser
import quantstats as qs

from SignalData import SignalData
from CrossoverStrategy import CrossoverStrategy
from FixedCommissionScheme import FixedCommissionScheme


def format_time(t):
    """Format the time in hh:mm:ss.

    Parameters
    ----------
    t : float
        A length of time in seconds.

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
    cerebro = bt.Cerebro(stdstats=False)  # stdstats=False

    cash = 1000000
    # Add broker commission
    comminfo = FixedCommissionScheme()
    cerebro.broker.addcommissioninfo(comminfo)
    cerebro.broker.setcash(cash)

    # Create and Configure Cerebro Instance
    data = pd.read_hdf(config['data']['path'], 'table')
    benchmark_data = pd.read_csv(config['data']['benchmark'])
    benchmark_data['date'] = pd.to_datetime(benchmark_data['date'])
    cerebro.adddata(SignalData(dataname=benchmark_data), name='XJO')
    tickers = ['CSR', 'NAB']
    # tickers = data['ticker'].unique()

    # Add input data
    for i, ticker in enumerate(tickers):
        ticker_data = data.loc[data['ticker'] == ticker]  # .sort_values(by='date')
        if ticker_data['date'].size > 200:
            print("Adding ticker: " + ticker)
            cerebro.adddata(SignalData(dataname=ticker_data), name=ticker)
            # cerebro.datas[i].plotinfo.plot = False
        else:
            print("Ignoring ticker: " + ticker)

    cerebro.addobservermulti(bt.observers.BuySell, barplot=True, bardist=0.0025)
    cerebro.addobserver(bt.observers.Broker)
    cerebro.addobserver(bt.observers.Trades)
    cerebro.addobserver(bt.observers.Benchmark, data=benchmark_data)

    # Run Strategy Backtest
    cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')


    try:
        os.remove('bt_log.csv')
    except OSError:
        pass

    cerebro.addstrategy(CrossoverStrategy, verbose=True, log_file='bt_log.csv')
    cerebro.addsizer(bt.sizers.PercentSizer, percents=2)
    start = time.time()
    results = cerebro.run()  # runonce=False

    ending_value = cerebro.broker.getvalue()
    cerebro.plot(volume=False)
    duration = time.time() - start

    print(f'Final Portfolio Value: {ending_value:,.2f}')
    print(f'Duration: {format_time(duration)}')

    portfolio_stats = results[0].analyzers.getbyname('pyfolio')
    returns, positions, transactions, gross_lev = portfolio_stats.get_pf_items()
    returns.index = returns.index.tz_convert(None)
    qs.reports.html(returns, output='stats-' + time.strftime("%Y%d%m-%H%M%S") + '.html', title='Strategy Performance')

    # "fpldraft-results-" + time.strftime("%Y%d%m-%H%M%S") + ".html", "w"


if __name__ == "__main__":
    main()
