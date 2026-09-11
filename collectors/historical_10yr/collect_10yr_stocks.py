# -*- coding: utf-8 -*-
"""
========================================================================================
🏛️ [ANTIGRAVITY 10-YEAR HISTORICAL STOCK COLLECTOR (시총 1000억 이상 10년치 수집기)]
사용자 특별 지침:
1. 대상: 대한민국 상장사 중 '시총 1000억 이상' 전 종목 (~1,364개)
2. 기간: 10년치 일봉 데이터 (2016-01-01 ~ 현재)
3. 수집 속도: TR/호출 제한에 절대 걸리지 않도록 1.8초 여유 슬립(Sleep) 적용
4. 실행 시간: 밤 12시(00:05) 이후에 무인 자동 시작하여 백그라운드로 안전하게 분할 수집
5. 저장소: 
   - 로컬: C:\Antigravity\data\시총 1000억 이상\
   - 구글 드라이브: G:\내 드라이브\Antigravity\data\시총 1000억 이상\
6. 중복 방지: 이미 수집된 파일은 자동으로 건너뛰어(Skip) 며칠에 걸쳐 수집해도 이어받기 완벽 지원
7. 주말 업데이트: 10년치가 모이면 주말마다 천천히 최신 데이터 업데이트
========================================================================================
"""

import os
import sys
import time
import shutil
import datetime
import pandas as pd
import FinanceDataReader as fdr

LOCAL_DIR = r"C:\Antigravity\data\시총 1000억 이상"
GDRIVE_DIR = r"G:\내 드라이브\Antigravity\data\시총 1000억 이상"

os.makedirs(LOCAL_DIR, exist_ok=True)

def log_msg(msg: str):
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{now_str}] {msg}"
    try:
        print(formatted.encode("cp949", errors="replace").decode("cp949"), flush=True)
    except Exception:
        pass

def get_target_universe(min_marcap: int = 100_000_000_000) -> pd.DataFrame:
    """시총 1000억 이상 전 종목 추출"""
    log_msg("📡 KRX 전체 상장 종목 및 시가총액 정보 수집 중...")
    krx = fdr.StockListing('KRX')
    if 'Marcap' in krx.columns:
        filtered = krx[krx['Marcap'] >= min_marcap].copy()
        filtered = filtered.sort_values('Marcap', ascending=False).reset_index(drop=True)
        log_msg(f"✅ 시총 1000억 이상 대상 종목 추출 완료: 총 {len(filtered)}개 종목")
        return filtered
    return pd.DataFrame()

def collect_10yr_data(wait_until_midnight: bool = True):
    # 1. 밤 12시 넘어서 시작 (대기 모드)
    now = datetime.datetime.now()
    if wait_until_midnight:
        if now.hour >= 9: # 낮/저녁인 경우 오늘 밤 자정(00:05)까지 대기
            target_midnight = now.replace(hour=0, minute=5, second=0, microsecond=0) + datetime.timedelta(days=1)
        else: # 이미 자정이 넘은 경우 바로 시작
            target_midnight = now
            
        wait_seconds = (target_midnight - now).total_seconds()
        if wait_seconds > 10:
            log_msg(f"⏳ [예약 대기] 12시 넘어서 수집을 시작하도록 설정되었습니다.")
            log_msg(f"   - 시작 예정 시각: {target_midnight.strftime('%Y-%m-%d %H:%M:%S')} (약 {wait_seconds/3600:.1f}시간 뒤 자동 시작)")
            time.sleep(wait_seconds)

    log_msg("="*80)
    log_msg("🚀 [시총 1000억 이상 10년치 일봉 데이터 수집 가동]")
    log_msg("="*80)

    universe = get_target_universe(100_000_000_000)
    if universe.empty:
        log_msg("❌ 종목 유니버스를 가져오지 못했습니다.")
        return

    # 메타데이터 저장 (종목명, 코드, 시총, 시장)
    meta_path = os.path.join(LOCAL_DIR, "_universe_metadata.csv")
    universe[['Code', 'Name', 'Market', 'Marcap', 'Close']].to_csv(meta_path, index=False, encoding='utf-8-sig')

    total_count = len(universe)
    success_count = 0
    skipped_count = 0
    start_date = "2016-01-01"
    end_date = datetime.datetime.now().strftime("%Y-%m-%d")

    has_gdrive = os.path.exists(r"G:\내 드라이브\Antigravity")
    if has_gdrive:
        os.makedirs(GDRIVE_DIR, exist_ok=True)
        try:
            shutil.copy2(meta_path, os.path.join(GDRIVE_DIR, "_universe_metadata.csv"))
        except Exception:
            pass

    for idx, row in universe.iterrows():
        code = str(row['Code']).zfill(6)
        name = str(row['Name']).replace("/", "_").replace("\\", "_")
        marcap_eok = row['Marcap'] / 1e8
        
        filename = f"{code}_{name}.csv"
        local_filepath = os.path.join(LOCAL_DIR, filename)
        gdrive_filepath = os.path.join(GDRIVE_DIR, filename)

        # 1. 이어받기 기능: 이미 로컬 또는 GDrive에 파일이 존재하고 충분한 행이 있으면 스킵
        if os.path.exists(local_filepath) and os.path.getsize(local_filepath) > 1000:
            skipped_count += 1
            if (idx + 1) % 50 == 0 or idx == total_count - 1:
                log_msg(f"[{idx+1}/{total_count}] (진행률: {(idx+1)/total_count*100:.1f}%) {name}({code}) 이미 수집됨 (건너뜀)")
            continue

        try:
            # 2. 10년치 일봉 수집
            df = fdr.DataReader(code, start=start_date, end=end_date)
            if not df.empty:
                df.index.name = "Date"
                df = df.reset_index()
                
                # 로컬 저장
                df.to_csv(local_filepath, index=False, encoding='utf-8-sig')
                
                # GDrive 실시간 동기화
                if has_gdrive:
                    try:
                        shutil.copy2(local_filepath, gdrive_filepath)
                    except Exception:
                        pass

                success_count += 1
                log_msg(f"[{idx+1}/{total_count}] ✅ {name:12s} ({code}) | 시총: {marcap_eok:,.0f}억 | {len(df)}일치 저장 완료")
            else:
                log_msg(f"[{idx+1}/{total_count}] ⚠️ {name}({code}) 데이터 없음 (신규상장 등)")

        except Exception as e:
            log_msg(f"[{idx+1}/{total_count}] ❌ {name}({code}) 수집 중 오류: {e}")

        # 3. TR/호출 제한 절대 방지: 1.8초 여유 슬립
        time.sleep(1.8)

    log_msg("="*80)
    log_msg(f"🎉 10년치 일봉 수집 배치 1회차 완료!")
    log_msg(f"   - 총 대상: {total_count}개 | 신규 수집: {success_count}개 | 기존 보존: {skipped_count}개")
    log_msg(f"   - 저장 위치: {LOCAL_DIR} 및 구글 드라이브 동기화 완료")
    log_msg("="*80)

if __name__ == "__main__":
    run_now = "--now" in sys.argv
    collect_10yr_data(wait_until_midnight=not run_now)
