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

    Attributes
    ----------
    asx300_constituents : pandas.core.frame.DataFrame
        The dataframe containing tickers of ASX300 stocks at a point in time.
    benchmark_data : pandas.core.frame.DataFrame
        The dataframe containing the benchmark OHCLV data.
    benchmark_end_value : float
        The final portfolio value for the benchmark.
    benchmark_gross_lev : pandas.core.series.Series
        The leverage for the benchmark.
    benchmark_positions : pandas.core.frame.DataFrame
        A dataframe containing the daily cash and stock positions for the benchmark.
    benchmark_results : list
        The results for the benchmark.
    benchmark_returns : pandas.core.series.Series
        The returns for the benchmark.
    benchmark_stats : backtrader.analyzers.pyfolio.PyFolio
        The statistics for the benchmark.
    benchmark_transactions : pandas.core.frame.DataFrame
        A dataframe containing the transactions for the benchmark.
    cerebro : backtrader.cerebro.Cerebro
        The cerebro instance for the strategy.
    cerebro_benchmark : backtrader.cerebro.Cerebro
        The cerebro instance for the benchmark.
    comminfo : FixedCommissionScheme.FixedCommissionScheme
        The broker commissions.
    config : configparser.RawConfigParser
        The object that will read configuration from the configuration file.
    data : pandas.core.frame.DataFrame
        The dataframe containing all OHCLV ticker data.
    end_value : float
        The final portfolio value for the strategy.
    gross_lev : pandas.core.series.Series
        The leverage for the strategy.
    portfolio_stats : backtrader.analyzers.pyfolio.PyFolio
        The statistics for the portfolio.
    positions : pandas.core.frame.DataFrame
        A dataframe containing the daily cash and stock positions for the strategy.
    returns : pandas.core.series.Series
        The returns for the strategy.
    strategy_results : list
        The results for the strategy.
    tickers : list
        The tickers for the strategy (if not in bulk mode).
    transactions : pandas.core.frame.DataFrame
        A dataframe containing the transactions for the strategy.

    Methods
    -------
    add_benchmark_data():
        Add the benchmark data to the benchmark strategy.
    add_strategy_data():
        Add the ticker data to the strategy.
    clean_logs():
        Remove the existing log files.
    find_correlation():
        TBC.
    format_time()
        Format the time in hh:mm:ss.
    global_settings():
        Apply global settings.
    import_data():
        Import OHLCV data.
    run_benchmark():
        Run the benchmark strategy.
    run_benchmark_reports():
        Run quantstats reports for the benchmark.
    run_strategy():
        Run the strategy.
    run_strategy_reports():
        Run quantstats reports for the strategy.
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
    def global_settings():
        """Apply global settings.

        Parameters
        ----------

        Raises
        ------

        """
        warnings.filterwarnings('ignore')
        pd.set_option('display.expand_frame_repr', False)
        np.random.seed(42)
        sns.set_style('darkgrid')

    def add_benchmark_data(self):
        """Add the benchmark data to the benchmark strategy.

        Parameters
        ----------

        Raises
        ------

        """
        print(f"Adding ticker to benchmark: {self.config['data']['benchmark']}")
        self.cerebro_benchmark.adddata(
            TickerData(
                dataname=self.data.loc[self.data['Ticker'] == self.config['data']['benchmark']]),
            name=self.config['data']['benchmark'])

    def add_strategy_data(self):
        """Add the ticker data to the strategy.

        Parameters
        ----------

        Raises
        ------

        """
        tickers = self.tickers
        index = 0
        ignore = 0
        limit = 0
        minimum_size_vectorised_false = 1

        for i, ticker in enumerate(tickers):
            if ticker not in self.config['data']['tickers_for_exclusion'].split(','):
                ticker_data = self.data.loc[self.data['Ticker'] == ticker]
                if self.config['global_options']['vectorised'] == 'True':
                    if self.config['global_options']['strategy'] == 'Crossover':
                        limit = int(self.config['crossover_strategy_options']['crossover_strategy_sma1'])
                    elif self.config['global_options']['strategy'] == 'CrossoverPlus':
                        limit = int(self.config['crossover_plus_strategy_options']['crossover_plus_strategy_sma2'])
                    elif self.config['global_options']['strategy'] == 'HolyGrail':
                        limit = 2 * int(self.config['holygrail_strategy_options']['adx_period'])
                    elif self.config['global_options']['strategy'] == 'Pump':
                        limit = max(int(self.config['pump_strategy_options']['price_average_period']),
                                    int(self.config['pump_strategy_options']['volume_average_period']))
                    if ticker_data['Date'].size > limit:
                        print(f"Adding {ticker} to strategy with {ticker_data['Date'].size} rows")
                        self.cerebro.adddata(TickerData(dataname=ticker_data), name=ticker)
                        if self.config['global_options']['plot_tickers'] == 'False':
                            self.cerebro.datas[index].plotinfo.plot = False
                        index = index + 1
                    else:
                        ignore = ignore + 1
                        print(f"Did not add {ticker} to strategy due to insufficient data with only "
                              f"{ticker_data['Date'].size} rows")
                else:
                    if ticker_data['Date'].size > minimum_size_vectorised_false:
                        self.cerebro.adddata(TickerData(dataname=ticker_data), name=ticker)
                        if self.config['global_options']['plot_tickers'] == 'False':
                            self.cerebro.datas[index].plotinfo.plot = False
                        print(f"Adding {ticker} to strategy with {ticker_data['Date'].size} rows")
                        index = index + 1
                    else:
                        ignore = ignore + 1
                        print(f"Did not add {ticker} to strategy due to insufficient data with only "
                              f"{ticker_data['Date'].size} rows")
            else:
                print(f"Did not add {ticker} as it is intentionally excluded.")
        print(f"Loaded data for {index} tickers and discarded data for {ignore} tickers")

    def run_strategy_reports(self):
        """Run quantstats reports for the strategy.

        Parameters
        ----------

        Raises
        ------

        """
        self.returns[0].index = self.returns[0].index.tz_convert(None)
        qs.reports.html(self.returns[0], output=os.path.join("out/strategy-stats-" + time.strftime(
            "%Y%d%m-%H%M%S") + os.extsep + ".html"), title='Strategy Performance')

    def run_benchmark_reports(self):
        """Run quantstats reports for the benchmark.

        Parameters
        ----------

        Raises
        ------

        """
        self.benchmark_returns.index = self.benchmark_returns.index.tz_convert(None)
        qs.reports.html(self.benchmark_returns, output=os.path.join("out/benchmark-stats-" + time.strftime(
            "%Y%d%m-%H%M%S") + os.extsep + ".html"), title='Benchmark Performance')

    def run_benchmark(self):
        """Run the benchmark strategy.

        Parameters
        ----------

        Raises
        ------

        """
        self.cerebro_benchmark.broker.addcommissioninfo(self.comminfo)
        self.cerebro_benchmark.broker.setcash(float(self.config['broker']['cash']))
        self.add_benchmark_data()
        self.cerebro_benchmark.addobservermulti(bt.observers.BuySell, barplot=True, bardist=0.0025)
        self.cerebro_benchmark.addobserver(bt.observers.Broker)
        self.cerebro_benchmark.addobserver(bt.observers.Trades)
        self.cerebro_benchmark.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')
        self.cerebro_benchmark.addstrategy(Benchmark, verbose=True, log_file='out/benchmark_log.csv')
        # unfortunately the AllInSizer does not work with cheat on close (so need to calculate order size manually)
        # self.cerebro_benchmark.addsizer(bt.sizers.AllInSizer)
        print(f"Running benchmark...")
        results = self.cerebro_benchmark.run()  # runonce=False
        if self.config['global_options']['plot_benchmark'] == 'True':
            self.cerebro_benchmark.plot(volume=False)
        return results

    def run_strategy(self):
        """Run the strategy.

        Parameters
        ----------

        Raises
        ------
        ValueError:
            If the Strategy from config is not implemented.
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

        if self.config['global_options']['strategy'] == 'Pump':
            self.cerebro.addstrategy(Pump, verbose=True, log_file='out/strategy_log.csv')
        elif self.config['global_options']['strategy'] == 'HolyGrail':
            self.cerebro.addstrategy(HolyGrail, verbose=True, log_file='out/strategy_log.csv')
        elif self.config['global_options']['strategy'] == 'Crossover':
            self.cerebro.addstrategy(Crossover, verbose=True, log_file='out/strategy_log.csv')
        elif self.config['global_options']['strategy'] == 'CrossoverLongOnly':
            self.cerebro.addstrategy(CrossoverLongOnly, verbose=True, log_file='out/strategy_log.csv')
        elif self.config['global_options']['strategy'] == 'CrossoverPlus':
            if self.config['crossover_plus_strategy_options']['optimise'] == "True":
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
                self.cerebro.addstrategy(CrossoverPlus, verbose=True, log_file='out/strategy_log.csv')
        else:
            raise ValueError(f"Strategy {self.config['global_options']['strategy']} must be Pump, HolyGrail, "
                             f"Crossover, CrossoverLongOnly or CrossoverPlus.")
        self.cerebro.addsizer(CustomSizer, percents=float(self.config['global_options']['position_size']))
        print(f"Running {self.config['global_options']['strategy']} strategy...")
        if self.config['global_options']['vectorised'] == 'True':
            results = self.cerebro.run(runonce=True, optreturn=False)  # optreturn defaults to True
        else:
            results = self.cerebro.run(runonce=False, optreturn=False)  # optreturn defaults to True
        if self.config['global_options']['plot_enabled'] == 'True':
            if self.config['global_options']['plot_volume'] == 'True':
                self.cerebro.plot(style='candlestick')
            else:
                self.cerebro.plot(volume=False, style='candlestick')
        return results

    @staticmethod
    def clean_logs():
        """Remove the existing log files.

        Parameters
        ----------

        Raises
        ------

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

    def find_correlation(self):
        """TBC.

        Parameters
        ----------

        Raises
        ------

        """
        self.data = self.data.set_index('date')
        # correlation_data = self.data.set_index('date')
        returns_matrix = pd.DataFrame(index=self.data.index, columns=self.tickers)
        for ticker in self.tickers:
            ticker_data = self.data.loc[self.data['Ticker'] == ticker]
            returns_matrix[ticker] = ticker_data['close'].pct_change()
            print(f"Adding {ticker}")
        correlation_matrix = returns_matrix.corr()

    def import_constituents(self):
        """
        Import the .csv file containing constituents at a point in time. The format is Rank,Ticker,Company,Mkt Cap.

        :return: The constituents data.
        :rtype: pandas.core.frame.DataFrame.
        """
        constituents = self.config['data']['constituents']
        if os.path.isfile(
                os.path.join(os.path.dirname(__file__), "data", constituents + os.extsep + "csv")):
            print(f"Reading {constituents} from .csv")
            constituents_data = pd.read_csv(
                os.path.join(os.path.dirname(__file__), "data", constituents + os.extsep + "csv"),
                index_col=False)
        return constituents_data

    def import_data(self):
        """Import OHLCV data. Read from a consolidated hdf file if available, else read from a consolidated .csv file,
        else consolidate the data from various .csv files.

        Parameters
        ----------

        Raises
        ------

        """
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
            print(f"Reading data from consolidated .h5")
            data = pd.read_hdf(os.path.join(directory, "data" + os.extsep + "h5"), 'table')
        elif os.path.isfile(os.path.join(directory, "data" + os.extsep + "csv")):
            print(f"Reading data from consolidated .csv")
            data = pd.read_csv(os.path.join(directory, "data" + os.extsep + "csv"), header=0, index_col=False,
                               parse_dates=["Date"], dayfirst=True)
            data.to_hdf(os.path.join(directory, "data" + os.extsep + "h5"), 'table', append=True)
        else:
            print(f"Reading data from .csv files in directory and creating consolidated files for future use")
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

                    x = pd.read_csv(file_path, names=cols,
                                    parse_dates=["Date"], dayfirst=True, skiprows=1, dtype=dtype_dict,
                                    date_parser=dateparse)

                    # add the Ticker column if it is not in the data
                    if "Ticker" not in cols:
                        x = x.assign(Ticker=file_name)
                    # use adjusted close if configured
                    if self.config.getboolean('global_options', 'use_adjusted_close'):
                        x['Close'] = x['Adjusted Close']
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
        # benchmark_data = benchmark_data[
        #     (benchmark_data['Date'] > comparison_start) & (benchmark_data['Date'] < comparison_end)]
        print(f"Data range is between {comparison_start.date()} and {comparison_end.date()}")
        return data

    def __init__(self):
        # set initial configuration
        self.config = configparser.RawConfigParser()
        self.config.read('config.properties')
        self.global_settings()
        self.comminfo = CustomCommissionScheme()
        self.clean_logs()

        # import data
        self.data = self.import_data()
        self.constituents = self.import_constituents()
        if self.config['data']['bulk'] == 'True' and self.config['global_options']['small_cap_only'] == 'True':
            self.tickers = set(self.data['Ticker'].unique()) - set(self.constituents['Ticker'])
        elif self.config['data']['bulk'] == 'True' and self.config['global_options']['small_cap_only'] == 'False':
            self.tickers = self.data['Ticker'].unique()
        else:
            self.tickers = self.config['data']['tickers'].split(',')

        # self.find_correlation()

        # run the strategy
        self.cerebro = bt.Cerebro(stdstats=False, optreturn=False)
        if self.config['global_options']['cheat_on_close'] == 'True':
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
            if self.config['global_options']['reports'] == 'True':
                self.run_strategy_reports()
        self.portfolio_stats = self.strategy_results[0].analyzers.getbyname('pyfolio')
        self.returns, self.positions, self.transactions, self.gross_lev = self.portfolio_stats.get_pf_items()
        self.end_value = self.cerebro.broker.getvalue()

        # run the benchmark
        self.cerebro_benchmark = bt.Cerebro(stdstats=False)
        self.benchmark_results = self.run_benchmark()
        self.benchmark_stats = self.benchmark_results[0].analyzers.getbyname('pyfolio')
        self.benchmark_returns, self.benchmark_positions, self.benchmark_transactions, \
        self.benchmark_gross_lev = self.benchmark_stats.get_pf_items()
        if self.config['global_options']['reports'] == 'True':
            self.run_benchmark_reports()
        self.benchmark_end_value = self.cerebro_benchmark.broker.getvalue()


def main():
    start = time.time()
    # patch backtrader methods (to avoid raising a pull request for backtrader which is no longer maintained)
    bt.linebuffer.LinesOperation.next = Patches.next
    bt.linebuffer.LinesOperation._once_op = Patches._once_op
    backtester = Backtester()
    duration = time.time() - start
    print(f"Runtime: {backtester.format_time(duration)}")


if __name__ == "__main__":
    main()
