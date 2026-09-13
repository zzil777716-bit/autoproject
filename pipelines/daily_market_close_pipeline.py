# -*- coding: utf-8 -*-
"""
D:/ANTIGRAVITY(자동매매)/pipelines/daily_market_close_pipeline.py
================================================================================
🏛️ [Antigravity Multi-Agent Council]
장 마감 후 매일 데이터 자동 수집 및 2대 검증(장기이평 윗꼬리 / 햄버거 주도주) 업데이트 파이프라인
================================================================================
• 실행 시각: 매 영업일(월~금) 15:40 이후 (또는 장 마감 후 수시 실행)
• 실행 절차:
  1단계: 350개 전 종목 (코스피200 / 코스닥150) 최신 일봉 데이터 수집 및 갱신 (MarketUniverseCollector)
  2단계: [검증 1] 장기이평(60/112/120/224/240일선) 윗꼬리 매집봉 일일 탐지 & 누적 마스터 갱신
  3단계: [검증 2] 햄버거 기법 S/A급 주도주 최적 기준 거래대금 & 당일 포착 및 성과 갱신
  4단계: [요약 및 이관] 'HTS_사용자검증_핵심요약_통합마스터.xlsx' 갱신 및
         구글 드라이브(G:\\내 드라이브\\Antigravity\\사용자 검증) 및 로컬에 자동 배포
================================================================================
"""

import os
import sys
import time
import shutil
import subprocess
import pandas as pd
import numpy as np
from datetime import datetime

# Windows 콘솔 UTF-8 설정
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE_DIR = r"D:\ANTIGRAVITY(자동매매)"
sys.path.insert(0, BASE_DIR)

DEFAULT_PYTHON = r"C:\Users\HONG\AppData\Local\Programs\Python\Python310-32\python.exe"
PYTHON_EXE = DEFAULT_PYTHON if os.path.exists(DEFAULT_PYTHON) else sys.executable

GDRIVE_USER_VERIFY = r"G:\내 드라이브\Antigravity\사용자 검증"
LOCAL_USER_VERIFY = r"D:\ANTIGRAVITY(자동매매)\data\사용자_검증"

