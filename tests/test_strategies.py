"""
========================================================================================
🧪 [CI/CD UNIT TEST: STRATEGY INTEGRITY & DUAL ENGINE]
Tests 15M 3-Lines Sustained Strategy (A) & Alignment Disparity Strategy (B).
========================================================================================
"""

import unittest
from datetime import datetime
import pandas as pd
import numpy as np

from sdk.data_feeds import BacktestDataFeed
from sdk.base_strategy import (
    Samsung3LinesSustainedStrategy,
    SKHynix3LinesMomentumStrategy,
    SamsungAlignmentDisparityStrategy,
    SKHynixAlignmentDisparityStrategy,
    DualStrategyEngine
)
from workers.worker_samsung_squeeze import SamsungDualWorkerStrategy
from workers.worker_hynix_pullback import SKHynixDualWorkerStrategy
from storage.timeseries_db import TimeseriesIndicatorEngine

class TestStrategyIntegrity(unittest.TestCase):
    def setUp(self):
        dates = pd.date_range("2026-08-28 09:00", periods=150, freq="15min")
        self.df_15m = pd.DataFrame({
            "open": np.linspace(80000, 85000, 150),
            "high": np.linspace(80500, 85500, 150),
            "low": np.linspace(79500, 84500, 150),
            "close": np.linspace(80000, 85000, 150),
            "volume": np.random.randint(1000, 5000, 150),
            "intensity": np.full(150, 115.0)
        }, index=dates)

        dates_5m = pd.date_range("2026-08-28 09:00", periods=100, freq="5min")
        self.df_5m = pd.DataFrame({
            "open": np.linspace(81000, 83000, 100),
            "high": np.linspace(81200, 83200, 100),
            "low": np.linspace(80800, 82800, 100),
            "close": np.linspace(81000, 83000, 100),
            "volume": np.random.randint(500, 2000, 100),
            "intensity": np.full(100, 120.0)
        }, index=dates_5m)

        dates_3m = pd.date_range("2026-08-28 09:00", periods=100, freq="3min")
        self.df_3m = pd.DataFrame({
            "open": np.linspace(82000, 83000, 100),
            "high": np.linspace(82200, 83200, 100),
            "low": np.linspace(81800, 82800, 100),
            "close": np.linspace(82000, 83000, 100),
            "volume": np.random.randint(300, 1500, 100),
            "intensity": np.full(100, 125.0)
        }, index=dates_3m)

        self.feed = BacktestDataFeed(self.df_15m, self.df_5m, self.df_3m)
        self.feed.current_price = 83000
        self.feed.current_intensity = 125.0

    def test_samsung_dual_worker_strategy_evaluation(self):
        strategy = SamsungDualWorkerStrategy()
        signal = strategy.evaluate(self.feed, datetime(2026, 8, 28, 9, 30))
        self.assertIsNotNone(signal)
        self.assertEqual(signal.side, "BUY")
        self.assertIsInstance(signal.should_enter, (bool, np.bool_))

    def test_sk_hynix_dual_worker_strategy_evaluation(self):
        strategy = SKHynixDualWorkerStrategy()
        signal = strategy.evaluate(self.feed, datetime(2026, 8, 28, 9, 30))
        self.assertIsNotNone(signal)
        self.assertEqual(signal.side, "BUY")
        self.assertIsInstance(signal.should_enter, (bool, np.bool_))

    def test_technical_indicators_math(self):
        close = self.df_15m['close']
        ma20 = close.rolling(20).mean()
        self.assertEqual(len(ma20), 150)
        self.assertTrue(pd.isna(ma20.iloc[18]))
        self.assertFalse(pd.isna(ma20.iloc[19]))

if __name__ == "__main__":
    unittest.main()
