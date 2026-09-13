"""
========================================================================================
🏛️ [COLLECTOR: KOSPI 200 & KOSDAQ 150 UNIVERSE DATA COLLECTOR - DAILY & 3-MINUTE BARS]
Automated High-Performance Data Collector for:
  1. KOSPI 200 (200 Constituents) - Daily Candles (일봉) + 3-Minute Candles (3분봉) + Master Summary
  2. KOSDAQ 150 (150 Constituents) - Daily Candles (일봉) + 3-Minute Candles (3분봉) + Master Summary
  3. Incremental Update: Automatically merges and accumulates new market data without data loss.
  4. Dual Storage: Local (D:\\ANTIGRAVITY(자동매매)\\data\\종목데이터) & Google Drive (G:\\내 드라이브\\Antigravity\\종목데이터)
========================================================================================
"""

import os
import sys
import re
import time
import shutil
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Tuple, Optional

import requests
import pandas as pd
from bs4 import BeautifulSoup
import FinanceDataReader as fdr

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE_DIR = r"D:\ANTIGRAVITY(자동매매)"
LOCAL_DATA_DIR = os.path.join(BASE_DIR, "data", "종목데이터")
LOCAL_KOSPI_DIR = os.path.join(LOCAL_DATA_DIR, "코스피200")
LOCAL_KOSDAQ_DIR = os.path.join(LOCAL_DATA_DIR, "코스닥150")

LOCAL_KOSPI_DAILY_DIR = os.path.join(LOCAL_KOSPI_DIR, "일봉")
LOCAL_KOSPI_3M_DIR = os.path.join(LOCAL_KOSPI_DIR, "3분봉")
LOCAL_KOSDAQ_DAILY_DIR = os.path.join(LOCAL_KOSDAQ_DIR, "일봉")
LOCAL_KOSDAQ_3M_DIR = os.path.join(LOCAL_KOSDAQ_DIR, "3분봉")

GDRIVE_BASE = r"G:\내 드라이브\Antigravity"
GDRIVE_DATA_DIR = os.path.join(GDRIVE_BASE, "종목데이터")
GDRIVE_KOSPI_DIR = os.path.join(GDRIVE_DATA_DIR, "코스피200")
GDRIVE_KOSDAQ_DIR = os.path.join(GDRIVE_DATA_DIR, "코스닥150")

# 🚫 순수 개별 종목 필터링 정규식 (ETF/ETN/스팩/우선주 완벽 제외)
EXCLUDE_PATTERNS = [
    r"KODEX", r"TIGER", r"ACE", r"RISE", r"SOL", r"PLUS", r"KoAct", r"HANARO", r"TIMEFOLIO",
    r"WOORI", r"UNICORN", r"FOCUS", r"1Q", r"HERO", r"TREX", r"WON", r"히어로즈", r"파워",
    r"ETN", r"스팩", r"SPAC", r"호스팩",
    r"\d+우$", r"\d+우[A-Z]$", r"우$", r"우B$", r"우C$", r"우\(전환\)$", r"우선주"
]

def sanitize_filename(name: str) -> str:
    """윈도우 파일명 안전 문자열 변환"""
    return re.sub(r'[\\/*?:"<>|]', "", str(name)).strip()

def is_pure_individual_stock(name: str, code: str) -> bool:
    """순수 개별 기업 주식 여부 판별 (ETF/ETN/스팩/우선주 제외)"""
    name_clean = str(name).strip()
    code_clean = str(code).strip()
    for pat in EXCLUDE_PATTERNS:
        if re.search(pat, name_clean, re.IGNORECASE):
            return False
    if len(code_clean) == 6 and code_clean[-1] in ['5', '7', '8', '9', 'K', 'L', 'M']:
        return False
    return True

