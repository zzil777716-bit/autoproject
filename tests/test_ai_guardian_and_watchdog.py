"""
========================================================================================
🧪 [CI/CD UNIT TEST SUITE: MULTI-AI GUARDIAN & SRE SENTINEL WATCHDOG]
========================================================================================
"""

import unittest
import time
from sdk.ai_guardian_mesh import AIGuardianMesh, GuardianDecision
from sdk.telemetry_watchdog import SystemWatchdogSentinel

class TestAIGuardianAndWatchdog(unittest.TestCase):
    def setUp(self):
        self.guardian = AIGuardianMesh()
        self.watchdog = SystemWatchdogSentinel()

    def test_gemini_flash_primary_evaluation_confirm(self):
        dec = self.guardian.evaluate_entry(
            code="005930",
            name="삼성전자",
            current_price=257000,
            strategy_name="SamsungDualWorkerStrategy",
            reason="15M 정배열 안착 & 5M 지지반등",
            market_context={"disparity_20ma": 102.1, "intensity": 115.0}
        )
        self.assertEqual(dec.decision, "CONFIRM")
        self.assertEqual(dec.provider, "Gemini Flash")
        self.assertGreater(dec.confidence, 0.85)

    def test_gemini_flash_veto_on_extreme_overheat(self):
        dec = self.guardian.evaluate_entry(
            code="000660",
            name="SK하이닉스",
            current_price=1653000,
            strategy_name="SKHynixDualWorkerStrategy",
            reason="단기 급등 돌파",
            market_context={"disparity_20ma": 106.5, "intensity": 140.0}
        )
        self.assertEqual(dec.decision, "VETO")
        self.assertIn("과열 위험", dec.reason)

    def test_multi_ai_failover_cascade_to_claude_and_local(self):
        # 강제로 gemini failure 발생 유도
        self.guardian.failure_counts["gemini"] = 3
        dec = self.guardian.evaluate_entry(
            code="005930",
            name="삼성전자",
            current_price=257000,
            strategy_name="SamsungDualWorkerStrategy",
            reason="테스트 신호",
            market_context={"disparity_20ma": 102.0, "intensity": 105.0}
        )
        self.assertEqual(dec.provider, "Claude Haiku")
        self.assertEqual(dec.decision, "CONFIRM")

        # 모든 AI 실패 시 로컬 룰 안전 폴백 검증
        self.guardian.failure_counts["claude"] = 3
        self.guardian.failure_counts["openai"] = 3
        dec_local = self.guardian.evaluate_entry(
            code="005930",
            name="삼성전자",
            current_price=257000,
            strategy_name="SamsungDualWorkerStrategy",
            reason="오프라인 비상 신호"
        )
        self.assertEqual(dec_local.provider, "Local Rule Engine")
        self.assertEqual(dec_local.decision, "CONFIRM")

    def test_watchdog_heartbeat_and_exception_trapping(self):
        self.watchdog.report_tick("005930", 257000)
        self.watchdog.report_account_sync()
        self.watchdog.report_ai_decision("Gemini Flash", 240.5)
        
        # 정상 상태 검증
        health = self.watchdog.get_health_status()
        self.assertEqual(health["health_score"], 100)
        self.assertIn("OK", health["socket_status"])

        # 예외 트래핑 검증
        self.watchdog.trap_exception("StrategyEngine", "DivisionByZero in indicator EMA")
        health_after = self.watchdog.get_health_status()
        self.assertEqual(health_after["error_count"], 1)

if __name__ == "__main__":
    unittest.main()
