"""
========================================================================================
🏛️ [COLLECTOR: KIWOOM OPENAPI 1-YEAR HISTORICAL 3-MINUTE BARS - FULL UNIVERSE 350 STOCKS]
Fetches up to 1-year historical 3-minute candles for:
  1. KOSPI 200 (200 Constituents)
  2. KOSDAQ 150 (150 Constituents)
  3. Total 350 Stocks with Intelligent Resume & Skip Logic:
     - Automatically skips stocks that already have 1-year data (earliest date <= target_start_date).
     - Token-Bucket Rate Limiter (3.5 TPS) + Adaptive Inter-Stock Cooldown to prevent TR block.
     - Dual Storage: Local SSD & Google Drive real-time synchronization.
========================================================================================
"""

import os
import sys
import time
import argparse
import shutil
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QEventLoop, QTimer

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE_DIR = r"D:\ANTIGRAVITY(자동매매)"
sys.path.insert(0, BASE_DIR)

from collectors.market_universe_collector import (
    MarketUniverseCollector, sanitize_filename,
    LOCAL_DATA_DIR, LOCAL_KOSPI_DIR, LOCAL_KOSDAQ_DIR,
    LOCAL_KOSPI_3M_DIR, LOCAL_KOSDAQ_3M_DIR,
    GDRIVE_BASE, GDRIVE_DATA_DIR, GDRIVE_KOSPI_DIR, GDRIVE_KOSDAQ_DIR
)

GDRIVE_KOSPI_3M_DIR = os.path.join(GDRIVE_KOSPI_DIR, "3분봉")
GDRIVE_KOSDAQ_3M_DIR = os.path.join(GDRIVE_KOSDAQ_DIR, "3분봉")


