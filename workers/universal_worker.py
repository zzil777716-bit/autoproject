"""
========================================================================================
🚀 [WORKER: UNIVERSAL QUANT TRADING BOT ENGINE]
Dynamic Universal Multi-Stock Worker:
  1. Instantiates any strategy dynamically from StrategyRegistry
  2. Runs 100% Real Kiwoom Open API+ WebSocket & TR
  3. Integrated with 4-Layer AI Guardian Mesh (Gemini Flash -> Claude -> Local)
  4. Integrated with Dual Local Risk (1-Share, -0.90% SL, +1.50% TP1, +2.80% TP2 Trailing)
  5. SQLite WAL Trade Journal (research/trade_journal_{code}.sqlite & master)
  6. SRE Telemetry Watchdog & Heartbeat reporting
========================================================================================
"""

import os
import sys
import time
import argparse
from datetime import datetime
from typing import Dict, Any, Optional

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import config
from sdk.base_strategy import DualStrategyEngine, BaseStrategy
from sdk.strategy_registry import StrategyRegistry
from sdk.data_feeds import MultiTimeframeFeed
from sdk.ai_guardian_mesh import ai_guardian_mesh
from sdk.telemetry_watchdog import system_watchdog
from risk_engine.local_risk import LocalRiskManager
from risk_engine.global_risk import GlobalRiskEngine
from storage.data_lake import QuantDataLake
from adapters.kiwoom_adapter import KiwoomAdapter

class UniversalTradingWorker:
    def __init__(self, code: str, stock_name: str, strategy_name: str = "DUAL"):
        self.code = code
        self.stock_name = stock_name
        self.strategy_name = strategy_name

        self.data_feed = MultiTimeframeFeed(code=self.code)
        self.risk_guard = LocalRiskManager(code=self.code, stock_name=self.stock_name)
        self.global_risk = GlobalRiskEngine()
        self.journal_db = QuantDataLake(base_dir=config.BASE_DIR, partition_key=self.code)

        # 전략 인스턴스 초기화
        if strategy_name.upper() == "DUAL":
            self.strategy = DualStrategyEngine(code=self.code, stock_name=self.stock_name)
        else:
            self.strategy = StrategyRegistry.create_strategy(strategy_name, code=self.code, stock_name=self.stock_name)
            if not self.strategy:
                print(f">> [WARN] 등록되지 않은 전략 '{strategy_name}' -> DUAL 모드로 기본 전환합니다.")
                self.strategy = DualStrategyEngine(code=self.code, stock_name=self.stock_name)

        self.adapter: Optional[KiwoomAdapter] = None
        self.is_running = False

    def start(self):
        """워커 시작 및 실시간 루프 진입"""
        print("=" * 80)
        print(f">> 🚀 [Universal Worker] {self.stock_name} ({self.code}) 퀀트 봇 가동")
        print(f">> 전략 모델 : {self.strategy.strategy_name}")
        print(f">> 주문 규격 : 1주 고정 | 손절 -0.90% | 익절1 +1.50% | 익절2 +2.80%(트레일링)")
        print(f">> AI 검증   : Gemini Flash 4단 가디언 연동")
        print("=" * 80)

        self.is_running = True
        system_watchdog.register_bot(self.code, self.stock_name)

        # 1개년 과거 데이터 로드
        self.data_feed.load_initial_history()

        # 키움 어댑터 연결
        self.adapter = KiwoomAdapter()
        if self.adapter.login():
            acc = self.adapter.account_list[0] if self.adapter.account_list else config.ACCOUNT_NO
            self.adapter.sync_account_state_to_file(acc)
            self.adapter.subscribe_realtime("1001", self.code, "10;11;12;13;15;20")
            print(f">> [Universal Worker] ✅ 키움 실시간 시세 구독 완료: {self.stock_name}({self.code})")

    def on_tick(self, price: float, volume: int, current_time_str: str):
        """실시간 틱 처리 및 전략/리스크 평가"""
        if not self.is_running:
            return

        system_watchdog.report_tick(self.code, price)
        self.data_feed.update_tick(price, volume, current_time_str)

        # 1. 포지션 보유 중인 경우: 손익 및 트레일링 스탑 평가
        if self.risk_guard.has_active_position():
            exit_signal = self.risk_guard.evaluate_exit(price)
            if exit_signal.should_exit:
                self.execute_sell(exit_signal)
            return

        # 2. 미보유 상태: 글로벌 킬스위치 확인
        if self.global_risk.is_blackout_active() or self.global_risk.is_kill_switch_tripped():
            return

        # 3. 전략 진입 신호 평가
        signal = self.strategy.evaluate(self.data_feed.get_timeframe_dfs(), current_time_str)
        if signal.should_enter:
            # 4. AI 가디언 심사
            decision = ai_guardian_mesh.evaluate_entry(
                code=self.code,
                name=self.stock_name,
                strategy_tag=signal.strategy_tag,
                current_price=price,
                indicators={"reason": signal.reason}
            )

            if decision.decision == "VETO":
                print(f">> [Universal Worker] 🛑 AI 가디언 거부권 발동 (매수 차단): {decision.reason}")
                return

            self.execute_buy(signal)

    def execute_buy(self, signal):
        """1주 매수 주문 실행"""
        price = signal.entry_price
        print(f"\n>> 🎯 [매수 신호 발생] {self.stock_name} @ {price:,.0f}원 ({signal.strategy_tag})")
        if self.adapter:
            acc = self.adapter.account_list[0] if self.adapter.account_list else config.ACCOUNT_NO
            self.adapter.send_order("universal_buy", "0101", acc, 1, self.code, 1, int(price), "03")

        self.risk_guard.record_entry(price=price, qty=1, strategy_name=signal.strategy_tag)
        self.journal_db.record_entry(
            stock_name=self.stock_name,
            side="BUY",
            price=price,
            qty=1,
            strategy_name=signal.strategy_tag,
            reason=signal.reason
        )

    def execute_sell(self, exit_signal):
        """매도 주문 실행"""
        price = exit_signal.exit_price
        print(f"\n>> 🔔 [매도 신호 발생] {self.stock_name} @ {price:,.0f}원 ({exit_signal.reason})")
        if self.adapter:
            acc = self.adapter.account_list[0] if self.adapter.account_list else config.ACCOUNT_NO
            self.adapter.send_order("universal_sell", "0101", acc, 2, self.code, 1, 0, "03")

        pnl_won, pnl_pct = self.risk_guard.record_exit(price=price)
        self.journal_db.record_exit(
            stock_name=self.stock_name,
            side="SELL",
            price=price,
            qty=1,
            pnl_won=pnl_won,
            pnl_pct=pnl_pct,
            reason=exit_signal.reason
        )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Antigravity Universal Quant Bot Engine")
    parser.add_argument("--code", type=str, default="005930", help="종목코드 (예: 005930, 000660)")
    parser.add_argument("--name", type=str, default="삼성전자", help="종목명")
    parser.add_argument("--strategy", type=str, default="DUAL", help="전략명 (DUAL, STRATEGY_A, STRATEGY_B)")
    args = parser.parse_args()

    worker = UniversalTradingWorker(code=args.code, stock_name=args.name, strategy_name=args.strategy)
    worker.start()
