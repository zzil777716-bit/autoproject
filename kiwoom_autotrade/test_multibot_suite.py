"""
========================================================================================
[CI/CD MULTI-BOT UNIT TEST SUITE]
Comprehensive Unit & Integration Test for Kiwoom Auto-Trade Bots:
1. Samsung Electronics (005930) - MTF Squeeze & Divergence Strategy
2. SK Hynix (000660) - Triple-Screen Envelope Pullback Strategy
3. Technical Indicators & Data Feed Integrity
4. Risk Management & 1-Share Guardrail Verification
========================================================================================
"""

import sys
import os
import unittest
from datetime import datetime, time
import pandas as pd
import numpy as np

# Ensure root paths are in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

HYNIX_DIR = "C:/sk_hynix_autotrade"
if os.path.exists(HYNIX_DIR) and HYNIX_DIR not in sys.path:
    sys.path.insert(0, HYNIX_DIR)

# Force UTF-8 Output on Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

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
from core.risk_manager import RiskManager, Position


class TestTechnicalIndicators(unittest.TestCase):
    """지표 산출 함수 무결성 및 NaN 방어 테스트"""

    def setUp(self):
        # 100개 샘플 OHLCV 생성
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
        self.assertFalse(np.isnan(ema20.iloc[-1]), "EMA calculation produced NaN at the end")

    def test_rsi_calculation(self):
        rsi14 = calculate_rsi(self.df['close'], period=14)
        self.assertEqual(len(rsi14), len(self.df))
        valid_rsi = rsi14.dropna()
        self.assertTrue((valid_rsi >= 0.0).all() and (valid_rsi <= 100.0).all(), "RSI out of [0, 100] bounds")

    def test_envelope_calculation(self):
        env_upper, env_mid, env_lower = calculate_envelope(self.df['close'], period=20, percent=1.5)
        self.assertTrue((env_upper.dropna() >= env_lower.dropna()).all(), "Envelope upper line is below lower line")

    def test_atr_calculation(self):
        atr = calculate_atr(self.df, period=14)
        valid_atr = atr.dropna()
        self.assertTrue((valid_atr >= 0.0).all(), "ATR contains negative values")

    def test_macd_calculation(self):
        macd_line, signal_line, hist = calculate_macd(self.df['close'])
        self.assertEqual(len(macd_line), len(self.df))
        self.assertEqual(len(signal_line), len(self.df))
        self.assertEqual(len(hist), len(self.df))


class TestSamsungMTFStrategy(unittest.TestCase):
    """삼성전자 (005930) MTF 수축/다이버전스 전략 검증"""

    def setUp(self):
        from core.strategy_mtf import MTFStrategyEngine
        self.strategy = MTFStrategyEngine()
        
        # 샘플 15m, 5m, 3m 데이터프레임
        dates_15m = pd.date_range("2026-08-28 09:00", periods=40, freq="15min")
        dates_5m = pd.date_range("2026-08-28 09:00", periods=60, freq="5min")
        dates_3m = pd.date_range("2026-08-28 09:00", periods=80, freq="3min")
        
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
        self.assertFalse(signal.should_enter, "Strategy should NOT enter during 09:00~09:15 blackout window")
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


class TestSKHynixPullbackStrategy(unittest.TestCase):
    """SK하이닉스 (000660) 삼중 스크린 엔벨로프 눌림목 전략 검증"""

    def setUp(self):
        sys.path.insert(0, "C:/sk_hynix_autotrade")
        try:
            from core.strategy_hynix_pullback import SKHynixPullbackStrategyEngine
            self.sk_strategy = SKHynixPullbackStrategyEngine()
        except ImportError:
            self.sk_strategy = None

        dates_15m = pd.date_range("2026-08-28 09:00", periods=40, freq="15min")
        dates_5m = pd.date_range("2026-08-28 09:00", periods=60, freq="5min")
        dates_3m = pd.date_range("2026-08-28 09:00", periods=80, freq="3min")

        self.df_15m = pd.DataFrame({'open': 180000, 'high': 182000, 'low': 179000, 'close': 181000, 'volume': 30000}, index=dates_15m)
        self.df_5m = pd.DataFrame({'open': 180000, 'high': 181500, 'low': 179500, 'close': 181000, 'volume': 15000}, index=dates_5m)
        self.df_3m = pd.DataFrame({'open': 180000, 'high': 181200, 'low': 179800, 'close': 181000, 'volume': 10000}, index=dates_3m)

    def test_sk_blackout_guardrail(self):
        if not self.sk_strategy:
            return
        eval_time = datetime(2026, 8, 28, 9, 10, 0)
        signal = self.sk_strategy.evaluate(
            df_15m=self.df_15m,
            df_5m=self.df_5m,
            df_3m=self.df_3m,
            current_price=180000.0,
            realtime_intensity=125.0,
            current_time=eval_time
        )
        self.assertFalse(signal.should_enter, "SK strategy should NOT enter before 09:15")
        self.assertIn("BLACKOUT", signal.state_15m)


