"""
========================================================================================
🛡️ [LOCAL RISK ENGINE: IN-MEMORY FAST 1ST LINE OF DEFENSE - OVERNIGHT & INTRADAY]
Zero-latency position guardrails, overnight holding automatic detection, 
-0.90% SL, trailing stop, and complete position liquidation.
========================================================================================
"""

import os
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class Position:
    code: str
    stock_name: str
    entry_price: float
    qty: int = 1
    entry_time: Optional[datetime] = None
    stop_loss_price: float = 0.0
    highest_price: float = 0.0
    lowest_price: float = 0.0
    is_tp1_triggered: bool = False
    is_trailing_active: bool = False
    status: str = "ACTIVE"  # "ACTIVE", "CLOSING", "CLOSED"

class LocalRiskManager:
    def __init__(self, code: str, stock_name: str, stop_loss_pct: float = -0.90, base_dir: str = r"D:\ANTIGRAVITY(자동매매)"):
        self.code = str(code).zfill(6)
        self.stock_name = stock_name
        self.stop_loss_pct = stop_loss_pct
        self.base_dir = base_dir
        self.position: Optional[Position] = None

        # 초기화 시 전일/기존 보유 잔고(오버나잇 포지션) 자동 연동
        self.load_existing_position()

    def load_existing_position(self, account_data: Optional[Dict[str, Any]] = None) -> Optional[Position]:
        """계좌 잔고 파일(account_state.json) 또는 전달된 데이터에서 기존 보유/오버나잇 잔고를 조회하여 포지션 자동 복원"""
        try:
            if account_data is not None:
                data = account_data
            else:
                acc_file = os.path.join(self.base_dir, "data", "account_state.json")
                if not os.path.exists(acc_file):
                    return None
                with open(acc_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

            holdings = data.get("holdings", [])
            target = next((h for h in holdings if str(h.get("code", "")).zfill(6) == self.code), None)

            if target and target.get("qty", 0) > 0:
                qty = int(target["qty"])
                buy_price = float(target.get("buy_price", 0.0))
                cur_price = float(target.get("current_price", buy_price))
                sl_price = buy_price * (1.0 + self.stop_loss_pct / 100.0)

                self.position = Position(
                    code=self.code,
                    stock_name=self.stock_name,
                    entry_price=buy_price,
                    qty=qty,
                    entry_time=datetime.now(),
                    stop_loss_price=sl_price,
                    highest_price=max(buy_price, cur_price),
                    lowest_price=min(buy_price, cur_price)
                )

                try:
                    print(f">> [LocalRiskManager] [HOLDING DETECTED] {self.stock_name}({self.code}) {qty}주 (평단 {buy_price:,.0f}원) -> 손절선 {sl_price:,.0f}원({self.stop_loss_pct:.2f}%) 자동 감시 가동!")
                except Exception:
                    pass
                return self.position
        except Exception:
            pass

        return None

    def on_order_filled(self, price: float, qty: int = 1) -> Position:
        """신규 매수 체결 시 포지션 등록 (1주 고정 원칙 강제)"""
        fixed_qty = 1  # 1주 고정 가드레일
        sl_price = price * (1.0 + self.stop_loss_pct / 100.0)
        self.position = Position(
            code=self.code,
            stock_name=self.stock_name,
            entry_price=price,
            qty=fixed_qty,
            entry_time=datetime.now(),
            stop_loss_price=sl_price,
            highest_price=price,
            lowest_price=price
        )
        try:
            print(f">> [LocalRiskManager] [POSITION ENTERED] {self.stock_name}({self.code}) {fixed_qty}주 @ {price:,.0f}원 | 손절선: {sl_price:,.0f}원")
        except Exception:
            pass
        return self.position

    def evaluate_tick(self, current_price: float) -> Optional[Dict[str, Any]]:
        """틱 수신 시 실시간 손익 평가 및 손절/익절/트레일링 액션 판정"""
        if not self.position or self.position.qty <= 0:
            return None

        pos = self.position
        if current_price > pos.highest_price:
            pos.highest_price = current_price
        if current_price < pos.lowest_price:
            pos.lowest_price = current_price

        pnl_pct = ((current_price - pos.entry_price) / pos.entry_price) * 100.0

        # 1. 하드 손절선 (-0.90%) 터치 시 즉시 전량 청산
        if current_price <= pos.stop_loss_price:
            return {
                "action": "SELL_ALL",
                "qty": pos.qty,
                "reason": f"하드 손절 도달 ({pnl_pct:.2f}%) <= {self.stop_loss_pct:.2f}% (평단: {pos.entry_price:,.0f}원)",
                "price": current_price,
                "pnl_pct": pnl_pct
            }

        # 2. 1차 목표가 (+1.30% ~ +1.50%) 도달 시 -> 본절 스탑 전환
        if pnl_pct >= 1.30 and not pos.is_tp1_triggered:
            pos.is_tp1_triggered = True
            pos.stop_loss_price = max(pos.stop_loss_price, pos.entry_price * 1.001)

        # 3. 2차 목표가 (+2.50% ~ +2.80%) 도달 시 -> 트레일링 스탑 활성화
        if pnl_pct >= 2.50:
            pos.is_trailing_active = True

        # 4. 트레일링 스탑 추적 (고점 대비 -0.50% 하락 시 청산)
        if pos.is_trailing_active:
            trailing_stop_price = pos.highest_price * 0.995
            if current_price <= trailing_stop_price:
                return {
                    "action": "SELL_ALL",
                    "qty": pos.qty,
                    "reason": f"트레일링 스탑 발동 (최고가 {pos.highest_price:,.0f}원 대비 -0.50% 하락, 실현수익 {pnl_pct:.2f}%)",
                    "price": current_price,
                    "pnl_pct": pnl_pct
                }

        return None

    def mark_closing(self):
        """매도 주문 전송 시 포지션을 청산 진행 중(CLOSING)으로 마킹"""
        if self.position:
            self.position.status = "CLOSING"

    def on_chejan_fill(self, side: str, fill_qty: int, fill_price: float = 0.0, remaining_qty: int = 0) -> bool:
        """키움 OnReceiveChejanData 체결 통보 수신 시 실체결 기반 포지션 확정/종료"""
        if side.upper() in ["BUY", "매수", "1"]:
            if not self.position or self.position.status == "PENDING_BUY":
                p = fill_price if fill_price > 0 else (self.position.entry_price if self.position else 0.0)
                self.on_order_filled(p, fill_qty)
                print(f">> [LocalRiskManager] ✅ [{self.stock_name}] {fill_qty}주 실체결 확인 완료 -> 포지션 ACTIVE 전환 (체결가: {p:,.0f}원)")
                return True
            return False

        if side.upper() in ["SELL", "매도", "2"]:
            if not self.position:
                return False
            if remaining_qty == 0:
                print(f">> [LocalRiskManager] ✅ [{self.stock_name}] {fill_qty}주 전량 매도 체결 확인 완료 -> 포지션 안전 소멸")
                self.close_position()
                return True
            else:
                self.position.qty = max(0, self.position.qty - fill_qty)
                print(f">> [LocalRiskManager] ⚠️ [{self.stock_name}] {fill_qty}주 부분 체결 (잔여: {self.position.qty}주)")
                return False

        return False

    def close_position(self):
        """포지션 청산 완료 처리"""
        self.position = None
