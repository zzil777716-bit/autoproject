"""
Risk Management & Execution Safety Engine (1-Share Execution & Red-Team Guardrails)
Optimized for Samsung Electronics Strategy 2 (MTF-Squeeze).
Includes Trade Journal MFE / MAE tracking for Quant Research.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from config.settings import config

@dataclass
class Position:
    code: str = "005930"
    trade_id: str = ""
    qty: int = 0
    avg_price: float = 0.0
    highest_price: float = 0.0
    lowest_price: float = float('inf')
    mfe_pct: float = 0.0  # Maximum Favorable Excursion
    mae_pct: float = 0.0  # Maximum Adverse Excursion
    status: str = "NONE"   # NONE, HOLDING, BREAK_EVEN_ACTIVE, TRAILING_ACTIVE
    entry_time: Optional[datetime] = None
    stop_loss_price: float = 0.0
    target_price_1: float = 0.0
    target_price_2: float = 0.0

@dataclass
class RiskAction:
    action_type: str = "NONE"  # NONE, BUY, FULL_SELL, STOP_LOSS, KILL_SWITCH
    qty: int = 0
    price: float = 0.0
    reason: str = ""
    trade_id: str = ""
    mfe_pct: float = 0.0
    mae_pct: float = 0.0
    holding_seconds: float = 0.0

class RiskManager:
    def __init__(self, initial_equity: float = 10_000_000):
        self.equity: float = initial_equity
        self.daily_start_equity: float = initial_equity
        self.daily_pnl: float = 0.0
        self.daily_trades_count: int = 0
        self.consecutive_losses: int = 0
        self.cooldown_until: datetime = datetime.min
        self.is_circuit_broken: bool = False
        self.position = Position()
        
    def can_trade(self, current_time: datetime) -> Tuple[bool, str]:
        if self.is_circuit_broken:
            return False, "일일 최대 손실 한도(-1.5%) 도달로 시스템 락다운(KILL_SWITCH)"
            
        daily_loss_pct = (self.daily_pnl / self.daily_start_equity) * 100.0
        if daily_loss_pct <= config.DAILY_MAX_LOSS_PCT:
            self.is_circuit_broken = True
            return False, f"당일 누적 손실({daily_loss_pct:.2f}%)이 한도({config.DAILY_MAX_LOSS_PCT}%) 초과"

        if self.daily_trades_count >= config.MAX_DAILY_TRADES:
            return False, f"일일 최대 매매 횟수({config.MAX_DAILY_TRADES}회) 도달로 신규 진입 중단"
            
        if current_time < self.cooldown_until:
            rem_sec = int((self.cooldown_until - current_time).total_seconds())
            return False, f"손절 후 뇌동매매 방지 쿨다운 중 (잔여: {rem_sec}초)"
            
        return True, "매매 가능 🟢"

    def calculate_order_qty(self, current_price: float) -> int:
        return config.DEFAULT_TRADE_QTY

    def on_position_entered(self, qty: int, price: float, current_time: datetime, stop_price: float = 0.0, target_price: float = 0.0, trade_id: str = ""):
        self.position.trade_id = trade_id or f"SAM-{current_time.strftime('%Y%m%d%H%M%S')}"
        self.position.qty = qty
        self.position.avg_price = price
        self.position.highest_price = price
        self.position.lowest_price = price
        self.position.mfe_pct = 0.0
        self.position.mae_pct = 0.0
        self.position.status = "HOLDING"
        self.position.entry_time = current_time
        self.position.stop_loss_price = stop_price if stop_price > 0 else round(price * (1.0 + config.STOP_LOSS_PCT / 100.0), 0)
        self.position.target_price_1 = target_price if target_price > 0 else round(price * (1.0 + config.TAKE_PROFIT_1_PCT / 100.0), 0)
        self.position.target_price_2 = round(price * (1.0 + config.TAKE_PROFIT_2_PCT / 100.0), 0)
        self.daily_trades_count += 1

    def check_position_risk(self, current_price: float, current_time: datetime) -> RiskAction:
        if self.position.qty <= 0:
            return RiskAction()

        # Update MFE / MAE
        if current_price > self.position.highest_price:
            self.position.highest_price = current_price
        if current_price < self.position.lowest_price:
            self.position.lowest_price = current_price

        entry_price = self.position.avg_price
        current_pnl_pct = ((current_price - entry_price) / entry_price) * 100.0
        self.position.mfe_pct = max(self.position.mfe_pct, ((self.position.highest_price - entry_price) / entry_price) * 100.0)
        self.position.mae_pct = min(self.position.mae_pct, ((self.position.lowest_price - entry_price) / entry_price) * 100.0)

        now_time = current_time.time()
        holding_sec = (current_time - self.position.entry_time).total_seconds() if self.position.entry_time else 0.0

        # [가드레일 4] 장마감 청산 (15:20)
        if now_time >= config.TIME_MARKET_CLOSE_SELL:
            return RiskAction(
                action_type="FULL_SELL", qty=self.position.qty, price=current_price,
                reason="15:20 장마감 오버나이트 방지 전량 청산",
                trade_id=self.position.trade_id, mfe_pct=self.position.mfe_pct, mae_pct=self.position.mae_pct, holding_seconds=holding_sec
            )

        # [타임아웃 청산] 45분간 모멘텀 부재 시
        if self.position.entry_time and (holding_sec / 60.0) >= config.TIMEOUT_MINUTES and current_pnl_pct < 0.30:
            return RiskAction(
                action_type="FULL_SELL", qty=self.position.qty, price=current_price,
                reason=f"{int(holding_sec/60.0)}분 경과 타임아웃 청산",
                trade_id=self.position.trade_id, mfe_pct=self.position.mfe_pct, mae_pct=self.position.mae_pct, holding_seconds=holding_sec
            )

        # [손절선 도달]
        if current_price <= self.position.stop_loss_price or current_pnl_pct <= config.STOP_LOSS_PCT:
            self._handle_stop_loss(current_time)
            return RiskAction(
                action_type="STOP_LOSS", qty=self.position.qty, price=current_price,
                reason=f"고정 손절선 도달 ({current_pnl_pct:.2f}%)",
                trade_id=self.position.trade_id, mfe_pct=self.position.mfe_pct, mae_pct=self.position.mae_pct, holding_seconds=holding_sec
            )

        # [1차 목표가 도달 시 본절 스탑 전환]
        if current_pnl_pct >= config.TAKE_PROFIT_1_PCT and self.position.status == "HOLDING":
            self.position.status = "BREAK_EVEN_ACTIVE"
            self.position.stop_loss_price = entry_price
            print(f">> [RISK GUARD] 1차 목표(+{current_pnl_pct:.2f}%) 도달! 손절가를 매수가({entry_price:,.0f}원)로 상향 방어합니다.")

        # [본절가 재도달 청산]
        if self.position.status in ["BREAK_EVEN_ACTIVE", "TRAILING_ACTIVE"] and current_price <= entry_price:
            return RiskAction(
                action_type="FULL_SELL", qty=self.position.qty, price=current_price,
                reason="본절가(매수가) 재도달로 원금보존 청산",
                trade_id=self.position.trade_id, mfe_pct=self.position.mfe_pct, mae_pct=self.position.mae_pct, holding_seconds=holding_sec
            )

        # [2차 목표가 도달 전량 익절]
        if current_pnl_pct >= config.TAKE_PROFIT_2_PCT:
            return RiskAction(
                action_type="FULL_SELL", qty=self.position.qty, price=current_price,
                reason=f"2차 최종 목표가(+{current_pnl_pct:.2f}%) 도달 전량 익절",
                trade_id=self.position.trade_id, mfe_pct=self.position.mfe_pct, mae_pct=self.position.mae_pct, holding_seconds=holding_sec
            )

        # [트레일링 스탑]
        highest_pnl = ((self.position.highest_price - entry_price) / entry_price) * 100.0
        if highest_pnl >= config.TRAILING_STOP_TRIGGER_PCT:
            self.position.status = "TRAILING_ACTIVE"
            drop_pct = ((current_price - self.position.highest_price) / self.position.highest_price) * 100.0
            if drop_pct <= config.TRAILING_STOP_DROP_PCT:
                return RiskAction(
                    action_type="FULL_SELL", qty=self.position.qty, price=current_price,
                    reason=f"최고점 대비 {drop_pct:.2f}% 반납으로 트레일링 익절",
                    trade_id=self.position.trade_id, mfe_pct=self.position.mfe_pct, mae_pct=self.position.mae_pct, holding_seconds=holding_sec
                )

        return RiskAction()

    def _handle_stop_loss(self, current_time: datetime):
        self.consecutive_losses += 1
        if self.consecutive_losses >= config.CONSECUTIVE_LOSS_LIMIT:
            self.cooldown_until = current_time + timedelta(minutes=config.COOLDOWN_MINUTES_CONSECUTIVE)
        else:
            self.cooldown_until = current_time + timedelta(minutes=config.COOLDOWN_MINUTES_DEFAULT)

    def on_trade_closed(self, realized_pnl: float):
        self.daily_pnl += realized_pnl
        self.equity += realized_pnl
        if realized_pnl > 0:
            self.consecutive_losses = 0
        self.position = Position()
