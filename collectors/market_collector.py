"""
========================================================================================
📡 [COLLECTOR: REAL-TIME MARKET COLLECTOR]
Dedicated real-time tick streaming collector decoupled from strategy execution.
========================================================================================
"""

from typing import Callable, Optional
from sdk.broker_adapter import BrokerAdapter

class RealtimeMarketCollector:
    def __init__(self, broker: BrokerAdapter, on_tick_callback: Callable):
        self.broker = broker
        self.on_tick_callback = on_tick_callback

    def subscribe_stock(self, screen_no: str, code: str):
        # 10:현재가, 15:거래량, 228:체결강도, 20:체결시간
        fids = "10;15;228;20"
        self.broker.subscribe_realtime(screen_no, code, fids)
        print(f">> [RealtimeCollector] 📡 종목 시세 구독 완료: {code} (화면: {screen_no})")
