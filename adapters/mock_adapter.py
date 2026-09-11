"""
========================================================================================
🔌 [BROKER ADAPTER: MOCK & BACKTEST IMPLEMENTATION]
Zero-dependency mock adapter for Unit Tests, CI/CD, and fast Backtesting.
========================================================================================
"""

from typing import Dict, Any, Optional
from sdk.broker_adapter import BrokerAdapter

class MockAdapter(BrokerAdapter):
    def __init__(self, initial_deposit: int = 10_000_000):
        self.deposit = initial_deposit
        self.orders = []
        self.positions = {}
        self.simulated_prices = {"005930": 82500, "000660": 265000}

    def login(self) -> bool:
        return True

    def get_deposit(self, account_no: str) -> Dict[str, Any]:
        return {"deposit": self.deposit, "orderable": self.deposit}

    def get_stock_info(self, code: str) -> Dict[str, Any]:
        price = self.simulated_prices.get(code, 50000)
        return {"price": price, "rate": 1.5, "volume": 1_000_000}

    def send_order(self, rq_name: str, screen_no: str, acc_no: str, order_type: int, code: str, qty: int, price: int, hoga_type: str) -> int:
        order_info = {
            "rq_name": rq_name,
            "order_type": "BUY" if order_type == 1 else "SELL",
            "code": code,
            "qty": qty,
            "price": price if price > 0 else self.simulated_prices.get(code, 50000),
            "hoga_type": hoga_type
        }
        self.orders.append(order_info)
        return 0

    def subscribe_realtime(self, screen_no: str, code: str, fids: str):
        pass
