"""
========================================================================================
✍️ [API LAYER: CQRS WRITE-COMMAND SERVICE (2.4 COMPONENT)]
Dispatches trading commands, emergency kill-switches, and manual orders via EventBus.
========================================================================================
"""

import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from events.event_bus import global_event_bus, OrderCommandEvent, RiskAlertEvent

class CommandService:
    """CQRS Command(쓰기) 전용 서비스 — 요청 검증 후 이벤트 버스에 즉시 발행 (Non-blocking)"""

    def __init__(self, event_bus=global_event_bus):
        self.event_bus = event_bus

    def trigger_emergency_kill_switch(self, reason: str = "User manual trigger") -> Dict[str, Any]:
        """긴급 킬스위치 발행"""
        event = RiskAlertEvent(
            rule_id="MANUAL_KILL_SWITCH",
            message=f"긴급 킬스위치 발동: {reason}",
            action="HALT_ALL_STRATEGIES"
        )
        self.event_bus.publish("risk.kill_switch", event)
        return {
            "status": "KILL_SWITCH_PUBLISHED",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "reason": reason
        }

    def dispatch_manual_order(self, code: str, side: str, qty: int = 1, price: float = 0.0) -> Dict[str, Any]:
        """수동 주문 발행"""
        event = OrderCommandEvent(
            code=code,
            side=side,
            qty=qty,
            price=price,
            strategy_name="Manual_Override"
        )
        self.event_bus.publish("orders.command", event)
        return {
            "status": "ORDER_COMMAND_DISPATCHED",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "code": code,
            "side": side,
            "qty": qty
        }
