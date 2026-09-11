"""
========================================================================================
[SK-BOT CI/CD UNIT TEST SUITE]
Target: SK Hynix (000660) Triple-Screen Pullback Auto-Trader
Verification: Strategy Engine, Envelope/EMA Indicators, Risk Guardrails, CSV Data
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
    calculate_envelope,
    calculate_macd,
    calculate_vwap,
    calculate_rsi,
    calculate_atr,
    calculate_rvol
)
from core.strategy_hynix_pullback import SKHynixPullbackStrategyEngine
from core.risk_manager import RiskManager, Position


class TestTechnicalIndicatorsSK(unittest.TestCase):
    """SK하이닉스 지표 산출 함수 무결성 테스트"""

    def setUp(self):
        dates = pd.date_range("2026-08-28 09:00", periods=100, freq="3min")
        np.random.seed(42)
        base = 180000.0 + np.cumsum(np.random.randn(100) * 200)
        self.df = pd.DataFrame({
            'open': base + np.random.randn(100) * 100,
            'high': base + 200 + np.abs(np.random.randn(100) * 100),
            'low': base - 200 - np.abs(np.random.randn(100) * 100),
            'close': base + np.random.randn(100) * 100,
            'volume': np.random.randint(2000, 30000, size=100)
        }, index=dates)

    def test_envelope_calculation(self):
        upper, mid, lower = calculate_envelope(self.df['close'], period=20, percent=2.0)
        self.assertEqual(len(upper), len(self.df))
        self.assertTrue((upper.dropna() >= lower.dropna()).all())

    def test_macd_calculation(self):
        macd, sig, hist = calculate_macd(self.df['close'])
        self.assertEqual(len(macd), len(self.df))
        self.assertEqual(len(sig), len(self.df))
        self.assertEqual(len(hist), len(self.df))

    def test_rsi_calculation(self):
        rsi14 = calculate_rsi(self.df['close'], period=14)
        valid_rsi = rsi14.dropna()
        self.assertTrue((valid_rsi >= 0.0).all() and (valid_rsi <= 100.0).all())

    def test_atr_calculation(self):
        atr = calculate_atr(self.df, period=14)
        valid_atr = atr.dropna()
        self.assertTrue((valid_atr >= 0.0).all())


class TestSKHynixStrategy(unittest.TestCase):
    """SK하이닉스 (000660) 삼중 스크린 엔벨로프 눌림목 전략 검증"""

    def setUp(self):
        self.strategy = SKHynixPullbackStrategyEngine()
        dates_15m = pd.date_range("2026-08-28 09:00", periods=50, freq="15min")
        dates_5m = pd.date_range("2026-08-28 09:00", periods=70, freq="5min")
        dates_3m = pd.date_range("2026-08-28 09:00", periods=90, freq="3min")
        
        self.df_15m = pd.DataFrame({'open': 180000, 'high': 182000, 'low': 179000, 'close': 181000, 'volume': 30000}, index=dates_15m)
        self.df_5m = pd.DataFrame({'open': 180000, 'high': 181500, 'low': 179500, 'close': 181000, 'volume': 15000}, index=dates_5m)
        self.df_3m = pd.DataFrame({'open': 180000, 'high': 181200, 'low': 179800, 'close': 181000, 'volume': 10000}, index=dates_3m)

    def test_blackout_guardrail(self):
        """09:00~09:15 시초가 블랙아웃 가드레일 작동 확인"""
        eval_time = datetime(2026, 8, 28, 9, 5, 0)
        signal = self.strategy.evaluate(
            df_15m=self.df_15m,
            df_5m=self.df_5m,
            df_3m=self.df_3m,
            current_price=180000.0,
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
            current_price=180500.0,
            realtime_intensity=115.0,
            current_time=eval_time
        )
        self.assertIsInstance(signal.should_enter, bool)
        self.assertIsInstance(signal.metrics, dict)


class TestRiskManagerGuardrailsSK(unittest.TestCase):
    """SK 1주 모의투자 리스크 관리 검증"""

    def setUp(self):
        self.rm = RiskManager(initial_equity=10_000_000)

    def test_1share_position_size(self):
        qty = self.rm.calculate_order_qty(current_price=180000.0)
        self.assertEqual(qty, 1)

    def test_entry_and_exit_lifecycle(self):
        entry_time = datetime(2026, 8, 28, 10, 0, 0)
        self.rm.on_position_entered(qty=1, price=180000.0, current_time=entry_time, stop_price=178000.0, target_price=183000.0)
        
        self.assertEqual(self.rm.position.qty, 1)
        self.assertEqual(self.rm.position.avg_price, 180000.0)
        
        # 정상 범위 홀딩
        action_hold = self.rm.check_position_risk(current_price=181000.0, current_time=datetime(2026, 8, 28, 10, 5, 0))
        self.assertEqual(action_hold.action_type, "NONE")
        
        # 손절선 도달
        action_sl = self.rm.check_position_risk(current_price=177900.0, current_time=datetime(2026, 8, 28, 10, 10, 0))
        self.assertEqual(action_sl.action_type, "STOP_LOSS")
        self.assertEqual(action_sl.qty, 1)

    def test_circuit_breaker(self):
        self.rm.daily_pnl = -200_000
        can_trade, reason = self.rm.can_trade(datetime(2026, 8, 28, 11, 0, 0))
        self.assertFalse(can_trade)


class TestDataPipelinesIntegritySK(unittest.TestCase):
    """SK하이닉스 분봉 데이터 무결성 검증"""

    def test_historical_csv_files(self):
        for timeframe in ['15m', '5m', '3m']:
            filepath = os.path.join(PROJECT_DIR, f"data/000660_{timeframe}.csv")
            if os.path.exists(filepath):
                df = pd.read_csv(filepath, index_col=0, parse_dates=True)
                self.assertFalse(df.empty)
                required_cols = {'open', 'high', 'low', 'close', 'volume'}
                self.assertTrue(required_cols.issubset(set(df.columns)))
                self.assertGreater(len(df), 100)


if __name__ == '__main__':
    print("=" * 75)
    print("⚡ [SK-BOT] Unit Tests Running...")
    print("=" * 75)
    unittest.main(verbosity=2)
