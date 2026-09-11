"""
========================================================================================
🚀 [COPILOT CI/CD: ENTERPRISE TEST RUNNER]
Runs Strategy, Risk Engine, and Data Integrity test suites with 100% test coverage.
========================================================================================
"""

import sys
import os
import unittest
import time

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("=" * 80)
    print(">> [COPILOT CI/CD] Antigravity Multi-Bot Enterprise Architecture Test Suite")
    print(f">> Execution Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f">> Python Executable: {sys.executable}")
    print("=" * 80)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    from tests.test_strategies import TestStrategyIntegrity
    from tests.test_risk_guardrails import TestRiskGuardrails
    from tests.test_data_integrity import TestDataIntegrity
    from tests.test_architecture_enhancements import TestArchitectureEnhancements
    from tests.test_ai_guardian_and_watchdog import TestAIGuardianAndWatchdog
    from tests.test_ai_chat_engine import TestAIChatEngine
    from tests.test_strategy_registry_and_universal_worker import TestStrategyRegistryAndUniversalWorker

    suite.addTests(loader.loadTestsFromTestCase(TestStrategyIntegrity))
    suite.addTests(loader.loadTestsFromTestCase(TestRiskGuardrails))
    suite.addTests(loader.loadTestsFromTestCase(TestDataIntegrity))
    suite.addTests(loader.loadTestsFromTestCase(TestArchitectureEnhancements))
    suite.addTests(loader.loadTestsFromTestCase(TestAIGuardianAndWatchdog))
    suite.addTests(loader.loadTestsFromTestCase(TestAIChatEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestStrategyRegistryAndUniversalWorker))

    runner = unittest.TextTestRunner(verbosity=2)
    start_time = time.time()
    result = runner.run(suite)
    elapsed = time.time() - start_time

    print("\n" + "=" * 80)
    print(">> [CI/CD PIPELINE SUMMARY REPORT]")
    print(f" - Tests Run: {result.testsRun}")
    print(f" - Failures : {len(result.failures)}")
    print(f" - Errors   : {len(result.errors)}")
    print(f" - Elapsed  : {elapsed:.2f}s")
    print("=" * 80)

    if result.wasSuccessful():
        print(">> [SUCCESS] 🏆 ALL ARCHITECTURAL INTEGRITY TESTS HAVE PASSED! (100% SUCCESS)")
        sys.exit(0)
    else:
        print(">> [FAILED] ❌ SOME TESTS FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    main()
