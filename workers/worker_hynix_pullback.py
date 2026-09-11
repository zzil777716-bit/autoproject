"""
========================================================================================
⚡ [WORKER: SK HYNIX TRIPLE-SCREEN ENVELOPE STRATEGY WORKER]
Isolated process executing SK Hynix (000660) 1-Share fixed quantitative strategy.
========================================================================================
"""

import os
import sys
import time
from datetime import datetime
from PyQt5.QtWidgets import QApplication

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sdk.base_strategy import BaseStrategy, StrategySignal
from sdk.data_feeds import LiveDataFeed
from adapters.kiwoom_adapter import KiwoomAdapter
from risk_engine.local_risk import LocalRiskManager
from risk_engine.global_risk import GlobalRiskEngine
from storage.timeseries_db import TimeseriesIndicatorEngine
from storage.data_lake import QuantDataLake
from config.settings import config

class SKHynixDualWorkerStrategy(BaseStrategy):
    """[SK하이닉스 통합 듀얼 엔진] 전략 A(3선점화) + 전략 B(정배열 황금 이격도) 동시 감시"""
    def __init__(self):
        super().__init__(config.HYNIX_CODE, config.HYNIX_NAME)
        self.strategy_name = "SK Hynix Dual Engine (3-Lines + MA Alignment Disparity)"

    def evaluate(self, feed, current_time: datetime) -> StrategySignal:
        df_15m = feed.get_ohlcv(self.code, 15, limit=130)
        df_3m = feed.get_ohlcv(self.code, 3, limit=30)
        current_price = feed.get_realtime_price(self.code)
        intensity = feed.get_realtime_intensity(self.code)

        signal = StrategySignal(
            should_enter=False,
            side="BUY",
            entry_price=current_price,
            reason=""
        )

        if len(df_15m) < 20 or len(df_3m) < 6 or current_price <= 0:
            return signal

        close15 = df_15m['close']
        ma20 = close15.rolling(20).mean()
        cum_vol15 = df_15m['volume'].rolling(20).sum()
        cum_val15 = (close15 * df_15m['volume']).rolling(20).sum()
        vwap20 = cum_val15 / (cum_vol15 + 1e-9)
        h13 = df_15m['high'].rolling(13).max()
        l13 = df_15m['low'].rolling(13).min()
        tenkan13 = (h13 + l13) / 2.0

        # --- 3M 점화 공통 트리거 (5EMA 상향 돌파 & RVOL >= 1.35) ---
        close3 = df_3m['close']
        ema5 = close3.ewm(span=5, adjust=False).mean()
        vol3 = df_3m['volume']
        vol_ma5 = vol3.rolling(5).mean()
        rvol = vol3 / (vol_ma5 + 1e-9)

        ema_cross = (current_price > ema5.iloc[-1]) and (close3.iloc[-2] <= ema5.iloc[-2])
        rvol_surge = rvol.iloc[-1] >= 1.35

        # --- 1. 전략 A: 15M 3선 종가 유지 검증 ---
        all_3lines = (close15 > ma20) & (close15 > vwap20) & (close15 > tenkan13)
        sustained_2bars = all_3lines & all_3lines.shift(1).fillna(False)
        sig_a_ready = sustained_2bars.iloc[-1] and ema_cross and rvol_surge and (intensity >= 105.0)

        # --- 2. 전략 B: 15M 20>60>120 정배열 & 황금 이격도 (101.5%~104.0%) ---
        sig_b_ready = False
        if len(df_15m) >= 120:
            ma60 = close15.rolling(60).mean().iloc[-1]
            ma120 = close15.rolling(120).mean().iloc[-1]
            is_aligned = (ma20.iloc[-1] > ma60) and (ma60 > ma120)
            disp_price_ma20 = (current_price / (ma20.iloc[-1] + 1e-9)) * 100.0
            is_golden_disp = (101.5 <= disp_price_ma20 <= 104.0)
            sig_b_ready = is_aligned and is_golden_disp and ema_cross and rvol_surge

        # --- 통합 신호 합성 ---
        if sig_a_ready and sig_b_ready:
            signal.should_enter = True
            signal.entry_price = current_price
            signal.stop_loss_price = current_price * 0.991
            signal.take_profit_price = current_price * 1.015
            signal.strategy_tag = "DUAL_CONFLUENCE_A+B"
            signal.reason = (
                f"🔥 [SK하이닉스 초강력 합의] 전략A(3선점화) + 전략B(20>60>120 정배열 황금이격 {disp_price_ma20:.1f}%) 동시충족 (현재가 {current_price:,.0f}원)"
            )
            return signal

        if sig_a_ready:
            signal.should_enter = True
            signal.entry_price = current_price
            signal.stop_loss_price = current_price * 0.991
            signal.take_profit_price = current_price * 1.015
            signal.strategy_tag = "STRATEGY_A_3LINES"
            signal.reason = (
                f"[SK하이닉스 전략 A: 3선점화] 15M 3선 지지 + 3M 5EMA돌파 & RVOL {rvol.iloc[-1]:.1f}배 (현재가 {current_price:,.0f}원)"
            )
            return signal

        if sig_b_ready:
            signal.should_enter = True
            signal.entry_price = current_price
            signal.stop_loss_price = current_price * 0.991
            signal.take_profit_price = current_price * 1.015
            signal.strategy_tag = "STRATEGY_B_DISPARITY"
            signal.reason = (
                f"[SK하이닉스 전략 B: 정배열이격] 15M 20>60>120 정배열 + 황금 이격도 {disp_price_ma20:.1f}% + 3M 점화 (현재가 {current_price:,.0f}원)"
            )
            return signal

        return signal

