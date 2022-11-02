<p align="center">
    <br>
    <br>
    <a href="https://docs.conda.io/projects/conda/en/latest/release-notes.html#id1" alt="Conda version">
        <img src="https://img.shields.io/badge/Anaconda.org-4.13.0-blue.svg?style=flat-square" />
    </a>
    <a href="https://img.shields.io/github/license/jrandj/backtester" alt="License">
        <img src="https://img.shields.io/github/license/jrandj/backtester" />
    </a>
</p>

# Backtester
Backtester is a Python application for testing trading strategies against historical data. Backtester is heavily reliant on the [Backtrader](https://github.com/mementum/backtrader) framework.

## Architecture
The package structure is shown below:
	<p align="center">
	<img src="/res/packages.png">
	</p>

The class structure is shown below:
	<p align="center">
	<img src="/res/classes.png">
	</p>

The diagrams have been generated using pyreverse:
```bash
pyreverse -o png .
```

## Data
The data used for the shown results is OHLCV with the following format:

| date       | open      | high      | low       | close     | volume | ticker |
|------------|-----------|-----------|-----------|-----------|--------|--------|
| 2000-01-21 | 554.73761 | 554.73761 | 508.50955 | 554.73761 | 26     | ZNT    |

This corresponds to the following line in `config.properties`:
```bash
cols=Date,Open,High,Low,Close,Volume,Ticker
```

Data was obtained from [Premium Data](https://www.premiumdata.net/products/premiumdata/asxhistorical.php) at 04/05/2018. The data covers 2,628 stocks listed on the ASX between 1992-05-29 and 2018-05-04.

By default the sample .csv files in the `data` subdirectory will be used when the application is run. To use a wider set of data update the path variable in `config.properties` to point to a folder with additional data.

The following data format is also supported:
```bash
Date,Low,Open,Volume,High,Close,Adjusted Close
```

## Results
The table below summarises the results for the strategies.

| Strategy          | Asset | Start Date | End Date   | Positions | Position Size | CAGR   | Sharpe Ratio | Skew  | Kurtosis | Maximum Drawdown | Maximum Monthly Return | Recovery Factor |
|-------------------|-------|------------|------------|-----------|---------------|--------|--------------|-------|----------|------------------|------------------------|-----------------|
| Crossover         | ASX   | 29/05/1992 | 04/05/2018 | 4         | 25%           | 4.55%  | 0.33         | 2.83  | 73.55    | -41.13%          | 24.91%                 | 5.27            |
| Crossover         | ASX   | 29/05/1992 | 04/05/2018 | 10        | 10%           | 2.42%  | 0.21         | 9.65  | 510.96   | -53.72%          | 61.62%                 | 1.59            |
| CrossoverLongOnly | ASX   | 17/04/2015 | 02/09/2022 | 4         | 25%           | -2.82% | -0.51        | -0.78 | 17.18    | -24.37%          | 4.98%                  | -0.78           |
| CrossoverPlus     | ASX   | 29/05/1992 | 04/05/2018 | 4         | 25%           | 5.94%  | 0.35         | 1.22  | 32.38    | -62.78%          | 46.81%                 | 5.53            |
| CrossoverPlus     | ASX   | 29/05/1992 | 04/05/2018 | 10        | 10%           | 3.26%  | 0.27         | 2.23  | 96.23    | -64.27%          | 25.9%                  | 2.02            |
| Pump              | ASX   | 29/05/1992 | 04/05/2018 | 4         | 25%           | 6.31%  | 0.42         | 0.6   | 120.1    | -24.64%          | 15.05%                 | 15.79           |
| Pump              | ASX   | 29/05/1992 | 04/05/2018 | 10        | 10%           | 5.58%  | 0.63         | -0.43 | 94.91    | -13.29%          | -10.28%                | 23.26           |
| HolyGrail         | ASX   | 29/05/1992 | 04/05/2018 | 4         | 25%           | 1.38%  | 0.17         | 0.29  | 9.26     | -43.14%          | 39.44%                 | 0.99            |
| HolyGrail         | ASX   | 29/05/1992 | 04/05/2018 | 10        | 10%           | 0.31%  | 0.08         | 0.02  | 9.19     | -30.73%          | 21.73%                 | 0.27            |
| Benchmark         | XJO   | 29/05/1992 | 04/05/2018 | 1         | 100%          | 5.04%  | 0.4          | -0.34 | 5.23     | -53.93%          | 8.18%                  | 4.78            |

The terms are defined:
* **Strategy:** The name of the strategy to be tested. Corresponds to a strategy implementation in the strategies folder.
* **Asset:** The universe of assets.
* **Start Date:** The earliest date in the dataset.
* **End Date:** The latest date in the dataset.
* **Positions:** The number of positions that can be held by the strategy.
* **Position Size:** The percentage of the total portfolio to be used when entering a position.
* **CAGR:** Compound Annual Growth Rate.
* **Sharpe Ratio:** A measure of the excess returns compared to the volatility. Ratios above 1 are generally considered good.
* **Skew:** A measure of the distortion of symmetrical distribution or asymmetry in the results. A positive skew indicates the tail of a distribution curve is longer on the right side, and vice-versa for a negative skew.
* **Kurtosis:** A measure of extreme values in either tail. A high kurtosis implies an occasional extreme return.
* **Maximum Drawdown:** The maximum observed loss from peak to trough of a portfolio.
* **Maximum Monthly Return:** The largest return in any month.
* **Recovery Factor:** The absolute value of the returns divided by the Maximum Drawdown. Indicates a strategies ability to overcome a drawdown.

### Assumptions
The following assumptions or decisions have been made:
1. The brokerage commission fee structure is as per [Nabtrade](https://www.nabtrade.com.au/investor/pricing). This is assumed to have been available historically.
1. There is only 1 open position per asset.
1. Orders from trading do not impact the market price.
1. No rebalancing is done for the positions. Entry and exit conditions are defined in the individual strategies.

### Strategies
Sample results for each strategy are shown below. Where results for multiple strategies are shown above, the graphs below are for runs with 4 long positions of 25% the portfolio value each.


#### Crossover
An implementation of a 50-day and 200-day moving average crossover strategy provided in [Crossover](/strategies/Crossover.py). This strategy will buy the individual equity when long and sell it when short.

<p align="center">
	<img src="/res/Crossover.png" width="600" height="350">
</p>

#### CrossoverPlus
An implementation of a strategy using 50-day and 200-day moving averages, the Percent Price Oscillator (PPO) indicator, and the Relative Strength Index (RSI) indicator is available in [CrossoverPlus](/strategies/CrossoverPlus.py).

<p align="center">
	<img src="/res/CrossoverPlus.png" width="600" height="350">
</p>

#### CrossoverLongOnly
An implementation of a 50-day and 200-day moving average crossover strategy provided in [CrossoverLongOnly](/strategies/CrossoverLongOnly.py). This implementation is long only, as instead of selling it buys an inversely correlated equity. This strategy configured to buy VAS when long and buy BBOZ when short. All cash available to the broker is used in each trade.

<p align="center">
	<img src="/res/CrossoverLongOnly.png" width="600" height="350">
</p>

#### Pump
An implementation of a strategy attempting to detect "pump and dump" schemes based on large volume, small price changes, and local price maxima is available in [Pump](/strategies/Pump.py). This implementation is long only.

<p align="center">
	<img src="/res/Pump.png" width="600" height="350">
</p>

#### HolyGrail
An implementation of a strategy attempting to detect "pump and dump" schemes based on large volume, small price changes, and local price maxima is available in [HolyGrail](/strategies/HolyGrail.py). This implementation is long only. This strategy when run for all data (2,377 stocks with 250 discarded due to insufficient data quantity for the indicators) returns a CAGR of 1.42% with 2,171 trades. This underperforms the XJO benchmark for this period by 3.6%.

<p align="center">
	<img src="/res/HolyGrail.png" width="600" height="350">
</p>

#### Benchmark
The benchmark strategy buys and holds the asset in `data/benchmark` (XJO in the examples above). This strategy is available in [Benchmark](/strategies/Benchmark.py).

<p align="center">
	<img src="/res/Benchmark.png" width="600" height="350">
</p>

## Getting Started

### Pre-requisites
The following pre-requisites are required:

1. [Anaconda 22.9.0](https://www.anaconda.com/products/distribution).

Once these are installed:

1. Open the Anaconda Prompt.
1. Run `where conda` and note the folder paths (excluding the file name component).
1. Add these folder paths to the PATH environment variable.
1. Open a new Command Prompt.
1. Run `conda --version` to verify that it is accessible.
1. Python should automatically be added to the PATH but run `python --version` to confirm.

### Installation
To install backtester:

1. Create the virtual environment:
    ```bash
    conda env create -f environment.yml
    ```

1. Activate the virtual environment:
    ```bash
    conda activate backtester
    ```

1. Configure your IDE to use the new environment.

To uninstall backtester:

1. Remove the virtual environment:
    ```bash
    conda env remove -n backtester
    ```

#### Updating Dependencies
1. Update the conda packages to the latest compatible versions:
    ```bash
    conda update --all
    ```

1. Create an updated environment.yml based on the current environment:
    ```bash
    conda env export > environment.yml
    ```

### Run
1. To run the backtester:
    ```bash
    backtester.py -strategy $strategy -verbose True
    ```

### Configuration
The `config.properties` file contains configuration for the backtester application. A description of each property is shown below.

| Property                                                               | Description                                                                                                                                                                    | Type  |
|------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------|
| data/path                                                              | The folder directory containing OLHCV data.                                                                                                                                    | Str   |
| data/cols                                                              | The column headers for the OLHCV data.                                                                                                                                         | Str   |
| data/constituents                                                      | The name of the file containing ASX300 data as at 22/10/21. This data is used if global_options/small_cap_only is set to True.                                                 | Str   |
| data/benchmark                                                         | The name of the comparison benchmark.                                                                                                                                          | Str   |
| data/bulk                                                              | True if all tickers are to be processed, and False if they will be set individually in data/tickers.                                                                           | Bool  |
| data/tickers                                                           | A comma separated list of tickers to be tested.                                                                                                                                | Str   |
| data/tickers_for_exclusion                                             | A comma separated list of tickers to be excluded from testing.                                                                                                                 | Str   |
| data/start_date                                                        | The overriding start date (%d/%m/%Y) of the strategy.                                                                                                                          | Str   |
| data/end_date                                                          | The overriding end date (%d/%m/%Y) of the strategy.                                                                                                                            | Str   |
| data/date_format                                                       | The data format of the OLHCV data.                                                                                                                                             | Str   |
| global_options/strategy                                                | The strategy to be tested.                                                                                                                                                     | Str   |
| global_options/position_limit                                          | The maximum number of positions that can be held. Must be consistent with global_options/position_size.                                                                        | Int   |
| global_options/position_size                                           | The size of each position. Must be consistent with global_options/position_limit.                                                                                              | Int   |
| global_options/plot_enabled                                            | True if a plot is to be created, and False otherwise.                                                                                                                          | Bool  |
| global_options/plot_tickers                                            | True if the individual tickers are to be plotted, and False otherwise. The global_options/plot_enabled property should also be set to True if this is set to True.             | Bool  |
| global_options/plot_volume                                             | True if the individual ticker plots are to include volume, and False otherwise.                                                                                                | Bool  |
| global_options/plot_benchmark                                          | True if the benchmark plot is to be created, and False otherwise.                                                                                                              | Bool  |
| global_options/reports                                                 | True if a quantstats report is to be created for the strategy, and False otherwise.                                                                                            | Bool  |
| global_options/vectorised                                              | True if the backtrader vectorised option is to be used, and False otherwise.                                                                                                   | Bool  |
| global_options/cheat_on_close                                          | True if the backtrader cheat on close functionality is to be used, and False otherwise. If True, you will eliminate slippage for orders at the cost of less realistic results. | Bool  |
| global_options/small_cap_only                                          | True if small cap stocks (as defined by not being a member of data/constituents) are to be used exclusively, and False otherwise.                                              | Bool  |
| global_options/no_penny_stocks                                         | True if penny stocks (close < $1) are to be excluded, and False otherwise.                                                                                                     | Bool  |
| global_options/use_adjusted_close                                      | True if the adjusted close column in the OLHCV data is to be used instead of close, and False otherwise.                                                                       | Bool  |
| crossover_strategy_options/crossover_strategy_sma1                     | The period of the fast moving average.                                                                                                                                         | Int   |
| crossover_strategy_options/crossover_strategy_sma2                     | The period of the slow moving average.                                                                                                                                         | Int   |
| crossover_strategy_long_only_options/crossover_strategy_long_only_sma1 | The period of the fast moving average.                                                                                                                                         | Int   |
| crossover_strategy_long_only_options/crossover_strategy_long_only_sma2 | The period of the slow moving average.                                                                                                                                         | Int   |
| crossover_plus_strategy_options/crossover_plus_strategy_sma1           | The period of the fast moving average.                                                                                                                                         | Int   |
| crossover_plus_strategy_options/crossover_plus_strategy_sma2           | The period of the slow moving average.                                                                                                                                         | Int   |
| crossover_plus_strategy_options/RSI_crossover_high                     | The upper bound for the RSI.                                                                                                                                                   | Int   |
| crossover_plus_strategy_options/RSI_crossover_low                      | The lower bound for the RSI.                                                                                                                                                   | Int   |
| crossover_plus_strategy_options/RSI_period                             | The period for the RSI.                                                                                                                                                        | Int   |
| crossover_plus_strategy_options/optimise                               | True if multiple versions of the strategy are to be run, and False otherwise.                                                                                                  | Bool  |
| crossover_plus_strategy_options/sma1_low                               | The lower bound of sma1 for optimisation.                                                                                                                                      | Int   |
| crossover_plus_strategy_options/sma1_high                              | The upper bound of sma1 for optimisation.                                                                                                                                      | Int   |
| crossover_plus_strategy_options/sma1_step                              | The step size of sma1 for optimisation.                                                                                                                                        | Int   |
| crossover_plus_strategy_options/sma2_low                               | The lower bound of sma2 for optimisation.                                                                                                                                      | Int   |
| crossover_plus_strategy_options/sma2_high                              | The upper bound of sma2 for optimisation.                                                                                                                                      | Int   |
| crossover_plus_strategy_options/sma2_step                              | The step size of sma2 for optimisation.                                                                                                                                        | Int   |
| crossover_plus_strategy_options/RSI_crossover_low_low                  | The lower bound of RSI_crossover_low for optimisation.                                                                                                                         | Int   |
| crossover_plus_strategy_options/RSI_crossover_low_high                 | The upper bound of RSI_crossover_low for optimisation.                                                                                                                         | Int   |
| crossover_plus_strategy_options/RSI_crossover_low_step                 | The step size of RSI_crossover_low for optimisation.                                                                                                                           | Int   |
| crossover_plus_strategy_options/RSI_crossover_high_low                 | The lower bound of RSI_crossover_high for optimisation.                                                                                                                        | Int   |
| crossover_plus_strategy_options/RSI_crossover_high_high                | The upper bound of RSI_crossover_high for optimisation.                                                                                                                        | Int   |
| crossover_plus_strategy_options/RSI_period_low                         | The lower bound of RSI_period for optimisation.                                                                                                                                | Int   |
| crossover_plus_strategy_options/RSI_period_high                        | The upper bound of RSI_period for optimisation.                                                                                                                                | Int   |
| crossover_plus_strategy_options/RSI_period_step                        | The step size of RSI_period for optimisation.                                                                                                                                  | Int   |
| holygrail_strategy_options/adx_period                                  | The period used to calculate the ADX.                                                                                                                                          | Int   |
| holygrail_strategy_options/ema_long_period                             | The period of the long EMA.                                                                                                                                                    | Int   |
| holygrail_strategy_options/ema_short_period                            | The period of the short EMA.                                                                                                                                                   | Int   |
| holygrail_strategy_options/lag_days                                    | The number of days we can wait after being tagged for a position but not hitting the entry condition. If the days go over, we abandon the possibility for a trade.             | Int   |
| holygrail_strategy_options/bounce_off_min                              | The bounce from min we require as part of tagging a potential future position.                                                                                                 | Float |
| holygrail_strategy_options/bounce_off_max                              | The bounce from max we require as part of tagging a potential future position.                                                                                                 | Float |
| holygrail_strategy_options/volume_period                               | The period used to calculate the average volume.                                                                                                                               | Int   |
| holygrail_strategy_options/minimum_volume                              | The minimum volume to consider a position in a particular ticker.                                                                                                              | Int   |
| pump_strategy_options/volume_factor                                    | The volume factor that must be exceeded to potentially open a long position.                                                                                                   | Float |
| pump_strategy_options/buy_timeout                                      | The number of days required between closing and opening a position in the same ticker.                                                                                         | Int   |
| pump_strategy_options/sell_timeout                                     | The number of days before we close the position.                                                                                                                               | Int   |
| pump_strategy_options/price_comparison_lower_bound                     | The lower bound for the price comparison to potentially open a long position.                                                                                                  | Float |
| pump_strategy_options/price_comparison_upper_bound                     | The upper bound for the price comparison to potentially open a long position.                                                                                                  | Float |
| pump_strategy_options/price_max_period                                 | The period for the maximum price indicator.                                                                                                                                    | Int   |
| pump_strategy_options/volume_average_period                            | The period for the average volume indicator.                                                                                                                                   | Int   |
| pump_strategy_options/profit_factor                                    | The profit factor required before closing a position.                                                                                                                          | Float |
| broker/cash                                                            | The total cash available for trading.                                                                                                                                          | Float |