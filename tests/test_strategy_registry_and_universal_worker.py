"""
========================================================================================
🧪 [CI/CD UNIT TEST: STRATEGY REGISTRY & UNIVERSAL WORKER ARCHITECTURE]
Tests:
  1. Strategy Dynamic Registration & Discovery
  2. Factory Instantiation of Registered Strategies
  3. Custom Strategy Plug-in capability
  4. Universal Worker dynamic binding with Risk Guardrails & SRE Watchdog
========================================================================================
"""

import unittest
from sdk.base_strategy import BaseStrategy, StrategySignal
from sdk.strategy_registry import StrategyRegistry, register_strategy
from workers.universal_worker import UniversalTradingWorker

# 테스트용 커스텀 플러그인 전략
@register_strategy(name="TEST_MOMENTUM_SCALPER", description="단위테스트용 모멘텀 스캘퍼")
class MockTestScalperStrategy(BaseStrategy):
    def evaluate(self, data_feed, current_time_str):
        return StrategySignal(
            should_enter=True,
            entry_price=10000.0,
            strategy_tag="TEST_MOMENTUM_SCALPER",
            reason="테스트 진입 신호"
        )

class TestStrategyRegistryAndUniversalWorker(unittest.TestCase):
    def test_registry_contains_builtin_strategies(self):
        names = StrategyRegistry.list_strategy_names()
        self.assertIn("STRATEGY_A_3LINES_SAM", names)
        self.assertIn("STRATEGY_B_MA_ALIGNMENT_SAM", names)
        self.assertIn("TEST_MOMENTUM_SCALPER", names)

    def test_factory_instantiation(self):
        strategy = StrategyRegistry.create_strategy("TEST_MOMENTUM_SCALPER", code="005930", stock_name="삼성전자")
        self.assertIsNotNone(strategy)
        self.assertEqual(strategy.code, "005930")
        signal = strategy.evaluate({}, "09:15:00")
        self.assertTrue(signal.should_enter)
        self.assertEqual(signal.entry_price, 10000.0)

    def test_universal_worker_binding(self):
        worker = UniversalTradingWorker(code="005930", stock_name="삼성전자", strategy_name="DUAL")
        self.assertEqual(worker.code, "005930")
        self.assertEqual(worker.stock_name, "삼성전자")
        self.assertIsNotNone(worker.strategy)
        self.assertIsNotNone(worker.risk_guard)
        self.assertIsNotNone(worker.global_risk)

if __name__ == "__main__":
    unittest.main()