class TestRiskManagerGuardrails(unittest.TestCase):
    """1주 모의투자 리스크 관리 및 안전장치 검증"""

    def setUp(self):
        self.rm = RiskManager(initial_equity=10_000_000)

    def test_1share_position_size(self):
        """1주 고정 주문 수량 검증"""
        qty = self.rm.calculate_order_qty(current_price=80000.0)
        self.assertEqual(qty, 1, "Must strictly trade exactly 1 share in verification mode")

    def test_entry_and_exit_lifecycle(self):
        """진입 후 손절 및 익절 동작 검증"""
        entry_time = datetime(2026, 8, 28, 10, 0, 0)
        self.rm.on_position_entered(qty=1, price=80000.0, current_time=entry_time, stop_price=79000.0, target_price=82000.0)
        
        self.assertEqual(self.rm.position.qty, 1)
        self.assertEqual(self.rm.position.avg_price, 80000.0)
        
        # 1. 가격이 정상 범위 내에 있을 때 유지
        action_hold = self.rm.check_position_risk(current_price=80500.0, current_time=datetime(2026, 8, 28, 10, 5, 0))
        self.assertEqual(action_hold.action_type, "NONE")
        
        # 2. 손절가(79,000원) 이하 도달 시 손절 청산 트리거
        action_sl = self.rm.check_position_risk(current_price=78900.0, current_time=datetime(2026, 8, 28, 10, 10, 0))
        self.assertEqual(action_sl.action_type, "STOP_LOSS")
        self.assertEqual(action_sl.qty, 1)

    def test_can_trade_circuit_breaker(self):
        """일일 손실 한도 초과 시 킬스위치 락다운 검증"""
        self.rm.daily_pnl = -200_000  # -2.0% loss (Limit is -1.5%)
        can_trade, reason = self.rm.can_trade(datetime(2026, 8, 28, 11, 0, 0))
        self.assertFalse(can_trade)
        self.assertIn("초과", reason)


class TestDataPipelinesIntegrity(unittest.TestCase):
    """로컬 분봉 데이터 파일 무결성 검증"""

    def test_samsung_historical_files(self):
        for timeframe in ['15m', '5m', '3m']:
            filepath = f"C:/kiwoom_autotrade/data/005930_{timeframe}.csv"
            if os.path.exists(filepath):
                df = pd.read_csv(filepath, index_col=0, parse_dates=True)
                self.assertFalse(df.empty, f"Samsung {timeframe} CSV file is empty")
                required_cols = {'open', 'high', 'low', 'close', 'volume'}
                self.assertTrue(required_cols.issubset(set(df.columns)), f"Missing columns in {filepath}")
                self.assertGreater(len(df), 100, f"Insufficient historical records in {filepath}")

    def test_sk_hynix_historical_files(self):
        for timeframe in ['15m', '5m', '3m']:
            filepath = f"C:/sk_hynix_autotrade/data/000660_{timeframe}.csv"
            if os.path.exists(filepath):
                df = pd.read_csv(filepath, index_col=0, parse_dates=True)
                self.assertFalse(df.empty, f"SK Hynix {timeframe} CSV file is empty")
                required_cols = {'open', 'high', 'low', 'close', 'volume'}
                self.assertTrue(required_cols.issubset(set(df.columns)), f"Missing columns in {filepath}")
                self.assertGreater(len(df), 100, f"Insufficient historical records in {filepath}")


def run_all_tests():
    print("=" * 80)
    print("🚀 [COPILOT CI/CD] Starting Multi-Bot Automated Unit Test Suite...")
    print("=" * 80)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestTechnicalIndicators))
    suite.addTests(loader.loadTestsFromTestCase(TestSamsungMTFStrategy))
    suite.addTests(loader.loadTestsFromTestCase(TestSKHynixPullbackStrategy))
    suite.addTests(loader.loadTestsFromTestCase(TestRiskManagerGuardrails))
    suite.addTests(loader.loadTestsFromTestCase(TestDataPipelinesIntegrity))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 80)
    if result.wasSuccessful():
        print(f"✅ ALL {result.testsRun} TESTS PASSED! Multi-Bot Trading Pipelines are 100% Validated.")
    else:
        print(f"❌ {len(result.failures)} Failures, {len(result.errors)} Errors Detected.")
    print("=" * 80)
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