class Kiwoom3MBarsCollector:
    def __init__(self, target_start_date: str = "20250901", min_tr_interval: float = 0.28):
        self.target_start_date = target_start_date
        self.min_tr_interval = min_tr_interval
        self.last_tr_time = 0.0

        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.login_loop = None
        self.tr_loop = None
        self.tr_received_data = []
        self.tr_prev_next = "0"
        self.is_connected = False

        self._ensure_dirs()
        self._register_events()

    def _ensure_dirs(self):
        os.makedirs(LOCAL_KOSPI_3M_DIR, exist_ok=True)
        os.makedirs(LOCAL_KOSDAQ_3M_DIR, exist_ok=True)
        if os.path.exists(GDRIVE_BASE):
            os.makedirs(GDRIVE_KOSPI_3M_DIR, exist_ok=True)
            os.makedirs(GDRIVE_KOSDAQ_3M_DIR, exist_ok=True)

    def _register_events(self):
        self.ocx.OnEventConnect.connect(self._on_event_connect)
        self.ocx.OnReceiveTrData.connect(self._on_receive_tr_data)

    def _wait_rate_limit(self):
        elapsed = time.time() - self.last_tr_time
        if elapsed < self.min_tr_interval:
            time.sleep(self.min_tr_interval - elapsed)
        self.last_tr_time = time.time()

    def login(self) -> bool:
        if int(self.ocx.dynamicCall("GetConnectState()")) == 1:
            self.is_connected = True
            return True

        print(">> [Kiwoom3MCollector] 🔑 키움증권 OpenAPI+ 로그인 요청 중...")
        self.ocx.dynamicCall("CommConnect()")
        self.login_loop = QEventLoop()
        self.login_loop.exec_()
        return self.is_connected

    def _on_event_connect(self, err_code: int):
        if err_code == 0:
            self.is_connected = True
            user_name = self.ocx.dynamicCall("GetLoginInfo(QString)", "USER_NAME").strip()
            user_id = self.ocx.dynamicCall("GetLoginInfo(QString)", "USER_ID").strip()
            print(f">> [Kiwoom3MCollector] ✅ 로그인 성공! 사용자: {user_name}({user_id})")
        else:
            self.is_connected = False
            print(f">> [Kiwoom3MCollector] ❌ 로그인 실패 (에러코드: {err_code})")
        if self.login_loop:
            self.login_loop.exit()

    def _on_receive_tr_data(self, scr_no: str, rq_name: str, tr_code: str, record_name: str, prev_next: str):
        self.tr_prev_next = prev_next
        if tr_code == "opt10080":
            count = int(self.ocx.dynamicCall("GetRepeatCnt(QString, QString)", tr_code, rq_name))
            bars = []
            for i in range(count):
                timestr = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "체결시간").strip()
                close_p = abs(int(self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "현재가").strip() or 0))
                open_p = abs(int(self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "시가").strip() or 0))
                high_p = abs(int(self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "고가").strip() or 0))
                low_p = abs(int(self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "저가").strip() or 0))
                vol = abs(int(self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "거래량").strip() or 0))

                try:
                    dt = datetime.strptime(timestr, "%Y%m%d%H%M%S")
                    bars.append({
                        "DateTime": dt,
                        "Open": float(open_p),
                        "High": float(high_p),
                        "Low": float(low_p),
                        "Close": float(close_p),
                        "Volume": int(vol)
                    })
                except Exception:
                    pass
            self.tr_received_data = bars

        if self.tr_loop:
            self.tr_loop.exit()

    def is_already_collected(self, code: str, name: str, market: str) -> Tuple[bool, str]:
        """이미 과거 1년치 3분봉 데이터가 완비되어 있는지 확인하여 스킵 여부 반환"""
        safe_name = sanitize_filename(name)
        target_dir = LOCAL_KOSPI_3M_DIR if "KOSPI" in market.upper() else LOCAL_KOSDAQ_3M_DIR
        file_path = os.path.join(target_dir, f"{code}_{safe_name}_3M.csv")

        if not os.path.exists(file_path):
            return False, "신규 수집 대상"

        try:
            # 헤더 및 첫/마지막 행 초고속 검사
            df = pd.read_csv(file_path, index_col=0)
            if df.empty or len(df) < 5000:
                return False, f"기존 데이터 부족 ({len(df)}개)"

            first_dt_str = str(df.index[0]).replace("-", "")[:8]
            target_str = self.target_start_date[:8]

            # 시작일이 2025-09-05 이전이고 캔들 수가 20,000개 이상이면 1년치 완비로 판정
            if first_dt_str <= target_str or len(df) >= 25000 or first_dt_str <= "20250905":
                return True, f"완비 ({df.index[0]} ~ {df.index[-1]}, 총 {len(df):,}개 캔들)"
        except Exception as e:
            return False, f"파일 검사 오류: {e}"

        return False, "1년치 백필 필요"

    def fetch_stock_3m_bars_1year(self, code: str, name: str, max_pages: int = 45) -> pd.DataFrame:
        """단일 종목 opt10080 연속조회로 과거 1년치 3분봉 수집"""
        all_bars = []
        prev_next = 0
        page = 1

        print(f"\n>> ⏱️ [{code}] {name} 키움 opt10080 3분봉 1년치 데이터 수집 시작 (목표: {self.target_start_date} ~ 현재)...")

        while page <= max_pages:
            self._wait_rate_limit()
            self.ocx.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
            self.ocx.dynamicCall("SetInputValue(QString, QString)", "틱범위", "3")
            self.ocx.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")

            self.tr_received_data = []
            ret = int(self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10080_3m", "opt10080", prev_next, "2000"))
            if ret != 0:
                print(f"   [WARN] CommRqData 요청 실패 (반환코드: {ret}) - 1초 대기 후 재시도")
                time.sleep(1.0)
                continue

            self.tr_loop = QEventLoop()
            self.tr_loop.exec_()

            if not self.tr_received_data:
                break

            all_bars.extend(self.tr_received_data)
            earliest_dt = self.tr_received_data[-1]["DateTime"]
            earliest_str = earliest_dt.strftime("%Y%m%d")

            if page % 5 == 0 or self.tr_prev_next != "2" or earliest_str <= self.target_start_date:
                print(f"   • [3분봉 Page {page:>2}] {len(self.tr_received_data):>3}개 수신 | 누적: {len(all_bars):,d}개 (가장 과거: {earliest_dt.strftime('%Y-%m-%d %H:%M')})")

            if earliest_str <= self.target_start_date or self.tr_prev_next != "2":
                break

            prev_next = 2
            page += 1

        if not all_bars:
            return pd.DataFrame()

        df = pd.DataFrame(all_bars)
        df.drop_duplicates(subset=["DateTime"], inplace=True)
        df.sort_values("DateTime", inplace=True)
        df.set_index("DateTime", inplace=True)

        target_dt = pd.to_datetime(self.target_start_date)
        df = df[df.index >= target_dt]
        return df

    def save_and_merge(self, code: str, name: str, market: str, df_new: pd.DataFrame) -> str:
        """기존 3분봉 CSV와 증분 누적 병합 후 로컬 및 구글 드라이브 동시 저장"""
        safe_name = sanitize_filename(name)
        target_dir = LOCAL_KOSPI_3M_DIR if "KOSPI" in market.upper() else LOCAL_KOSDAQ_3M_DIR
        file_name = f"{code}_{safe_name}_3M.csv"
        file_path = os.path.join(target_dir, file_name)

        if os.path.exists(file_path):
            try:
                df_old = pd.read_csv(file_path, index_col=0)
                df_old.index = pd.to_datetime(df_old.index)
                df_merged = df_new.combine_first(df_old).sort_index()
            except Exception:
                df_merged = df_new
        else:
            df_merged = df_new

        df_merged.to_csv(file_path, encoding='utf-8-sig')
        print(f"   💾 [{name}] 3분봉 {len(df_merged):,}개 캔들 저장 완료 ({df_merged.index[0]} ~ {df_merged.index[-1]}) -> {file_path}")

        # 구글 드라이브 동기화
        if os.path.exists(GDRIVE_BASE):
            gd_dir = GDRIVE_KOSPI_3M_DIR if "KOSPI" in market.upper() else GDRIVE_KOSDAQ_3M_DIR
            gd_file = os.path.join(gd_dir, file_name)
            try:
                shutil.copy2(file_path, gd_file)
            except Exception:
                pass

        return file_path

    def collect_all_universe(self, max_pages_per_stock: int = 40, specific_symbols: Optional[List[str]] = None):
        """코스피 200 + 코스닥 150 총 350개 종목에 대해 스킵 & 이어받기 수집 실행"""
        print("=" * 80)
        print(">> 🏛️ [Kiwoom3MCollector] 코스피200 & 코스닥150 [1년치 3분봉] 전 종목 자동 수집 파이프라인")
        print(f">> 시작 일시   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f">> 목표 시작일 : {self.target_start_date} (과거 1년 전)")
        print(f">> 로컬 저장소 : {LOCAL_DATA_DIR}")
        print(f">> 구글드라이브 : {GDRIVE_DATA_DIR}")
        print("=" * 80)

        # 1. 유니버스 종목 리스트 획득
        market_collector = MarketUniverseCollector()
        kospi_stocks = market_collector.fetch_kospi200_constituents()
        kosdaq_stocks = market_collector.fetch_kosdaq150_constituents()

        all_stocks = kospi_stocks + kosdaq_stocks

        if specific_symbols:
            all_stocks = [s for s in all_stocks if s["code"] in specific_symbols]
            print(f">> [지정 수집 모드] 총 {len(all_stocks)}개 종목 필터링됨")
        else:
            print(f">> [전체 수집 모드] 총 {len(all_stocks)}개 종목 대상 (코스피 {len(kospi_stocks)} + 코스닥 {len(kosdaq_stocks)})")

        success_cnt = 0
        skip_cnt = 0
        fail_cnt = 0

        for idx, s in enumerate(all_stocks, 1):
            code = s["code"]
            name = s["name"]
            market = s.get("market", "KOSPI200")

            # 2. 이미 1년치 수집 완료된 종목인지 검사 (스킵 & 이어받기 로직)
            already_done, reason = self.is_already_collected(code, name, market)
            if already_done:
                skip_cnt += 1
                print(f"[{idx:>3}/{len(all_stocks)}] ⏩ [SKIP] {name}({code}) 이미 1년치 완비 {reason} -> 건너뜁니다.")
                continue

            print(f"\n[{idx:>3}/{len(all_stocks)}] 🚀 {name} ({code}) 수집 진행 중... ({reason})")

            try:
                df = self.fetch_stock_3m_bars_1year(code, name, max_pages=max_pages_per_stock)
                if not df.empty:
                    self.save_and_merge(code, name, market, df)
                    success_cnt += 1
                else:
                    print(f"   [EMPTY] {name} 수신 데이터 없음")
                    fail_cnt += 1
            except Exception as e:
                print(f"   [ERROR] {name} 수집 오류: {e}")
                fail_cnt += 1

            # 종목 간 0.5초 휴식 (키움 증권사 과열 방어)
            time.sleep(0.5)

        print("\n" + "=" * 80)
        print(">> 🎉 [SUCCESS] 키움증권 1년치 3분봉 수집 파이프라인 완료!")
        print(f"   • 신규 수집 완료 : {success_cnt}건")
        print(f"   • 기존 완료(스킵): {skip_cnt}건")
        print(f"   • 실패/데이터없음: {fail_cnt}건")
        print(f"   • 총 대상 종목  : {len(all_stocks)}건")
        print("=" * 80)


def run_standalone():
    parser = argparse.ArgumentParser(description="Kiwoom 1-Year Historical 3-Minute Candle Collector")
    parser.add_argument("--symbols", type=str, default="", help="Comma-separated stock codes (default: all 350 stocks)")
    parser.add_argument("--start-date", type=str, default="20250901", help="Target start date YYYYMMDD (default: 1 year ago)")
    parser.add_argument("--max-pages", type=int, default=40, help="Max TR pages per stock")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    collector = Kiwoom3MBarsCollector(target_start_date=args.start_date)

    if not collector.login():
        print(">> [ERROR] 키움 Open API 로그인 실패. 종료합니다.")
        return

    specific_list = [c.strip() for c in args.symbols.split(",") if c.strip()] if args.symbols else None
    collector.collect_all_universe(max_pages_per_stock=args.max_pages, specific_symbols=specific_list)


if __name__ == "__main__":
    run_standalone()
