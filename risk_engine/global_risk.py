"""
========================================================================================
🛡️ [GLOBAL RISK ENGINE: ACCOUNT-LEVEL 2ND LINE OF DEFENSE]
Monitors overall account daily PnL, consecutive loss cooldowns, and executes Kill-Switch rules.
========================================================================================
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

class GlobalRiskEngine:
    def __init__(self, rules_file_path: Optional[str] = None):
        if rules_file_path is None:
            rules_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "kill_switch_rules.json")
        self.rules_file_path = rules_file_path
        self.daily_pnl_won = 0.0
        self.daily_trade_count = 0
        self.daily_order_attempts = 0
        self.consecutive_losses = 0
        self.cooldown_until: Optional[datetime] = None
        self.is_kill_switch_triggered = False
        self.kill_switch_reason = ""
        self.rules = self.load_rules()

    def load_rules(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.rules_file_path):
            try:
                with open(self.rules_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("kill_switch_rules", [])
            except Exception as e:
                print(f">> [GlobalRiskEngine] 룰 로드 오류: {e}")
        return []

    def register_order_attempt(self) -> bool:
        """주문 발주 직전 시도 횟수 기록 및 한도 초과 시 킬스위치 발동"""
        self.daily_order_attempts += 1
        return self.evaluate_kill_switch()

    def register_trade_result(self, pnl_won: float):
        self.daily_pnl_won += pnl_won
        self.daily_trade_count += 1
        if pnl_won < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0

        self.evaluate_kill_switch()

    def evaluate_kill_switch(self) -> bool:
        """JSON 룰 기반 킬 스위치 판정"""
        for r in self.rules:
            r_type = r.get("type")
            if r_type == "daily_loss_limit":
                thresh = r.get("threshold_won", -500000)
                if self.daily_pnl_won <= thresh:
                    self.is_kill_switch_triggered = True
                    self.kill_switch_reason = f"일일 누적 손실 한도 초과 ({self.daily_pnl_won:,.0f}원 <= {thresh:,.0f}원)"
                    return True

            elif r_type == "consecutive_losses":
                thresh = r.get("threshold_count", 2)
                cooldown_min = r.get("cooldown_minutes", 15)
                if self.consecutive_losses >= thresh:
                    self.cooldown_until = datetime.now() + timedelta(minutes=cooldown_min)
                    print(f">> [GlobalRiskEngine] ⚠️ {self.consecutive_losses}회 연속 손실 발생 -> {cooldown_min}분간 쿨다운 발동!")

            elif r_type == "max_daily_trades":
                thresh = r.get("threshold_count", 3)
                if self.daily_trade_count >= thresh:
                    self.is_kill_switch_triggered = True
                    self.kill_switch_reason = f"일일 최대 매매 횟수 도달 ({self.daily_trade_count}/{thresh}회)"
                    return True

            elif r_type == "max_order_attempts":
                thresh = r.get("threshold_count", 5)
                if self.daily_order_attempts >= thresh:
                    self.is_kill_switch_triggered = True
                    self.kill_switch_reason = f"일일 최대 주문 시도 횟수 도달 ({self.daily_order_attempts}/{thresh}회) - 주문 폭격 방어"
                    return True

        return self.is_kill_switch_triggered

    def is_halted(self) -> bool:
        """
        [이중 방어선 JIT 풀 체크]
        1) 인메모리 플래그 확인
        2) SQLite 공용 상태 테이블(global_system_state) 실시간 확인
        이벤트가 유실되더라도 주문 직전에 확실하게 차단합니다.
        """
        if self.is_kill_switch_triggered:
            return True

        from events.event_bus import global_event_bus
        if global_event_bus.check_global_halt_state():
            self.is_kill_switch_triggered = True
            self.kill_switch_reason = "DB 공유 상태 테이블 킬스위치 감지"
            return True

        return False

    def can_enter_new_trade(self, current_time: datetime, order_routing: str = "SOR") -> Tuple[bool, str]:
        """신규 주문 진입 가능 여부 확인 (SOR 최선집행 / NXT 08:00~20:00 지원)"""
        if self.is_halted():
            return False, f"킬스위치 가동 중: {self.kill_switch_reason}"

        if self.cooldown_until and current_time < self.cooldown_until:
            rem = int((self.cooldown_until - current_time).total_seconds())
            return False, f"연속 손실 쿨다운 중 (잔여: {rem}초)"

        time_str = current_time.strftime("%H:%M:%S")

        # 1. NXT 및 SOR 모드 지원 (08:00 ~ 20:00 거래)
        if order_routing.upper() in ["SOR", "NXT"]:
            # 프리마켓 개장 전 (08:00 이전) 또는 애프터마켓 종료 후 (20:00 이후)
            if time_str < "08:00:00" or time_str >= "20:00:00":
                return False, f"장 운영 시간 외 (NXT/SOR 운영: 08:00~20:00)"
            
            # 정규장 전환 및 시초가 휩쏘 구간 (08:50 ~ 09:15)
            if "08:50:00" <= time_str < "09:15:00":
                return False, "시초가 블랙아웃 (08:50~09:15 신규 진입 제한)"
            
            # 점심시간 휩쏘 구간 (12:00 ~ 13:00)
            if "12:00:00" <= time_str < "13:00:00":
                return False, "점심시간 휩쏘 방어 블랙아웃 (12:00~13:00 신규 진입 제한)"
            
            # 정규장 마감 동시호가 전환 구간 (15:20 ~ 15:35)
            if "15:20:00" <= time_str < "15:35:00":
                return False, "장 마감 동시호가 블랙아웃 (15:20~15:35 신규 진입 제한)"

            return True, f"정상 진입 가능 ({order_routing} 모드)"

        # 2. KRX 정규장 전용 모드 (09:00 ~ 15:30)
        if time_str < "09:00:00":
            return False, "정규장 개장 전 (09:00 이전 신규 진입 제한)"
        if "09:00:00" <= time_str < "09:15:00":
            return False, "시초가 블랙아웃 (09:00~09:15 신규 진입 제한)"
        if "12:00:00" <= time_str < "13:00:00":
            return False, "점심시간 휩쏘 방어 블랙아웃 (12:00~13:00 신규 진입 제한)"
        if time_str >= "15:15:00":
            return False, "장 마감 직전 블랙아웃 (15:15 이후 신규 진입 제한)"

        return True, "정상 진입 가능 (KRX 모드)"
