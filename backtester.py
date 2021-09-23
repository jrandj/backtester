import os
import warnings
import time
import numpy as np
import pandas as pd
import seaborn as sns
import backtrader as bt
import configparser
import quantstats as qs

from TickerData import TickerData
from CrossoverStrategy import CrossoverStrategy
from Benchmark import Benchmark
from FixedCommissionScheme import FixedCommissionScheme


class Backtester:
    """
    TBC

    Attributes
    ----------
    leagueID : sequence
        The unique identifier for the league.

    Methods
    -------
    parse_input()
        Parse the user input.
    """

    @staticmethod
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

    @staticmethod
    def global_settings(self):
        """Format the time in hh:mm:ss.

        Parameters
        ----------

        Raises
        ------

        """
        warnings.filterwarnings('ignore')
        pd.set_option('display.expand_frame_repr', False)
        np.random.seed(42)
        sns.set_style('darkgrid')

    def import_data(self):
        """Format the time in hh:mm:ss.

        Parameters
        ----------

        Raises
        ------

        """
        for i, ticker in enumerate(self.tickers):
            ticker_data = self.data.loc[self.data['ticker'] == ticker]  # .sort_values(by='date')
            if ticker_data['date'].size > 200:
                print("Adding ticker: " + ticker)
                self.cerebro.adddata(TickerData(dataname=ticker_data), name=ticker)
                # cerebro.datas[i].plotinfo.plot = False
            else:
                print("Ignoring ticker: " + ticker)

    def run_reports(self):
        self.returns.index = self.returns.index.tz_convert(None)
        qs.reports.html(self.returns, output='stats-' + time.strftime("%Y%d%m-%H%M%S") + '.html',
                        title='Strategy Performance')

    def run(self):
        """Format the time in hh:mm:ss.

        Parameters
        ----------

        Raises
        ------

        """
        start = time.time()
        self.cerebro.broker.addcommissioninfo(self.comminfo)
        self.cerebro.broker.setcash(self.cash)
        self.cerebro.addobservermulti(bt.observers.BuySell, barplot=True, bardist=0.0025)
        self.cerebro.addobserver(bt.observers.Broker)
        self.cerebro.addobserver(bt.observers.Trades)
        self.cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')

        self.cerebro.addstrategy(CrossoverStrategy, verbose=True, log_file='bt_log.csv')
        self.cerebro.addsizer(bt.sizers.PercentSizer, percents=2)

        results = self.cerebro.run()  # runonce=False

        self.cerebro.plot(volume=False)

        duration = time.time() - start

        print(f'Final Portfolio Value: {self.ending_value:,.2f}')
        print(f'Duration: {self.format_time(duration)}')

        return results

    @staticmethod
    def prepare_log(self):
        """Format the time in hh:mm:ss.

        Parameters
        ----------

        Raises
        ------

        """
        try:
            os.remove('bt_log.csv')
        except OSError:
            pass

    def __init__(self):
        self.config = configparser.RawConfigParser()
        self.config.read('config.properties')
        self.global_settings()

        # The strategy
        self.cerebro = bt.Cerebro(stdstats=False)  # stdstats=False
        self.cash = self.config['broker']['cash']
        self.comminfo = FixedCommissionScheme()
        self.data = pd.read_hdf(self.config['data']['path'], 'table').sort_values(by='date', ascending=True)
        self.tickers = self.config['data']['tickers']
        self.results = self.run()
        self.portfolio_stats = self.results[0].analyzers.getbyname('pyfolio')
        self.returns, self.positions, self.transactions, self.gross_lev = self.portfolio_stats.get_pf_items()
        self.run_reports()

        self.ending_value = self.cerebro_benchmark.broker.getvalue()


def main():
    # Create and Configure Cerebro Instance

    # Run Strategy Backtest

    # Remove the dropped elements from data

    # "fpldraft-results-" + time.strftime("%Y%d%m-%H%M%S") + ".html", "w"

    # Benchmark
    cerebro_benchmark = bt.Cerebro(stdstats=False)  # stdstats=False
    cerebro_benchmark.broker.addcommissioninfo(comminfo)
    cerebro_benchmark.broker.setcash(cash)
    benchmark_data = pd.read_csv(config['data']['benchmark'], parse_dates=['date'], dayfirst=True)
    benchmark_data = benchmark_data.sort_values(by='date', ascending=True)
    # benchmark_data['date'] = pd.to_datetime(benchmark_data['date'])
    cerebro_benchmark.adddata(TickerData(dataname=benchmark_data), name='XJO')

    # Find date range for strategy
    comparison_start = max(data['date'].min(), benchmark_data['date'].min())
    comparison_end = min(data['date'].max(), benchmark_data['date'].max())

    cerebro_benchmark.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')
    cerebro_benchmark.addstrategy(Benchmark, data=benchmark_data, verbose=True)

    start = time.time()
    results = cerebro_benchmark.run()  # runonce=False

    cerebro_benchmark.plot(volume=False)
    duration = time.time() - start


if __name__ == "__main__":
    main()
