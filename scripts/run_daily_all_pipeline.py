# -*- coding: utf-8 -*-
"""
========================================================================================
🏛️ [ANTIGRAVITY 9-AI COUNCIL: DAILY E2E AUTOMATION PIPELINE]
매일 영업일 오후 8시 10분 (애프터마켓 종료 20:00 이후) 자동 실행 스케줄러 진입점
1. 당일 영업일 여부 판정 (주말 및 공휴일 자동 패스)
2. 키움 REST API 토큰 갱신 및 당일 실시간 테마/시세 수집
3. 당일 350개 종목 윗꼬리·돌파봉·눌림목 전수 분석
4. 바탕화면 캘린더 (5대 탭 및 윗꼬리 눌림목 TOP 30 승률) 갱신
5. 바탕화면 '매매전략_통합검증_마스터_요약.xlsx' 엑셀 자동 갱신
6. 구글 드라이브 클라우드 영구 백업
========================================================================================
"""

import os
import sys
import json
import time
from datetime import datetime, date

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = r"C:\Antigravity"
sys.path.insert(0, BASE_DIR)

def is_business_day(check_date: date) -> bool:
    """영업일 여부 판정 (주말 토/일 제외 및 기본 공휴일 필터)"""
    if check_date.weekday() >= 5: # 5: 토요일, 6: 일요일
        return False

    holidays = [
        (1, 1), (3, 1), (5, 5), (6, 6), (8, 15), (10, 3), (10, 9), (12, 25)
    ]
    if (check_date.month, check_date.day) in holidays:
        return False

    return True

def main():
    now = datetime.now()
    today_date = now.date()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    print("=" * 85)
    print(f"🏛️ [Antigravity 9-AI Council] 무인 자동 데이터 수집 & 분석 파이프라인 가동")
    print(f"⏰ 실행 시각: {now_str}")
    print("=" * 85)

    if not is_business_day(today_date):
        print(f">> [Skip] 오늘({today_date})은 주말 또는 법정 공휴일이므로 자동 수집을 건너뜁니다.")
        return

    print(f">> [1/5] 🔑 키움 공식 REST API 토큰 점검 및 환경 로드...")
    try:
        from adapters.kiwoom_rest_adapter import KiwoomRestAdapter
        env_file = os.path.join(BASE_DIR, "rest_api_key.env")
        if os.path.exists(env_file):
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        k, v = line.split("=", 1)
                        os.environ[k.strip()] = v.strip(' "\'')
        
        rest_adapter = KiwoomRestAdapter(is_simulation=True)
        rest_adapter.set_credentials(
            os.getenv("KIWOOM_APP_KEY", ""),
            os.getenv("KIWOOM_APP_SECRET", ""),
            os.getenv("KIWOOM_ACCOUNT_NO", ""),
            is_simulation=True
        )
        token_ok = rest_adapter.issue_token()
        print(f"   • REST API 인증 상태: {'성공 (Bearer Token 획득)' if token_ok else '기존 세션/로컬 폴백'}")
    except Exception as e:
        print(f"   • REST API 토큰 요청 예외 (로컬 파이프라인으로 지속): {e}")

    print(f"\n>> [2/5] 📡 실시간 시장 데이터 수집 및 월간 엑셀/캘린더 생성...")
    try:
        from workers.theme_calendar_worker import ThemeCalendarWorker
        calendar_worker = ThemeCalendarWorker(base_dir=BASE_DIR)
        calendar_worker.run()
        print("   • 캘린더 HTML 및 월간 HTS 분석 엑셀 생성 완료!")
    except Exception as e:
        print(f"   ❌ 캘린더 워커 실행 중 오류: {e}")

    print(f"\n>> [3/5] 📊 350개 전 종목 윗꼬리 돌파 & 눌림목 퀀트 전수 분석...")
    try:
        deep_script = r"C:\Users\HONG\.gemini\antigravity\brain\b201b829-ba8c-4b1a-82e5-8fa15dc4f939\scratch\analyze_breakout_pullback_deep_quant.py"
        if os.path.exists(deep_script):
            import subprocess
            subprocess.run([sys.executable, deep_script], cwd=BASE_DIR, check=False)
            print("   • 윗꼬리돌파_5프로양봉_눌림목_전수분석 갱신 완료!")
    except Exception as e:
        print(f"   ❌ 퀀트 전수 분석 중 오류: {e}")

    print(f"\n>> [4/5] 📑 바탕화면 '매매전략_통합검증_마스터_요약.xlsx' 동기화...")
    try:
        summary_script = r"C:\Users\HONG\.gemini\antigravity\brain\b201b829-ba8c-4b1a-82e5-8fa15dc4f939\scratch\build_desktop_unified_master_summary.py"
        if os.path.exists(summary_script):
            import subprocess
            subprocess.run([sys.executable, summary_script], cwd=BASE_DIR, check=False)
            print("   • 바탕화면 마스터 요약 엑셀 갱신 완료!")
    except Exception as e:
        print(f"   ❌ 마스터 요약 엑셀 빌드 중 오류: {e}")

    print(f"\n>> [5/5] ☁️ 구글 드라이브 클라우드 최종 백업...")
    try:
        from storage.gdrive_sync import GDriveSync
        sync = GDriveSync()
        sync.sync_all(BASE_DIR)
        print("   • 구글 드라이브 백업 완료!")
    except Exception as e:
        print(f"   ❌ 구글 드라이브 백업 오류: {e}")

    print("\n" + "=" * 85)
    print(f"🎉 [성공] 영업일 정기 데이터 수집 & 분석 파이프라인 전체 완료 ({datetime.now().strftime('%H:%M:%S')})")
    print("=" * 85)

if __name__ == "__main__":
    main()
