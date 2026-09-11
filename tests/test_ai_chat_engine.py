"""
========================================================================================
🧪 [CI/CD UNIT TEST: GOOGLE GEMINI TRADING COPILOT ENGINE]
========================================================================================
"""

import unittest
from sdk.ai_chat_engine import GeminiTradingCopilot, ai_chat_engine

class TestAIChatEngine(unittest.TestCase):
    def setUp(self):
        self.engine = GeminiTradingCopilot()

    def test_account_query_response(self):
        reply = self.engine.process_query("현재 계좌 상태와 예수금 브리핑해줘")
        self.assertTrue(len(reply) > 10)
        self.assertTrue(any(w in reply for w in ["계좌", "예수금", "Gemini", "원", "잔고"]))

    def test_stock_diagnosis_query(self):
        reply = self.engine.process_query("삼성전자와 SK하이닉스 퀀트 진단해줘")
        self.assertTrue(len(reply) > 10)
        self.assertTrue(any(w in reply for w in ["삼성전자", "SK하이닉스", "15", "퀀트", "Gemini"]))

    def test_strategy_query(self):
        reply = self.engine.process_query("전략 A와 전략 B 조건 설명해줘")
        self.assertTrue(len(reply) > 10)
        self.assertTrue(any(w in reply for w in ["전략", "3선", "정배열", "Gemini"]))

    def test_system_orders_query(self):
        reply = self.engine.process_query("최근 주문 및 체결 내역 리포트해줘")
        self.assertTrue(len(reply) > 10)
        self.assertTrue(any(w in reply for w in ["주문", "체결", "내역", "Gemini"]))

if __name__ == "__main__":
    unittest.main()