class SKHynixWorker:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.engine = TimeseriesIndicatorEngine(config.HYNIX_CODE, config.HYNIX_NAME)
        self.strategy = SKHynixDualWorkerStrategy()
        self.local_risk = LocalRiskManager(config.HYNIX_CODE, config.HYNIX_NAME, config.STOP_LOSS_PCT)
        self.global_risk = GlobalRiskEngine()
        self.datalake = QuantDataLake(partition_key="000660")
        
        self.current_price = 0.0
        self.current_volume = 0
        self.current_intensity = 100.0

        # [Triple-Lock Guardrails]
        self.is_ordering = False
        self.last_order_candle_time: str = ""
        self.last_order_timestamp: float = 0.0

        self.feed = LiveDataFeed(
            self.engine,
            lambda: self.current_price,
            lambda: self.current_intensity
        )

        self.adapter = KiwoomAdapter(
            on_tick_callback=self.on_tick,
            on_chejan_callback=self.on_chejan
        )

    def on_tick(self, code: str, price: float, volume: int, intensity: float, timestr: str):
        if code != config.HYNIX_CODE:
            return
        self.current_price = price
        self.current_volume = volume
        self.current_intensity = intensity

        self.engine.add_tick(price, volume, intensity, timestr)
        now = datetime.now()

        # 1. 포지션 보유 시 로컬 리스크 평가 (오버나잇 및 당일 보유분 전량 감시)
        if self.local_risk.position and self.local_risk.position.status == "ACTIVE":
            risk_action = self.local_risk.evaluate_tick(price)
            if risk_action and risk_action["action"] == "SELL_ALL":
                self.execute_sell(
                    risk_action["price"],
                    risk_action["reason"],
                    risk_action["pnl_pct"],
                    qty=risk_action.get("qty", 1)
                )
            return

        # 2. 주문 진행 중이거나 PENDING 상태면 신규 매수 차단
        if self.is_ordering or (self.local_risk.position and self.local_risk.position.status == "PENDING_BUY"):
            return

        # 3. 신규 진입 글로벌 가드레일 확인
        can_enter, block_reason = self.global_risk.can_enter_new_trade(now)
        if not can_enter:
            return

        # 4. 봉 단위 중복 진입 락 (15분봉 기준 동일 봉 재진입 방지)
        current_15m_str = now.strftime("%Y-%m-%d %H:") + f"{(now.minute // 15) * 15:02d}"
        if self.last_order_candle_time == current_15m_str:
            return

        # 5. 초 단위 쿨다운 (최소 30초 간격)
        if time.time() - self.last_order_timestamp < 30.0:
            return

        # 실시간 텔레메트리 틱 보고
        try:
            from sdk.telemetry_watchdog import system_watchdog
            system_watchdog.report_tick(config.HYNIX_CODE, price)
        except Exception:
            pass

        # 6. 전략 신호 산출
        signal = self.strategy.evaluate(self.feed, now)
        if signal.should_enter:
            # 7. AI 가디언 심사
            from sdk.ai_guardian_mesh import ai_guardian_mesh
            decision = ai_guardian_mesh.evaluate_entry(
                config.HYNIX_CODE,
                config.HYNIX_NAME,
                price,
                signal.strategy_tag,
                signal.reason
            )

            if decision.decision == "VETO":
                print(f">> [SK-BOT] 🛑 AI 가디언 거부권 발동 (매수 차단): {decision.reason}")
                return

            self.last_order_candle_time = current_15m_str
            self.last_order_timestamp = time.time()
            self.execute_buy(price, signal.reason)

    def execute_buy(self, price: float, reason: str):
        # 1. Just-In-Time 킬스위치 2차 방어선 확인 (주문 직전 0.001초 검증)
        if self.global_risk.is_halted():
            print(f">> [SK-BOT] 🛑 주문 직전 킬스위치 감지 -> 매수 주문 즉시 취소 ({self.global_risk.kill_switch_reason})")
            return

        is_halted_after_attempt = self.global_risk.register_order_attempt()
        if is_halted_after_attempt:
            print(f">> [SK-BOT] 🛑 일일 주문 시도 한도 초과 -> 주문 즉시 차단 ({self.global_risk.kill_switch_reason})")
            return

        from sdk.order_router import adaptive_order_router
        order_params = adaptive_order_router.get_order_params("BUY", price)
        if not order_params["can_order"]:
            print(f">> [SK-BOT] ⚠️ 주문 불가 세션: {order_params['reason']}")
            return

        self.is_ordering = True

        from events.event_bus import global_event_bus, OrderCommandEvent
        # 2. Transactional Outbox: 주문 발행 전 DB에 먼저 기록
        global_event_bus.publish_critical("orders.command", OrderCommandEvent(
            code=config.HYNIX_CODE,
            side="BUY",
            qty=1,
            price=price,
            strategy_name=self.strategy.strategy_name,
            reason=reason
        ))

        hoga_type = order_params["hoga_type"]
        order_price = order_params["order_price"]
        print(f"\n>> [SK-BOT] 🚀 1주 매수 주문 전송 ({order_params['session']}): {price:,.0f}원 (호가: {hoga_type}) - {reason}")
        
        from risk_engine.local_risk import Position
        self.local_risk.position = Position(
            code=config.HYNIX_CODE,
            stock_name=config.HYNIX_NAME,
            entry_price=price,
            qty=1,
            entry_time=datetime.now(),
            stop_loss_price=price * 0.991,
            highest_price=price,
            lowest_price=price,
            status="PENDING_BUY"
        )

        ret = self.adapter.send_order(
            "SK_BUY_1SHARE",
            "5000",  # 하이닉스봇 전용 화면번호 분리
            config.ACCOUNT_NO,
            1,
            config.HYNIX_CODE,
            1,
            order_price,
            hoga_type
        )
        if ret != 0:
            print(f">> [SK-BOT] ❌ 주문 전송 실패(ret={ret}) -> In-Flight 락 및 포지션 롤백 해제")
            self.is_ordering = False
            self.local_risk.close_position()

    def execute_sell(self, price: float, reason: str, pnl_pct: float, qty: int = 1):
        pos = self.local_risk.position
        sell_qty = qty or (pos.qty if pos else 1)
        pnl_won = (price - pos.entry_price) * sell_qty if pos else 0.0

        from sdk.order_router import adaptive_order_router
        order_params = adaptive_order_router.get_order_params("SELL", price)
        hoga_type = order_params["hoga_type"]
        order_price = order_params["order_price"]

        from events.event_bus import global_event_bus, TradeFilledEvent
        # Transactional Outbox: 체결 및 청산 이벤트 기록
        global_event_bus.publish_critical("trades.filled", TradeFilledEvent(
            code=config.HYNIX_CODE,
            side="SELL",
            qty=sell_qty,
            price=price,
            pnl_won=pnl_won,
            pnl_pct=pnl_pct,
            mfe_pct=((pos.highest_price - pos.entry_price) / pos.entry_price) * 100 if pos else 0.0,
            mae_pct=((pos.lowest_price - pos.entry_price) / pos.entry_price) * 100 if pos else 0.0,
            hold_time_seconds=int((datetime.now() - pos.entry_time).total_seconds()) if pos and pos.entry_time else 0,
            reason=reason
        ))

        print(f"\n>> [SK-BOT] 🛑 {sell_qty}주 전량 매도 주문 전송 ({order_params['session']}): {price:,.0f}원 (호가: {hoga_type}, 손익: {pnl_pct:+.2f}%, {pnl_won:,.0f}원) - {reason}")
        
        # 포지션 상태를 CLOSING으로 설정 (체결 통보 올 때까지 임의 소멸 금지)
        self.local_risk.mark_closing()
        self.is_ordering = True

        self.adapter.send_order(
            "SK_SELL",
            "5001",  # 하이닉스봇 전용 매도 화면번호
            config.ACCOUNT_NO,
            2,
            config.HYNIX_CODE,
            sell_qty,
            order_price,
            hoga_type
        )
        self.global_risk.register_trade_result(pnl_won)
        self.datalake.record_trade(
            self.strategy.strategy_name,
            config.HYNIX_CODE,
            config.HYNIX_NAME,
            "SELL",
            price,
            sell_qty,
            pnl_won,
            pnl_pct,
            ((pos.highest_price - pos.entry_price) / pos.entry_price) * 100 if pos else 0.0,
            ((pos.lowest_price - pos.entry_price) / pos.entry_price) * 100 if pos else 0.0,
            int((datetime.now() - pos.entry_time).total_seconds()) if pos and pos.entry_time else 0,
            reason
        )

    def on_chejan(self, gubun: str, order_no: str, code: str, status: str, qty: int, price: int):
        print(f">> [SK-BOT] 📝 체결 통보: 구분({gubun}), 주문번호({order_no}), 상태({status}), 수량({qty}), 체결가({price:,.0f})")
        self.is_ordering = False
        if "매수" in status or "1" in gubun:
            if "체결" in status or qty > 0:
                self.local_risk.on_chejan_fill("BUY", qty, fill_price=float(price))
        elif "매도" in status or "2" in gubun:
            if "체결" in status or qty > 0:
                self.local_risk.on_chejan_fill("SELL", qty, fill_price=float(price), remaining_qty=0)

    def run(self):
        print("=" * 80)
        print("⚡ [SK-BOT] SK Hynix Dual Strategy Worker Started")
        print("=" * 80)
        if self.adapter.login():
            acc_no = self.adapter.account_list[0] if self.adapter.account_list else config.ACCOUNT_NO
            self.adapter.sync_account_state_to_file(acc_no)
            
            # 실시간 계좌 기반 오버나잇 잔고 포지션 주입
            eval_data = self.adapter.get_account_evaluation(acc_no)
            self.local_risk.load_existing_position(eval_data)

            info = self.adapter.get_stock_info(config.HYNIX_CODE)
            self.current_price = info["price"]
            self.adapter.subscribe_realtime("5010", config.HYNIX_CODE, "10;15;228;20")
            print(f">> [SK-BOT] 실시간 시세 구독 완료: 현재가 {self.current_price:,.0f}원")
            self.app.exec_()

if __name__ == "__main__":
    worker = SKHynixWorker()
    worker.run()
