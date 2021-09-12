# Backtester

Stock-backtester is a Python application for testing trading strategies against historical data.

Running stockbacktester.py will test the buying and selling of stocks based on strategy parameters. The strategy parameters for buy signals are defined using: 
* Today's volume above the 20 day moving average volume.
* Today's close price change compared to the previous day price change.

The buy signal is intended to model accumulation (i.e. large volume increase with minimal price increase). 

Sell signals are generated using:
* Profit required for exiting the currently held position.

## Architecture

## Output

## Getting Started

### Pre-requisites

* Python 3.9.7
* Conda 4.10.3

### Installation

Use [Anaconda](https://www.anaconda.com/products/individual) to install backtester.

1. Create the virtual environment:
    ```bash
    conda env create -f environment.yml
    ```

2. Activate the virtual environment:
    ```bash
    conda activate backtester
    ```

To check for and update outdated packages run `conda update --all`. To create an updated environment.yml based on the current environment run `conda env export > environment.yml`. To uninstall run `conda env remove -n backtester`.