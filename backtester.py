import os
import warnings
import time
import numpy as np
import pandas as pd
import seaborn as sns
import backtrader as bt
import configparser
import quantstats as qs
import glob
# from yahooquery import Ticker

from CustomSizer import CustomSizer
from TickerData import TickerData
from CrossoverStrategy import CrossoverStrategy
from PumpStrategy import PumpStrategy
from CrossoverPlusStrategy import CrossoverPlusStrategy
# from PairStrategy import PairStrategy
from Benchmark import Benchmark
from CustomCommissionScheme import CustomCommissionScheme


class Backtester:
    """A class that wraps the Backtrader framework.

    Attributes
    ----------
    returns.index : pandas.core.indexes.datetimes.DatetimeIndex
        A datetime index for the strategy returns.
    benchmark_returns.index : pandas.core.indexes.datetimes.DatetimeIndex
        A datetime index for the benchmark returns.
    cash : float
        The cash available for the strategies.
    bulk : str
        True if all tickers are to be used, False if the tickers are being provided.
    data : pandas.core.frame.DataFrame
        The dataframe containing all OHCLV ticker data.
    asx300_constituents : pandas.core.frame.DataFrame
        The dataframe containing tickers of ASX300 stocks at a point in time.
    benchmark_data : pandas.core.frame.DataFrame
        The dataframe containing the benchmark OHCLV data.
    cerebro : backtrader.cerebro.Cerebro
        The cerebro instance for the strategy.
    comminfo : FixedCommissionScheme.FixedCommissionScheme
        The broker commissions.
    returns : pandas.core.series.Series
        The returns for the strategy.
    positions : pandas.core.frame.DataFrame
        A dataframe containing the daily cash and stock positions for the strategy.
    transactions : pandas.core.frame.DataFrame
        A dataframe containing the transactions for the strategy.
    gross_lev : pandas.core.series.Series
        The leverage for the strategy.
    benchmark_returns : pandas.core.series.Series
        The returns for the benchmark.
    benchmark_positions : pandas.core.frame.DataFrame
        A dataframe containing the daily cash and stock positions for the benchmark.
    benchmark_transactions : pandas.core.frame.DataFrame
        A dataframe containing the transactions for the benchmark.
    benchmark_gross_lev : pandas.core.series.Series
        The leverage for the benchmark.
    end_value : float
        The final portfolio value for the strategy.
    benchmark_end_value : float
        The final portfolio value for the benchmark.

    Methods
    -------
    format_time()
        Format the time in hh:mm:ss.
    global_settings():
        Apply global settings.
    add_benchmark_data():
        Add the benchmark data to the benchmark strategy.
    add_strategy_data():
        Add the ticker data to the strategy.
    run_strategy_reports():
        Run quantstats reports for the strategy.
    run_benchmark_reports():
        Run quantstats reports for the benchmark.
    run_benchmark():
        Run the benchmark strategy.
    run_strategy():
        Run the strategy.
    clean_logs():
        Remove the existing log files.
    import_data():
        Import OHLCV data.
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
                dataname=self.benchmark_data.loc[self.benchmark_data['ticker'] == self.config['data']['benchmark']]),
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
            ticker_data = self.data.loc[self.data['ticker'] == ticker]
            if self.config['global_options']['vectorised'] == 'True':
                if self.config['global_options']['strategy'] == 'CrossOver':
                    limit = int(self.config['crossover_strategy_options']['crossover_sma2'])
                elif self.config['global_options']['strategy'] == 'CrossoverPlus':
                    limit = int(self.config['crossover_plus_strategy_options']['crossover_plus_sma2'])
                if ticker_data['date'].size > limit:
                    print(f"Adding {ticker} to strategy with {ticker_data['date'].size} rows")
                    self.cerebro.adddata(TickerData(dataname=ticker_data), name=ticker)
                    if self.config['global_options']['plot_tickers'] == 'False':
                        self.cerebro.datas[index].plotinfo.plot = False
                    index = index + 1
                else:
                    ignore = ignore + 1
                    print(f"Did not add {ticker} to strategy due to insufficient data with only "
                          f"{ticker_data['date'].size} rows")
            else:
                if ticker_data['date'].size > minimum_size_vectorised_false:
                    self.cerebro.adddata(TickerData(dataname=ticker_data), name=ticker)
                    if self.config['global_options']['plot_tickers'] == 'False':
                        self.cerebro.datas[index].plotinfo.plot = False
                    print(f"Adding {ticker} to strategy with {ticker_data['date'].size} rows")
                    index = index + 1
                else:
                    ignore = ignore + 1
                    print(f"Did not add {ticker} to strategy due to insufficient data with only "
                          f"{ticker_data['date'].size} rows")
        print(f"Loaded data for {index} tickers and discarded data for {ignore} tickers")

    def run_strategy_reports(self):
        """Run quantstats reports for the strategy.

        Parameters
        ----------

        Raises
        ------

        """
        self.returns.index = self.returns.index.tz_convert(None)
        qs.reports.html(self.returns, output='strategy-stats-' + time.strftime("%Y%d%m-%H%M%S") + '.html',
                        title='Strategy Performance')

    def run_benchmark_reports(self):
        """Run quantstats reports for the benchmark.

        Parameters
        ----------

        Raises
        ------

        """
        self.benchmark_returns.index = self.benchmark_returns.index.tz_convert(None)
        qs.reports.html(self.benchmark_returns, output='benchmark-stats-' + time.strftime("%Y%d%m-%H%M%S") + '.html',
                        title='Benchmark Performance')

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
        self.cerebro_benchmark.addstrategy(Benchmark, verbose=True, log_file='benchmark_log.csv')
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
        self.add_strategy_data()
        self.cerebro.addobservermulti(bt.observers.BuySell, barplot=True, bardist=0.0025)
        self.cerebro.addobserver(bt.observers.Broker)
        self.cerebro.addobserver(bt.observers.Trades)
        self.cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')
        if self.config['global_options']['strategy'] == 'Pump':
            self.cerebro.addstrategy(PumpStrategy, verbose=True, log_file='strategy_log.csv')
        elif self.config['global_options']['strategy'] == 'Crossover':
            self.cerebro.addstrategy(CrossoverStrategy, verbose=True, log_file='strategy_log.csv')
        elif self.config['global_options']['strategy'] == 'CrossoverPlus':
            # self.cerebro.addstrategy(CrossoverPlusStrategy, verbose=True, log_file='strategy_log.csv')
            # build this yourself
            self.cerebro.optstrategy(CrossoverPlusStrategy,
                                     sma1=[20, 30, 40, 50, 60],
                                     sma2=[50, 60, 70, 80, 90],
                                     RSI_crossover_low=[20, 30, 40],
                                     RSI_crossover_high=[60, 70, 80],
                                     RSI_period=[14, 17, 21, 24, 28],
                                     verbose=True, log_file='strategy_log.csv')
        else:
            raise ValueError(f"Strategy {self.config['global_options']['strategy']} must be Pump or Crossover.")
        self.cerebro.addsizer(CustomSizer, percents=float(self.config['global_options']['position_size']))
        print(f"Running {self.config['global_options']['strategy']} strategy...")
        if self.config['global_options']['vectorised'] == 'True':
            results = self.cerebro.run(runonce=True, optreturn=False)  # optreturn defaults to True
        else:
            results = self.cerebro.run(runonce=False, optreturn=False)  # optreturn defaults to True
        if self.config['global_options']['plot_enabled'] == 'True':
            if self.config['global_options']['plot_volume'] == 'True':
                self.cerebro.plot()
            else:
                self.cerebro.plot(volume=False)
        return results

    @staticmethod
    def clean_logs():
        """Remove the existing log files.

        Parameters
        ----------

        Raises
        ------

        """
        try:
            os.remove('benchmark_log.csv')
        except OSError:
            pass
        try:
            os.remove('strategy_log.csv')
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
            ticker_data = self.data.loc[self.data['ticker'] == ticker]
            returns_matrix[ticker] = ticker_data['close'].pct_change()
            print(f"Adding {ticker}")
        correlation_matrix = returns_matrix.corr()

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
            directory = os.path.join(os.path.dirname(__file__), "data",
                                     self.config['data']['path'])

        # read asx300 constituents data
        if os.path.isfile(
                os.path.join(os.path.dirname(__file__), "data", "asx300_constituents_221021" + os.extsep + "csv")):
            print(f"Reading asx300 constituents (as at 22/10/21) from .csv")
            asx300_constituents = pd.read_csv(
                os.path.join(os.path.dirname(__file__), "data", "asx300_constituents_221021" + os.extsep + "csv"),
                index_col=False)

        # read data
        if os.path.isfile(os.path.join(directory, "data" + os.extsep + "h5")):
            print(f"Reading data from consolidated .h5")
            data = pd.read_hdf(os.path.join(directory, "data" + os.extsep + "h5"), 'table')
        elif os.path.isfile(os.path.join(directory, "data" + os.extsep + "csv")):
            print(f"Reading data from consolidated .csv")
            data = pd.read_csv(os.path.join(directory, "data" + os.extsep + "csv"), header=0, index_col=False,
                               parse_dates=["date"], dayfirst=True)
            data.to_hdf(os.path.join(directory, "data" + os.extsep + "h5"), 'table', append=True)
        else:
            print(f"Reading data from .csv in directory and creating consolidated files for future use")
            data = pd.DataFrame()
            all_files = glob.glob(os.path.join(directory, "*.csv"))

            def dateparse(x):
                return pd.datetime.strptime(x, "%d/%m/%Y")

            for file_name in all_files:
                if file_name != os.path.join(directory, self.config['data']['benchmark'] + os.extsep + "csv"):
                    x = pd.read_csv(file_name, names=["date", "open", "high", "low", "close", "volume", "ticker"],
                                    parse_dates=["date"], dayfirst=True, dtype={"ticker": str}, skiprows=1,
                                    date_parser=dateparse)
                    data = pd.concat([data, x], ignore_index=True)
                    os.path.join(directory, "data" + os.extsep + "csv")
            data.to_csv(os.path.join(directory, "data" + os.extsep + "csv"), sep=",",
                        header=["date", "open", "high", "low", "close", "volume", "ticker"], index=False)
            data.to_hdf(os.path.join(directory, "data" + os.extsep + "h5"), 'table', append=True)

        # read benchmark data
        benchmark_data = pd.read_csv(
            os.path.join(directory, self.config['data']['benchmark'] + os.extsep + "csv"),
            parse_dates=['date'], dayfirst=True)

        # apply date ranges
        comparison_start = max(data['date'].min(), benchmark_data['date'].min())
        comparison_end = min(data['date'].max(), benchmark_data['date'].max())
        # allow override from config
        if len(self.config['data']['start_date']) > 0 and pd.to_datetime(self.config['data']['start_date'],
                                                                         format='%d/%m/%Y') < comparison_end:
            comparison_start = pd.to_datetime(self.config['data']['start_date'])
        if len(self.config['data']['end_date']) > 0 and pd.to_datetime(self.config['data']['end_date'],
                                                                       format='%d/%m/%Y') > comparison_start:
            comparison_end = pd.to_datetime(self.config['data']['end_date'])
        data = data[(data['date'] > comparison_start) & (data['date'] < comparison_end)]
        benchmark_data = benchmark_data[
            (benchmark_data['date'] > comparison_start) & (benchmark_data['date'] < comparison_end)]
        print(f"Data range is between {comparison_start.date()} and {comparison_end.date()}")
        return data, benchmark_data, asx300_constituents

    def __init__(self):
        # set initial configuration
        self.config = configparser.RawConfigParser()
        self.config.read('config.properties')
        self.global_settings()
        self.comminfo = CustomCommissionScheme()
        self.clean_logs()

        # import data
        self.data, self.benchmark_data, self.asx300_constituents = self.import_data()
        if self.config['data']['bulk'] == 'True' and self.config['global_options']['small_cap_only'] == 'True':
            self.tickers = set(self.data['ticker'].unique()) - set(self.asx300_constituents['Ticker'])
        elif self.config['data']['bulk'] == 'True' and self.config['global_options']['small_cap_only'] == 'False':
            self.tickers = self.data['ticker'].unique()
        else:
            self.tickers = self.config['data']['tickers'].split(',')

        # self.find_correlation()

        # run the strategy
        self.cerebro = bt.Cerebro(stdstats=False)
        if self.config['global_options']['cheat_on_close'] == 'True':
            self.cerebro.broker.set_coc(True)
        self.strategy_results = self.run_strategy()
        # self.portfolio_stats = self.strategy_results[0].analyzers.getbyname('pyfolio')
        # self.returns, self.positions, self.transactions, self.gross_lev = self.portfolio_stats.get_pf_items()
        if self.config['global_options']['reports'] == 'True':
            self.run_strategy_reports()
        self.end_value = self.cerebro.broker.getvalue()

        # run the benchmark
        self.cerebro_benchmark = bt.Cerebro(stdstats=False)
        self.benchmark_results = self.run_benchmark()
        self.benchmark_stats = self.benchmark_results[0].analyzers.getbyname('pyfolio')
        self.benchmark_returns, self.benchmark_positions, self.benchmark_transactions, self.benchmark_gross_lev = self.benchmark_stats.get_pf_items()
        if self.config['global_options']['reports'] == 'True':
            self.run_benchmark_reports()
        self.benchmark_end_value = self.cerebro_benchmark.broker.getvalue()


def main():
    start = time.time()
    backtester = Backtester()
    duration = time.time() - start
    print(f"Runtime: {backtester.format_time(duration)}")


if __name__ == "__main__":
    main()
