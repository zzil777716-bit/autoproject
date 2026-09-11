"""
========================================================================================
[SAM-BOT CI/CD UNIT TEST SUITE]
Target: Samsung Electronics (005930) MTF-Squeeze Auto-Trader
Verification: Strategy Engine, Technical Indicators, Risk Guardrails, CSV Data
========================================================================================
"""

import sys
import os
import unittest
from datetime import datetime, time
import pandas as pd
import numpy as np

# Set current dir to sys.path
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

# Force UTF-8 Output on Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

from config.settings import config
from core.indicators import (
    calculate_ema,
    calculate_vwap,
    calculate_rsi,
    calculate_atr,
    calculate_bollinger_bands,
    calculate_envelope,
    calculate_macd,
    calculate_rvol
)
from core.strategy_mtf import MTFStrategyEngine
from core.risk_manager import RiskManager, Position


class TestTechnicalIndicators(unittest.TestCase):
    """지표 산출 함수 무결성 및 NaN 방어 테스트"""

    def setUp(self):
        dates = pd.date_range("2026-08-28 09:00", periods=100, freq="3min")
        np.random.seed(42)
        base = 80000.0 + np.cumsum(np.random.randn(100) * 100)
        self.df = pd.DataFrame({
            'open': base + np.random.randn(100) * 50,
            'high': base + 100 + np.abs(np.random.randn(100) * 50),
            'low': base - 100 - np.abs(np.random.randn(100) * 50),
            'close': base + np.random.randn(100) * 50,
            'volume': np.random.randint(1000, 50000, size=100)
        }, index=dates)

    def test_ema_calculation(self):
        ema20 = calculate_ema(self.df['close'], period=20)
        self.assertEqual(len(ema20), len(self.df))
        self.assertFalse(np.isnan(ema20.iloc[-1]))

    def test_rsi_calculation(self):
        rsi14 = calculate_rsi(self.df['close'], period=14)
        self.assertEqual(len(rsi14), len(self.df))
        valid_rsi = rsi14.dropna()
        self.assertTrue((valid_rsi >= 0.0).all() and (valid_rsi <= 100.0).all())

    def test_bollinger_bands(self):
        upper, mid, lower, bw = calculate_bollinger_bands(self.df['close'], period=20, num_std=2.0)
        self.assertTrue((upper.dropna() >= lower.dropna()).all())

    def test_atr_calculation(self):
        atr = calculate_atr(self.df, period=14)
        valid_atr = atr.dropna()
        self.assertTrue((valid_atr >= 0.0).all())


class TestSamsungMTFStrategy(unittest.TestCase):
    """삼성전자 (005930) MTF 수축/다이버전스 전략 검증"""

    def setUp(self):
        self.strategy = MTFStrategyEngine()
        dates_15m = pd.date_range("2026-08-28 09:00", periods=50, freq="15min")
        dates_5m = pd.date_range("2026-08-28 09:00", periods=70, freq="5min")
        dates_3m = pd.date_range("2026-08-28 09:00", periods=90, freq="3min")
        
        self.df_15m = pd.DataFrame({'open': 80000, 'high': 80500, 'low': 79500, 'close': 80100, 'volume': 50000}, index=dates_15m)
        self.df_5m = pd.DataFrame({'open': 80000, 'high': 80300, 'low': 79800, 'close': 80100, 'volume': 20000}, index=dates_5m)
        self.df_3m = pd.DataFrame({'open': 80000, 'high': 80200, 'low': 79900, 'close': 80100, 'volume': 15000}, index=dates_3m)

    def test_blackout_guardrail(self):
        """09:00~09:15 시초가 블랙아웃 가드레일 작동 확인"""
        eval_time = datetime(2026, 8, 28, 9, 5, 0)
        signal = self.strategy.evaluate(
            df_15m=self.df_15m,
            df_5m=self.df_5m,
            df_3m=self.df_3m,
            current_price=80000.0,
            realtime_intensity=120.0,
            current_time=eval_time
        )
        self.assertFalse(signal.should_enter)
        self.assertIn("BLACKOUT", signal.state_15m)

    def test_after_blackout_evaluation(self):
        """09:15 이후 정상 평가 및 신호 구조 검증"""
        eval_time = datetime(2026, 8, 28, 10, 0, 0)
        signal = self.strategy.evaluate(
            df_15m=self.df_15m,
            df_5m=self.df_5m,
            df_3m=self.df_3m,
            current_price=80100.0,
            realtime_intensity=110.0,
            current_time=eval_time
        )
        self.assertIsInstance(signal.should_enter, bool)
        self.assertIsInstance(signal.metrics, dict)


class TestRiskManagerGuardrails(unittest.TestCase):
    """1주 모의투자 리스크 관리 및 안전장치 검증"""

    def setUp(self):
        self.rm = RiskManager(initial_equity=10_000_000)

    def test_1share_position_size(self):
        qty = self.rm.calculate_order_qty(current_price=80000.0)
        self.assertEqual(qty, 1)

    def test_entry_and_exit_lifecycle(self):
        entry_time = datetime(2026, 8, 28, 10, 0, 0)
        self.rm.on_position_entered(qty=1, price=80000.0, current_time=entry_time, stop_price=79000.0, target_price=82000.0)
        
        self.assertEqual(self.rm.position.qty, 1)
        self.assertEqual(self.rm.position.avg_price, 80000.0)
        
        # 유지
        action_hold = self.rm.check_position_risk(current_price=80500.0, current_time=datetime(2026, 8, 28, 10, 5, 0))
        self.assertEqual(action_hold.action_type, "NONE")
        
        # 손절
        action_sl = self.rm.check_position_risk(current_price=78900.0, current_time=datetime(2026, 8, 28, 10, 10, 0))
        self.assertEqual(action_sl.action_type, "STOP_LOSS")
        self.assertEqual(action_sl.qty, 1)

    def test_circuit_breaker(self):
        self.rm.daily_pnl = -200_000
        can_trade, reason = self.rm.can_trade(datetime(2026, 8, 28, 11, 0, 0))
        self.assertFalse(can_trade)


class TestDataPipelinesIntegrity(unittest.TestCase):
    """삼성전자 분봉 데이터 무결성 검증"""

    def test_historical_csv_files(self):
        for timeframe in ['15m', '5m', '3m']:
            filepath = os.path.join(PROJECT_DIR, f"data/005930_{timeframe}.csv")
            if os.path.exists(filepath):
                df = pd.read_csv(filepath, index_col=0, parse_dates=True)
                self.assertFalse(df.empty)
                required_cols = {'open', 'high', 'low', 'close', 'volume'}
                self.assertTrue(required_cols.issubset(set(df.columns)))
                self.assertGreater(len(df), 100)


if __name__ == '__main__':
    print("=" * 75)
    print("🤖 [SAM-BOT] Unit Tests Running...")
    print("=" * 75)
    unittest.main(verbosity=2)
