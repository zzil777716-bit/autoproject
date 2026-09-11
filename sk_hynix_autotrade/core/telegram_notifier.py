"""
Telegram Alert Notifier for SK Hynix (000660)
"""

import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from config.settings import config

class TelegramNotifier:
    def __init__(self):
        self.token = config.TELEGRAM_BOT_TOKEN
        self.chat_id = config.TELEGRAM_CHAT_ID
        self.enabled = config.ENABLE_TELEGRAM and bool(self.token) and bool(self.chat_id)

    def _send(self, text: str):
        if not self.enabled:
            return
        # Async telegram sending logic if configured
        pass

    def notify_entry(self, code: str, price: float, qty: int, reason: str, metrics: Dict[str, Any]):
        msg = f"🚀 [SK하이닉스 매수 진입] {price:,.0f}원 ({qty}주)\n사유: {reason}"
        self._send(msg)

    def notify_stop_loss(self, code: str, loss_won: int, loss_pct: float, cooldown_min: int):
        msg = f"🔴 [SK하이닉스 손절] {loss_won:,}원 ({loss_pct:.2f}%)\n쿨다운: {cooldown_min}분"
        self._send(msg)

    def notify_trailing_exit(self, code: str, exit_price: float, total_pnl_won: int, total_pnl_pct: float):
        msg = f"✨ [SK하이닉스 익절 청산] {exit_price:,.0f}원 | 손익: {total_pnl_won:+,}원 ({total_pnl_pct:+.2f}%)"
        self._send(msg)
