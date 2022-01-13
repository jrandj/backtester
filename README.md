# Backtester

Backtester is a Python application for testing trading strategies against historical data. Backtester is heavily reliant on the [Backtrader](https://github.com/mementum/backtrader) framework.

## Architecture

## Data

The data is OHLCV with the an example shown below:

| date       | open      | high      | low       | close     | volume | ticker |
|------------|-----------|-----------|-----------|-----------|--------|--------|
| 2000-01-21 | 554.73761 | 554.73761 | 508.50955 | 554.73761 | 26     | ZNT    |

Data was obtained from [Premium Data](https://www.premiumdata.net/products/premiumdata/asxhistorical.php) at a point in time. The data covers 2,628 stocks listed on the ASX between 1992-05-29 and 2018-05-04.

By default the sample .csv files in the `data` subdirectory will be used when the application is run. To use a wider set of data update the path variable in `config.properties` to point to a folder with additional data.

## Results

Multiple algorithmic trading strategies have been tested below.

### Assumptions

The following assumptions or decisions have been made:

1. The brokerage commission fee structure is as per [Nabtrade](https://www.nabtrade.com.au/investor/pricing). This is assumed to have been available historically.
1. The relative sizing of any order is 2% of the starting cash, if possible, else 2% of the remaining cash.
1. There is a limit of 50 open positions and 1 open position only per asset.
1. Slippage is 0%.
1. When an order is executed, the price of the asset is taken to be the opening price of the asset on that day (the day after the signal was generated).
1. Orders from trading do not impact the market price.

### Time Series Models

These models extract signals from a time series history to predict future values for the same time series.

#### Price-Momentum

##### Crossover

An implementation of a 50-day and 200-day moving average crossover strategy is available in [CrossoverStrategy](CrossoverStrategy.py). This implementation is long only. This strategy when run for all data (2,172 stocks with 456 discarded due to insufficient data quantity for the indicators) returns a CAGR of 7.79%. This outperforms the XJO benchmark for this period by 2.76%.

##### CrossoverPlus

An implementation of a strategy using 50-day and 200-day moving averages, the Percent Price Oscillator (PPO) indicator, and the Relative Strength Index (RSI) indicator is available in [CrossoverStrategyPlus](CrossoverStrategyPlus.py). This implementation is long only. This strategy when run for all data (2,461 stocks with 166 discarded due to insufficient data quantity for the indicators) returns a CAGR of 5.64%. This outperforms the XJO benchmark for this period by 0.61%.

Data for the RRP ticker is excluded as the returns are not accurate.

##### Pump

An implementation of a strategy based on large volume, small price changes, and local price maxima is available in [Pump][PumpStrategy.py]. This implementation is long only. This strategy when run for all data (2,377 stocks with 250 discarded due to insufficient data quantity for the indicators) returns a CAGR of 1.42%. This underperforms the XJO benchmark for this period by 3.6%.

### Statistical Arbitrage

#### Pairs Trading

This strategy finds assets whose prices have historically moved together. The difference between assets these is tracked, and, if it widens, a long position is taken on the loser and a short position is taken on the winner. If the relationship persists, the long and/or short leg will deliver profits as prices converge and the positions are closed.

### Machine Learning

#### Decision Trees

Decision trees are a machine learning algorithm that predicts the value of a target variable based on decision rules learned from data.

#### Random Forests

Random forests are combinations of many individual decision trees with randomly varied designs to address overfitting and high variance problems.

#### Feedforward Neural Networks

#### Recurrent Neural Networks

### Other

#### Index Fund Rebalancing

This strategy aims to profit from index funds which are required to periodically rebalance their holdings according to their respective benchmark.

## Getting Started

### Pre-requisites

The following pre-requisites are required:

1. [Python 3.9.7](https://www.python.org/downloads/release/python-397/).
1. [Anaconda](https://www.anaconda.com/products/individual).

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

To update the backtester dependencies (FYI only):

1. Update the conda packages to the latest compatible versions:
    ```bash
    conda update --all
    ```

1. Create an updated environment.yml based on the current environment:
    ```bash
    conda env export > environment.yml
    ```

### Configuration

The `config.properties` file contains configuration for the backtester application. A description of each property is shown below.

```markdown
[data]
path: The folder directory containing OLHCV data.
    Allowed Values: A valid directory.
benchmark: The benchmarking ticker.
    Allowed Values: A ticker from the OHLCV dataframe.
bulk: A flag used to decide whether to look at all data from path or use the tickers field.
    Allowed Values: A Boolean.
tickers: A list of comma separated codes from the consolidated OHLCV data read from path. Only used when bulk is set to False.
    Allowed Values: Comma separated list
tickers_for_exclusion: A list of comma separated codes to exclude.
	Allowed Values: Comma separated list
start_date: The strategy start date. Cannot be earlier than the earliest date in the OHLCV dataframe.
    Allowed Values: Date (DD/MM/YYYY).
end_date: The strategy end date. Cannot be after the latest date in the OHLCV dataframe.
    Allowed Values: Date (DD/MM/YYYY).

[global_options]
strategy: The strategy to be backtested.
    Allowed Values: Pump, CrossoverPlus, or Crossover.
position_limit: The number of positions that can be held.
    Allowed Values: An int.
position_size: The relative size of each position as a percent out of 100. Must equal 100 when multiplied with the position_limit. For example, a position_limit of 50 and a position_size of 2.
    Allowed Values: An int.
plot_enabled: A flag used to decide whether to plot the strategy performance.
    Allowed Values: A Boolean.
plot_tickers: A flag used to decide whether to plot individual tickers.
    Allowed Values: A Boolean.
plot_volume: A flag used to decide whether to show the volume when plotting the strategy performance. Only relevant if plot_enabled is set to True.
    Allowed Values: A Boolean.
plot_benchmark: A flag used to decide whether to plot the benchmark performance.
    Allowed Values: A Boolean.
reports: True if quantstats reports are to be generated, and False if not.
    Allowed Values: A Boolean.
vectorised: True if the backtrader batch mode is to be used, and False if not. True gives a ~30% performance increase.
    Allowed Values: A Boolean.
cheat_on_close: True if cheat on close functionality is to be used, and False if not. If cheat on close functionality is enabled, the close price from the day of the signal is used in the order. If cheat on close functionality is not enabled, the open price of the next day is used in the order. It is more realistic not to use this functionality but it means the order sizing is more complex as you don't know the price of execution when sizing the order.
    Allowed Values: A Boolean.
small_cap_only: True if all tickers are to be used, False if only tickers outside of the ASX300 are to be used.
    Allowed Values: A Boolean.

[crossover_strategy_options]
crossover_sma1: The fast moving average used to calculate a crossover.
    Allowed Values: An int.
crossover_sma2: The slow moving average used to calculate a crossover.
    Allowed Values: An int.

[crossover_plus_strategy_options]
crossover_plus_sma1: The fast moving average used to calculate a crossover.
    Allowed Values: An int.
crossover_plus_sma2: The slow moving average used to calculate a crossover.
    Allowed Values: An int.
RSI_crossover_high: The RSI value representing the overbought (sell) signal.
    Allowed Values: An int.
RSI_crossover_low: The RSI value representing the oversold (buy) signal.
    Allowed Values: An int.
RSI_period: The time period for calculating the RSI.
    Allowed Values: An int.
PPO_crossover: The PPO oscillator value.
    Allowed Values: An int.
optimise: A flag which specifies if optstrategy is to be used to run multiple strategies. The vectorised property must be True if this is set to True.
    Allowed Values: A Boolean.
sma1_low: Only used if optimise is set to True. The lower bound for sma1.
    Allowed Values: An int.
sma1_high: Only used if optimise is set to True. The upper bound for sma1.
    Allowed Values: An int.
sma1_step: Only used if optimise is set to True. The steps to be used between the lower and upper bounds for sma1.
    Allowed Values: An int.
sma2_low: Only used if optimise is set to True. The lower bound for sma2.
    Allowed Values: An int.
sma2_high: Only used if optimise is set to True. The upper bound for sma2.
    Allowed Values: An int.
sma2_step: Only used if optimise is set to True. The steps to be used between the lower and upper bounds for sma2.
    Allowed Values: An int.
RSI_crossover_low_low: Only used if optimise is set to True. The lower bound for the RSI crossover for an oversold (buy) signal.
    Allowed Values: An int.
RSI_crossover_low_high: Only used if optimise is set to True. The upper bound for the RSI crossover for an oversold (buy) signal.
    Allowed Values: An int.
RSI_crossover_low_step: Only used if optimise is set to True. The steps to be used between the lower and upper bounds for RSI_crossover_low_low and RSI_crossover_low_high.
    Allowed Values: An int.
RSI_crossover_high_low: Only used if optimise is set to True. The lower bound for the RSI crossover for an overbought (sell) signal.
    Allowed Values: An int.
RSI_crossover_high_high: Only used if optimise is set to True. The upper bound for the RSI crossover for an overbought (sell) signal.
    Allowed Values: An int.
RSI_crossover_high_step: Only used if optimise is set to True. The steps to be used between the lower and upper bounds for RSI_crossover_high_low and RSI_crossover_high_high.
    Allowed Values: An int.
RSI_period_low: Only used if optimise is set to True. The lower bound for the time period used to calculate the RSI.
    Allowed Values: An int.
RSI_period_high: Only used if optimise is set to True. The upper bound for the time period used to calculate the RSI.
    Allowed Values: An int.
RSI_period_step: Only used if optimise is set to True. The steps to be used between the lower and upper bounds for the time period used to calculate the RSI.
    Allowed Values: An int.

[pump_strategy_options]
volume_factor: The multiple used when comparing today's volume against the average volume.
    Allowed Values: An int.
buy_timeout: The time in days required after selling a position in a ticker, before buying back into the same ticker is possible.
    Allowed Values: An int.
sell_timeout: The time in days before we abandon a position.
    Allowed Values: An int.
price_average_period: The averaging period used when calculating the price average.
    Allowed Values: An int.
price_comparison_lower_bound: The lower bound for the ratio of prices.
    Allowed Values: A float.
price_comparison_upper_bound: The upper bound for the ratio of prices.
    Allowed Values: A float.
volume_average_period: The averaging period used when calculating the volume average.
    Allowed Values: An int.
profit_factor: The required profit before closing a position.
    Allowed Values: A float.

[broker]
cash: The amount of cash in the portfolio.
    Allowed Values: A float.
```
