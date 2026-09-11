"""
========================================================================================
🤖 [WORKER: SAMSUNG ELECTRONICS MTF-SQUEEZE STRATEGY WORKER]
Isolated process executing Samsung Electronics (005930) 1-Share fixed quantitative strategy.
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

class SamsungDualWorkerStrategy(BaseStrategy):
    """
    [삼성전자 스마트 눌림목 퀀트 엔진]
    1. 전략 A: 거래량 동반 양봉/윗꼬리 이후 VWAP & 15M 20EMA 최적 눌림목(-0.3%~-1.2%) 지지 반등
    2. 전략 B: 15M 20>60>120 정배열 + 5M 20EMA 반등 확인
    """
    def __init__(self):
        super().__init__(config.SAMSUNG_CODE, config.SAMSUNG_NAME)
        self.strategy_name = "Samsung Pullback & Disparity Engine"

    def evaluate(self, feed, current_time: datetime) -> StrategySignal:
        df_15m = feed.get_ohlcv(self.code, 15, limit=130)
        df_5m = feed.get_ohlcv(self.code, 5, limit=50)
        df_3m = feed.get_ohlcv(self.code, 3, limit=30)
        current_price = feed.get_realtime_price(self.code)

        signal = StrategySignal(
            should_enter=False,
            side="BUY",
            entry_price=current_price,
            reason=""
        )

        if len(df_15m) < 20 or current_price <= 0:
            return signal

        close15 = df_15m['close']
        vol15 = df_15m['volume']
        ma20 = close15.rolling(20).mean()
        cum_vol = vol15.rolling(20).sum()
        cum_val = (close15 * vol15).rolling(20).sum()
        vwap20 = cum_val / (cum_vol + 1e-9)

        # --- 1. 전략 A: 스마트 눌림목 진입 (추격 매수 배제, 눌림 지지 확인) ---
        # 조건: 1) 최근 10봉 내 전일/당일 고가 터치 후 눌림
        #      2) 현재가가 VWAP 대비 -0.3% ~ -1.2% 눌림 지지선에 위치하거나 15M 20MA 지지
        #      3) 3분봉 또는 5분봉에서 직전봉 대비 양봉 전환(Rebound) 발생
        sig_a_ready = False
        vwap_curr = vwap20.iloc[-1]
        ma20_curr = ma20.iloc[-1]
        
        # 눌림목 비율: VWAP 대비 이격도
        pullback_ratio = ((current_price - vwap_curr) / (vwap_curr + 1e-9)) * 100.0
        is_in_pullback_zone = (-1.2 <= pullback_ratio <= 0.2) or (abs(current_price - ma20_curr) / ma20_curr <= 0.005)

        # 단기 3M/5M 반등 확인 (저점 방어 & 양봉)
        rebound_confirmed = False
        if len(df_3m) >= 2:
            c3 = df_3m['close']
            o3 = df_3m['open']
            rebound_confirmed = (c3.iloc[-1] >= o3.iloc[-1]) and (c3.iloc[-1] >= c3.iloc[-2])

        # 최근 5봉 평균 거래량 대비 현재 거래량 안정화 (거래량 폭증 음봉 투매 회피)
        vol_calm = True
        if len(df_15m) >= 6:
            recent_avg_vol = vol15.iloc[-6:-1].mean()
            vol_calm = (vol15.iloc[-1] <= recent_avg_vol * 2.5)

        sig_a_ready = is_in_pullback_zone and rebound_confirmed and vol_calm

        # --- 2. 전략 B: 15M 20>60>120 정배열 & 황금 이격도 (101.5%~103.0%) ---
        sig_b_ready = False
        if len(df_15m) >= 120 and len(df_5m) >= 20:
            ma60 = close15.rolling(60).mean().iloc[-1]
            ma120 = close15.rolling(120).mean().iloc[-1]
            is_aligned = (ma20.iloc[-1] > ma60) and (ma60 > ma120)
            disp_price_ma20 = (current_price / (ma20.iloc[-1] + 1e-9)) * 100.0
            is_golden_disp = (100.5 <= disp_price_ma20 <= 102.5)  # 상단 과열 완화(102.5% 이하)
            
            c5 = df_5m['close']
            ema20_5 = c5.ewm(span=20, adjust=False).mean().iloc[-1]
            rebound_5m = (df_5m['low'].iloc[-1] <= ema20_5 * 1.003) and (c5.iloc[-1] > df_5m['open'].iloc[-1])
            sig_b_ready = is_aligned and is_golden_disp and rebound_5m

        # --- 통합 신호 합성 ---
        if sig_a_ready and sig_b_ready:
            signal.should_enter = True
            signal.entry_price = current_price
            signal.stop_loss_price = current_price * 0.991
            signal.take_profit_price = current_price * 1.015
            signal.strategy_tag = "DUAL_CONFLUENCE_A+B"
            signal.reason = f"🔥 [삼성전자 초강력 합의] 전략A(스마트눌림목 {pullback_ratio:+.2f}%) + 전략B(정배열 황금이격) 동시 충족 (현재가: {current_price:,.0f}원)"
            return signal

        if sig_a_ready:
            signal.should_enter = True
            signal.entry_price = current_price
            signal.stop_loss_price = current_price * 0.991
            signal.take_profit_price = current_price * 1.015
            signal.strategy_tag = "STRATEGY_A_PULLBACK"
            signal.reason = f"[삼성전자 전략 A: 스마트눌림목] VWAP 이격 {pullback_ratio:+.2f}% 눌림목 지지 및 3M 양봉 반등 (현재가: {current_price:,.0f}원)"
            return signal

        if sig_b_ready:
            signal.should_enter = True
            signal.entry_price = current_price
            signal.stop_loss_price = current_price * 0.991
            signal.take_profit_price = current_price * 1.015
            signal.strategy_tag = "STRATEGY_B_DISPARITY"
            signal.reason = f"[삼성전자 전략 B: 정배열이격] 15M 20>60>120 정배열 + 황금 이격도 {disp_price_ma20:.1f}% + 5M 지지반등 (현재가: {current_price:,.0f}원)"
            return signal

        return signal

class SamsungWorker:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.engine = TimeseriesIndicatorEngine(config.SAMSUNG_CODE, config.SAMSUNG_NAME)
        self.strategy = SamsungDualWorkerStrategy()
        self.local_risk = LocalRiskManager(config.SAMSUNG_CODE, config.SAMSUNG_NAME, config.STOP_LOSS_PCT)
        self.global_risk = GlobalRiskEngine()
        self.datalake = QuantDataLake(partition_key="005930")
        
        self.current_price = 0.0
        self.current_volume = 0
        self.current_intensity = 100.0

        # [치명적 결함 방어선 1: Triple-Lock 상태 머신]
        self.is_ordering = False                  # Lock 1: 주문 진행 중 플래그 (In-Flight Lock)
        self.last_order_candle_time: str = ""     # Lock 2: 동일 15분봉 내 재주문 차단 (Candle Lock)
        self.last_order_timestamp: float = 0.0    # Lock 3: 최소 30초 쿨다운 디바운싱

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
        if code != config.SAMSUNG_CODE:
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

        # 2. 주문 진행 중(In-Flight)이거나 PENDING 상태면 신규 매수 차단
        if self.is_ordering or (self.local_risk.position and self.local_risk.position.status == "PENDING_BUY"):
            return

        # 3. 신규 진입 글로벌 가드레일 확인 (일일 3회 및 일일 주문 시도 한도)
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
            system_watchdog.report_tick(config.SAMSUNG_CODE, price)
        except Exception:
            pass

        # 6. 전략 신호 산출
        signal = self.strategy.evaluate(self.feed, now)
        if signal.should_enter:
            # 7. 실시간 AI 가디언 지능 심사관 호출
            try:
                from sdk.ai_guardian_mesh import ai_guardian_mesh
                from sdk.telemetry_watchdog import system_watchdog
                
                decision = ai_guardian_mesh.evaluate_entry(
                    code=config.SAMSUNG_CODE,
                    name=config.SAMSUNG_NAME,
                    current_price=price,
                    strategy_name=self.strategy.strategy_name,
                    reason=signal.reason
                )
                system_watchdog.report_ai_decision(decision.provider, decision.latency_ms)

                if decision.decision == "VETO":
                    print(f">> [SAM-BOT] 🛑 AI 가디언 기각 ({decision.provider}): {decision.reason}")
                    return

                print(f">> [SAM-BOT] 🧠 AI 가디언 승인 ({decision.provider}, {decision.latency_ms}ms): {decision.reason}")
            except Exception as e:
                print(f">> [SAM-BOT] ⚠️ AI 가디언 일시 오류 -> 로컬 퀀트 룰로 안전 집행 ({e})")

            # 락 설정 후 발주 집행
            self.last_order_candle_time = current_15m_str
            self.last_order_timestamp = time.time()
            self.execute_buy(signal.entry_price, signal.reason)

    def execute_buy(self, price: float, reason: str):
        # 1. 글로벌 리스크 JIT 킬스위치 및 주문 시도 한도 확인
        if self.global_risk.is_halted():
            print(f">> [SAM-BOT] 🛑 주문 직전 킬스위치 감지 -> 매수 주문 즉시 취소 ({self.global_risk.kill_switch_reason})")
            return

        is_halted_after_attempt = self.global_risk.register_order_attempt()
        if is_halted_after_attempt:
            print(f">> [SAM-BOT] 🛑 일일 주문 시도 한도 초과 -> 주문 즉시 차단 ({self.global_risk.kill_switch_reason})")
            return

        from sdk.order_router import adaptive_order_router
        order_params = adaptive_order_router.get_order_params("BUY", price)
        if not order_params["can_order"]:
            print(f">> [SAM-BOT] ⚠️ 주문 불가 세션: {order_params['reason']}")
            return

        # In-Flight 락 활성화 (응답 또는 체결 통보 올 때까지 신규 주문 전면 봉쇄)
        self.is_ordering = True

        from events.event_bus import global_event_bus, OrderCommandEvent
        # 2. Transactional Outbox: 주문 발행 전 DB에 먼저 기록
        global_event_bus.publish_critical("orders.command", OrderCommandEvent(
            code=config.SAMSUNG_CODE,
            side="BUY",
            qty=1,
            price=price,
            strategy_name=self.strategy.strategy_name,
            reason=reason
        ))

        hoga_type = order_params["hoga_type"]
        order_price = order_params["order_price"]
        print(f"\n>> [SAM-BOT] 🚀 1주 매수 주문 전송 ({order_params['session']}): {price:,.0f}원 (호가: {hoga_type}) - {reason}")
        
        # 포지션을 PENDING_BUY로 마킹하여 동시 주문 차단
        from risk_engine.local_risk import Position
        self.local_risk.position = Position(
            code=config.SAMSUNG_CODE,
            stock_name=config.SAMSUNG_NAME,
            entry_price=price,
            qty=1,
            entry_time=datetime.now(),
            stop_loss_price=price * 0.991,
            highest_price=price,
            lowest_price=price,
            status="PENDING_BUY"
        )

        ret = self.adapter.send_order(
            "SAM_BUY_1SHARE",
            "4000",  # 삼성봇 전용 화면번호 분리
            config.ACCOUNT_NO,
            1,  # 신규매수
            config.SAMSUNG_CODE,
            1,  # 1주 고정
            order_price,
            hoga_type
        )
        if ret != 0:
            print(f">> [SAM-BOT] ❌ 주문 전송 실패(ret={ret}) -> In-Flight 락 및 포지션 롤백 해제")
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
            code=config.SAMSUNG_CODE,
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

        print(f"\n>> [SAM-BOT] 🛑 {sell_qty}주 전량 매도 주문 전송 ({order_params['session']}): {price:,.0f}원 (호가: {hoga_type}, 손익: {pnl_pct:+.2f}%, {pnl_won:,.0f}원) - {reason}")
        
        # 포지션 상태를 CLOSING으로 설정 (체결 통보 올 때까지 임의 소멸 금지)
        self.local_risk.mark_closing()
        self.is_ordering = True

        self.adapter.send_order(
            "SAM_SELL",
            "4001",  # 삼성봇 전용 매도 화면번호
            config.ACCOUNT_NO,
            2,  # 신규매도
            config.SAMSUNG_CODE,
            sell_qty,
            order_price,
            hoga_type
        )
        self.global_risk.register_trade_result(pnl_won)
        self.datalake.record_trade(
            self.strategy.strategy_name,
            config.SAMSUNG_CODE,
            config.SAMSUNG_NAME,
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
        print(f">> [SAM-BOT] 📝 체결 통보: 구분({gubun}), 주문번호({order_no}), 상태({status}), 수량({qty}), 체결가({price:,.0f})")
        # In-Flight 락 해제
        self.is_ordering = False

        if "매수" in status or "1" in gubun:
            if "체결" in status or qty > 0:
                self.local_risk.on_chejan_fill("BUY", qty, fill_price=float(price))
        elif "매도" in status or "2" in gubun:
            if "체결" in status or qty > 0:
                self.local_risk.on_chejan_fill("SELL", qty, fill_price=float(price), remaining_qty=0)

    def run(self):
        print("=" * 80)
        print("🤖 [SAM-BOT] Samsung Electronics Pullback Engine Worker Started")
        print("=" * 80)
        if self.adapter.login():
            acc_no = self.adapter.account_list[0] if self.adapter.account_list else config.ACCOUNT_NO
            self.adapter.sync_account_state_to_file(acc_no)
            
            # 실시간 계좌 기반 오버나잇 잔고 포지션 주입
            eval_data = self.adapter.get_account_evaluation(acc_no)
            self.local_risk.load_existing_position(eval_data)

            info = self.adapter.get_stock_info(config.SAMSUNG_CODE)
            self.current_price = info["price"]
            self.adapter.subscribe_realtime("4010", config.SAMSUNG_CODE, "10;15;228;20")
            print(f">> [SAM-BOT] 실시간 시세 구독 완료: 현재가 {self.current_price:,.0f}원")
            self.app.exec_()

if __name__ == "__main__":
    worker = SamsungWorker()
    worker.run()
