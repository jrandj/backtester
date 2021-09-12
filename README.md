# Backtester

Backtester is a Python application for testing trading strategies against historical data.

## Architecture

## Data

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