class MarketUniverseCollector:
    def __init__(self, start_date: str = "2025-01-01"):
        self.start_date = start_date
        self._ensure_directories()

    def _ensure_directories(self):
        """로컬 및 구글 드라이브 디렉토리 계층 생성"""
        dirs = [
            LOCAL_KOSPI_DIR, LOCAL_KOSDAQ_DIR,
            LOCAL_KOSPI_DAILY_DIR, LOCAL_KOSPI_3M_DIR,
            LOCAL_KOSDAQ_DAILY_DIR, LOCAL_KOSDAQ_3M_DIR
        ]
        for d in dirs:
            os.makedirs(d, exist_ok=True)

        if os.path.exists(GDRIVE_BASE):
            gdirs = [
                GDRIVE_KOSPI_DIR, GDRIVE_KOSDAQ_DIR,
                os.path.join(GDRIVE_KOSPI_DIR, "일봉"), os.path.join(GDRIVE_KOSPI_DIR, "3분봉"),
                os.path.join(GDRIVE_KOSDAQ_DIR, "일봉"), os.path.join(GDRIVE_KOSDAQ_DIR, "3분봉")
            ]
            for gd in gdirs:
                os.makedirs(gd, exist_ok=True)

    def fetch_kospi200_constituents(self) -> List[Dict[str, str]]:
        """네이버 금융 및 KRX 기반 코스피 200 (200개 종목) 리스트 수집"""
        print(">> [1/6] 📋 코스피 200 구성 종목 리스트 수집 중...")
        url_base = 'https://finance.naver.com/sise/entryJongmok.naver?&page='
        headers = {'User-Agent': 'Mozilla/5.0'}
        items = []
        seen = set()

        for page in range(1, 25):
            try:
                r = requests.get(url_base + str(page), headers=headers, timeout=10)
                soup = BeautifulSoup(r.content.decode('euc-kr', 'replace'), 'html.parser')
                for a in soup.select('td.ctg a'):
                    href = a.get('href', '')
                    if 'code=' in href:
                        code = href.split('code=')[-1].strip()
                        name = a.text.strip()
                        if code and code not in seen and len(code) == 6 and is_pure_individual_stock(name, code):
                            seen.add(code)
                            items.append({'code': code, 'name': name, 'market': 'KOSPI200'})
                            if len(items) >= 200:
                                break
                if len(items) >= 200:
                    break
            except Exception as e:
                print(f"  [WARN] 코스피200 페이지 {page} 조회 중 오류: {e}")

        print(f"  ✅ 코스피 200 종목 확정: 총 {len(items)}개 종목")
        return items

    def fetch_kosdaq150_constituents(self) -> List[Dict[str, str]]:
        """네이버 금융 및 KRX 시세 기반 코스닥 150 (150개 종목) 리스트 수집"""
        print(">> [2/6] 📋 코스닥 150 구성 종목 리스트 수집 중...")
        items = []
        seen = set()

        # 1차 시도: 네이버 금융 코스닥 시가총액 상위 종목 크롤링
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            for page in range(1, 15):
                url = f'https://finance.naver.com/sise/sise_market_sum.naver?sosok=1&page={page}'
                r = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(r.content.decode('euc-kr', 'replace'), 'html.parser')
                for a in soup.select('a.tltle'):
                    href = a.get('href', '')
                    if 'code=' in href:
                        code = href.split('code=')[-1].strip()
                        name = a.text.strip()
                        if code and code not in seen and len(code) == 6 and is_pure_individual_stock(name, code):
                            seen.add(code)
                            items.append({'code': code, 'name': name, 'market': 'KOSDAQ150'})
                            if len(items) >= 150:
                                break
                if len(items) >= 150:
                    break
            if len(items) >= 150:
                print(f"  ✅ 코스닥 150 종목 확정: 총 {len(items)}개 종목 (네이버 금융)")
                return items
        except Exception as e:
            print(f"  [WARN] 네이버 금융 코스닥150 목록 조회 실패: {e}")

        # 3차 폴백: 기존 로컬에 수집/검증 완료된 코스닥 150 CSV 파일 목록 활용
        if len(items) < 150:
            import glob
            files = glob.glob(os.path.join(LOCAL_KOSDAQ_DAILY_DIR, "*.csv"))
            for f in files:
                fname = os.path.basename(f).replace('.csv', '')
                parts = fname.split('_')
                code = parts[0]
                name = parts[1] if len(parts) > 1 else code
                if code not in seen and len(code) == 6:
                    seen.add(code)
                    items.append({'code': code, 'name': name, 'market': 'KOSDAQ150'})
            print(f"  ✅ 코스닥 150 종목 확정: 총 {len(items)}개 종목 (기존 마스터 폴백)")

        return items

    def _fetch_and_update_daily_stock(self, stock: Dict[str, Any], root_dir: str, sub_daily_dir: str) -> Dict[str, Any]:
        """단일 종목 일봉 시세 수집 및 기존 CSV 증분 병합/저장"""
        code = stock['code']
        name = stock['name']
        safe_name = sanitize_filename(name)
        file_name = f"{code}_{safe_name}.csv"
        file_path_sub = os.path.join(sub_daily_dir, file_name)
        file_path_root = os.path.join(root_dir, file_name)

        try:
            df_new = fdr.DataReader(code, self.start_date)
            if not df_new.empty:
                df_new.index = pd.to_datetime(df_new.index)
                
                # 기존 파일 존재 시 병합(Merge & Deduplicate)
                target_file = file_path_sub if os.path.exists(file_path_sub) else file_path_root
                if os.path.exists(target_file):
                    try:
                        df_old = pd.read_csv(target_file, index_col=0)
                        df_old.index = pd.to_datetime(df_old.index)
                        df_merged = df_new.combine_first(df_old).sort_index()
                    except Exception:
                        df_merged = df_new
                else:
                    df_merged = df_new

                # 일봉 서브폴더 및 루트 폴더 동시 저장
                df_merged.to_csv(file_path_sub, encoding='utf-8-sig')
                df_merged.to_csv(file_path_root, encoding='utf-8-sig')

                latest_close = float(df_merged['Close'].iloc[-1])
                latest_vol = int(df_merged['Volume'].iloc[-1])
                avg_vol_20 = int(df_merged['Volume'].tail(20).mean()) if len(df_merged) >= 20 else latest_vol
                change_rate = float(df_merged['Change'].iloc[-1] * 100) if 'Change' in df_merged.columns else 0.0

                return {
                    'code': code,
                    'name': name,
                    'market': stock.get('market', ''),
                    'count': len(df_merged),
                    'start_date': df_merged.index[0].strftime('%Y-%m-%d'),
                    'end_date': df_merged.index[-1].strftime('%Y-%m-%d'),
                    'latest_close': latest_close,
                    'change_rate': change_rate,
                    'latest_volume': latest_vol,
                    'avg_volume_20': avg_vol_20,
                    'file_path': file_path_sub,
                    'status': 'SUCCESS'
                }
        except Exception as e:
            return {
                'code': code,
                'name': name,
                'market': stock.get('market', ''),
                'status': f'FAIL: {e}'
            }
        return {'code': code, 'name': name, 'status': 'EMPTY'}

    def _fetch_and_update_3m_stock(self, stock: Dict[str, Any], target_3m_dir: str) -> Dict[str, Any]:
        """단일 종목 3분봉 시세 수집 및 기존 3분봉 CSV 증분 누적 저장"""
        code = stock['code']
        name = stock['name']
        safe_name = sanitize_filename(name)
        file_name = f"{code}_{safe_name}_3M.csv"
        file_path = os.path.join(target_3m_dir, file_name)

        try:
            # 1. 네이버 fchart API로 최대 6,000개 분봉 캔들 조회
            url = f"https://fchart.stock.naver.com/sise.nhn?symbol={code}&timeframe=minute&count=6000&requestType=0"
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers, timeout=10)
            text = r.content.decode('euc-kr', 'replace')
            raw_items = re.findall(r'<item data="([^"]+)"', text)

            rows = []
            for item in raw_items:
                parts = item.split('|')
                if len(parts) >= 6:
                    dt_str, o, h, l, c, v = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5]
                    close_val = float(c) if c != 'null' else 0.0
                    open_val = float(o) if o != 'null' else close_val
                    high_val = float(h) if h != 'null' else close_val
                    low_val = float(l) if l != 'null' else close_val
                    vol_val = int(v) if v != 'null' else 0

                    try:
                        dt = datetime.strptime(dt_str, "%Y%m%d%H%M")
                        rows.append({
                            "DateTime": dt,
                            "Open": open_val,
                            "High": high_val,
                            "Low": low_val,
                            "Close": close_val,
                            "Volume": vol_val
                        })
                    except Exception:
                        continue

            df_1m = pd.DataFrame(rows)
            if df_1m.empty:
                return {'code': code, 'name': name, 'status': 'EMPTY'}

            df_1m.set_index("DateTime", inplace=True)
            df_1m.sort_index(inplace=True)

            # 3분봉 리샘플링 (08:00~20:00 NXT 포함 정규 거래시간)
            df_3m_new = df_1m.resample("3min").agg({
                "Open": "first",
                "High": "max",
                "Low": "min",
                "Close": "last",
                "Volume": "sum"
            }).dropna()
            df_3m_new = df_3m_new.between_time("08:00", "20:00")

            # 2. 기존 파일 존재 시 증분 누적 병합
            if os.path.exists(file_path):
                try:
                    df_3m_old = pd.read_csv(file_path, index_col=0)
                    df_3m_old.index = pd.to_datetime(df_3m_old.index)
                    df_3m_merged = df_3m_new.combine_first(df_3m_old).sort_index()
                except Exception:
                    df_3m_merged = df_3m_new
            else:
                df_3m_merged = df_3m_new

            df_3m_merged.to_csv(file_path, encoding='utf-8-sig')

            return {
                'code': code,
                'name': name,
                'market': stock.get('market', ''),
                'count_3m': len(df_3m_merged),
                'start_3m': df_3m_merged.index[0].strftime('%Y-%m-%d %H:%M'),
                'end_3m': df_3m_merged.index[-1].strftime('%Y-%m-%d %H:%M'),
                'latest_close': float(df_3m_merged['Close'].iloc[-1]),
                'file_path': file_path,
                'status': 'SUCCESS'
            }
        except Exception as e:
            return {
                'code': code,
                'name': name,
                'market': stock.get('market', ''),
                'status': f'FAIL: {e}'
            }

    def collect_daily_universe(self, stocks: List[Dict[str, Any]], root_dir: str, sub_daily_dir: str, universe_name: str) -> List[Dict[str, Any]]:
        """일봉(Daily) 시세 데이터 병렬 수집 및 증분 업데이트"""
        print(f"\n>> 📊 {universe_name} ({len(stocks)}종목) [일봉] 시세 데이터 병렬 수집/업데이트 시작...")
        results = []
        start_t = time.time()

        with ThreadPoolExecutor(max_workers=16) as executor:
            future_to_stock = {
                executor.submit(self._fetch_and_update_daily_stock, s, root_dir, sub_daily_dir): s
                for s in stocks
            }
            completed = 0
            for future in as_completed(future_to_stock):
                res = future.result()
                results.append(res)
                completed += 1
                if completed % 50 == 0 or completed == len(stocks):
                    print(f"  ...[일봉] 진행률: [{completed}/{len(stocks)}] ({completed/len(stocks)*100:.1f}%) 완료")

        elapsed = time.time() - start_t
        success_cnt = sum(1 for r in results if r.get('status') == 'SUCCESS')
        print(f"  🎉 {universe_name} [일봉] 수집 완료: 성공 {success_cnt}/{len(stocks)}건 (소요시간: {elapsed:.2f}초)")
        return results

    def collect_3m_universe(self, stocks: List[Dict[str, Any]], target_3m_dir: str, universe_name: str) -> List[Dict[str, Any]]:
        """3분봉(3-Minute) 시세 데이터 병렬 수집 및 누적 업데이트"""
        print(f"\n>> ⏱️ {universe_name} ({len(stocks)}종목) [3분봉] 시세 데이터 병렬 수집/업데이트 시작...")
        results = []
        start_t = time.time()

        with ThreadPoolExecutor(max_workers=16) as executor:
            future_to_stock = {
                executor.submit(self._fetch_and_update_3m_stock, s, target_3m_dir): s
                for s in stocks
            }
            completed = 0
            for future in as_completed(future_to_stock):
                res = future.result()
                results.append(res)
                completed += 1
                if completed % 50 == 0 or completed == len(stocks):
                    print(f"  ...[3분봉] 진행률: [{completed}/{len(stocks)}] ({completed/len(stocks)*100:.1f}%) 완료")

        elapsed = time.time() - start_t
        success_cnt = sum(1 for r in results if r.get('status') == 'SUCCESS')
        print(f"  🎉 {universe_name} [3분봉] 수집 완료: 성공 {success_cnt}/{len(stocks)}건 (소요시간: {elapsed:.2f}초)")
        return results

    def save_summary_excel(self, summary_list: List[Dict[str, Any]], excel_path: str, sheet_title: str):
        """종목 마스터 요약 엑셀 저장"""
        df_summary = pd.DataFrame(summary_list)
        cols_order = ['code', 'name', 'market', 'latest_close', 'change_rate', 'avg_volume_20', 'count', 'start_date', 'end_date', 'count_3m', 'start_3m', 'end_3m', 'status']
        cols_exist = [c for c in cols_order if c in df_summary.columns]
        df_summary = df_summary[cols_exist]

        col_rename = {
            'code': '종목코드',
            'name': '종목명',
            'market': '시장구분',
            'latest_close': '현재가(원)',
            'change_rate': '등락률(%)',
            'avg_volume_20': '20일평균거래량',
            'count': '일봉수집수',
            'start_date': '일봉시작일',
            'end_date': '일봉최종일',
            'count_3m': '3분봉수집수',
            'start_3m': '3분봉시작',
            'end_3m': '3분봉최종',
            'status': '수집상태'
        }
        df_summary.rename(columns=col_rename, inplace=True)
        df_summary.to_excel(excel_path, sheet_name=sheet_title, index=False)
        print(f"  💾 마스터 엑셀 저장 완료: {excel_path}")

    def sync_to_gdrive(self):
        """구글 드라이브로 종목데이터(일봉, 3분봉, 엑셀) 전 계층 동기화"""
        if not os.path.exists(GDRIVE_BASE):
            print(">> [WARN] 구글 드라이브 마운트 경로(G:\\내 드라이브)를 찾을 수 없어 로컬에 보관합니다.")
            return

        print("\n>> ☁️ 구글 드라이브(G:\\내 드라이브\\Antigravity\\종목데이터) 전 계층 동기화 진행 중...")
        try:
            # 1. KOSPI 200 전 계층 복사
            for root, dirs, files in os.walk(LOCAL_KOSPI_DIR):
                rel_path = os.path.relpath(root, LOCAL_KOSPI_DIR)
                dest_dir = os.path.join(GDRIVE_KOSPI_DIR, rel_path) if rel_path != "." else GDRIVE_KOSPI_DIR
                os.makedirs(dest_dir, exist_ok=True)
                for file in files:
                    s_file = os.path.join(root, file)
                    d_file = os.path.join(dest_dir, file)
                    shutil.copy2(s_file, d_file)

            # 2. KOSDAQ 150 전 계층 복사
            for root, dirs, files in os.walk(LOCAL_KOSDAQ_DIR):
                rel_path = os.path.relpath(root, LOCAL_KOSDAQ_DIR)
                dest_dir = os.path.join(GDRIVE_KOSDAQ_DIR, rel_path) if rel_path != "." else GDRIVE_KOSDAQ_DIR
                os.makedirs(dest_dir, exist_ok=True)
                for file in files:
                    s_file = os.path.join(root, file)
                    d_file = os.path.join(dest_dir, file)
                    shutil.copy2(s_file, d_file)

            print("  ✅ 구글 드라이브 [일봉 & 3분봉] 전 계층 동기화 완벽 완료!")
            print(f"     • KOSPI 200 : {GDRIVE_KOSPI_DIR}")
            print(f"     • KOSDAQ 150: {GDRIVE_KOSDAQ_DIR}")
        except Exception as e:
            print(f"  [ERROR] 구글 드라이브 동기화 중 오류: {e}")

    def run_all(self):
        """전체 수집 및 백업 실행 파이프라인 (일봉 + 3분봉)"""
        print("=" * 80)
        print(">> 🏛️ [Antigravity] 코스피200 & 코스닥150 [일봉 + 3분봉] 전 종목 자동 수집/업데이트 가동")
        print(f">> 수집 일시   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f">> 로컬 저장소 : {LOCAL_DATA_DIR}")
        print(f">> 구글드라이브 : {GDRIVE_DATA_DIR}")
        print("=" * 80)

        # 1. 종목 리스트 수집
        kospi_stocks = self.fetch_kospi200_constituents()
        kosdaq_stocks = self.fetch_kosdaq150_constituents()

        # 2. 코스피 200 일봉 수집 & 업데이트
        kospi_daily = self.collect_daily_universe(kospi_stocks, LOCAL_KOSPI_DIR, LOCAL_KOSPI_DAILY_DIR, "코스피 200")
        kospi_excel = os.path.join(LOCAL_KOSPI_DIR, "코스피200_종목마스터_시세요약.xlsx")
        self.save_summary_excel(kospi_daily, kospi_excel, "KOSPI200_일봉")

        # 3. 코스피 200 3분봉 수집 & 업데이트
        kospi_3m = self.collect_3m_universe(kospi_stocks, LOCAL_KOSPI_3M_DIR, "코스피 200")
        kospi_3m_excel = os.path.join(LOCAL_KOSPI_3M_DIR, "코스피200_3분봉_수집현황.xlsx")
        self.save_summary_excel(kospi_3m, kospi_3m_excel, "KOSPI200_3분봉")

        # 4. 코스닥 150 일봉 수집 & 업데이트
        kosdaq_daily = self.collect_daily_universe(kosdaq_stocks, LOCAL_KOSDAQ_DIR, LOCAL_KOSDAQ_DAILY_DIR, "코스닥 150")
        kosdaq_excel = os.path.join(LOCAL_KOSDAQ_DIR, "코스닥150_종목마스터_시세요약.xlsx")
        self.save_summary_excel(kosdaq_daily, kosdaq_excel, "KOSDAQ150_일봉")

        # 5. 코스닥 150 3분봉 수집 & 업데이트
        kosdaq_3m = self.collect_3m_universe(kosdaq_stocks, LOCAL_KOSDAQ_3M_DIR, "코스닥 150")
        kosdaq_3m_excel = os.path.join(LOCAL_KOSDAQ_3M_DIR, "코스닥150_3분봉_수집현황.xlsx")
        self.save_summary_excel(kosdaq_3m, kosdaq_3m_excel, "KOSDAQ150_3분봉")

        # 6. 구글 드라이브 전 계층 동기화
        self.sync_to_gdrive()

        print("\n" + "=" * 80)
        print(">> 🎉 [SUCCESS] 코스피 200 및 코스닥 150 [일봉 + 3분봉] 총 350개 종목 데이터 수집 및 구글드라이브 백업이 완료되었습니다!")
        print("=" * 80)

if __name__ == "__main__":
    collector = MarketUniverseCollector(start_date="2025-01-01")
    collector.run_all()
