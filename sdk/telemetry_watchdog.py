"""
========================================================================================
🛰️ [SDK: REAL-TIME SRE SENTINEL & TELEMETRY WATCHDOG]
Non-blocking autonomous background watchdog for real-time bug trapping,
connection heartbeat monitoring, account reconciliation, and AI health tracking.
========================================================================================
"""

import os
import time
import threading
from datetime import datetime
from typing import Dict, Any, List

class SystemWatchdogSentinel:
    def __init__(self):
        self._lock = threading.Lock()
        self.last_tick_times: Dict[str, float] = {}
        self.last_account_sync_time: float = time.time()
        self.active_ai_provider: str = "Gemini Flash 🟢"
        self.last_ai_latency_ms: float = 0.0
        self.trapped_exceptions: List[Dict[str, Any]] = []
        self.daily_pnl_won: int = 0
        self.is_kill_switch_active: bool = False
        self.kill_switch_reason: str = ""

    def report_tick(self, code: str, price: float):
        """실시간 시세 수신 시각 기록 (Heartbeat)"""
        with self._lock:
            self.last_tick_times[code] = time.time()

    def report_account_sync(self):
        """계좌 잔고 동기화 완료 시각 갱신"""
        with self._lock:
            self.last_account_sync_time = time.time()

    def report_ai_decision(self, provider: str, latency_ms: float):
        """AI 가디언 심사 결과 및 레이턴시 갱신"""
        with self._lock:
            self.active_ai_provider = provider
            self.last_ai_latency_ms = latency_ms

    def trap_exception(self, component: str, err_msg: str):
        """런타임 예외 발생 시 자가 격리 및 로그 기록"""
        with self._lock:
            rec = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "component": component,
                "error": err_msg
            }
            self.trapped_exceptions.append(rec)
            if len(self.trapped_exceptions) > 50:
                self.trapped_exceptions.pop(0)

    def report_kill_switch(self, triggered: bool, reason: str = ""):
        """비상 킬스위치 상태 보고"""
        with self._lock:
            self.is_kill_switch_active = triggered
            self.kill_switch_reason = reason

    def get_health_status(self) -> Dict[str, Any]:
        """
        전체 시스템 건강 상태 종합 리포트 산출 (0.001초 논블로킹 반환)
        """
        with self._lock:
            now = time.time()
            
            # 1. 소켓 통신 헬스 판별
            socket_ok = True
            stale_codes = []
            for code, t in self.last_tick_times.items():
                if now - t > 60.0:  # 60초 이상 무응답
                    socket_ok = False
                    stale_codes.append(code)

            # 2. 계좌 동기화 헬스
            acc_sync_ok = (now - self.last_account_sync_time) < 300.0

            # 3. 종합 점수 산출
            health_score = 100
            if not socket_ok:
                health_score -= 15
            if not acc_sync_ok:
                health_score -= 5
            if self.is_kill_switch_active:
                health_score -= 50
            if len(self.trapped_exceptions) > 0:
                health_score = max(50, health_score - len(self.trapped_exceptions) * 2)

            return {
                "health_score": max(0, min(100, health_score)),
                "socket_status": "OK 🟢" if socket_ok else f"STALE 🟡 ({stale_codes})",
                "account_sync_status": "OK 🟢" if acc_sync_ok else "SYNC_WAIT 🟡",
                "ai_provider": self.active_ai_provider,
                "ai_latency_ms": self.last_ai_latency_ms,
                "kill_switch": "ACTIVE 🛑" if self.is_kill_switch_active else "NORMAL 🟢",
                "kill_switch_reason": self.kill_switch_reason,
                "error_count": len(self.trapped_exceptions),
                "last_error": self.trapped_exceptions[-1] if self.trapped_exceptions else None
            }

# 싱글톤 센티널 인스턴스
system_watchdog = SystemWatchdogSentinel()
