"""
========================================================================================
📊 [DATA COLLECTOR] SK하이닉스(000660) 3분봉 / 5분봉 / 15분봉 과거 데이터 전수 수집기
수집 기간: 2025년 8월 1일 ~ 현재
저장 형식: SQLite DB (data/hynix_market_data.sqlite) + CSV (data/000660_*.csv) + Parquet
========================================================================================
"""

import sys
import os
import time
from datetime import datetime
import pandas as pd

# Windows UTF-8 stdout configuration
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

from PyQt5.QtWidgets import QApplication
from config.settings import config
from core.kiwoom_api import KiwoomAPI
from data.timeseries_db import TimeSeriesDB

def main():
    print("=" * 75)
    print(">> [SK-BOT Data Collector] SK하이닉스(000660) 멀티 분봉 데이터 수집 시작")
    print(">> 수집 타임프레임 : 3분봉, 5분봉, 15분봉")
    print(">> 수집 목표 기간   : 2025년 8월 1일 ~ 현재")
    print("=" * 75)
    
    app = QApplication(sys.argv)
    api = KiwoomAPI()
    db = TimeSeriesDB()
    
    # 1. 키움 Open API+ 로그인
    print("\n>> [Step 1] 키움 Open API+ 로그인 진행...")
    success = api.login()
    if not success:
        print(">> [FAIL] 로그인 실패로 수집을 중단합니다.")
        sys.exit(1)
        
    code = config.STOCK_CODE # 000660
    target_start_date = "20250801" # 2025년 8월 1일
    timeframes = [3, 5, 15]
    summary_results = {}
    
    # 2. 각 분봉별 순차 수집 및 DB/CSV/Parquet 적재
    for tf in timeframes:
        print("\n" + "=" * 75)
        print(f">> [Step 2-{tf}] SK하이닉스({code}) {tf}분봉 과거 데이터 수집 시작...")
        
        df_bars = api.get_minute_bars(
            code=code,
            tick_range=tf,
            target_start_date=target_start_date
        )
        
        if not df_bars.empty:
            db.save_timeframe_bars(code, f"{tf}m", df_bars)
            summary_results[f"{tf}분봉"] = {
                "count": len(df_bars),
                "start": df_bars.index[0].strftime('%Y-%m-%d %H:%M'),
                "end": df_bars.index[-1].strftime('%Y-%m-%d %H:%M'),
                "csv_file": f"data/{code}_{tf}m.csv",
                "parquet_file": f"data/{code}_{tf}m.parquet"
            }
        else:
            print(f">> [WARN] {tf}분봉 수신 데이터가 없습니다.")
            
        time.sleep(1.0)
        
    # 3. 수집 완료 리포트 출력
    print("\n" + "=" * 75)
    print(">> [Result] 🎉 SK하이닉스 모든 분봉 데이터 수집 및 저장이 완료되었습니다!")
    print("=" * 75)
    print(f"{'타임프레임':<10} | {'수집 봉 수':<10} | {'수집 기간':<35} | {'저장 파일'}")
    print("-" * 75)
    for tf_label, info in summary_results.items():
        period_str = f"{info['start']} ~ {info['end']}"
        print(f"{tf_label:<10} | {info['count']:>8,d}개 | {period_str:<35} | {info['csv_file']}")
    print("=" * 75)
    print("\n>> 💡 저장된 데이터 파일 위치:")
    print(f"   • SQLite DB : {os.path.abspath('data/hynix_market_data.sqlite')}")
    print(f"   • CSV 파일  : {os.path.abspath('data/')} (Excel / Pandas 즉시 분석 가능)")
    print(f"   • Parquet   : {os.path.abspath('data/')} (초고속 백테스팅용)")
    print("\n수집이 완료되었습니다.")

if __name__ == "__main__":
    main()