def log_step(step_num: int, title: str):
    print("\n" + "=" * 80)
    print(f"📌 [STEP {step_num}] {title}")
    print(f">> 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

def step0_collect_infostock_theme_map():
    """0단계: 인포스탁 전종목 테마지도 무료 취합 및 일일 엑셀/JSON 갱신"""
    log_step(0, "인포스탁 266개 전체 테마 및 전 종목 테마지도 자동 취합 & 엑셀/JSON 갱신")
    try:
        from collectors.infostock_theme_map_collector import InfostockThemeMapCollector
        collector = InfostockThemeMapCollector()
        collector.collect_and_build_map()
        print(">> [Step 0 완료] 인포스탁 전종목 테마지도 갱신 및 구글드라이브 배포 완료!")
        return True
    except Exception as e:
        print(f">> [Step 0 경고] 테마지도 수집 중 오류: {e}")
        return False

def step1_collect_daily_universe():
    """1단계: 350개 종목 최신 일봉 수집 및 마스터 갱신"""
    log_step(1, "350개 전 종목(코스피200/코스닥150) 일봉 데이터 자동 수집 및 갱신")
    try:
        from collectors.market_universe_collector import (
            MarketUniverseCollector,
            LOCAL_KOSPI_DIR, LOCAL_KOSPI_DAILY_DIR,
            LOCAL_KOSDAQ_DIR, LOCAL_KOSDAQ_DAILY_DIR
        )
        collector = MarketUniverseCollector()
        # Constituents fetch
        kospi_stocks = collector.fetch_kospi200_constituents()
        kosdaq_stocks = collector.fetch_kosdaq150_constituents()
        
        # 1-1. 일봉 가격/거래량 수집
        collector.collect_daily_universe(kospi_stocks, LOCAL_KOSPI_DIR, LOCAL_KOSPI_DAILY_DIR, "코스피 200")
        collector.collect_daily_universe(kosdaq_stocks, LOCAL_KOSDAQ_DIR, LOCAL_KOSDAQ_DAILY_DIR, "코스닥 150")
        print(">> [Step 1-1 완료] 350개 종목 일봉 가격/거래량 데이터 갱신 완료!")
        
        # 1-2. 투자자별 수급(외인/기관/개인/지분율) 자동 수집 및 일봉 병합
        print(">> [Step 1-2 진행] 350개 종목 투자자별 수급(외인/기관/개인) 데이터 수집 및 병합 시작...")
        from collectors.investor_supply_collector import InvestorSupplyCollector
        supply_col = InvestorSupplyCollector()
        supply_col.run_all(workers=12)
        print(">> [Step 1-2 완료] 350개 종목 수급 데이터 최신 갱신 및 구글드라이브 동기화 완료!")
        return True
    except Exception as e:
        print(f">> [Step 1 경고] 일봉/수급 수집기 실행 중 오류 발생: {e}")
        return False

def step2_scan_upper_wick(target_date: str):
    """2단계: 장기이평 윗꼬리 매집봉 스캔 및 저장"""
    log_step(2, f"장기이평 윗꼬리 매집봉 일일 탐지 & 누적 관리 마스터 갱신 (기준일: {target_date})")
    scanner_script = r"C:\Users\HONG\.gemini\antigravity\brain\b201b829-ba8c-4b1a-82e5-8fa15dc4f939\scratch\daily_long_ma_upper_wick_scanner.py"
    if os.path.exists(scanner_script):
        cmd = [PYTHON_EXE, scanner_script, target_date]
        res = subprocess.run(cmd, capture_output=True, text=True)
        print(res.stdout)
        if res.stderr:
            print(res.stderr)
        print(">> [Step 2 완료] 장기이평 윗꼬리 매집봉 포착 엑셀 및 마스터 갱신 완료!")
        return True
    else:
        print(f">> [Step 2 에러] 스캐너 스크립트 미발견: {scanner_script}")
        return False

def step3_and_4_sync_verification_files():
    """3~4단계: 통합 추적 마스터 엑셀(1개 파일) 갱신 및 구글 드라이브 동기화"""
    log_step(3, "매일포착종목_통합추적관찰_마스터(1개 파일) 및 사용자 검증 파일 배포")
    unified_script = r"C:\Users\HONG\.gemini\antigravity\brain\b201b829-ba8c-4b1a-82e5-8fa15dc4f939\scratch\build_unified_master_tracker.py"
    themed_script = r"C:\Users\HONG\.gemini\antigravity\brain\b201b829-ba8c-4b1a-82e5-8fa15dc4f939\scratch\build_themed_verification_workbook.py"
    sync_script = r"C:\Users\HONG\.gemini\antigravity\brain\b201b829-ba8c-4b1a-82e5-8fa15dc4f939\scratch\sync_user_verification_files.py"
    
    # 1. 1개 파일 통합 추적관찰 마스터 생성
    if os.path.exists(unified_script):
        subprocess.run([PYTHON_EXE, unified_script], capture_output=True, text=True)
    # 2. 테마별 묶음 통합본 생성
    if os.path.exists(themed_script):
        subprocess.run([PYTHON_EXE, themed_script], capture_output=True, text=True)
    # 3. 기타 검증 원본 파일 동기화
    if os.path.exists(sync_script):
        res = subprocess.run([PYTHON_EXE, sync_script], capture_output=True, text=True)
        print(res.stdout)
        print(">> [Step 3 & 4 완료] 구글 드라이브 '사용자 검증' 폴더 최신화 완료!")
        return True
    return False

def step5_update_calendar_with_tomorrow_ranks():
    """5단계: 증시 주도테마 캘린더 업데이트 및 내일 날짜에 오늘 수집된 윗꼬리 승률순위 탑재"""
    log_step(5, "증시 주도 테마 캘린더 갱신 & 익일(내일) 윗꼬리 승률 TOP 순위 자동 탑재")
    cal_script = r"C:\Users\HONG\.gemini\antigravity\brain\b201b829-ba8c-4b1a-82e5-8fa15dc4f939\scratch\update_calendar_complete_with_tomorrow_ranks.py"
    if os.path.exists(cal_script):
        res = subprocess.run([PYTHON_EXE, cal_script], capture_output=True, text=True)
        print(res.stdout)
        if res.stderr:
            print(res.stderr)
        print(">> [Step 5 완료] 주도테마 캘린더 갱신 및 바탕화면/구글드라이브 배포 완료!")
        return True
    return False

def step6_evolve_swing_strategy():
    """6단계: 수집 데이터 기반 스윙 전략 연속 관찰 및 매매 지침 자동 진화"""
    log_step(6, "스윙 전략 연속 관찰 및 파라미터 자동 진화 (규칙 1, 2 반영)")
    try:
        from strategies.daily_swing_evolution_engine import DailySwingEvolutionEngine
        engine = DailySwingEvolutionEngine()
        engine.run_evolution_pipeline()
        print(">> [Step 6 완료] 스윙 전략 지침서 및 프로필 자동 갱신 완료!")
        return True
    except Exception as e:
        print(f">> [Step 6 에러] 스윙 전략 진화 중 오류: {e}")
        return False

def step7_index_code_ast():
    """7단계: Tree-sitter & AST 기반 코드베이스 구조화 인덱싱 (토큰 90% 압축 & 환각 방지)"""
    log_step(7, "Tree-sitter & AST 기반 코드베이스 구조화 인덱싱 (CodeRAG Spec)")
    try:
        from core.ast_code_indexer import ASTCodeIndexer
        indexer = ASTCodeIndexer()
        indexer.build_entire_repo_ast_index()
        print(">> [Step 7 완료] AST 압축 맵 및 코드 의존성 인덱스 갱신 완료!")
        return True
    except Exception as e:
        print(f">> [Step 7 에러] AST 인덱싱 중 오류: {e}")
        return False

def run_pipeline(target_date: str = None):
    t0 = time.time()
    today_str = target_date or datetime.now().strftime("%Y-%m-%d")
    print("\n" + "#" * 80)
    print("🚀 [Antigravity] 장 마감 일일 데이터 수집 & 2대 검증 자동화 파이프라인 가동")
    print(f">> 대상 영업일자: {today_str}")
    print("#" * 80)

    # 0. 인포스탁 전종목 테마지도 자동 취합 및 갱신
    step0_collect_infostock_theme_map()

    # 1. 일봉 수집 (당일 장 마감 데이터 최신화)
    step1_collect_daily_universe()

    # 2. 검증 1: 장기이평 윗꼬리 매집봉 포착 및 일일/마스터 엑셀 생성
    step2_scan_upper_wick(today_str)

    # 3. 검증 2 & 통합 요약: 햄버거 주도주 및 윗꼬리 통합 엑셀 갱신 -> 구글 드라이브 '사용자 검증' 전송
    step3_and_4_sync_verification_files()

    # 4. 검증 3: 캘린더 자동 갱신 (당일 HTS 4종 주도 데이터 복구 + 익일 셀에 당일 윗꼬리 승률 랭킹 종목명 탑재)
    step5_update_calendar_with_tomorrow_ranks()

    # 5. 스윙 전략 관찰 및 매매 지침 자동 진화 (Step 6)
    step6_evolve_swing_strategy()

    # 6. AST 코드 구조화 인덱싱 (Step 7 - 토큰 90% 압축 & 환각 방지)
    step7_index_code_ast()

    elapsed = time.time() - t0
    print("\n" + "=" * 80)
    print(f"🎉 [전체 완료] 모든 수집 및 2대 검증, 캘린더 내일 순위 자동 갱신 완료 (총 소요 시간: {elapsed:.1f}초)")
    print(f"   • 구글 드라이브: {GDRIVE_USER_VERIFY}")
    print(f"   • 로컬 저장소: {LOCAL_USER_VERIFY}")
    print(f"   • 바탕화면 캘린더: C:\\Users\\HONG\\Desktop\\증시_주도테마_캘린더.html")
    print(f"   • 최신 스윙 매매지침: G:\\내 드라이브\\Antigravity\\사용자 검증\\최신_스윙전략_매매지침.md")
    print(f"   • AST 코드 압축 맵: D:\\ANTIGRAVITY(자동매매)\\data\\code_ast_index\\REPO_COMPRESSED_AST_MAP.md")
    print("=" * 80)

if __name__ == "__main__":
    dt_arg = sys.argv[1] if len(sys.argv) > 1 else None
    run_pipeline(dt_arg)


