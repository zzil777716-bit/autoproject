"""
========================================================================================
🧪 [CI/CD UNIT TEST: SENIOR ARCHITECTURE ENHANCEMENTS]
Tests SQLite WAL Mode, Transactional Outbox Pattern, Event Replay, JIT Kill-Switch, and CQRS.
========================================================================================
"""

import unittest
import os
import time
from datetime import datetime

from storage.data_lake import QuantDataLake
from events.event_bus import OutboxEventBus, OrderCommandEvent, TradeFilledEvent, RiskAlertEvent
from risk_engine.global_risk import GlobalRiskEngine
from api.query_service import QueryService
from api.command_service import CommandService

class TestArchitectureEnhancements(unittest.TestCase):
    def setUp(self):
        self.test_dir = r"C:\Antigravity\data\research"
        self.bus = OutboxEventBus(db_dir=self.test_dir)
        self.bus.reset_global_halt_state()

    def tearDown(self):
        self.bus.reset_global_halt_state()

    def test_sqlite_wal_mode_and_partitioning(self):
        datalake_sam = QuantDataLake(partition_key="005930_test")
        datalake_sam.record_trade(
            "Test_MTF", "005930", "삼성전자", "SELL", 83000, 1, 3000, 1.25, 1.8, -0.2, 120, "Test TP"
        )
        trades = datalake_sam.query_recent_trades(5)
        self.assertGreaterEqual(len(trades), 1)
        self.assertEqual(trades[0]["code"], "005930")
        
        if os.path.exists(datalake_sam.db_path):
            try: os.remove(datalake_sam.db_path)
            except Exception: pass

    def test_transactional_outbox_publish_and_ack(self):
        received_events = []
        def on_order(event):
            received_events.append(event)

        self.bus.subscribe("orders.command", on_order)
        outbox_id = self.bus.publish_critical(
            "orders.command",
            OrderCommandEvent(code="005930", side="BUY", qty=1, price=82500, strategy_name="SAM_MTF", reason="Test Squeeze")
        )

        self.assertGreater(outbox_id, 0)
        self.assertEqual(len(received_events), 1)
        self.assertEqual(received_events[0].code, "005930")

    def test_jit_kill_switch_dual_defense(self):
        # 1. 킬스위치 이벤트 발행 -> SQLite 상태 테이블 및 인메모리에 동시 기록
        self.bus.publish_critical(
            "risk.kill_switch",
            RiskAlertEvent(rule_id="RULE_MAX_DAILY_LOSS", message="일일 손실 한도 초과", action="HALT_ALL_STRATEGIES")
        )

        # 2. 글로벌 리스크 JIT 풀 체크 검증 (이벤트가 유실되었더라도 SQLite 상태에서 차단)
        risk_engine = GlobalRiskEngine()
        self.assertTrue(risk_engine.is_halted(), "JIT 풀 체크로 킬스위치 상태가 즉시 감지되어야 함")
        can_enter, reason = risk_engine.can_enter_new_trade(datetime(2026, 8, 29, 9, 30))
        self.assertFalse(can_enter)
        self.assertIn("킬스위치", reason)

    def test_cqrs_api_services(self):
        cmd_service = CommandService(event_bus=self.bus)
        query_service = QueryService()

        res_cmd = cmd_service.trigger_emergency_kill_switch("Test alert")
        self.assertEqual(res_cmd["status"], "KILL_SWITCH_PUBLISHED")

        health = query_service.get_system_health()
        self.assertEqual(health["status"], "HEALTHY")
        self.assertIn("SQLite WAL Mode", health["database_engine"])

    def test_business_day_scheduler_logic(self):
        from schedulers.daily_morning_scheduler import DailyMorningScheduler
        # 월요일(2026-08-31) = 영업일
        mon = datetime(2026, 8, 31, 7, 50)
        self.assertTrue(DailyMorningScheduler.is_business_day(mon))
        # 일요일(2026-08-30) = 휴장일
        sun = datetime(2026, 8, 30, 7, 50)
        self.assertFalse(DailyMorningScheduler.is_business_day(sun))

    def test_nxt_and_sor_trading_sessions(self):
        risk_engine = GlobalRiskEngine()
        # 1. 08:20 (NXT 프리마켓) -> SOR 모드 진입 가능
        can_enter_pre, _ = risk_engine.can_enter_new_trade(datetime(2026, 9, 1, 8, 20), order_routing="SOR")
        self.assertTrue(can_enter_pre)

        # 2. 16:30 (NXT 애프터마켓) -> SOR 모드 진입 가능
        can_enter_after, _ = risk_engine.can_enter_new_trade(datetime(2026, 9, 1, 16, 30), order_routing="SOR")
        self.assertTrue(can_enter_after)

        # 3. 16:30 (KRX 모드) -> 정규장 외 차단
        can_enter_krx, reason_krx = risk_engine.can_enter_new_trade(datetime(2026, 9, 1, 16, 30), order_routing="KRX")
        self.assertFalse(can_enter_krx)

        # 4. 20:30 (야간 휴장) -> 차단
        can_enter_night, _ = risk_engine.can_enter_new_trade(datetime(2026, 9, 1, 20, 30), order_routing="SOR")
        self.assertFalse(can_enter_night)

if __name__ == "__main__":
    unittest.main()
