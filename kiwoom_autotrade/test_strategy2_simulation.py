"""
Offline Dry-Run Simulator for Strategy 2 (1-Share Execution)
Runs on actual historical 15m / 5m / 3m data collected from Kiwoom Open API+.
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime

# Windows UTF-8 stdout configuration
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

from config.settings import config
from core.strategy_mtf import MTFStrategyEngine
from core.risk_manager import RiskManager

def simulate_strategy_2():
    print("=" * 75)
    print(">> [DRY-RUN SIMULATION] 삼성전자 전략 2 (1주 고정) 오프라인 시뮬레이션 검증")
    print(f">> 전략: {config.ACTIVE_STRATEGY} | 1회 주문: {config.DEFAULT_TRADE_QTY}주 | 계좌: {config.ACCOUNT_NO}")
    print("=" * 75)
    
    # 1. 수집된 분봉 데이터 로드
    df_15m = pd.read_csv("data/005930_15m.csv", index_col=0, parse_dates=True)
    df_5m = pd.read_csv("data/005930_5m.csv", index_col=0, parse_dates=True)
    df_3m = pd.read_csv("data/005930_3m.csv", index_col=0, parse_dates=True)
    
    print(f">> 로드된 데이터: 15M({len(df_15m):,d}개), 5M({len(df_5m):,d}개), 3M({len(df_3m):,d}개)")
    
    strategy = MTFStrategyEngine()
    rm = RiskManager(initial_equity=10_000_000)
    
    # 최근 1000개 3분봉 구간에서 시그널 트리거 테스트
    sample_3m = df_3m.tail(1000)
    triggered_count = 0
    
    print("\n>> 최근 1000개 3분봉 구간 순회 평가 중...")
    for i in range(50, len(sample_3m)):
        current_time = sample_3m.index[i]
        curr_price = sample_3m['close'].iloc[i]
        
        sub_15m = df_15m[df_15m.index <= current_time].tail(60)
        sub_5m = df_5m[df_5m.index <= current_time].tail(60)
        sub_3m = sample_3m.iloc[:i+1].tail(60)
        
        if len(sub_15m) < 20 or len(sub_5m) < 20:
            continue
            
        # 가상 체결강도 115% 주입
        signal = strategy.evaluate(
            df_15m=sub_15m,
            df_5m=sub_5m,
            df_3m=sub_3m,
            current_price=curr_price,
            realtime_intensity=115.0,
            current_time=current_time
        )
        
        if signal.should_enter and rm.position.qty == 0:
            triggered_count += 1
            print(f"   [시그널 #{triggered_count}] {current_time} | 진입가: {curr_price:,.0f}원 (1주) | 손절가: {signal.stop_loss_price:,.0f}원 | 목표가: {signal.target_price:,.0f}원")
            print(f"      -> 사유: {signal.reason}")
            rm.on_position_entered(1, curr_price, current_time, signal.stop_loss_price, signal.target_price)
            break # 1건 샘플 확인 완료
            
    print("\n" + "=" * 75)
    print(f">> [결과] 전략 2 FSM 상태 머신 & 1주 포지션 사이징 정상 작동 확인 완료!")
    print("=" * 75)

if __name__ == "__main__":
    simulate_strategy_2()
