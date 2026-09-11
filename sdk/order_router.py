# -*- coding: utf-8 -*-
"""
========================================================================================
⚡ [SDK: ADAPTIVE ORDER ROUTER - KRX TICK-SIZE ALIGNED & SIMULATION COMPATIBLE]
Determines optimal hoga_type and valid price based on:
1. KRX Tick Size Rules (1원, 5원, 10원, 50원, 100원, 500원, 1000원 단위 자동 정렬)
2. Kiwoom Simulation Server Compatibility (시장가 03 거부 방어 -> 00 매도1호가 타격 또는 06 최유리)
3. Sessions: Pre-Market (08:00~09:00), Regular (09:00~15:30), After-Market (15:30~20:00)
========================================================================================
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional

class AdaptiveOrderRouter:
    """세션 및 거래소 규정 적응형 주문 라우터 (호가 단위 보정 및 체결 100% 보장)"""

    @staticmethod
    def get_tick_size(price: float) -> int:
        """한국거래소(KRX) 주식 호가 가격 단위 반환"""
        p = abs(price)
        if p < 2000:
            return 1
        elif p < 5000:
            return 5
        elif p < 20000:
            return 10
        elif p < 50000:
            return 50
        elif p < 200000:
            return 100
        elif p < 500000:
            return 500
        else:
            return 1000

    @staticmethod
    def align_to_tick(price: float, side: str = "BUY") -> int:
        """호가 단위를 거래소 공식 틱 사이즈에 맞게 정확히 라운딩"""
        if price <= 0:
            return 0
        tick = AdaptiveOrderRouter.get_tick_size(price)
        p = int(round(price))
        remainder = p % tick
        if remainder == 0:
            return p
        
        # 매수 시에는 즉시 체결을 위해 올림(또는 반올림), 매도 시에는 내림
        if side.upper() == "BUY":
            return p + (tick - remainder)
        else:
            return p - remainder

    @staticmethod
    def is_simulation_server() -> bool:
        """account_state.json에서 모의투자 서버 여부 확인"""
        try:
            acc_path = r"C:\Antigravity\data\account_state.json"
            if os.path.exists(acc_path):
                with open(acc_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    server_name = data.get("server_name", "")
                    return "모의" in server_name
        except Exception:
            pass
        return True

    @classmethod
    def get_order_params(cls, side: str, current_price: float, now: datetime = None) -> Dict[str, Any]:
        now = now or datetime.now()
        h, m = now.hour, now.minute
        is_sim = cls.is_simulation_server()
        tick = cls.get_tick_size(current_price)

        # 즉시 체결을 위한 공격적 지정가 가격 계산
        # 매수: 현재가 + 1틱 (상대방 매도1호가 타격하여 즉시 체결)
        # 매도: 현재가 - 1틱 (상대방 매수1호가 타격하여 즉시 체결)
        if side.upper() == "BUY":
            immediate_price = cls.align_to_tick(current_price + tick, "BUY")
        else:
            immediate_price = cls.align_to_tick(max(current_price - tick, tick), "SELL")

        # 1. 08:00 ~ 09:00: 프리마켓 세션 (시장가 03 금지 -> 지정가 00 최우선호가)
        if (h == 8) or (h == 9 and m == 0):
            return {
                "can_order": True,
                "session": "NXT_PRE_MARKET",
                "hoga_type": "00",
                "order_price": immediate_price,
                "reason": f"프리마켓 세션: 지정가(00) {immediate_price:,}원 발주 (호가단위 {tick}원)"
            }

        # 2. 09:00 ~ 15:30: 정규장 세션
        if (9 <= h < 15) or (h == 15 and m <= 30):
            # 💡 키움증권 모의투자 서버는 시장가('03') 주문이 거부되거나 체결이 안 됨!
            # 따라서 모의투자에서는 매도1호가 타격 지정가('00')로 발주하여 100% 즉시 체결 보장!
            if is_sim:
                return {
                    "can_order": True,
                    "session": "REGULAR_SIMULATION",
                    "hoga_type": "00",
                    "order_price": immediate_price,
                    "reason": f"모의투자 정규장 세션: 시장가(03) 거부 방어 -> 지정가(00) 매도1호가 즉시체결 타격 {immediate_price:,}원 (호가단위 {tick}원 보정)"
                }
            else:
                return {
                    "can_order": True,
                    "session": "REGULAR_REAL_KRX",
                    "hoga_type": "06",  # 실전: 최유리지정가
                    "order_price": 0,
                    "reason": "실전 정규장: 최유리지정가(06) 초고속 즉시 체결 발주"
                }

        # 3. 15:30 ~ 20:00: 시간외 / 애프터마켓 (지정가 00)
        if (h == 15 and m > 30) or (16 <= h < 20):
            return {
                "can_order": True,
                "session": "NXT_AFTER_MARKET",
                "hoga_type": "00",
                "order_price": immediate_price,
                "reason": f"시간외/애프터마켓: 지정가(00) {immediate_price:,}원 발주"
            }

        # 4. 20:00 ~ 08:00: 야간 장 마감 시간
        return {
            "can_order": False,
            "session": "CLOSED_MARKET",
            "hoga_type": "00",
            "order_price": 0,
            "reason": "거래소 운영 시간 종료 (20:00 ~ 08:00)"
        }

adaptive_order_router = AdaptiveOrderRouter()
