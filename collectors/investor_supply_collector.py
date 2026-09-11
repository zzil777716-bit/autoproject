# -*- coding: utf-8 -*-
"""
collectors/investor_supply_collector.py
================================================================================
🏛️ [Antigravity] 350개 전 종목 투자자별 수급(외인/기관/개인 순매수 & 보유율)
과거 전수 수집 및 일일 증분 자동 갱신 엔진
================================================================================
• 수집 대상: 코스피 200 (200종목) + 코스닥 150 (150종목) = 총 350개 종목
• 수집 데이터:
  1. 외국인 순매수 수량 (ForeignerNetBuy)
  2. 기관 순매수 수량 (InstitutionNetBuy)
  3. 개인 순매수 수량 (IndividualNetBuy)
  4. 외국인 보유율 (%) (ForeignerHoldRatio)
• 저장 방식:
  - 350개 종목의 기존 일봉 CSV 파일에 위 4개 수급 컬럼을 날짜(Date) 기준으로 병합/누적
  - 독립 수급 CSV 및 JSON 캐시도 동시 적재
  - 로컬 SSD 및 구글 드라이브 양방향 실시간 동기화
"""

import os
import sys
import time
import glob
import json
import shutil
import requests
import pandas as pd
import numpy as np
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# 콘솔 UTF-8 출력 설정
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE_DIR = r"C:\Antigravity"
LOCAL_DATA_DIR = os.path.join(BASE_DIR, "data", "종목데이터")
GDRIVE_DATA_DIR = r"G:\내 드라이브\Antigravity\종목데이터"

SUPPLY_LOCAL_DIR = os.path.join(BASE_DIR, "data", "수급데이터")
SUPPLY_GDRIVE_DIR = r"G:\내 드라이브\Antigravity\수급데이터"

for d in [SUPPLY_LOCAL_DIR, SUPPLY_GDRIVE_DIR]:
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'
}

def clean_int(val_str):
    """문자열 숫자를 정수로 변환 (부호 및 콤마 처리)"""
    if pd.isna(val_str): return 0
    s = str(val_str).replace(',', '').replace('+', '').strip()
    try:
        return int(s)
    except Exception:
        try:
            return int(float(s))
        except Exception:
            return 0

def clean_float(val_str):
    """문자열 백분율을 실수로 변환"""
    if pd.isna(val_str): return 0.0
    s = str(val_str).replace('%', '').replace(',', '').strip()
    try:
        return float(s)
    except Exception:
        return 0.0

