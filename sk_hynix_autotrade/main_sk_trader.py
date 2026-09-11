"""
========================================================================================
🚀 [SK-BOT v1.2] SK하이닉스(000660) 키움증권 1주 모의투자 다중 주기 자동매매 엔진
Strategy: [부자회사원 7개월 검증 삼중 스크린 엔벨로프/EMA 주도주 눌림목 매매 전략]
Includes Daily Top 3 Market Themes & 9 Leading Stocks Excel/Google Sheets Auto-Sync (G:\내 드라이브\Antigravity\테마).
========================================================================================
"""

import sys
import os
import time

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass
from datetime import datetime, time as dtime
from typing import Optional, Dict, Any
import pandas as pd
import numpy as np

# PyQt5 GUI Framework
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# Internal Modules
from config.settings import config
from core.kiwoom_api import KiwoomAPI
from core.candle_engine import CandleEngine
from core.strategy_hynix_pullback import SKHynixPullbackStrategyEngine, StrategySignal
from core.risk_manager import RiskManager, RiskAction
from core.telegram_notifier import TelegramNotifier
from core.research_logger import ResearchLogger
from core.theme_scanner import ThemeScanner
from data.timeseries_db import TimeSeriesDB

class SKHynixTradingSystem:
    def __init__(self):
        print("=" * 80)
        print(">> [System] SK하이닉스(000660) [부자회사원 삼중스크린 엔벨로프 눌림목] 1주 모의투자 엔진 가동...")
        print(f">> 계좌번호: {config.ACCOUNT_NO} | 1회 주문: {config.DEFAULT_TRADE_QTY}주 고정 | 일일 한도: {config.MAX_DAILY_TRADES}회")
        print("=" * 80)
        
        self.app = QApplication(sys.argv)
        
        # 핵심 컴포넌트
        self.candle_engine = CandleEngine(config.STOCK_CODE)
        self.strategy_engine = SKHynixPullbackStrategyEngine()
        self.risk_manager = RiskManager(initial_equity=10_000_000)
        self.telegram = TelegramNotifier()
        self.db = TimeSeriesDB()
        self.research_logger = ResearchLogger(config.STOCK_CODE, config.STOCK_NAME)
        
        # 실시간 계좌 및 시세
        self.deposit: int = 0
        self.orderable_cash: int = 0
        self.total_eval: int = 0
        self.current_price: float = 0.0
        self.price_diff_rate: float = 0.0
        self.realtime_intensity: float = 100.0
        
        self.last_dashboard_time: float = 0.0
        self.last_account_sync_time: float = 0.0
        self.last_signal: Optional[StrategySignal] = None
        
        try:
            self.api = KiwoomAPI(
                on_tick_callback=self._on_realtime_tick,
                on_chejan_callback=self._on_chejan_update
            )
        except Exception as e:
            print(f">> [Warning] Kiwoom QAxWidget 초기화 불가: {e}")
            self.api = None

    def start(self):
        if self.api:
            # 1. 로그인
            success = self.api.login()
            if not success:
                print(">> [Error] 로그인 실패")
                sys.exit(1)
                
            # 2. 계좌 설정
            if not config.ACCOUNT_NO and self.api.account_list:
                config.ACCOUNT_NO = self.api.account_list[0]
            print(f">> [System] 거래 계좌: {config.ACCOUNT_NO} (모의투자)")

            # 3. 예수금 및 잔고 동기화
            self._sync_account_info()

            # 4. SK하이닉스 현재가 조회
            self._sync_stock_info()

            # 5. 영업일 기준 당일 HTS 4종 주도 데이터(0659, 0198, 0184) 수집 및 바탕화면 캘린더 생성/구글드라이브 동기화
            try:
                from core.calendar_generator import DesktopCalendarGenerator
                cal_gen = DesktopCalendarGenerator()
                cal_gen.update_and_build(self.api)
            except Exception as e:
                print(f">> [Warning] 캘린더 생성 중 오류: {e}")

            # 6. 실시간 시세 등록
            self.api.set_real_reg(
                config.SCREEN_NO_REAL,
                config.STOCK_CODE,
                "10;11;12;15;20;228;27;28",
                "0"
            )

        # 7. 과거 분봉 프리로드
        df_history = self.db.load_recent_bars(config.STOCK_CODE, limit=500)
        if not df_history.empty:
            self.candle_engine.preload_historical_bars(df_history)
            print(f">> [System] ✅ SK하이닉스 과거 분봉 {len(df_history)}개 프리로드 완료")

        # 8. 1초 주기 타이머
        self.timer = QTimer()
        self.timer.timeout.connect(self._on_system_heartbeat)
        self.timer.start(1000)
        
        print("\n>> [System] 🚀 SK하이닉스 부자회사원 눌림목 자동매매 엔진이 정상 가동되었습니다!")
        sys.exit(self.app.exec_())

    def _sync_account_info(self):
        if not self.api:
            return
        try:
            dep_data = self.api.get_deposit(config.ACCOUNT_NO)
            if dep_data:
                self.deposit = dep_data.get('deposit', 0)
                self.orderable_cash = dep_data.get('orderable', 0)
                self.risk_manager.equity = float(self.deposit)
                self.risk_manager.daily_start_equity = float(self.deposit)
                
            bal_data = self.api.get_account_balance(config.ACCOUNT_NO)
            if bal_data:
                self.total_eval = bal_data.get('total_eval', self.deposit)
                
            print(f">> [System] 💰 계좌 동기화: 예수금 {self.deposit:,}원 | 주문가능 {self.orderable_cash:,}원 | 총평가 {self.total_eval:,}원")
        except Exception as e:
            pass

    def _sync_stock_info(self):
        if not self.api:
            return
        try:
            stock_data = self.api.get_stock_info(config.STOCK_CODE)
            if stock_data:
                self.current_price = float(stock_data.get('price', 0.0))
                self.price_diff_rate = float(stock_data.get('rate', 0.0))
                print(f">> [System] 📊 SK하이닉스 시세 동기화: {self.current_price:,.0f}원 ({self.price_diff_rate:+.2f}%)")
        except Exception as e:
            pass

    def _on_realtime_tick(self, code: str, price: float, volume: int, intensity: float, timestr: str):
        if code != config.STOCK_CODE:
            return
            
        now = datetime.now()
        self.current_price = price
        self.realtime_intensity = intensity
        
        new_bar_closed = self.candle_engine.on_tick(now, price, volume)
        if new_bar_closed:
            df_1m = self.candle_engine.get_df_1m()
            if not df_1m.empty:
                self.db.save_bars(config.STOCK_CODE, df_1m.tail(1))

        if self.risk_manager.position.qty > 0:
            risk_action = self.risk_manager.check_position_risk(price, now)
            self._handle_risk_action(risk_action)

    def _on_system_heartbeat(self):
        now = datetime.now()
        
        df_15m = self.candle_engine.get_15m_df()
        df_5m = self.candle_engine.get_5m_df()
        df_3m = self.candle_engine.get_3m_df()

        can_trade, block_reason = self.risk_manager.can_trade(now)

        if self.current_price > 0 and len(df_15m) >= 20:
            signal = self.strategy_engine.evaluate(
                df_15m=df_15m,
                df_5m=df_5m,
                df_3m=df_3m,
                current_price=self.current_price,
                realtime_intensity=self.realtime_intensity,
                current_time=now
            )
            self.last_signal = signal

            if time.time() - self.last_dashboard_time >= 5.0:
                self.research_logger.log_market_snapshot(
                    now=now,
                    price=self.current_price,
                    diff_rate=self.price_diff_rate,
                    intensity=self.realtime_intensity,
                    volume=int(df_3m['volume'].iloc[-1]) if not df_3m.empty else 0,
                    state_15m=signal.state_15m,
                    state_5m=signal.state_5m,
                    state_3m=signal.state_3m,
                    indicators=signal.metrics or {}
                )
                
                if "5M_WAVE" in signal.state_5m and not signal.should_enter:
                    self.research_logger.log_near_miss(
                        now=now,
                        price=self.current_price,
                        strategy_name=signal.strategy_name,
                        stage=signal.state_3m,
                        reason=signal.reason,
                        metrics=signal.metrics or {}
                    )

            if can_trade and self.risk_manager.position.qty == 0 and signal.should_enter:
                self._execute_entry(signal, now)

        if time.time() - self.last_dashboard_time >= 5.0:
            self._render_tui_dashboard(now, can_trade, block_reason)
            self.last_dashboard_time = time.time()

        if time.time() - self.last_account_sync_time >= 60.0:
            self._sync_account_info()
            self.last_account_sync_time = time.time()

    def _execute_entry(self, signal: StrategySignal, now: datetime):
        trade_id = f"SK-{now.strftime('%Y%m%d%H%M%S')}"
        order_qty = self.risk_manager.calculate_order_qty(self.current_price)
        print(f"\n🚀 [SK HYNIX ENTRY] ID:{trade_id} | {signal.reason} | 수량: {order_qty}주")

        if self.api:
            try:
                from sdk.order_router import adaptive_order_router
                order_params = adaptive_order_router.get_order_params("BUY", self.current_price, now)
                order_price = order_params["order_price"]
                hoga_type = order_params["hoga_type"]
                print(f">> [KiwoomAPI] 🎯 {order_params['reason']}")
            except Exception:
                order_price, hoga_type = 0, "03"

            self.api.send_order(
                rq_name="HYNIX_ENVELOPE_ENTRY",
                screen_no=config.SCREEN_NO_ORDER,
                acc_no=config.ACCOUNT_NO,
                order_type=1,
                code=config.STOCK_CODE,
                qty=order_qty,
                price=order_price,
                hoga_type=hoga_type
            )
        
        self.risk_manager.on_position_entered(
            qty=order_qty,
            price=self.current_price,
            current_time=now,
            stop_price=signal.stop_loss_price,
            target_price=signal.target_price,
            trade_id=trade_id
        )
        
        self.research_logger.log_trade_entry(
            trade_id=trade_id,
            strategy_name=signal.strategy_name,
            qty=order_qty,
            entry_time=now,
            entry_price=self.current_price,
            reason=signal.reason,
            indicators=signal.metrics or {}
        )
        
        self.telegram.notify_entry(
            code=config.STOCK_CODE,
            price=self.current_price,
            qty=order_qty,
            reason=signal.reason,
            metrics=signal.metrics or {}
        )

    def _handle_risk_action(self, action: RiskAction):
        if action.action_type == "NONE":
            return

        now = datetime.now()
        pos = self.risk_manager.position
        
        if action.action_type in ["FULL_SELL", "STOP_LOSS"]:
            print(f"\n🔴 [SK HYNIX EXIT] 사유: {action.reason} | 수량: {action.qty}주")
            if self.api:
                self.api.send_order(
                    rq_name="HYNIX_ENVELOPE_EXIT",
                    screen_no=config.SCREEN_NO_ORDER,
                    acc_no=config.ACCOUNT_NO,
                    order_type=2,
                    code=config.STOCK_CODE,
                    qty=action.qty,
                    price=0,
                    hoga_type="03"
                )
                
            realized_pnl = (action.price - pos.avg_price) * action.qty
            pnl_pct = ((action.price - pos.avg_price) / pos.avg_price) * 100.0
            
            self.research_logger.log_trade_exit(
                trade_id=action.trade_id or pos.trade_id,
                exit_time=now,
                exit_price=action.price,
                exit_reason=action.reason,
                holding_seconds=action.holding_seconds,
                pnl_won=realized_pnl,
                pnl_pct=pnl_pct,
                mfe_pct=action.mfe_pct,
                mae_pct=action.mae_pct
            )
            
            if action.action_type == "STOP_LOSS":
                self.telegram.notify_stop_loss(
                    code=config.STOCK_CODE,
                    loss_won=int(realized_pnl),
                    loss_pct=pnl_pct,
                    cooldown_min=config.COOLDOWN_MINUTES_CONSECUTIVE if self.risk_manager.consecutive_losses >= 2 else config.COOLDOWN_MINUTES_DEFAULT
                )
            else:
                self.telegram.notify_trailing_exit(
                    code=config.STOCK_CODE,
                    exit_price=action.price,
                    total_pnl_won=int(realized_pnl),
                    total_pnl_pct=pnl_pct
                )
                
            self.risk_manager.on_trade_closed(realized_pnl)
            self._sync_account_info()

    def _on_chejan_update(self, gubun: str, order_no: str, code: str, order_status: str, qty: int, price: int):
        pass

    def _render_tui_dashboard(self, now: datetime, can_trade: bool, block_reason: str):
        pos = self.risk_manager.position
        pnl_pct = ((self.current_price - pos.avg_price) / pos.avg_price * 100) if pos.qty > 0 else 0.0
        pnl_won = int((self.current_price - pos.avg_price) * pos.qty) if pos.qty > 0 else 0
        
        state_15m = self.last_signal.state_15m if self.last_signal else "INITIALIZING"
        state_5m = self.last_signal.state_5m if self.last_signal else "INITIALIZING"
        state_3m = self.last_signal.state_3m if self.last_signal else "INITIALIZING"
        
        tui = f"""
┌─ [SK-BOT v1.2] SK하이닉스(000660) [부자회사원 삼중스크린 엔벨로프 눌림목] 1주 모의투자 모드 ─────┐
│ 현재시간: {now.strftime('%Y-%m-%d %H:%M:%S')} │ SK하이닉스: {self.current_price:>9,.0f}원 ({self.price_diff_rate:>+6.2f}%) │ 체결강도: {self.realtime_intensity:>5.1f}% │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ [1] 계좌 자산 현황 (모의투자: {config.ACCOUNT_NO})                                                     │
│  • 계좌 예수금 : {self.deposit:>13,d}원  │ 주문가능금액 : {self.orderable_cash:>13,d}원  │ 총평가자산 : {self.total_eval:>13,d}원 │
│  • 1회 주문수량: {config.DEFAULT_TRADE_QTY:>4}주 고정        │ 당일 매매횟수: {self.risk_manager.daily_trades_count:>2}/{config.MAX_DAILY_TRADES}회        │ 당일실현손익: {self.risk_manager.daily_pnl:>+11,.0f}원 │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ [2] 삼중 스크린 상태 (Triple-Screen Pullback Status)                                                   │
│  • 15분봉 (Tide)   : {state_15m:<55} │
│  • 05분봉 (Wave)   : {state_5m:<55} │
│  • 03분봉 (Ripple) : {state_3m:<55} │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ [3] 실시간 포지션 & 퀀트 연구 (MFE / MAE)                                                             │
│  • 보유수량: {pos.qty:>4}주 | 평균단가: {pos.avg_price:>9,.0f}원 | MFE: +{pos.mfe_pct:>5.2f}% | MAE: {pos.mae_pct:>5.2f}% │
│  • 평가손익: {pnl_won:>+9,d}원 ({pnl_pct:>+6.2f}%) │ 매매가부: {'[매매 가능 🟢]' if can_trade else '[매매 제한 ⛔ ' + block_reason + ']'}
│  • 클라우드 백업: G:\\내 드라이브\\Antigravity\\테마\\테마_분석_*.xlsx (3대 테마 & 9대 대장주 자동 동기화 중)│
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘"""
        print(tui)

if __name__ == "__main__":
    bot = SKHynixTradingSystem()
    bot.start()
