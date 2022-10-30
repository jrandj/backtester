from backtester import Backtester

import unittest


class Tests(unittest.TestCase):
    def test_holygrail_1(self):
        backtester = Backtester(strategy="HolyGrail", verbose=False)
        test_strategy_cagr = -0.05
        test_benchmark_cagr = 4.70
        self.assertEqual(test_strategy_cagr, round(backtester.strategy_cagr, 2))
        self.assertEqual(test_benchmark_cagr, round(backtester.benchmark_cagr, 2))

    def test_pump_1(self):
        backtester = Backtester(strategy="Pump", verbose=False)
        test_strategy_cagr = 0.00
        test_benchmark_cagr = 4.70
        self.assertEqual(test_strategy_cagr, round(backtester.strategy_cagr, 2))
        self.assertEqual(test_benchmark_cagr, round(backtester.benchmark_cagr, 2))

    def test_crossover_1(self):
        backtester = Backtester(strategy="Crossover", verbose=False)
        test_strategy_cagr = 1.34
        test_benchmark_cagr = 4.70
        self.assertEqual(test_strategy_cagr, round(backtester.strategy_cagr, 2))
        self.assertEqual(test_benchmark_cagr, round(backtester.benchmark_cagr, 2))

    def test_crossoverplus_1(self):
        backtester = Backtester(strategy="CrossoverPlus", verbose=False)
        test_strategy_cagr = 3.15
        test_benchmark_cagr = 4.70
        self.assertEqual(test_strategy_cagr, round(backtester.strategy_cagr, 2))
        self.assertEqual(test_benchmark_cagr, round(backtester.benchmark_cagr, 2))

    # todo: get long, short as ticker values for this config
    def test_crossoverlongonly_1(self):
        backtester = Backtester(strategy="CrossoverLongOnly", verbose=False)
        test_strategy_cagr = 1.74
        test_benchmark_cagr = 4.70
        self.assertEqual(test_strategy_cagr, round(backtester.strategy_cagr, 2))
        self.assertEqual(test_benchmark_cagr, round(backtester.benchmark_cagr, 2))


if __name__ == '__main__':
    unittest.main()
