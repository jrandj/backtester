# Backtester

Backtester is a Python application for testing trading strategies against historical data. Backtester is heavily reliant on the [Backtrader](https://github.com/mementum/backtrader) framework.

## Architecture

## Data

The data is OHLCV with the an example shown below:

| date       | open      | high      | low       | close     | volume | ticker |
|------------|-----------|-----------|-----------|-----------|--------|--------|
| 2000-01-21 | 554.73761 | 554.73761 | 508.50955 | 554.73761 | 26     | ZNT    |

Data was obtained from [Premium Data](https://www.premiumdata.net/products/premiumdata/asxhistorical.php) at a point in time. The data covers 2,628 stocks listed on the ASX between 1992-05-29 and 2018-05-04.

By default the sample .csv files in the `data` subdirectory will be used when the application is run. To use a wider set of data update the path variable in config.properties to point to a folder with additional data.

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

An implementation of a 50-day and 200-day moving average crossover strategy is available in [CrossoverStrategy](CrossoverStrategy.py). This implementation is long only. This strategy when run for all data (2,172 stocks with 456 discarded due to insufficient data quantity for SMA indicators) returns a CAGR of 7.79%. This outperforms the XJO benchmark for this period by 2.76%.

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

To install Backtester:

1. Create the virtual environment:
    ```bash
    conda env create -f environment.yml
    ```

1. Activate the virtual environment:
    ```bash
    conda activate backtester
    ```

1. Configure your IDE to use the new environment.

To uninstall Backtester:

1. Remove the virtual environment:
    ```bash
    conda env remove -n backtester
    ```

To update the Backtester dependencies (FYI only):

1. Update the conda packages to the latest compatible versions:
    ```bash
    conda update --all
    ```

1. Create an updated environment.yml based on the current environment:
    ```bash
    conda env export > environment.yml
    ```
