"""
========================================================================================
🧪 [CI/CD UNIT TEST: RISK GUARDRAILS & KILL SWITCH]
Tests Local 1-share position sizing, -0.90% SL, trailing stops, and global kill switch rules.
========================================================================================
"""

import unittest
from datetime import datetime
from risk_engine.local_risk import LocalRiskManager
from risk_engine.global_risk import GlobalRiskEngine
from events.event_bus import global_event_bus

class TestRiskGuardrails(unittest.TestCase):
    def setUp(self):
        global_event_bus.reset_global_halt_state()

    def tearDown(self):
        global_event_bus.reset_global_halt_state()
    def test_1share_position_size(self):
        manager = LocalRiskManager("005930", "삼성전자", stop_loss_pct=-0.90)
        pos = manager.on_order_filled(80000, qty=100)  # 아무리 큰 수량을 넘겨도
        self.assertEqual(pos.qty, 1, "포지션 수량은 무조건 1주로 강제되어야 함")
        self.assertEqual(pos.entry_price, 80000)

    def test_stop_loss_trigger(self):
        manager = LocalRiskManager("005930", "삼성전자", stop_loss_pct=-0.90)
        manager.on_order_filled(80000, 1)
        # -1.0% 하락 시
        res = manager.evaluate_tick(79200)
        self.assertIsNotNone(res)
        self.assertEqual(res["action"], "SELL_ALL")
        self.assertIn("하드 손절", res["reason"])

    def test_trailing_stop_lifecycle(self):
        manager = LocalRiskManager("005930", "삼성전자", stop_loss_pct=-0.90)
        manager.on_order_filled(80000, 1)
        # +3.0% 상승 (82,400원) -> 트레일링 활성화
        manager.evaluate_tick(82400)
        self.assertTrue(manager.position.is_trailing_active)
        # 고점 대비 -0.6% 하락 (81,800원)
        res = manager.evaluate_tick(81800)
        self.assertIsNotNone(res)
        self.assertEqual(res["action"], "SELL_ALL")
        self.assertIn("트레일링", res["reason"])

    def test_global_blackout_and_kill_switch(self):
        engine = GlobalRiskEngine()
        # 1. 09:05 아침 블랙아웃
        can_enter, reason = engine.can_enter_new_trade(datetime(2026, 8, 29, 9, 5))
        self.assertFalse(can_enter)
        self.assertIn("시초가 블랙아웃", reason)

        # 2. 12:30 점심 휩쏘 방어 블랙아웃
        can_enter, reason = engine.can_enter_new_trade(datetime(2026, 8, 29, 12, 30))
        self.assertFalse(can_enter)
        self.assertIn("점심시간", reason)

        # 3. 09:30 정상 진입
        can_enter, reason = engine.can_enter_new_trade(datetime(2026, 8, 29, 9, 30))
        self.assertTrue(can_enter)

        # 4. 일일 손실 한도 초과
        engine.register_trade_result(-600000)
        self.assertTrue(engine.is_kill_switch_triggered)
        can_enter, reason = engine.can_enter_new_trade(datetime(2026, 8, 29, 10, 0))
        self.assertFalse(can_enter)
        self.assertIn("킬스위치", reason)

    def test_overnight_position_detection_and_liquidation(self):
        manager = LocalRiskManager("005930", "삼성전자", stop_loss_pct=-0.90)
        # 1. 오버나잇 보유 포지션 로드 (삼성전자 1주, 평단 260,000원)
        manager.load_existing_position(account_data={
            "holdings": [{"code": "005930", "name": "삼성전자", "qty": 1, "buy_price": 260000, "current_price": 255250}]
        })
        self.assertIsNotNone(manager.position, "오버나잇 보유 포지션이 자동으로 로드되어야 함")
        self.assertEqual(manager.position.qty, 1)
        self.assertEqual(manager.position.entry_price, 260000)

        # 2. 현재가 255,250원 (-1.8% 하락) 수신 시 즉시 하드 손절 SELL_ALL 액션 및 수량 반환
        res = manager.evaluate_tick(255250)
        self.assertIsNotNone(res)
        self.assertEqual(res["action"], "SELL_ALL")
        self.assertEqual(res["qty"], 1)
        self.assertIn("하드 손절", res["reason"])

if __name__ == "__main__":
    unittest.main()