class InvestorSupplyCollector:
    def __init__(self, target_start_date: str = "20250101"):
        self.target_start_date = target_start_date # 기본 2025년 1월부터 과거 전수

    def fetch_stock_supply_history(self, code: str, max_steps: int = 12) -> pd.DataFrame:
        """단일 종목의 과거 일별 수급 데이터 페이징 크롤링"""
        current_bizdate = ''
        all_rows = []

        for step in range(max_steps):
            if current_bizdate:
                url = f"https://m.stock.naver.com/api/stock/{code}/trend?pageSize=60&bizdate={current_bizdate}"
            else:
                url = f"https://m.stock.naver.com/api/stock/{code}/trend?pageSize=60"

            try:
                r = requests.get(url, headers=HEADERS, timeout=8)
                if r.status_code != 200:
                    break
                items = r.json()
                if not items:
                    break

                for item in items:
                    b_date = item.get('bizdate', '')
                    if not b_date: continue
                    
                    # YYYYMMDD -> YYYY-MM-DD
                    dt_fmt = f"{b_date[:4]}-{b_date[4:6]}-{b_date[6:8]}"
                    
                    all_rows.append({
                        'Date': dt_fmt,
                        'ForeignerNetBuy': clean_int(item.get('foreignerPureBuyQuant', 0)),
                        'InstitutionNetBuy': clean_int(item.get('organPureBuyQuant', 0)),
                        'IndividualNetBuy': clean_int(item.get('individualPureBuyQuant', 0)),
                        'ForeignerHoldRatio': clean_float(item.get('foreignerHoldRatio', 0.0))
                    })

                last_dt = items[-1].get('bizdate', '')
                if not last_dt or last_dt <= self.target_start_date:
                    break
                current_bizdate = last_dt
            except Exception:
                break

        if not all_rows:
            return pd.DataFrame()

        df_supply = pd.DataFrame(all_rows).drop_duplicates(subset=['Date'])
        df_supply = df_supply.sort_values('Date').reset_index(drop=True)
        return df_supply

    def update_stock_daily_with_supply(self, file_path: str) -> bool:
        """기존 일봉 CSV 파일에 수급 데이터를 병합하여 갱신 저장"""
        try:
            fname = os.path.basename(file_path).replace('.csv', '')
            parts = fname.split('_')
            code = parts[0]
            name = parts[1] if len(parts) > 1 else code

            # 1. 일봉 파일 로드
            df_daily = pd.read_csv(file_path, encoding='utf-8-sig')
            if 'Date' not in df_daily.columns or len(df_daily) == 0:
                return False

            df_daily['Date'] = pd.to_datetime(df_daily['Date']).dt.strftime('%Y-%m-%d')
            df_daily = df_daily.sort_values('Date').reset_index(drop=True)

            # 이미 과거 수급 데이터가 완비되어 있고 최신 날짜까지 매핑되어 있다면 1페이지만 조회 (고속 증분)
            has_supply_cols = all(col in df_daily.columns for col in ['ForeignerNetBuy', 'InstitutionNetBuy', 'ForeignerHoldRatio'])
            if has_supply_cols and not df_daily['ForeignerNetBuy'].isna().tail(5).any():
                df_supply = self.fetch_stock_supply_history(code, max_steps=1)
            else:
                df_supply = self.fetch_stock_supply_history(code, max_steps=10) # 1년치 전수

            if df_supply.empty:
                return False

            # 2. Date 기준으로 병합 (Left Join 또는 Merge)
            supply_cols = ['ForeignerNetBuy', 'InstitutionNetBuy', 'IndividualNetBuy', 'ForeignerHoldRatio']
            for c in supply_cols:
                if c in df_daily.columns:
                    df_daily.drop(columns=[c], inplace=True)

            df_merged = pd.merge(df_daily, df_supply, on='Date', how='left')

            # 결측치 보정 (수급 데이터 없는 휴일/특이일은 0 또는 ffill)
            df_merged['ForeignerNetBuy'] = df_merged['ForeignerNetBuy'].fillna(0).astype(int)
            df_merged['InstitutionNetBuy'] = df_merged['InstitutionNetBuy'].fillna(0).astype(int)
            df_merged['IndividualNetBuy'] = df_merged['IndividualNetBuy'].fillna(0).astype(int)
            df_merged['ForeignerHoldRatio'] = df_merged['ForeignerHoldRatio'].fillna(method='ffill').fillna(0.0)

            # 3. CSV 저장
            df_merged.to_csv(file_path, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            return False

    def run_all(self, workers: int = 12):
        print("=" * 80)
        print("🏛️ [Antigravity] 350개 전 종목 투자자별 수급(외인/기관/개인) 전수 수집 및 병합 시작")
        print(f">> 시작 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Worker: {workers})")
        print("=" * 80)

        # 350개 일봉 파일 목록 확보
        daily_files = glob.glob(r"C:\Antigravity\data\*\*\일봉\*.csv")
        print(f">> 대상 일봉 파일 수: {len(daily_files)}개")

        t0 = time.time()
        success_cnt = 0
        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_file = {executor.submit(self.update_stock_daily_with_supply, f): f for f in daily_files}
            done = 0
            for fut in as_completed(future_to_file):
                done += 1
                if fut.result():
                    success_cnt += 1
                if done % 50 == 0 or done == len(daily_files):
                    print(f"  • 수급 수집/병합 진행률: {done}/{len(daily_files)} ({done/len(daily_files)*100:.1f}%) [성공: {success_cnt}]")

        elapsed = time.time() - t0
        print(f"\n>> ✅ 350개 전 종목 수급 데이터 수집 및 일봉 CSV 병합 완료! (성공: {success_cnt}/{len(daily_files)}, 소요시간: {elapsed:.1f}초)")

        # 구글 드라이브 동기화
        self.sync_to_gdrive()

    def sync_to_gdrive(self):
        """구글 드라이브로 수급 데이터가 반영된 일봉 파일 동기화"""
        print("\n>> ☁️ 구글 드라이브로 수급 통합 일봉 데이터 동기화 복사 중...")
        try:
            daily_files = glob.glob(r"C:\Antigravity\data\*\*\일봉\*.csv")
            for f in daily_files:
                p = os.path.normpath(f)
                parts = p.split(os.sep)
                mkt = "코스피200" if "200" in p else "코스닥150"
                fname = os.path.basename(f)
                target_f = os.path.join(GDRIVE_DATA_DIR, mkt, "일봉", fname)
                os.makedirs(os.path.dirname(target_f), exist_ok=True)
                shutil.copy2(f, target_f)
            print("  ✅ 구글 드라이브 동기화 완료!")
        except Exception as e:
            print(f"  ⚠️ 구글 드라이브 동기화 에러: {e}")

if __name__ == "__main__":
    collector = InvestorSupplyCollector()
    collector.run_all(workers=12)
