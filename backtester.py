import argparse

import os
import warnings
import time
import numpy as np
import pandas as pd
import seaborn as sns

import Patches as Patches
import backtrader as bt
import configparser
import quantstats as qs
import glob

from CustomSizer import CustomSizer
from TickerData import TickerData
from strategies.Crossover import Crossover
from strategies.Pump import Pump
from strategies.CrossoverPlus import CrossoverPlus
from strategies.CrossoverLongOnly import CrossoverLongOnly
from strategies.HolyGrail import HolyGrail
from strategies.Benchmark import Benchmark
from CustomCommissionScheme import CustomCommissionScheme


class Backtester:
    """
    A class that wraps the Backtrader framework.

    Attributes:
        asx300_constituents: Pandas.Core.Frame.DataFrame.
            The dataframe containing tickers of ASX300 stocks at a point in time.
        benchmark_data: Pandas.Core.Frame.DataFrame.
            The dataframe containing the benchmark OHCLV data.
        benchmark_end_value: Float.
            The final portfolio value for the benchmark.
        benchmark_gross_lev: Pandas.Core.Series.Series.
            The leverage for the benchmark.
        benchmark_positions: Pandas.Core.Frame.DataFrame.
            A dataframe containing the daily cash and stock positions for the benchmark.
        benchmark_results: List.
            The results for the benchmark.
        benchmark_returns: Pandas.Core.Series.Series.
            The returns for the benchmark.
        benchmark_stats: Backtrader.Analyzers.Pyfolio.PyFolio.
            The statistics for the benchmark.
        benchmark_transactions: Pandas.Core.Frame.DataFrame.
            A dataframe containing the transactions for the benchmark.
        cerebro: Backtrader.Cerebro.Cerebro.
            The cerebro instance for the strategy.
        cerebro_benchmark: Backtrader.Cerebro.Cerebro.
            The cerebro instance for the benchmark.
        comminfo: FixedCommissionScheme.FixedCommissionScheme.
            The broker commissions.
        config: configparser.RawConfigParser.
            The object that will read configuration from the configuration file.
        data: Pandas.Core.Frame.DataFrame.
            The dataframe containing all OHCLV ticker data.
        end_value: Float.
            The final portfolio value for the strategy.
        gross_lev: Pandas.Core.Series.Series.
            The leverage for the strategy.
        portfolio_stats: Backtrader.Analyzers.Pyfolio.PyFolio.
            The statistics for the portfolio.
        positions: Pandas.Core.Frame.DataFrame.
            A dataframe containing the daily cash and stock positions for the strategy.
        returns: Pandas.Core.Series.Series.
            The returns for the strategy.
        strategy_results: List.
            The results for the strategy.
        tickers: List.
            The tickers for the strategy (if not in bulk mode).
        transactions: Pandas.Core.Frame.DataFrame.
            A dataframe containing the transactions for the strategy.
    """

    @staticmethod
    def format_time(t):
        """
        Format the time in hh:mm:ss.

        :param t: A length of time in seconds.
        :type t: Float.
        :return: The time formatted as hh:mm:ss.
        :rtype: Str.
        """
        m_, s = divmod(t, 60)
        h, m = divmod(m_, 60)
        time = f'{h:>02.0f}:{m:>02.0f}:{s:>02.0f}'
        return time

    @staticmethod
    def global_settings():
        """
        Apply global settings.

        :return: NoneType.
        :rtype: NoneType.
        """
        warnings.filterwarnings('ignore')
        pd.set_option('display.expand_frame_repr', False)
        np.random.seed(42)
        sns.set_style('darkgrid')

    def add_benchmark_data(self):
        """
        Add the benchmark data to the benchmark strategy.

        :return: NoneType.
        :rtype: NoneType.
        """
        print(f"Loading benchmark data...")
        print(f"Adding ticker to benchmark: {self.config['data']['benchmark']}")
        self.cerebro_benchmark.adddata(
            TickerData(dataname=self.data.loc[self.data['Ticker'] == self.config['data']['benchmark']]),
            name=self.config['data']['benchmark'])
        print(f"Benchmark data load complete")

    def add_strategy_data(self):
        """
        Add the ticker data to the strategy.

        :return: NoneType.
        :rtype: NoneType.
        """
        tickers = self.tickers
        index = 0
        ignore = 0
        limit = 0
        minimum_size_vectorised_false = 1

        for i, ticker in enumerate(tickers):
            if ticker not in self.config['data']['tickers_for_exclusion'].split(','):
                ticker_data = self.data.loc[self.data['Ticker'] == ticker]
                if self.config.getboolean('global_options', 'vectorised'):
                    if self.strategy == 'Crossover':
                        limit = int(self.config['crossover_strategy_options']['crossover_strategy_sma2'])
                    elif self.strategy == 'CrossoverPlus':
                        limit = int(self.config['crossover_plus_strategy_options']['crossover_plus_strategy_sma2'])
                    elif self.strategy == 'HolyGrail':
                        limit = 2 * int(self.config['holygrail_strategy_options']['adx_period'])
                    elif self.strategy == 'Pump':
                        limit = max(int(self.config['pump_strategy_options']['price_max_period']),
                                    int(self.config['pump_strategy_options']['volume_average_period']))
                    if ticker_data['Date'].size > limit:
                        print(f"Adding {ticker} to strategy with {ticker_data['Date'].size} rows")
                        self.cerebro.adddata(TickerData(dataname=ticker_data), name=ticker)
                        if not self.config.getboolean('global_options', 'plot_tickers'):
                            self.cerebro.datas[index].plotinfo.plot = False
                        index = index + 1
                    else:
                        ignore = ignore + 1
                        print(f"Did not add {ticker} to strategy due to insufficient data with only "
                              f"{ticker_data['Date'].size} rows")
                else:
                    if ticker_data['Date'].size > minimum_size_vectorised_false:
                        self.cerebro.adddata(TickerData(dataname=ticker_data), name=ticker)
                        if not self.config.getboolean('global_options', 'plot_tickers'):
                            self.cerebro.datas[index].plotinfo.plot = False
                        print(f"Adding {ticker} to strategy with {ticker_data['Date'].size} rows")
                        index = index + 1
                    else:
                        ignore = ignore + 1
                        print(f"Did not add {ticker} to strategy due to insufficient data with only "
                              f"{ticker_data['Date'].size} rows")
            else:
                print(f"Did not add {ticker} as it is intentionally excluded.")
        print(f"Loaded data for {index} tickers and discarded data for {ignore} tickers"
              f"\n{self.strategy} data load complete")

    def run_strategy_reports(self):
        """
        Run quantstats reports for the strategy.

        :return: NoneType.
        :rtype: NoneType.
        """
        self.returns[0].index = self.returns[0].index.tz_convert(None)
        qs.reports.html(self.returns[0], output=True, download_filename=os.path.join(
            "out/strategy-stats-" + time.strftime("%Y%d%m-%H%M%S") + os.extsep + "html"), title="Strategy Performance")

    def run_benchmark_reports(self):
        """
        Run quantstats reports for the benchmark.

        :return: NoneType.
        :rtype: NoneType.
        """
        self.benchmark_returns.index = self.benchmark_returns.index.tz_convert(None)
        qs.reports.html(self.benchmark_returns, output=True, download_filename=os.path.join(
            "out/benchmark-stats-" + time.strftime("%Y%d%m-%H%M%S") + os.extsep + "html"),
                        title="Benchmark Performance")

    def run_benchmark(self):
        """
        Run the benchmark.

        :return: The results.
        :rtype: List.
        """
        self.cerebro_benchmark.broker.addcommissioninfo(self.comminfo)
        self.cerebro_benchmark.broker.setcash(float(self.config['broker']['cash']))
        self.add_benchmark_data()
        self.cerebro_benchmark.addobservermulti(bt.observers.BuySell, barplot=True, bardist=0.0025)
        self.cerebro_benchmark.addobserver(bt.observers.Broker)
        self.cerebro_benchmark.addobserver(bt.observers.Trades)
        self.cerebro_benchmark.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')
        self.cerebro_benchmark.addstrategy(Benchmark, verbose=False, log_file='out/benchmark_log.csv')
        print(f"Running benchmark...")
        results = self.cerebro_benchmark.run()  # runonce=False
        if self.config.getboolean('global_options', 'plot_enabled') and \
                self.config.getboolean('global_options', 'plot_benchmark'):
            self.cerebro_benchmark.plot(volume=self.config.getboolean('global_options', 'plot_volume'),
                                        style='candlestick', iplot=False)
        return results

    def run_strategy(self):
        """
        Run the strategy.

        :return: The results.
        :rtype: List.
        :raises ValueError: If the provided strategy has no implementation.
        """
        self.cerebro.broker.addcommissioninfo(self.comminfo)
        self.cerebro.broker.setcash(float(self.config['broker']['cash']))
        # If True then cash will be increased when a stocklike asset is shorted and the calculated value for the asset
        # will be negative. If False then the cash will be deducted as operation cost and the calculated value will be
        # positive to end up with the same amount
        self.cerebro.broker.set_shortcash(False)
        # this needs to be aware of the ranges
        self.add_strategy_data()
        self.cerebro.addobservermulti(bt.observers.BuySell, barplot=True, bardist=0.0025)
        self.cerebro.addobserver(bt.observers.Broker)
        self.cerebro.addobserver(bt.observers.Trades)
        self.cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')

        if self.strategy == 'Pump':
            self.cerebro.addstrategy(Pump, verbose=self.verbose, log_file='out/strategy_log.csv')
        elif self.strategy == 'HolyGrail':
            self.cerebro.addstrategy(HolyGrail, verbose=self.verbose, log_file='out/strategy_log.csv')
        elif self.strategy == 'Crossover':
            self.cerebro.addstrategy(Crossover, verbose=self.verbose, log_file='out/strategy_log.csv')
        elif self.strategy == 'CrossoverLongOnly':
            self.cerebro.addstrategy(CrossoverLongOnly, verbose=self.verbose, log_file='out/strategy_log.csv')
        elif self.strategy == 'CrossoverPlus':
            if self.config.getboolean('crossover_plus_strategy_options', 'optimise'):
                for ii in range(int(self.config['crossover_plus_strategy_options']['sma1_low']),
                                int(self.config['crossover_plus_strategy_options']['sma1_high']),
                                int(self.config['crossover_plus_strategy_options']['sma1_step'])):
                    for jj in range(int(self.config['crossover_plus_strategy_options']['sma2_low']),
                                    int(self.config['crossover_plus_strategy_options']['sma2_high']),
                                    int(self.config['crossover_plus_strategy_options']['sma2_step'])):
                        for kk in range(int(self.config['crossover_plus_strategy_options']['RSI_crossover_low_low']),
                                        int(self.config['crossover_plus_strategy_options']['RSI_crossover_low_high']),
                                        int(self.config['crossover_plus_strategy_options']['RSI_crossover_low_step'])):
                            for ll in range(
                                    int(self.config['crossover_plus_strategy_options']['RSI_crossover_high_low']),
                                    int(self.config['crossover_plus_strategy_options']['RSI_crossover_high_high']),
                                    int(self.config['crossover_plus_strategy_options']['RSI_crossover_high_step'])):
                                for mm in range(int(self.config['crossover_plus_strategy_options']['RSI_period_low']),
                                                int(self.config['crossover_plus_strategy_options']['RSI_period_high']),
                                                int(self.config['crossover_plus_strategy_options']['RSI_period_step'])):
                                    self.cerebro.optstrategy(CrossoverPlus, sma1=ii, sma2=jj,
                                                             RSI_crossover_low=kk,
                                                             RSI_crossover_high=ll, RSI_period=mm)
            else:
                self.cerebro.addstrategy(CrossoverPlus, verbose=self.verbose, log_file='out/strategy_log.csv')
        else:
            raise ValueError(f"Strategy {self.strategy} must be Pump, HolyGrail, "
                             f"Crossover, CrossoverLongOnly or CrossoverPlus.")
        self.cerebro.addsizer(CustomSizer, percents=float(self.config['global_options']['position_size']))
        print(f"Running {self.strategy} strategy...")

        if self.config.getboolean('global_options', 'vectorised'):
            results = self.cerebro.run(runonce=True, optreturn=False)  # optreturn defaults to True
        else:
            results = self.cerebro.run(runonce=False, optreturn=False)  # optreturn defaults to True
        if self.config.getboolean('global_options', 'plot_enabled'):
            self.cerebro.plot(volume=self.config.getboolean('global_options', 'plot_volume'), style='candlestick',
                              iplot=False)
        return results

    @staticmethod
    def clean_logs():
        """
        Remove the existing log files.

        :return: NoneType.
        :rtype: NoneType.
        """
        if not os.path.exists('out'):
            os.makedirs('out')

        try:
            os.remove('out/benchmark_log.csv')
        except OSError:
            pass
        try:
            os.remove('out/strategy_log.csv')
        except OSError:
            pass

    def import_constituents(self):
        """
        Import the .csv file containing constituents at a point in time. The format is Rank,Ticker,Company,Mkt Cap.

        :return: The constituents data.
        :rtype: Pandas.Core.Frame.DataFrame.
        """
        constituents = self.config['data']['constituents']
        if os.path.isfile(
                os.path.join(os.path.dirname(__file__), "data", constituents + os.extsep + "csv")):
            print(f"Loading {constituents} from .csv")
            constituents_data = pd.read_csv(
                os.path.join(os.path.dirname(__file__), "data", constituents + os.extsep + "csv"),
                index_col=False)
        return constituents_data

    def import_data(self):
        """
        Import OLHCV data. Read from a consolidated hdf file if available, else read from a consolidated .csv file,
        else consolidate the data from various .csv files.

        :return: The imported data.
        :rtype: Pandas.Core.Frame.DataFrame.
        """
        print(f"Loading {self.strategy} data...")
        if len(self.config['data']['path']) > 0:
            directory = self.config['data']['path']
        else:
            directory = os.path.join(os.path.dirname(__file__), "data", self.config['data']['path'])

        def dateparse(x):
            if self.config['data']['date_format'] == 'yyyymmdd':
                return pd.datetime.strptime(x, "%Y%m%d")
            elif self.config['data']['date_format'] == 'dd-mm-yyyy':
                return pd.datetime.strptime(x, "%d-%m-%Y")
            else:
                raise ValueError(f"Unexpected date format for {x} with parsing format "
                                 f"{self.config['data']['date_format']}. Date format must "
                                 f"be yyyymmdd or dd-mm-yyyy.")

        # read data
        if os.path.isfile(os.path.join(directory, "data" + os.extsep + "h5")):
            print(f"Loading data from consolidated .h5")
            data = pd.read_hdf(os.path.join(directory, "data" + os.extsep + "h5"), 'table')

            if self.config.getboolean('global_options', 'use_adjusted_close'):
                data['Close'] = np.where(data['Adjusted Close'].notnull() & data['Adjusted Close'] != 0,
                                         data['Adjusted Close'], data['Close'])
        elif os.path.isfile(os.path.join(directory, "data" + os.extsep + "csv")):
            print(f"Loading data from consolidated .csv")
            data = pd.read_csv(os.path.join(directory, "data" + os.extsep + "csv"), header=0, index_col=False,
                               parse_dates=["Date"], dayfirst=True)
            if self.config.getboolean('global_options', 'use_adjusted_close'):
                data['Close'] = np.where(data['Adjusted Close'].notnull() & data['Adjusted Close'] != 0,
                                         data['Adjusted Close'], data['Close'])
            data.to_hdf(os.path.join(directory, "data" + os.extsep + "h5"), 'table', append=True)
        else:
            print(f"Loading data from .csv files in directory and creating consolidated files for future use")
            data = pd.DataFrame()
            all_files = glob.glob(os.path.join(directory, "*.csv"))

            for file_path in all_files:
                file_name = os.path.basename(file_path).split(os.extsep)[0]
                if file_name != os.path.join(self.config['data']['constituents']):
                    cols = self.config['data']['cols'].split(",")
                    if "Adjusted Close" in cols and "Ticker" in cols:
                        dtype_dict = {"Adjusted Close": float, "Ticker": str}
                    elif "Adjusted Close" in cols:
                        dtype_dict = {"Adjusted Close": float}
                    elif "Ticker" in cols:
                        dtype_dict = {"Ticker": str}

                    x = pd.read_csv(file_path, names=cols, parse_dates=["Date"], dayfirst=True, skiprows=1,
                                    dtype=dtype_dict, date_parser=dateparse)

                    # add the Ticker column if it is not in the data
                    if "Ticker" not in cols:
                        x = x.assign(Ticker=file_name)
                    # use adjusted close if configured (does not work at present because no adjusted low, open, high)
                    if self.config.getboolean('global_options', 'use_adjusted_close'):
                        x['Close'] = np.where(x['Adjusted Close'].notnull() & x['Adjusted Close'] != 0,
                                              x['Adjusted Close'], x['Close'])
                    data = pd.concat([data, x], ignore_index=True)
                    os.path.join(directory, "data" + os.extsep + "csv")

            data.to_csv(os.path.join(directory, "data" + os.extsep + "csv"), sep=",", index=False, date_format='%Y%m%d')
            data.to_hdf(os.path.join(directory, "data" + os.extsep + "h5"), 'table', append=True)

        # apply date ranges
        comparison_start = max(data['Date'].min(),
                               data[data['Ticker'] == self.config['data']['benchmark']]['Date'].min())
        comparison_end = min(data['Date'].max(), data[data['Ticker'] == self.config['data']['benchmark']]['Date'].max())
        # allow override from config
        if len(self.config['data']['start_date']) > 0 and pd.to_datetime(self.config['data']['start_date'],
                                                                         format='%d/%m/%Y') < comparison_end:
            comparison_start = pd.to_datetime(self.config['data']['start_date'])
        if len(self.config['data']['end_date']) > 0 and pd.to_datetime(self.config['data']['end_date'],
                                                                       format='%d/%m/%Y') > comparison_start:
            comparison_end = pd.to_datetime(self.config['data']['end_date'])
        data = data[(data['Date'] > comparison_start) & (data['Date'] < comparison_end)]
        self.start_date = comparison_start
        self.end_date = comparison_end
        print(f"Data range is between {self.start_date.date().strftime('%d/%m/%Y')} and "
              f"{self.end_date.date().strftime('%d/%m/%Y')}")
        return data

    def __init__(self, strategy, verbose):
        # read input arguments
        self.strategy_cagr = None
        self.benchmark_cagr = None
        self.strategy = strategy
        self.verbose = verbose

        # set initial configuration
        self.end_date = None
        self.start_date = None
        self.config = configparser.RawConfigParser()
        self.config.read('config.properties')
        self.global_settings()
        self.verbose = verbose
        self.comminfo = CustomCommissionScheme()
        self.clean_logs()
        apply_patches()

        # import data
        self.data = self.import_data()
        self.constituents = self.import_constituents()
        if self.config.getboolean('data', 'bulk') and self.config.getboolean('global_options', 'small_cap_only'):
            self.tickers = set(self.data['Ticker'].unique()) - set(self.constituents['Ticker'])
        elif self.config.getboolean('data', 'bulk') and not self.config.getboolean('global_options', 'small_cap_only'):
            self.tickers = self.data['Ticker'].unique()
        else:
            self.tickers = self.config['data']['tickers'].split(',')

        # run the strategy
        self.cerebro = bt.Cerebro(stdstats=False, optreturn=False)
        if self.config.getboolean('global_options', 'cheat_on_close'):
            self.cerebro.broker.set_coc(True)
        self.strategy_results = self.run_strategy()
        self.returns, self.positions, self.transactions, self.gross_lev = [None] * len(self.strategy_results[0]), [
            None] * len(self.strategy_results[0]), [None] * len(self.strategy_results[0]), [None] * len(
            self.strategy_results[0])
        if type(self.strategy_results[0]) is list:
            object_for_iteration = self.strategy_results[0]
        else:
            object_for_iteration = self.strategy_results
        for idx, val in enumerate(object_for_iteration):
            self.portfolio_stats = val.analyzers.getbyname('pyfolio')
            self.returns[idx], self.positions[idx], self.transactions[idx], self.gross_lev[idx] \
                = self.portfolio_stats.get_pf_items()
            if self.config.getboolean('global_options', 'reports'):
                self.run_strategy_reports()
        self.portfolio_stats = self.strategy_results[0].analyzers.getbyname('pyfolio')
        self.returns, self.positions, self.transactions, self.gross_lev = self.portfolio_stats.get_pf_items()
        self.end_value = self.cerebro.broker.getvalue()
        self.calculate_strategy_performance()

        # run the benchmark
        self.cerebro_benchmark = bt.Cerebro(stdstats=False)
        self.cerebro_benchmark.broker.set_coc(True)
        self.benchmark_results = self.run_benchmark()
        self.benchmark_stats = self.benchmark_results[0].analyzers.getbyname('pyfolio')
        self.benchmark_returns, self.benchmark_positions, self.benchmark_transactions, \
        self.benchmark_gross_lev = self.benchmark_stats.get_pf_items()
        if self.config.getboolean('global_options', 'reports'):
            self.run_benchmark_reports()
        self.benchmark_end_value = self.cerebro_benchmark.broker.getvalue()
        self.calculate_benchmark_performance()

    def calculate_strategy_performance(self):
        """
        Calculate the return for the strategies.

        :return: NoneType.
        :rtype: NoneType.
        """
        elapsed_days = (self.end_date - self.start_date).days
        self.strategy_cagr = 100 * (((self.cerebro.broker.fundvalue * self.cerebro.broker.fundshares) /
                                     self.cerebro.broker.startingcash) ** (1 / (elapsed_days / 365.25)) - 1)
        total = self.cerebro.broker.fundvalue * self.cerebro.broker.fundshares
        print(f"{self.strategy} portfolio value (incl. cash): {total:.2f}")
        print(f"{self.strategy} CAGR: {self.strategy_cagr:.2f}% (over "
              f"{(elapsed_days / 365.25):.2f} years with {len(self.transactions)} trades). Start date "
              f"{self.start_date.date()} and end date {self.end_date.date()}")
        print(f"Finished running {self.strategy} strategy\n")

    def calculate_benchmark_performance(self):
        """
        Calculate the return for the benchmark strategy.

        :return: NoneType.
        :rtype: NoneType.
        """
        elapsed_days = (self.end_date - self.start_date).days
        self.benchmark_cagr = 100 * (((self.cerebro_benchmark.broker.fundvalue *
                                       self.cerebro_benchmark.broker.fundshares) /
                                      self.cerebro_benchmark.broker.startingcash) ** (1 / (elapsed_days / 365.25)) - 1)
        total = self.cerebro_benchmark.broker.fundvalue * self.cerebro_benchmark.broker.fundshares
        print(f"Benchmark portfolio value (incl. cash): {total:.2f}")
        print(f"Benchmark CAGR: {self.benchmark_cagr:.2f}% (over "
              f"{(elapsed_days / 365.25):.2f} years. Start date {self.start_date.date()} and end date "
              f"{self.end_date.date()}")
        print(f"Finished running Benchmark strategy\n")


def main():
    """
    The main() method.

    :return: NoneType.
    :rtype: NoneType.
    """
    start = time.time()
    strategy, verbose = parse_input()
    backtester = Backtester(strategy, verbose)
    duration = time.time() - start
    print(f"Runtime: {backtester.format_time(duration)}")


def apply_patches():
    """
    Patch backtrader methods (to avoid raising a pull request for backtrader which is no longer maintained).

    :return: NoneType.
    :rtype: NoneType.
    """
    bt.linebuffer.LinesOperation.next = Patches.next
    bt.linebuffer.LinesOperation._once_op = Patches._once_op


def parse_input():
    """
    Parse the command line input.
    :return: A string containing the strategy.
    :rtype: Str.
    :return: A boolean value which determines if detailed logging is required.
    :rtype: Bool.
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("-strategy", required=True, help="The strategy to run (Pump, HolyGrail, Crossover, "
                                                     "CrossoverLongOnly or CrossoverPlus)")
    ap.add_argument("-verbose", required=False, help="True for detailed logging, and False otherwise")
    args = vars(ap.parse_args())
    strategy = args.get('strategy')
    verbose = args.get('verbose')
    return strategy, verbose


if __name__ == "__main__":
    main()
